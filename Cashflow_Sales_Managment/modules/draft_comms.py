"""
draft_comms.py
===============
Generates draft email / Microsoft Teams messages for each major risk category.

Output:  output/draft_communications.txt
         (human-readable, ready to copy-paste / adapt)
"""
import pandas as pd
from datetime import date


TODAY_STR = date.today().strftime("%d %B %Y")


def generate_draft_communications(
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
):
    """
    Returns a single string with all draft comms, clearly separated.
    Also returns a list of dicts for Excel output.
    """

    comms = []

    # ══════════════════════════════════════════════════════════════════════
    # EXTRACT KEY METRICS
    # ══════════════════════════════════════════════════════════════════════
    sales_pct   = float(sales_result["Achievement %"].iloc[0])   if not sales_result.empty   else 0
    col_pct     = float(collections_result["Achievement %"].iloc[0]) if not collections_result.empty else 0
    con_pct     = float(construction_result["Achievement %"].iloc[0]) if not construction_result.empty else 0

    actual_sales      = float(sales_result["Actual Booking Value"].iloc[0])     if not sales_result.empty   else 0
    target_sales      = float(sales_result["Target Booking Value"].iloc[0])     if not sales_result.empty   else 0
    actual_col        = float(collections_result["Actual Collection"].iloc[0])  if not collections_result.empty else 0
    target_col        = float(collections_result["Target Collection"].iloc[0])  if not collections_result.empty else 0
    actual_con        = float(construction_result["Actual Progress %"].iloc[0]) if not construction_result.empty else 0
    target_con        = float(construction_result["Target Progress %"].iloc[0]) if not construction_result.empty else 0

    overdue_df = final_dataset[
        pd.to_numeric(final_dataset.get("Days Overdue", pd.Series([])), errors="coerce") > 30
    ] if "Days Overdue" in final_dataset.columns else pd.DataFrame()

    overdue_amount = pd.to_numeric(
        overdue_df.get("Outstanding Amount", pd.Series([])), errors="coerce"
    ).sum() if not overdue_df.empty else 0

    high_risk_count = (final_dataset.get("Risk Level", pd.Series([])) == "High").sum()
    ceo_esc_count   = (final_dataset.get("Escalation", pd.Series([])) == "CEO").sum()

    dq_summary = data_quality_report.get("summary", pd.DataFrame())
    dq_count   = len(data_quality_report.get("all_issues", pd.DataFrame()))

    cf_summary = cash_flow_report.get("summary", pd.DataFrame())
    ncf_row    = cf_summary[cf_summary["Metric"] == "Net Cash Flow (Actual)"]["Value (₹)"].values
    ncf_actual = float(ncf_row[0]) if len(ncf_row) > 0 else 0

    # ══════════════════════════════════════════════════════════════════════
    # 1. SITE LEADERSHIP — MONTHLY PERFORMANCE SUMMARY
    # ══════════════════════════════════════════════════════════════════════
    sales_rag = "✅ ON TRACK" if sales_pct >= 80 else ("⚠️ AT RISK" if sales_pct >= 60 else "🔴 CRITICAL")
    col_rag   = "✅ ON TRACK" if col_pct   >= 85 else ("⚠️ AT RISK" if col_pct   >= 65 else "🔴 CRITICAL")
    con_rag   = "✅ ON TRACK" if con_pct   >= 90 else ("⚠️ AT RISK" if con_pct   >= 70 else "🔴 CRITICAL")

    comm1 = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DRAFT COMMUNICATION #1
TO:      Site Leadership Team / CBE Review
FROM:    [Your Name] — AI Performance Analytics
SUBJECT: Month-End Site Performance & Cash Flow Review — {TODAY_STR}
CHANNEL: Email / Teams
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Hi Team,

Please find below the AI-generated month-end performance summary for your review.

──────────────────────────────────────
EXECUTIVE SUMMARY — {TODAY_STR}
──────────────────────────────────────

SALES           {sales_rag}
  Actual     : ₹{actual_sales:>16,.0f}
  AOP Target : ₹{target_sales:>16,.0f}
  Achievement: {sales_pct:.1f}%

COLLECTIONS     {col_rag}
  Actual     : ₹{actual_col:>16,.0f}
  AOP Target : ₹{target_col:>16,.0f}
  Achievement: {col_pct:.1f}%

CONSTRUCTION    {con_rag}
  Actual Avg Progress : {actual_con:.1f}%
  AOP Plan Progress   : {target_con:.1f}%
  Achievement         : {con_pct:.1f}%

NET CASH FLOW
  Actual NCF : ₹{ncf_actual:>16,.0f}

──────────────────────────────────────
KEY RISKS
──────────────────────────────────────
- {high_risk_count} unit(s) flagged as High Risk
- {len(overdue_df)} customer(s) overdue >30 days | ₹{overdue_amount:,.0f} at risk
- {ceo_esc_count} item(s) require CEO-level escalation
- {dq_count} data quality issue(s) flagged for human review

All detailed reports (cash flow, action plan, data quality, escalation summary) are attached.

Please review and confirm actions before the next CBE review session.

Regards,
[Your Name]
[Your Designation] — Godrej Properties
""".strip()

    comms.append({
        "Communication #": 1,
        "To":              "Site Leadership Team / CBE Review",
        "Subject":         f"Month-End Site Performance & Cash Flow Review — {TODAY_STR}",
        "Channel":         "Email",
        "Draft":           comm1
    })

    # ══════════════════════════════════════════════════════════════════════
    # 2. SALES HEAD — BOOKING PERFORMANCE ALERT
    # ══════════════════════════════════════════════════════════════════════
    if sales_pct < 80:
        comm2 = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DRAFT COMMUNICATION #2
TO:      Sales Head
FROM:    [Your Name]
SUBJECT: 🔴 URGENT — Sales Booking Shortfall vs AOP — Action Required
CHANNEL: Email + Teams
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Hi [Sales Head Name],

This is a formal alert regarding this month's booking performance:

  Actual Booking Value : ₹{actual_sales:,.0f}
  AOP Target           : ₹{target_sales:,.0f}
  Achievement          : {sales_pct:.1f}%  ← BELOW 80% THRESHOLD

REQUIRED ACTIONS:
  1. Share a revised weekly booking forecast by {date.today().strftime('%d %b %Y')}
  2. Identify high-potential leads and activate channel partner outreach
  3. Resolve all {int(sales['Sales Owner'].isna().sum()) if 'Sales Owner' in sales.columns else 'N/A'} units without an assigned Sales Owner
  4. Submit product-mix recovery plan (1BHK / 2BHK / 3BHK split) by this week's review

This will be flagged in the leadership CBE deck if not addressed.

Please confirm receipt and share updated numbers by EOD.

Regards,
[Your Name]
""".strip()

        comms.append({
            "Communication #": 2,
            "To":              "Sales Head",
            "Subject":         "🔴 URGENT — Sales Booking Shortfall vs AOP — Action Required",
            "Channel":         "Email + Teams",
            "Draft":           comm2
        })

    # ══════════════════════════════════════════════════════════════════════
    # 3. COLLECTIONS TEAM — OVERDUE RECOVERY
    # ══════════════════════════════════════════════════════════════════════
    if not overdue_df.empty:
        top_overdue = overdue_df.nlargest(
            min(5, len(overdue_df)),
            "Outstanding Amount"
        )[["Customer Name", "Unit Number", "Outstanding Amount", "Days Overdue"]].to_string(index=False) \
            if "Customer Name" in overdue_df.columns else f"{len(overdue_df)} customers"

        comm3 = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DRAFT COMMUNICATION #3
TO:      Collections Head + Collections Team
FROM:    [Your Name]
SUBJECT: 🔴 Overdue Collections — {len(overdue_df)} Customers Require Immediate Action
CHANNEL: Email + WhatsApp (team)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Hi Collections Team,

The AI analysis has flagged {len(overdue_df)} customers with overdue payments >30 days:
  Total Outstanding Amount at Risk: ₹{overdue_amount:,.0f}

TOP PRIORITY CUSTOMERS:
{top_overdue}

REQUIRED ACTIONS — IMMEDIATE:
  1. Issue formal demand notices to all overdue customers TODAY
  2. Personal call by Collections Owner within 24 hours
  3. If no response in 7 days → escalate to Legal + Site Head
  4. Update collection status in the tracker by EOD for leadership review

Monthly collections achievement is currently {col_pct:.1f}% — recovery of overdue amounts
is critical to meeting the {85}% minimum threshold.

Regards,
[Your Name]
""".strip()

        comms.append({
            "Communication #": 3,
            "To":              "Collections Head + Collections Team",
            "Subject":         f"🔴 Overdue Collections — {len(overdue_df)} Customers Require Immediate Action",
            "Channel":         "Email + WhatsApp",
            "Draft":           comm3
        })

    # ══════════════════════════════════════════════════════════════════════
    # 4. CONSTRUCTION HEAD — DELAYED MILESTONES
    # ══════════════════════════════════════════════════════════════════════
    if "Delay Days" in construction.columns:
        delayed = construction[pd.to_numeric(construction["Delay Days"], errors="coerce") > 15]
        if not delayed.empty:
            delay_list = delayed[["Activity", "Delay Days", "Responsible Owner"]].head(5).to_string(index=False) \
                if "Activity" in delayed.columns else f"{len(delayed)} activities delayed"

            comm4 = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DRAFT COMMUNICATION #4
TO:      Construction Head + Site Manager
FROM:    [Your Name]
SUBJECT: ⚠️ Construction Delay Alert — {len(delayed)} Milestone(s) Behind Schedule
CHANNEL: Teams + Email
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Hi [Construction Head Name],

AI analysis has flagged the following construction delays (>15 days behind plan):

DELAYED MILESTONES:
{delay_list}

These delays directly impact:
  - Customer milestone-linked collection demands
  - Project cash flow (estimated collection trigger delayed)
  - Leadership CBE reporting thresholds

REQUIRED ACTIONS:
  1. Submit delay reason for ALL flagged milestones by EOD TODAY (mandatory for leadership report)
  2. Provide revised completion dates and recovery plan by {date.today().strftime('%d %b %Y')}
  3. Identify if any additional cost will be incurred (budget vs actual)
  4. Confirm if any construction milestones are 100% complete — collections team needs to trigger demands

Please expedite this to avoid cross-functional escalation to CEO.

Regards,
[Your Name]
""".strip()

            comms.append({
                "Communication #": 4,
                "To":              "Construction Head + Site Manager",
                "Subject":         f"⚠️ Construction Delay Alert — {len(delayed)} Milestone(s) Behind Schedule",
                "Channel":         "Teams + Email",
                "Draft":           comm4
            })

    # ══════════════════════════════════════════════════════════════════════
    # 5. DATA QUALITY — CLARIFICATION REQUEST
    # ══════════════════════════════════════════════════════════════════════
    if dq_count > 0:
        comm5 = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DRAFT COMMUNICATION #5
TO:      All Department Heads (Sales, Collections, Construction, Finance)
FROM:    [Your Name]
SUBJECT: ⚠️ Data Clarification Required — {dq_count} Issues Flagged by AI System
CHANNEL: Email
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Hi All,

The AI data validation engine has flagged {dq_count} data quality issues that require
human review and correction before the next leadership report.

Please refer to the attached **Data Quality Report** (data_quality_report.xlsx) for the
complete list, sorted by severity.

Key issue types identified:
{dq_summary.to_string(index=False) if not dq_summary.empty else 'See attached report'}

ACTION REQUIRED:
  - Each department head to review issues in their area
  - Correct source data in the respective systems
  - Confirm corrections to [Your Name] by {date.today().strftime('%d %b %Y')}

Data integrity is essential for accurate leadership reporting. Uncorrected items
will appear as "Clarification Required" in the CBE deck.

Regards,
[Your Name]
""".strip()

        comms.append({
            "Communication #": 5,
            "To":              "All Department Heads",
            "Subject":         f"⚠️ Data Clarification Required — {dq_count} Issues Flagged",
            "Channel":         "Email",
            "Draft":           comm5
        })

    # ══════════════════════════════════════════════════════════════════════
    # BUILD OUTPUTS
    # ══════════════════════════════════════════════════════════════════════
    full_text = "\n\n".join([c["Draft"] for c in comms])
    comms_df  = pd.DataFrame(comms)

    return {
        "text":     full_text,
        "table":    comms_df,
    }
