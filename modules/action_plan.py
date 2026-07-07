"""
action_plan.py
===============
Generates an owner-wise action plan from the final merged dataset,
AOP comparison results, and risk/escalation data.

Produces a DataFrame with columns:
  Department | Action | Priority | Metric | Due Date | Owner | Supporting Data
"""
import pandas as pd
from datetime import date, timedelta

TODAY      = date.today()
DUE_7DAYS  = (TODAY + timedelta(days=7)).strftime("%d %b %Y")
DUE_3DAYS  = (TODAY + timedelta(days=3)).strftime("%d %b %Y")
DUE_TODAY  = TODAY.strftime("%d %b %Y")
DUE_14DAYS = (TODAY + timedelta(days=14)).strftime("%d %b %Y")

CRORE = 10_000_000


def generate_action_plan(
    final_dataset,
    sales,
    collections,
    construction,
    aop,
    sales_result,
    collections_result,
    construction_result,
):
    actions = []

    # ══════════════════════════════════════════════════════════════════════
    # SALES HEAD ACTIONS
    # ══════════════════════════════════════════════════════════════════════

    sales_pct = float(sales_result["Achievement %"].iloc[0]) if not sales_result.empty else 0
    sales_gap = float(sales_result["Gap"].iloc[0]) if "Gap" in sales_result.columns else 0

    if sales_pct < 80:
        actions.append({
            "Department":      "Sales",
            "Owner":           _get_sales_head(aop),
            "Priority":        "🔴 Critical",
            "Action":          (
                f"Sales achievement is only {sales_pct:.1f}% of AOP target. "
                f"Gap of ₹{abs(sales_gap):,.0f} must be recovered within this month."
            ),
            "Metric Impacted": "Booking Value vs AOP",
            "Due Date":        DUE_7DAYS,
            "Supporting Data": f"Actual: ₹{float(sales_result['Actual Booking Value'].iloc[0]):,.0f} | Target: ₹{float(sales_result['Target Booking Value'].iloc[0]):,.0f}",
        })

    # Product mix shortfall
    if "Type" in sales.columns:
        product_mix = sales["Type"].value_counts()
        aop_sales_df = aop.get("sales", pd.DataFrame())
        if not aop_sales_df.empty:
            for bhk_col, bhk_type in [
                ("1BHK Units Target", "1BHK"),
                ("2BHK Units Target", "2BHK"),
                ("3BHK Units Target", "3BHK"),
            ]:
                if bhk_col in aop_sales_df.columns:
                    target_units = pd.to_numeric(aop_sales_df[bhk_col], errors="coerce").sum()
                    # Match Type column flexibly
                    actual_units = sum(
                        v for k, v in product_mix.items()
                        if str(bhk_type[0]) in str(k)
                    )
                    if target_units > 0 and actual_units < target_units * 0.8:
                        shortfall = int(target_units - actual_units)
                        actions.append({
                            "Department":      "Sales",
                            "Owner":           _get_sales_head(aop),
                            "Priority":        "🟡 High",
                            "Action":          (
                                f"Product Mix shortfall: {bhk_type} units — "
                                f"actual {int(actual_units)} vs target {int(target_units)} "
                                f"({shortfall} units short). Realign sales focus."
                            ),
                            "Metric Impacted": f"{bhk_type} Product Mix",
                            "Due Date":        DUE_7DAYS,
                            "Supporting Data": f"Actual {bhk_type}: {int(actual_units)} | Target: {int(target_units)}",
                        })

    # No-owner bookings
    if "Sales Owner" in sales.columns:
        no_owner_count = sales["Sales Owner"].isna().sum()
        if no_owner_count > 0:
            actions.append({
                "Department":      "Sales",
                "Owner":           "Sales Head",
                "Priority":        "🟡 High",
                "Action":          f"{no_owner_count} booking(s) have no Sales Owner assigned. Assign immediately for accountability.",
                "Metric Impacted": "Ownership / Accountability",
                "Due Date":        DUE_TODAY,
                "Supporting Data": f"{no_owner_count} units without owner",
            })

    # ══════════════════════════════════════════════════════════════════════
    # COLLECTIONS TEAM ACTIONS
    # ══════════════════════════════════════════════════════════════════════

    col_pct = float(collections_result["Achievement %"].iloc[0]) if not collections_result.empty else 0
    col_gap = float(collections_result["Gap"].iloc[0]) if "Gap" in collections_result.columns else 0

    if col_pct < 85:
        actions.append({
            "Department":      "Collections",
            "Owner":           "Collections Head",
            "Priority":        "🔴 Critical",
            "Action":          (
                f"Collections at {col_pct:.1f}% of AOP — below 85% threshold. "
                f"Gap of ₹{abs(col_gap):,.0f}. Activate demand letters and personal outreach."
            ),
            "Metric Impacted": "Collections vs AOP",
            "Due Date":        DUE_3DAYS,
            "Supporting Data": f"Actual: ₹{float(collections_result['Actual Collection'].iloc[0]):,.0f} | Target: ₹{float(collections_result['Target Collection'].iloc[0]):,.0f}",
        })

    # Overdue > 30 days customers
    if "Days Overdue" in final_dataset.columns:
        overdue_df = final_dataset[
            pd.to_numeric(final_dataset["Days Overdue"], errors="coerce") > 30
        ]
        if not overdue_df.empty:
            total_overdue = pd.to_numeric(
                overdue_df.get("Outstanding Amount", pd.Series([])),
                errors="coerce"
            ).sum()
            actions.append({
                "Department":      "Collections",
                "Owner":           "Collections Head + Legal (if unresolved)",
                "Priority":        "🔴 Critical",
                "Action":          (
                    f"{len(overdue_df)} customer(s) overdue >30 days. "
                    f"₹{total_overdue:,.0f} at risk. "
                    f"Issue final demand notices. Escalate to legal if no response in 7 days."
                ),
                "Metric Impacted": "Overdue Collections",
                "Due Date":        DUE_TODAY,
                "Supporting Data": f"{len(overdue_df)} units | ₹{total_overdue:,.0f} outstanding",
            })

    # Cash-flow leakage customers
    if "Actual Progress %" in final_dataset.columns:
        leakage = final_dataset[
            (pd.to_numeric(final_dataset["Actual Progress %"], errors="coerce") >= 100) &
            (pd.to_numeric(final_dataset.get("Outstanding Amount", pd.Series([])), errors="coerce") > 0)
        ]
        if not leakage.empty:
            leak_amt = pd.to_numeric(leakage.get("Outstanding Amount", pd.Series([])), errors="coerce").sum()
            actions.append({
                "Department":      "Collections",
                "Owner":           "Collections Head",
                "Priority":        "🔴 Critical",
                "Action":          (
                    f"Cash-flow leakage: {len(leakage)} unit(s) where milestone is completed "
                    f"but collection of ₹{leak_amt:,.0f} not yet received. "
                    f"Raise demand notes and collect within 48 hours."
                ),
                "Metric Impacted": "Cash Flow Leakage",
                "Due Date":        DUE_3DAYS,
                "Supporting Data": f"{len(leakage)} milestones complete, collections pending",
            })

    # ══════════════════════════════════════════════════════════════════════
    # CONSTRUCTION TEAM ACTIONS
    # ══════════════════════════════════════════════════════════════════════

    con_pct = float(construction_result["Achievement %"].iloc[0]) if not construction_result.empty else 0
    con_gap = float(construction_result.get("Gap %", pd.Series([0])).iloc[0]) if "Gap %" in construction_result.columns else 0

    if con_pct < 90:
        actions.append({
            "Department":      "Construction",
            "Owner":           "Construction Head / Site Manager",
            "Priority":        "🟡 High",
            "Action":          (
                f"Construction progress at {con_pct:.1f}% of AOP plan. "
                f"Gap of {abs(con_gap):.1f}% behind schedule. "
                f"Identify bottlenecks and increase shift capacity."
            ),
            "Metric Impacted": "Construction Progress vs AOP",
            "Due Date":        DUE_7DAYS,
            "Supporting Data": f"Actual: {float(construction_result['Actual Progress %'].iloc[0]):.2f}% | Target: {float(construction_result['Target Progress %'].iloc[0]):.2f}%",
        })

    # Delayed milestones with no reason
    if "Delay Reason" in construction.columns and "Delay Days" in construction.columns:
        delayed = construction[pd.to_numeric(construction["Delay Days"], errors="coerce") > 15]
        missing_reason = delayed[
            delayed["Delay Reason"].isna() |
            (delayed["Delay Reason"].astype(str).str.strip().isin(["", "nan"]))
        ]
        if not missing_reason.empty:
            actions.append({
                "Department":      "Construction",
                "Owner":           "Construction Head",
                "Priority":        "🔴 Critical",
                "Action":          (
                    f"{len(missing_reason)} delayed milestone(s) have no documented Delay Reason. "
                    f"All responsible owners must submit reasons by EOD — required for leadership reporting."
                ),
                "Metric Impacted": "Data Completeness / Construction Tracking",
                "Due Date":        DUE_TODAY,
                "Supporting Data": f"Activities: {', '.join(missing_reason['Activity'].dropna().astype(str).head(5).tolist())}",
            })

    # Cost overrun
    if "Actual Cost INR" in construction.columns and "Planned Cost INR" in construction.columns:
        cons_merged = construction.copy()
        cons_merged["Actual Cost INR"]  = pd.to_numeric(cons_merged["Actual Cost INR"], errors="coerce")
        cons_merged["Planned Cost INR"] = pd.to_numeric(cons_merged["Planned Cost INR"], errors="coerce")
        overrun = cons_merged[
            cons_merged["Actual Cost INR"] > cons_merged["Planned Cost INR"] * 1.10
        ]
        if not overrun.empty:
            overrun_amt = (overrun["Actual Cost INR"] - overrun["Planned Cost INR"]).sum()
            actions.append({
                "Department":      "Construction",
                "Owner":           "Construction Head + Finance",
                "Priority":        "🔴 Critical",
                "Action":          (
                    f"Cost overrun detected in {len(overrun)} activity/milestone(s). "
                    f"Excess cost of ₹{overrun_amt:,.0f} vs plan. Review with Finance and approve change orders."
                ),
                "Metric Impacted": "Cost of Construction (CoC)",
                "Due Date":        DUE_7DAYS,
                "Supporting Data": f"{len(overrun)} activities >10% over planned cost",
            })

    # ══════════════════════════════════════════════════════════════════════
    # FINANCE / LEADERSHIP ACTIONS
    # ══════════════════════════════════════════════════════════════════════

    # Cross-functional escalations
    if "Escalation" in final_dataset.columns:
        cfo_esc = final_dataset[final_dataset["Escalation"] == "CEO"]
        if not cfo_esc.empty:
            actions.append({
                "Department":      "Leadership / CEO",
                "Owner":           "CEO / Site Head",
                "Priority":        "🔴 Critical",
                "Action":          (
                    f"{len(cfo_esc)} unit(s) have reached Critical escalation — "
                    f"Combined High Outstanding + Overdue + Construction Delay. "
                    f"CEO review required in next leadership meeting."
                ),
                "Metric Impacted": "Multi-Risk Escalation",
                "Due Date":        DUE_3DAYS,
                "Supporting Data": f"Units: {', '.join(cfo_esc['Unit Number'].dropna().astype(str).head(5).tolist())}",
            })

    # NCF review
    ncf_df = aop.get("ncf", pd.DataFrame())
    if not ncf_df.empty and "GPL Pre-BD NCF" in ncf_df.columns:
        ncf_target = pd.to_numeric(ncf_df["GPL Pre-BD NCF"], errors="coerce").sum() * CRORE
        actions.append({
            "Department":      "Finance",
            "Owner":           "Finance Head / CFO",
            "Priority":        "🟡 High",
            "Action":          (
                f"Review NCF bridge plan against AOP GPL Pre-BD NCF target of ₹{ncf_target:,.0f}. "
                f"Ensure cash headroom is adequate given collections shortfall. Defer non-critical outflows."
            ),
            "Metric Impacted": "Net Cash Flow (NCF)",
            "Due Date":        DUE_7DAYS,
            "Supporting Data": f"AOP NCF Target: ₹{ncf_target:,.0f}",
        })

    # Decision items from AOP
    decision_df = aop.get("decision", pd.DataFrame())
    if not decision_df.empty:
        pending = decision_df[
            decision_df.get("Status", pd.Series([])).astype(str).str.lower().isin(
                ["open", "pending", "in progress", ""]
            )
        ]
        for _, dec in pending.iterrows():
            actions.append({
                "Department":      "Leadership",
                "Owner":           dec.get("Owner", "Leadership"),
                "Priority":        "🟡 High",
                "Action":          (
                    f"Pending decision item: '{dec.get('Decision Item', 'Unknown')}'. "
                    f"Linked metric: {dec.get('Linked Metric', 'N/A')}. Status: {dec.get('Status', 'Unknown')}."
                ),
                "Metric Impacted": dec.get("Linked Metric", "N/A"),
                "Due Date":        str(dec.get("Timeline", DUE_14DAYS)),
                "Supporting Data": dec.get("Expected Impact", ""),
            })

    # ── RETURN ────────────────────────────────────────────────────────────
    actions_df = pd.DataFrame(actions) if actions else pd.DataFrame(columns=[
        "Department", "Owner", "Priority", "Action", "Metric Impacted", "Due Date", "Supporting Data"
    ])

    # Sort by priority
    priority_order = {
        "🔴 Critical": 0,
        "🟡 High":     1,
        "🟢 Low":      2,
    }
    if not actions_df.empty:
        actions_df["_sort"] = actions_df["Priority"].map(priority_order).fillna(3)
        actions_df = actions_df.sort_values(["Department", "_sort"]).drop(columns=["_sort"])

    # Dept summary
    dept_summary = pd.DataFrame()
    if not actions_df.empty:
        dept_summary = (
            actions_df.groupby(["Department", "Priority"])
            .size()
            .reset_index(name="Count")
            .sort_values("Count", ascending=False)
        )

    return {
        "all_actions":   actions_df,
        "dept_summary":  dept_summary,
    }


def _get_sales_head(aop):
    """Extract Sales Head name from AOP sales targets sheet."""
    sales_df = aop.get("sales", pd.DataFrame())
    if not sales_df.empty and "Sales Head" in sales_df.columns:
        head = sales_df["Sales Head"].dropna().iloc[0] if not sales_df["Sales Head"].dropna().empty else "Sales Head"
        return str(head)
    return "Sales Head"
