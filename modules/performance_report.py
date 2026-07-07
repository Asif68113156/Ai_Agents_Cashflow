"""
performance_report.py
======================
Generates the Month-End Site Performance Report — leadership-ready,
CBE-style executive summary covering:
  - Executive KPI scorecard (RAG)
  - Sales performance
  - Collections performance
  - Construction progress
  - Cost / CoC
  - Net Cash Flow
  - Escalation summary (Red / Amber table)
  - Key decision items
  - AI recommendations
"""
import pandas as pd
from datetime import date


TODAY_STR = date.today().strftime("%d %B %Y")
CRORE     = 10_000_000


def _rag(val, green_thresh, amber_thresh, higher_is_better=True):
    """Return RAG status string."""
    if higher_is_better:
        if val >= green_thresh:
            return "🟢 Green"
        elif val >= amber_thresh:
            return "🟡 Amber"
        else:
            return "🔴 Red"
    else:
        if val <= green_thresh:
            return "🟢 Green"
        elif val <= amber_thresh:
            return "🟡 Amber"
        else:
            return "🔴 Red"


def generate_performance_report(
    final_dataset,
    sales,
    collections,
    construction,
    aop,
    sales_result,
    collections_result,
    construction_result,
    cash_flow_report,
    data_quality_report,
    action_plan,
    ai_summary,
):
    """Returns a dict of DataFrames, one per tab in the Excel report."""

    # ──────────────────────────────────────────────────────────────────────
    # 1. EXECUTIVE SCORECARD
    # ──────────────────────────────────────────────────────────────────────
    sales_pct   = float(sales_result["Achievement %"].iloc[0])   if not sales_result.empty   else 0
    col_pct     = float(collections_result["Achievement %"].iloc[0]) if not collections_result.empty else 0
    con_pct     = float(construction_result["Achievement %"].iloc[0]) if not construction_result.empty else 0

    actual_sales   = float(sales_result["Actual Booking Value"].iloc[0])     if not sales_result.empty   else 0
    target_sales   = float(sales_result["Target Booking Value"].iloc[0])     if not sales_result.empty   else 0
    actual_col     = float(collections_result["Actual Collection"].iloc[0])  if not collections_result.empty else 0
    target_col     = float(collections_result["Target Collection"].iloc[0])  if not collections_result.empty else 0
    actual_con     = float(construction_result["Actual Progress %"].iloc[0]) if not construction_result.empty else 0
    target_con     = float(construction_result["Target Progress %"].iloc[0]) if not construction_result.empty else 0

    cf_sum  = cash_flow_report.get("summary", pd.DataFrame())
    ncf_row = cf_sum[cf_sum["Metric"] == "Net Cash Flow (Actual)"]["Value (₹)"].values
    ncf_actual = float(ncf_row[0]) if len(ncf_row) > 0 else 0

    ncf_target_row = cf_sum[cf_sum["Metric"] == "Net Cash Flow Target (AOP — GPL Pre-BD NCF)"]["Value (₹)"].values
    ncf_target = float(ncf_target_row[0]) if len(ncf_target_row) > 0 else 0

    high_risk   = (final_dataset.get("Risk Level", pd.Series([])) == "High").sum()
    ceo_esc     = (final_dataset.get("Escalation", pd.Series([])) == "CEO").sum()
    total_units = final_dataset["Unit Number"].nunique() if "Unit Number" in final_dataset.columns else len(final_dataset)
    dq_issues   = len(data_quality_report.get("all_issues", pd.DataFrame()))

    overdue_df = final_dataset[
        pd.to_numeric(final_dataset.get("Days Overdue", pd.Series([])), errors="coerce") > 30
    ] if "Days Overdue" in final_dataset.columns else pd.DataFrame()

    scorecard = pd.DataFrame([
        {
            "KPI":            "Sales — Booking Value Achievement",
            "Actual":         f"₹{actual_sales:,.0f}",
            "Target (AOP)":   f"₹{target_sales:,.0f}",
            "Achievement %":  f"{sales_pct:.1f}%",
            "RAG Status":     _rag(sales_pct, 80, 60),
            "Threshold":      "Green ≥80% | Amber ≥60% | Red <60%",
            "Comment":        "Below 80% AOP — Sales Head action required" if sales_pct < 80 else "Tracking as per plan",
        },
        {
            "KPI":            "Collections — Monthly Achievement",
            "Actual":         f"₹{actual_col:,.0f}",
            "Target (AOP)":   f"₹{target_col:,.0f}",
            "Achievement %":  f"{col_pct:.1f}%",
            "RAG Status":     _rag(col_pct, 85, 65),
            "Threshold":      "Green ≥85% | Amber ≥65% | Red <65%",
            "Comment":        "Below 85% threshold — Collections Head action required" if col_pct < 85 else "On track",
        },
        {
            "KPI":            "Construction Progress Achievement",
            "Actual":         f"{actual_con:.1f}% avg progress",
            "Target (AOP)":   f"{target_con:.1f}% planned progress",
            "Achievement %":  f"{con_pct:.1f}%",
            "RAG Status":     _rag(con_pct, 90, 70),
            "Threshold":      "Green ≥90% | Amber ≥70% | Red <70%",
            "Comment":        "Behind plan" if con_pct < 90 else "On schedule",
        },
        {
            "KPI":            "Net Cash Flow (NCF)",
            "Actual":         f"₹{ncf_actual:,.0f}",
            "Target (AOP)":   f"₹{ncf_target:,.0f}",
            "Achievement %":  f"{(ncf_actual/ncf_target*100) if ncf_target else 0:.1f}%",
            "RAG Status":     "🟢 Green" if ncf_actual >= ncf_target else ("🟡 Amber" if ncf_actual > 0 else "🔴 Red"),
            "Threshold":      "Green = Positive / on target",
            "Comment":        "NCF positive" if ncf_actual > 0 else "NCF negative — review outflows",
        },
        {
            "KPI":            "High Risk Units",
            "Actual":         str(high_risk),
            "Target (AOP)":   "0",
            "Achievement %":  "N/A",
            "RAG Status":     _rag(high_risk, 0, 5, higher_is_better=False),
            "Threshold":      "Green = 0 | Amber ≤5 | Red >5",
            "Comment":        f"{high_risk} unit(s) flagged — immediate action required" if high_risk > 0 else "No high-risk units",
        },
        {
            "KPI":            "CEO-Level Escalations",
            "Actual":         str(ceo_esc),
            "Target (AOP)":   "0",
            "Achievement %":  "N/A",
            "RAG Status":     _rag(ceo_esc, 0, 2, higher_is_better=False),
            "Threshold":      "Green = 0 | Amber ≤2 | Red >2",
            "Comment":        f"{ceo_esc} item(s) require CEO review" if ceo_esc > 0 else "No critical escalations",
        },
        {
            "KPI":            "Customers Overdue >30 Days",
            "Actual":         str(len(overdue_df)),
            "Target (AOP)":   "0",
            "Achievement %":  "N/A",
            "RAG Status":     _rag(len(overdue_df), 0, 5, higher_is_better=False),
            "Threshold":      "Green = 0 | Amber ≤5 | Red >5",
            "Comment":        f"₹{pd.to_numeric(overdue_df.get('Outstanding Amount', pd.Series([])), errors='coerce').sum():,.0f} at risk" if not overdue_df.empty else "No overdue customers",
        },
        {
            "KPI":            "Data Quality Issues Flagged",
            "Actual":         str(dq_issues),
            "Target (AOP)":   "0",
            "Achievement %":  "N/A",
            "RAG Status":     _rag(dq_issues, 0, 5, higher_is_better=False),
            "Threshold":      "Green = 0 | Amber ≤5 | Red >5",
            "Comment":        "Human clarification required" if dq_issues > 0 else "Data quality clean",
        },
    ])

    # ──────────────────────────────────────────────────────────────────────
    # 2. ESCALATION SUMMARY — RED / AMBER TABLE
    # ──────────────────────────────────────────────────────────────────────
    esc_rows = []

    # Build from final_dataset Risk Level + Escalation
    for _, row in final_dataset.iterrows():
        risk  = str(row.get("Risk Level", ""))
        esc   = str(row.get("Escalation", ""))
        rules = str(row.get("Business Rule", ""))

        if risk in ("High", "Critical") or esc in ("CEO", "Project Head"):
            esc_rows.append({
                "Status":          "🔴 Red" if (risk == "Critical" or esc == "CEO") else "🟡 Amber",
                "Project":         row.get("Project Name", "N/A"),
                "Unit Number":     row.get("Unit Number", "N/A"),
                "Customer":        row.get("Customer Name", row.get("Primary Customer: Full Name", "N/A")),
                "Risk Level":      risk,
                "Metric Impacted": rules,
                "Escalation To":   esc,
                "Suggested Action": (
                    "CEO review required — multi-risk unit" if esc == "CEO"
                    else "Project Head to review and resolve overdue collections + construction delays"
                ),
                "Due Date":        date.today().strftime("%d %b %Y"),
            })

    esc_df = pd.DataFrame(esc_rows) if esc_rows else pd.DataFrame(
        columns=["Status", "Project", "Unit Number", "Customer",
                 "Risk Level", "Metric Impacted", "Escalation To",
                 "Suggested Action", "Due Date"]
    )

    # ──────────────────────────────────────────────────────────────────────
    # 3. PRODUCT MIX ANALYSIS
    # ──────────────────────────────────────────────────────────────────────
    product_mix_df = pd.DataFrame()
    if "Type" in sales.columns:
        mix = sales["Type"].value_counts().reset_index()
        mix.columns = ["Product Type", "Units Sold (Actual)"]
        aop_sales = aop.get("sales", pd.DataFrame())
        if not aop_sales.empty:
            targets = {}
            for col, label in [("1BHK Units Target", "1BHK"), ("2BHK Units Target", "2BHK"), ("3BHK Units Target", "3BHK")]:
                if col in aop_sales.columns:
                    targets[label] = pd.to_numeric(aop_sales[col], errors="coerce").sum()
            mix["AOP Target Units"] = mix["Product Type"].map(targets)
            mix["Achievement %"] = (mix["Units Sold (Actual)"] / mix["AOP Target Units"] * 100).round(1)
            mix["RAG"] = mix["Achievement %"].apply(
                lambda x: "🟢 Green" if x >= 80 else ("🟡 Amber" if x >= 60 else "🔴 Red")
                if pd.notna(x) else "⚪ No Target"
            )
        product_mix_df = mix

    # ──────────────────────────────────────────────────────────────────────
    # 4. DECISION ITEMS (from AOP)
    # ──────────────────────────────────────────────────────────────────────
    decision_df = aop.get("decision", pd.DataFrame())
    if decision_df.empty:
        decision_df = pd.DataFrame(columns=["Decision Item", "Linked Metric", "Owner", "Timeline", "Expected Impact", "Status", "Remark"])

    # ──────────────────────────────────────────────────────────────────────
    # 5. AI RECOMMENDATIONS SHEET
    # ──────────────────────────────────────────────────────────────────────
    recommendations = [
        {
            "Priority": "🔴 1",
            "Area": "Collections Recovery",
            "Recommendation": f"Activate demand notices for all {len(overdue_df)} overdue customers within 24 hours. Priority recovery of ₹{pd.to_numeric(overdue_df.get('Outstanding Amount', pd.Series([])), errors='coerce').sum():,.0f}.",
            "Expected Impact": "Reduce overdue book; improve NCF this month",
            "Owner": "Collections Head",
            "Rule Triggered": "Collections overdue >30 days",
        },
        {
            "Priority": "🔴 2",
            "Area": "Sales Acceleration",
            "Recommendation": f"Sales achievement at {sales_pct:.1f}%. Sales Head to activate channel partners and review pipeline conversion rates. Focus on shortfall product types.",
            "Expected Impact": f"Close gap of ₹{abs(float(sales_result['Gap'].iloc[0]) if 'Gap' in sales_result.columns else 0):,.0f} vs AOP",
            "Owner": "Sales Head",
            "Rule Triggered": "Sales <80% of AOP",
        },
        {
            "Priority": "🟡 3",
            "Area": "Construction Milestone Completion",
            "Recommendation": "Expedite completion of milestones where collection demands are pending. Each completed milestone unlocks a collection trigger — prioritise these to improve cash flow.",
            "Expected Impact": "Unlock deferred collections; improve NCF",
            "Owner": "Construction Head",
            "Rule Triggered": "Cash-flow leakage: milestone complete, collection pending",
        },
        {
            "Priority": "🟡 4",
            "Area": "Cost Control",
            "Recommendation": "Review all construction activities with actual costs >10% above planned. Raise change orders promptly and report to Finance for NCF reforecasting.",
            "Expected Impact": "Contain CoC within AOP; protect NCF",
            "Owner": "Construction Head + Finance",
            "Rule Triggered": "CoC overrun >10% of planned",
        },
        {
            "Priority": "🟡 5",
            "Area": "Data Quality",
            "Recommendation": f"{dq_issues} data issues flagged. All department heads must correct and resubmit data before next cycle. Missing delay reasons must be submitted by EOD.",
            "Expected Impact": "Accurate reporting; reduce manual reconciliation",
            "Owner": "All Dept Heads",
            "Rule Triggered": "Data quality checks",
        },
    ]
    recs_df = pd.DataFrame(recommendations)

    # ──────────────────────────────────────────────────────────────────────
    # 6. REPORT HEADER / METADATA
    # ──────────────────────────────────────────────────────────────────────
    metadata = pd.DataFrame([
        {"Field": "Report Title",       "Value": "Month-End Site Performance & Cash Flow Report"},
        {"Field": "Generated On",        "Value": TODAY_STR},
        {"Field": "Prepared By",         "Value": "AI Performance Analytics Engine"},
        {"Field": "Report Period",        "Value": "Current Month (as per input files)"},
        {"Field": "Total Units Tracked", "Value": str(total_units)},
        {"Field": "Files Processed",     "Value": "Sales, Construction, Collections, AOP Targets"},
        {"Field": "AI Rules Applied",    "Value": "Business Rule Engine (10 rules), Risk Detector, Escalation Engine"},
        {"Field": "Data Quality Issues", "Value": str(dq_issues)},
        {"Field": "Report Tabs",         "Value": "Cover, Scorecard, Escalation, Product Mix, Cash Flow, Action Plan, Decision Items, AI Recommendations, Data Quality"},
    ])

    return {
        "cover":        metadata,
        "scorecard":    scorecard,
        "escalation":   esc_df,
        "product_mix":  product_mix_df,
        "action_plan":  action_plan.get("all_actions", pd.DataFrame()),
        "decision":     decision_df,
        "ai_recs":      recs_df,
        "cash_flow":    cf_sum,
    }
