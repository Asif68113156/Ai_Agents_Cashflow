"""
escalation_engine.py
=====================
Generates the escalation report at TWO levels:

1. ROW-LEVEL: each unit gets a Risk Level and Escalation owner
   based on the business rules detected.

2. PROJECT-LEVEL: cross-functional escalation where the SAME PROJECT
   has Sales Risk + Collections Risk OR Construction Risk.
   These are flagged as "Cross-Functional Escalation" and escalated
   to Site Head / CEO.

Output columns added to the dataset:
  - Risk Level   : Critical / High / Medium / Low
  - Escalation   : CEO / Site Head / Project Head / Site Manager / No Escalation
  - Escalation Reason : human-readable combination of risks
  - Suggested Action  : what the owner must do
  - Due Date          : deadline for action
"""
import pandas as pd
from datetime import date, timedelta

TODAY     = date.today()
DUE_7D    = (TODAY + timedelta(days=7)).strftime("%d %b %Y")
DUE_3D    = (TODAY + timedelta(days=3)).strftime("%d %b %Y")
TODAY_STR = TODAY.strftime("%d %b %Y")


def _determine_risk_level(rule: str) -> str:
    """Assign risk level based on set of triggered rules."""
    if "Cross-Functional Escalation" in rule:
        return "Critical"
    if (
        "High Outstanding" in rule
        and "Overdue Collection" in rule
        and "Construction Delay" in rule
    ):
        return "Critical"
    if "Cash Flow Leakage" in rule and "Overdue Collection" in rule:
        return "Critical"
    if "High Outstanding" in rule and "Overdue Collection" in rule:
        return "High"
    if "Cost Overrun" in rule and "Construction Delay" in rule:
        return "High"
    if (
        "High Outstanding" in rule
        or "Overdue Collection" in rule
        or "Construction Delay" in rule
        or "Cash Flow Leakage" in rule
        or "Cost Overrun" in rule
        or "Sales Risk" in rule
        or "Collections Risk" in rule
        or "Missing Delay Reason" in rule
    ):
        return "Medium"
    return "Low"


def _determine_escalation(risk_level: str, rule: str) -> tuple:
    """Return (Escalation Owner, Reason, Suggested Action, Due Date)."""

    if risk_level == "Critical" or "Cross-Functional Escalation" in rule:
        return (
            "CEO / Site Head",
            "Multi-domain risk: Sales + Collections/Construction failure in same project",
            "CEO to review cross-functional failure. Convene emergency project review within 48 hours.",
            DUE_3D,
        )

    if risk_level == "High":
        if "Overdue Collection" in rule and "High Outstanding" in rule:
            return (
                "Project Head",
                "High outstanding + overdue >30 days",
                "Project Head to personally call customer. Legal notice if no response in 3 days.",
                DUE_3D,
            )
        if "Cost Overrun" in rule:
            return (
                "Construction Head + Finance",
                "CoC cost overrun >10% of planned",
                "Construction Head to submit cost variance report and revised forecast to Finance.",
                DUE_7D,
            )
        return (
            "Project Head",
            "High combined risk",
            "Project Head to review and assign recovery actions within this week.",
            DUE_7D,
        )

    if risk_level == "Medium":
        if "Missing Delay Reason" in rule:
            return (
                "Site Manager",
                "Missing delay reason for delayed milestone",
                "Site Manager to collect delay reason from Responsible Owner by EOD.",
                TODAY_STR,
            )
        if "Cash Flow Leakage" in rule:
            return (
                "Collections Team",
                "Milestone complete but collection not received",
                "Collections team to raise demand notice and follow up for immediate payment.",
                DUE_3D,
            )
        if "Construction Delay" in rule:
            return (
                "Site Manager",
                "Construction milestone delayed >15 days",
                "Site Manager to expedite activity and submit recovery plan.",
                DUE_7D,
            )
        return (
            "Site Manager",
            "Moderate risk detected",
            "Site Manager to review and close within this week.",
            DUE_7D,
        )

    return ("No Escalation", "—", "No action required — continue monitoring", "—")


def generate_escalation(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds Risk Level, Escalation, Escalation Reason, Suggested Action,
    and Due Date columns to the dataset.
    """

    risk_levels          = []
    escalation_owners    = []
    escalation_reasons   = []
    suggested_actions    = []
    due_dates            = []

    for _, row in df.iterrows():
        rule = str(row.get("Business Rule", ""))

        risk  = _determine_risk_level(rule)
        owner, reason, action, due = _determine_escalation(risk, rule)

        risk_levels.append(risk)
        escalation_owners.append(owner)
        escalation_reasons.append(reason)
        suggested_actions.append(action)
        due_dates.append(due)

    df = df.copy()
    df["Risk Level"]         = risk_levels
    df["Escalation"]         = escalation_owners
    df["Escalation Reason"]  = escalation_reasons
    df["Suggested Action"]   = suggested_actions
    df["Due Date"]           = due_dates

    return df


def build_escalation_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Returns a deduplicated, formatted escalation summary table —
    leadership-ready, with only escalated items (not 'No Escalation').
    Sorted: Critical → High → Medium.
    """

    escalated = df[df["Escalation"] != "No Escalation"].copy()

    if escalated.empty:
        return pd.DataFrame(columns=[
            "Status", "Project", "Unit Number", "Customer",
            "Risk Level", "Metric Impacted", "Escalation To",
            "Escalation Reason", "Suggested Action", "Due Date"
        ])

    rag_map = {
        "Critical": "🔴 Red",
        "High":     "🔴 Red",
        "Medium":   "🟡 Amber",
        "Low":      "🟢 Green",
    }

    summary = pd.DataFrame({
        "Status":           escalated["Risk Level"].map(rag_map),
        "Project":          escalated.get("Project Name", pd.Series(["N/A"] * len(escalated))),
        "Unit Number":      escalated.get("Unit Number", pd.Series(["N/A"] * len(escalated))),
        "Customer":         escalated.get(
                                "Customer Name",
                                escalated.get(
                                    "Primary Customer: Full Name",
                                    pd.Series(["N/A"] * len(escalated))
                                )
                            ),
        "Risk Level":       escalated["Risk Level"],
        "Metric Impacted":  escalated["Business Rule"],
        "Escalation To":    escalated["Escalation"],
        "Escalation Reason": escalated["Escalation Reason"],
        "Suggested Action": escalated["Suggested Action"],
        "Due Date":         escalated["Due Date"],
    })

    # Sort by severity
    order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
    summary["_sort"] = summary["Risk Level"].map(order).fillna(4)
    summary = summary.sort_values("_sort").drop(columns=["_sort"]).reset_index(drop=True)

    return summary