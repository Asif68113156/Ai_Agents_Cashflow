"""
cash_flow_engine.py
====================
Builds the Cash Flow Report:
  - Collections Inflow  : sum of Amount Collected (actual)
  - CoC Outflow         : sum of Actual Cost INR (construction actuals)
  - Other Costs         : Marketing, MOSA, Liaison, Tax, Interest (from AOP NCF sheet)
  - Net Cash Flow       : Inflow - CoC - Other Costs
  - Variance vs NCF AOP : Actual NCF minus GPL Pre-BD NCF target
  - Top Cash Flow Risks : overdue amounts, cost overruns, leakage items
"""
import pandas as pd


CRORE = 10_000_000


def build_cash_flow_report(collections, construction, aop):
    """
    Parameters
    ----------
    collections : pd.DataFrame  — raw collections tracker
    construction : pd.DataFrame — raw construction tracker
    aop : dict of pd.DataFrame  — keyed by sheet alias
    """

    # ── 1. INFLOWS ─────────────────────────────────────────────────────────
    actual_inflow = pd.to_numeric(
        collections.get("Amount Collected", pd.Series([])),
        errors="coerce"
    ).sum()

    overdue_amount = pd.to_numeric(
        collections.get("Outstanding Amount", pd.Series([])),
        errors="coerce"
    ).sum()

    # Overdue > 30 days
    overdue_30 = collections.copy()
    if "Days Overdue" in overdue_30.columns:
        overdue_30 = overdue_30[
            pd.to_numeric(overdue_30["Days Overdue"], errors="coerce") > 30
        ]
    overdue_30_amount = pd.to_numeric(
        overdue_30.get("Outstanding Amount", pd.Series([])),
        errors="coerce"
    ).sum()

    # ── 2. CONSTRUCTION OUTFLOW (CoC) ───────────────────────────────────────
    actual_coc = pd.to_numeric(
        construction.get("Actual Cost INR", pd.Series([])),
        errors="coerce"
    ).sum()

    additional_cost = pd.to_numeric(
        construction.get("Additional Cost Expected INR", pd.Series([])),
        errors="coerce"
    ).sum()

    total_coc = actual_coc + additional_cost

    # ── 3. AOP NCF TARGETS ─────────────────────────────────────────────────
    ncf_df = aop.get("ncf", pd.DataFrame())

    def _sum_col(df, col):
        if col in df.columns:
            return pd.to_numeric(df[col], errors="coerce").sum() * CRORE
        return 0.0

    aop_collection_target = _sum_col(ncf_df, "Collection Target")
    aop_coc_target        = _sum_col(ncf_df, "CoC Target")
    aop_other_costs       = sum([
        _sum_col(ncf_df, "Other Cost excl. Land & Interest"),
        _sum_col(ncf_df, "Marketing & Brokerage"),
        _sum_col(ncf_df, "MOSA"),
        _sum_col(ncf_df, "Liaison & Approvals"),
        _sum_col(ncf_df, "Income Tax"),
        _sum_col(ncf_df, "Other Outflow"),
        _sum_col(ncf_df, "Interest Cost"),
    ])
    aop_ncf_target = _sum_col(ncf_df, "GPL Pre-BD NCF")

    # ── 4. ACTUAL OTHER COSTS (use AOP as proxy — real data not in inputs) ─
    # We use AOP Other cost targets as the planned outflow for non-CoC items
    other_costs_actual = aop_other_costs  # cannot be extracted from the 4 input files

    # ── 5. NET CASH FLOW ────────────────────────────────────────────────────
    actual_ncf      = actual_inflow - total_coc - other_costs_actual
    ncf_variance    = actual_ncf - aop_ncf_target
    collection_gap  = aop_collection_target - actual_inflow

    # ── 6. CoC OVERRUN CHECK ────────────────────────────────────────────────
    coc_overrun = ((total_coc - aop_coc_target) / aop_coc_target * 100
                   if aop_coc_target != 0 else 0)
    coc_flag = "⚠️ COST OVERRUN" if coc_overrun > 10 else "✅ Within Limit"

    # ── 7. SUMMARY SHEET ───────────────────────────────────────────────────
    summary = pd.DataFrame({
        "Metric": [
            "Collections Inflow (Actual)",
            "Collections Target (AOP)",
            "Collections Gap",
            "Collection Achievement %",
            "Overdue Amount (>30 days)",
            "———",
            "CoC Outflow — Actual",
            "CoC Outflow — Additional Expected",
            "Total CoC Outflow",
            "CoC Target (AOP)",
            "CoC Overrun %",
            "CoC Status",
            "———",
            "Other Costs (AOP-based proxy)",
            "———",
            "Net Cash Flow (Actual)",
            "Net Cash Flow Target (AOP — GPL Pre-BD NCF)",
            "NCF Variance (Actual vs AOP)",
            "NCF Variance %",
        ],
        "Value (₹)": [
            round(actual_inflow, 0),
            round(aop_collection_target, 0),
            round(collection_gap, 0),
            round((actual_inflow / aop_collection_target * 100) if aop_collection_target else 0, 2),
            round(overdue_30_amount, 0),
            "—",
            round(actual_coc, 0),
            round(additional_cost, 0),
            round(total_coc, 0),
            round(aop_coc_target, 0),
            round(coc_overrun, 2),
            coc_flag,
            "—",
            round(other_costs_actual, 0),
            "—",
            round(actual_ncf, 0),
            round(aop_ncf_target, 0),
            round(ncf_variance, 0),
            round((ncf_variance / aop_ncf_target * 100) if aop_ncf_target else 0, 2),
        ],
        "RAG Status": [
            "🟢" if (actual_inflow / aop_collection_target >= 0.85 if aop_collection_target else True) else "🔴",
            "—",
            "🔴" if collection_gap > 0 else "🟢",
            "—",
            "🔴" if overdue_30_amount > 0 else "🟢",
            "—",
            "—",
            "—",
            "🔴" if coc_overrun > 10 else ("🟡" if coc_overrun > 5 else "🟢"),
            "—",
            "—",
            "—",
            "—",
            "—",
            "—",
            "🟢" if actual_ncf > 0 else "🔴",
            "—",
            "🟢" if ncf_variance >= 0 else "🔴",
            "—",
        ]
    })

    # ── 8. MONTHLY BREAKDOWN ────────────────────────────────────────────────
    monthly_df = pd.DataFrame()
    if "Month" in ncf_df.columns:
        monthly = ncf_df.copy()
        monthly["Collection Target (₹)"] = pd.to_numeric(
            monthly.get("Collection Target", 0), errors="coerce"
        ).fillna(0) * CRORE
        monthly["CoC Target (₹)"] = pd.to_numeric(
            monthly.get("CoC Target", 0), errors="coerce"
        ).fillna(0) * CRORE
        monthly["GPL Pre-BD NCF Target (₹)"] = pd.to_numeric(
            monthly.get("GPL Pre-BD NCF", 0), errors="coerce"
        ).fillna(0) * CRORE
        monthly_df = monthly[["Month", "Collection Target (₹)", "CoC Target (₹)", "GPL Pre-BD NCF Target (₹)"]].copy()

    # ── 9. TOP RISKS ────────────────────────────────────────────────────────
    risk_rows = []

    # Collections risk
    col_achieve = (actual_inflow / aop_collection_target * 100) if aop_collection_target else 0
    if col_achieve < 85:
        risk_rows.append({
            "Risk Area": "Collections",
            "Description": f"Collections achievement {col_achieve:.1f}% — below 85% AOP threshold",
            "Value (₹)": round(collection_gap, 0),
            "Severity": "🔴 High",
            "Suggested Action": "Collections Head to activate demand notices for all overdue customers this week"
        })

    if coc_overrun > 10:
        risk_rows.append({
            "Risk Area": "Cost of Construction (CoC)",
            "Description": f"CoC overrun is {coc_overrun:.1f}% above AOP target",
            "Value (₹)": round(total_coc - aop_coc_target, 0),
            "Severity": "🔴 High",
            "Suggested Action": "Construction Head to review cost drivers and raise change orders immediately"
        })

    if overdue_30_amount > 1_000_000:
        risk_rows.append({
            "Risk Area": "Overdue Collections",
            "Description": f"₹{overdue_30_amount:,.0f} outstanding for customers overdue > 30 days",
            "Value (₹)": round(overdue_30_amount, 0),
            "Severity": "🟡 Medium",
            "Suggested Action": "Collections team to issue final demand notices; escalate to legal if unresolved in 7 days"
        })

    if ncf_variance < 0:
        risk_rows.append({
            "Risk Area": "Net Cash Flow",
            "Description": f"NCF is ₹{abs(ncf_variance):,.0f} below AOP target",
            "Value (₹)": round(ncf_variance, 0),
            "Severity": "🔴 High",
            "Suggested Action": "Finance team to review NCF bridge plan; defer non-critical outflows"
        })

    risk_df = pd.DataFrame(risk_rows) if risk_rows else pd.DataFrame(
        columns=["Risk Area", "Description", "Value (₹)", "Severity", "Suggested Action"]
    )
    risk_df.loc[len(risk_df)] = {
        "Risk Area": "—",
        "Description": "Note: Other cost actuals not available in input files — AOP targets used as proxy",
        "Value (₹)": "—",
        "Severity": "ℹ️ Info",
        "Suggested Action": "Finance to provide actual Marketing, Tax, Interest outflow data for next cycle"
    }

    return {
        "summary":  summary,
        "monthly":  monthly_df,
        "top_risks": risk_df
    }
