"""
business_rules.py
==================
Applies ALL 10 business rules defined in the assignment brief.

Row-level rules (applied to each unit in final_dataset):
  1. Overdue collection >30 days          → "Overdue Collection"
  2. Construction delay >15 days          → "Construction Delay"
  3. Outstanding amount >₹10L             → "High Outstanding"
  4. Total paid percent <50%              → "Low Collection"
  5. Milestone complete, collection pending → "Cash Flow Leakage"
  6. Missing delay reason for >15-day delay → "Missing Delay Reason [Clarification Required]"
  7. Actual cost > planned cost by >10%   → "Cost Overrun (CoC)"

Aggregate-level rules (appended as metadata):
  8. Sales < 80% AOP                      → Sales Risk flag
  9. Collections < 85% AOP               → Collections Risk flag
 10. Same project has Sales+Collections/Construction risk → Cross-Functional Escalation

All rules use deterministic calculations — no AI inference.
"""
import pandas as pd


CRORE = 10_000_000


def generate_business_rules(
    final_dataset,
    sales_result=None,
    collections_result=None,
    construction_agg=None,
):
    """
    Parameters
    ----------
    final_dataset       : pd.DataFrame  — merged dataset (sales+collections+construction)
    sales_result        : pd.DataFrame  — output from compare_sales()
    collections_result  : pd.DataFrame  — output from compare_collections()
    construction_agg    : pd.DataFrame  — raw construction data (for CoC cost overrun)
    """

    df = final_dataset.copy()

    # ── AGGREGATE FLAGS (computed once) ──────────────────────────────────
    agg_flags = {}

    if sales_result is not None and not sales_result.empty:
        sales_pct = float(sales_result["Achievement %"].iloc[0])
        agg_flags["sales_risk"]          = sales_pct < 80
        agg_flags["sales_pct"]           = sales_pct
    else:
        agg_flags["sales_risk"] = False

    if collections_result is not None and not collections_result.empty:
        col_pct = float(collections_result["Achievement %"].iloc[0])
        agg_flags["collections_risk"]    = col_pct < 85
        agg_flags["collections_pct"]     = col_pct
    else:
        agg_flags["collections_risk"] = False

    # ── ROW-LEVEL RULES ───────────────────────────────────────────────────
    business_rules      = []
    sales_risk_flags    = []
    collections_flags   = []
    construction_flags  = []

    for _, row in df.iterrows():
        risk = []

        # Rule 1: Overdue collection >30 days
        days_overdue = pd.to_numeric(row.get("Days Overdue"), errors="coerce")
        if pd.notna(days_overdue) and days_overdue > 30:
            risk.append("Overdue Collection")
            collections_flags.append(True)
        else:
            collections_flags.append(False)

        # Rule 2: Construction delay >15 days
        delay_days = pd.to_numeric(row.get("Delay Days"), errors="coerce")
        if pd.notna(delay_days) and delay_days > 15:
            risk.append("Construction Delay")
            construction_flags.append(True)
        else:
            construction_flags.append(False)

        # Rule 3: High outstanding amount
        outstanding = pd.to_numeric(row.get("Outstanding Amount"), errors="coerce")
        if pd.notna(outstanding) and outstanding > 1_000_000:
            risk.append("High Outstanding")

        # Rule 4: Low payment received (<50% of agreement value)
        paid_pct = pd.to_numeric(row.get("Total Paid Percent"), errors="coerce")
        if pd.notna(paid_pct) and paid_pct < 50:
            risk.append("Low Collection")

        # Rule 5: Cash-flow leakage — milestone 100% complete but outstanding > 0
        actual_progress = pd.to_numeric(row.get("Actual Progress %"), errors="coerce")
        if (
            pd.notna(actual_progress)
            and actual_progress >= 100
            and pd.notna(outstanding)
            and outstanding > 0
        ):
            risk.append("Cash Flow Leakage")

        # Rule 6: Construction delay >15 days but no delay reason
        delay_reason = str(row.get("Delay Reason", "")).strip()
        if (
            pd.notna(delay_days)
            and delay_days > 15
            and (delay_reason == "" or delay_reason.lower() in ["nan", "none"])
        ):
            risk.append("Missing Delay Reason [Clarification Required]")

        # Rule 7: CoC cost overrun >10%
        actual_cost  = pd.to_numeric(row.get("Actual Cost INR"),  errors="coerce")
        planned_cost = pd.to_numeric(row.get("Planned Cost INR"), errors="coerce")
        if pd.notna(actual_cost) and pd.notna(planned_cost) and planned_cost > 0:
            overrun_pct = (actual_cost - planned_cost) / planned_cost * 100
            if overrun_pct > 10:
                risk.append(f"Cost Overrun (CoC) +{overrun_pct:.1f}%")

        # Rule 8 (aggregate): Sales risk flag
        if agg_flags["sales_risk"]:
            risk.append(f"Sales Risk ({agg_flags.get('sales_pct', 0):.1f}% of AOP)")
            sales_risk_flags.append(True)
        else:
            sales_risk_flags.append(False)

        # Rule 9 (aggregate): Collections risk flag
        if agg_flags["collections_risk"]:
            risk.append(f"Collections Risk ({agg_flags.get('collections_pct', 0):.1f}% of AOP)")

        if len(risk) == 0:
            risk.append("Healthy")

        business_rules.append(", ".join(risk))

    df["Business Rule"]        = business_rules
    df["_sales_risk_flag"]     = sales_risk_flags
    df["_collections_flag"]    = collections_flags
    df["_construction_flag"]   = construction_flags

    # ── RULE 10: Cross-Functional Escalation flag ────────────────────────────
    # At project level: if a project has Sales Risk PLUS (Collections risk OR Construction delay)
    if "Project Name" in df.columns:
        project_sales_risk = (
            df.groupby("Project Name")["_sales_risk_flag"].any()
        )
        project_col_risk = (
            df.groupby("Project Name")["_collections_flag"].any()
        )
        project_con_risk = (
            df.groupby("Project Name")["_construction_flag"].any()
        )

        cross_func_projects = project_sales_risk.index[
            project_sales_risk & (project_col_risk | project_con_risk)
        ].tolist()

        if cross_func_projects:
            mask = df["Project Name"].isin(cross_func_projects)
            df.loc[mask, "Business Rule"] = df.loc[mask, "Business Rule"].apply(
                lambda x: x + ", Cross-Functional Escalation" if "Cross-Functional Escalation" not in x else x
            )

    # Drop helper columns
    df = df.drop(columns=["_sales_risk_flag", "_collections_flag", "_construction_flag"])

    return df