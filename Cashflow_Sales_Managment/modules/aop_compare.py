import pandas as pd

CRORE = 10000000  # 1 Crore = 10,000,000


# =====================================================
# HELPERS
# =====================================================
def _parse_date_column(series):
    """
    Robust date parser. Handles:
      - normal datetime-like strings/timestamps
      - raw Excel serial numbers (e.g. 46080.0) that pandas
        sometimes leaves as plain floats when read from certain exports

    IMPORTANT: pd.to_datetime() on a numeric/float column does NOT raise
    or return NaT — it silently reinterprets the number as a Unix epoch
    timestamp (giving 1970-ish dates), so numeric columns must be routed
    to the Excel-serial converter BEFORE calling pd.to_datetime at all.
    """
    if pd.api.types.is_numeric_dtype(series):
        numeric_vals = pd.to_numeric(series, errors="coerce")
        return pd.to_datetime("1899-12-30") + pd.to_timedelta(numeric_vals, unit="D")

    parsed = pd.to_datetime(series, errors="coerce")

    # Object-dtype columns can still contain numeric-looking strings
    # (e.g. "46080") representing Excel serials -> catch those too.
    still_missing = parsed.isna()
    numeric_vals = pd.to_numeric(series, errors="coerce")
    serial_mask = still_missing & numeric_vals.notna()

    if serial_mask.any():
        converted = pd.to_datetime("1899-12-30") + pd.to_timedelta(
            numeric_vals[serial_mask], unit="D"
        )
        parsed.loc[serial_mask] = converted

    return parsed


def _period_window(aop_df, month_col="Month"):
    """Return the set of Year-Month periods covered by an AOP target sheet."""
    months = pd.to_datetime(aop_df[month_col], errors="coerce").dt.to_period("M")
    return set(months.dropna())


def _restrict_to_window(actual_df, date_col, window):
    """Keep only actual rows whose date falls inside the AOP's target period."""
    actual_df = actual_df.copy()
    parsed_dates = _parse_date_column(actual_df[date_col])
    actual_df["_Period"] = parsed_dates.dt.to_period("M")
    in_window = actual_df[actual_df["_Period"].isin(window)]
    return in_window, actual_df["_Period"]


def _period_label(window):
    if not window:
        return "N/A"
    ordered = sorted(window)
    if len(ordered) == 1:
        return str(ordered[0])
    return f"{ordered[0]} to {ordered[-1]} ({len(ordered)} months)"


# =====================================================
# SALES vs AOP SALES
# =====================================================
def compare_sales(sales_actual, aop_sales, date_col="Booking Date"):
    """
    Compares actual sales bookings against the AOP sales target,
    restricted to the same months the AOP target actually covers.
    Without this restriction, a multi-month actual file gets compared
    against a fixed-quarter target (or vice-versa), which produces
    meaningless achievement percentages.
    """
    window = _period_window(aop_sales, "Month")
    actual_in_window, _ = _restrict_to_window(sales_actual, date_col, window)

    actual_booking = pd.to_numeric(
        actual_in_window["Total Agreement Amount"], errors="coerce"
    ).sum()

    # Convert target from Crores to Rupees
    target_booking = (
        pd.to_numeric(aop_sales["Booking Value Target"], errors="coerce").sum()
        * CRORE
    )

    achievement = (actual_booking / target_booking) * 100 if target_booking != 0 else 0
    gap = target_booking - actual_booking

    result = pd.DataFrame({
        "Period Compared":      [_period_label(window)],
        "Actual Booking Value": [round(actual_booking, 2)],
        "Target Booking Value": [round(target_booking, 2)],
        "Achievement %":        [round(achievement, 2)],
        "Gap":                  [round(gap, 2)],
        "Records In Period":    [len(actual_in_window)],
        "Records Excluded (Outside AOP Period)": [len(sales_actual) - len(actual_in_window)],
    })

    return result


def sales_monthly_breakdown(sales_actual, aop_sales, date_col="Booking Date"):
    """Month-by-month Actual vs Target booking value (for the rule
    'if MONTHLY booking value is below 80% of AOP target')."""
    sales_actual = sales_actual.copy()
    sales_actual["_Period"] = _parse_date_column(sales_actual[date_col]).dt.to_period("M")
    aop_sales = aop_sales.copy()
    aop_sales["_Period"] = pd.to_datetime(aop_sales["Month"], errors="coerce").dt.to_period("M")

    monthly_actual = (
        sales_actual.groupby("_Period")["Total Agreement Amount"]
        .apply(lambda s: pd.to_numeric(s, errors="coerce").sum())
    )
    monthly_target = (
        aop_sales.groupby("_Period")["Booking Value Target"]
        .apply(lambda s: pd.to_numeric(s, errors="coerce").sum() * CRORE)
    )

    monthly = pd.DataFrame({
        "Actual Booking Value": monthly_actual,
        "Target Booking Value": monthly_target,
    }).fillna(0)
    monthly = monthly.loc[monthly_target.index.union(monthly.index[monthly["Target Booking Value"] > 0])] \
        if not monthly.empty else monthly
    monthly["Achievement %"] = monthly.apply(
        lambda r: round((r["Actual Booking Value"] / r["Target Booking Value"]) * 100, 2)
        if r["Target Booking Value"] else 0,
        axis=1,
    )
    monthly["Gap"] = monthly["Target Booking Value"] - monthly["Actual Booking Value"]
    monthly["Sales Risk (<80%)"] = monthly["Achievement %"] < 80
    monthly = monthly.reset_index().rename(columns={"_Period": "Month"})
    monthly["Month"] = monthly["Month"].astype(str)
    return monthly.sort_values("Month")


# =====================================================
# COLLECTIONS vs AOP COLLECTIONS
# =====================================================
def compare_collections(collections_actual, aop_collections, date_col="Due Date"):
    """
    Compares actual collections against the AOP collections target,
    restricted to the same months the AOP target covers. 'Due Date' is
    used (rather than Demand Raised Date) because it represents when the
    collection was expected — the same timing basis as the AOP target.
    """
    window = _period_window(aop_collections, "Month")
    actual_in_window, _ = _restrict_to_window(collections_actual, date_col, window)

    actual_collection = pd.to_numeric(
        actual_in_window["Amount Collected"], errors="coerce"
    ).sum()

    # Convert target from Crores to Rupees
    target_collection = (
        pd.to_numeric(aop_collections["Expected Demand Value"], errors="coerce").sum()
        * CRORE
    )

    achievement = (
        (actual_collection / target_collection) * 100 if target_collection != 0 else 0
    )
    gap = target_collection - actual_collection

    result = pd.DataFrame({
        "Period Compared":       [_period_label(window)],
        "Actual Collection":     [round(actual_collection, 2)],
        "Target Collection":     [round(target_collection, 2)],
        "Achievement %":         [round(achievement, 2)],
        "Gap":                   [round(gap, 2)],
        "Records In Period":     [len(actual_in_window)],
        "Records Excluded (Outside AOP Period)": [len(collections_actual) - len(actual_in_window)],
    })

    return result


def collections_monthly_breakdown(collections_actual, aop_collections, date_col="Due Date"):
    """Month-by-month Actual vs Target collections (for the rule
    'if MONTHLY collections are below 85% of target')."""
    collections_actual = collections_actual.copy()
    collections_actual["_Period"] = pd.to_datetime(
        collections_actual[date_col], errors="coerce"
    ).dt.to_period("M")
    aop_collections = aop_collections.copy()
    aop_collections["_Period"] = pd.to_datetime(
        aop_collections["Month"], errors="coerce"
    ).dt.to_period("M")

    monthly_actual = (
        collections_actual.groupby("_Period")["Amount Collected"]
        .apply(lambda s: pd.to_numeric(s, errors="coerce").sum())
    )
    monthly_target = (
        aop_collections.groupby("_Period")["Expected Demand Value"]
        .apply(lambda s: pd.to_numeric(s, errors="coerce").sum() * CRORE)
    )

    monthly = pd.DataFrame({
        "Actual Collection": monthly_actual,
        "Target Collection": monthly_target,
    }).fillna(0)
    monthly["Achievement %"] = monthly.apply(
        lambda r: round((r["Actual Collection"] / r["Target Collection"]) * 100, 2)
        if r["Target Collection"] else 0,
        axis=1,
    )
    monthly["Gap"] = monthly["Target Collection"] - monthly["Actual Collection"]
    monthly["Collections Risk (<85%)"] = monthly["Achievement %"] < 85
    monthly = monthly.reset_index().rename(columns={"_Period": "Month"})
    monthly["Month"] = monthly["Month"].astype(str)
    return monthly.sort_values("Month")


# =====================================================
# CONSTRUCTION vs AOP CONSTRUCTION
# =====================================================
def compare_construction(construction_actual, aop_construction):
    """
    Progress % is a point-in-time / cumulative metric (not a monthly sum),
    so no period restriction is applied here — comparing the current mean
    actual progress against the mean planned progress across all tracked
    milestones is the correct basis for this metric.
    """
    construction_actual = construction_actual.copy()
    aop_construction = aop_construction.copy()

    construction_actual["Actual Progress %"] = pd.to_numeric(
        construction_actual["Actual Progress %"],
        errors="coerce"
    )

    aop_construction["Planned Progress %"] = pd.to_numeric(
        aop_construction["Planned Progress %"],
        errors="coerce"
    )

    actual_progress = construction_actual["Actual Progress %"].mean()

    target_progress = aop_construction["Planned Progress %"].mean()

    achievement = (
        (actual_progress / target_progress) * 100
        if target_progress != 0 else 0
    )

    gap = target_progress - actual_progress

    result = pd.DataFrame({
        "Actual Progress %": [round(actual_progress, 2)],
        "Target Progress %": [round(target_progress, 2)],
        "Achievement %": [round(achievement, 2)],
        "Gap %": [round(gap, 2)]
    })

    return result
