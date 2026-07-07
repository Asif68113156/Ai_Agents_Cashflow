"""
data_quality.py
================
Detects and reports data quality issues across all 4 input files:
  - Unit mismatches between Sales and Collections
  - Milestone mismatches between Collections and Construction
  - Missing delay reasons for delayed activities
  - Missing owners (Sales Owner, Collections Owner, Responsible Owner)
  - Conflicting customer codes between files
  - Records with null critical fields
"""
import pandas as pd
import numpy as np


def detect_data_quality_issues(sales, construction, collections, aop):
    """
    Returns a dict of DataFrames, one per quality category.
    """

    issues = []

    # ── 1. UNIT NUMBER MISMATCH (Sales vs Collections) ──────────────────────
    sales_units       = set(sales["Unit Number"].dropna().astype(str).str.strip())
    collections_units = set(collections["Unit Number"].dropna().astype(str).str.strip())

    in_sales_not_col = sales_units - collections_units
    in_col_not_sales = collections_units - sales_units

    for u in sorted(in_sales_not_col):
        issues.append({
            "Category":    "Unit Mismatch",
            "Field":       "Unit Number",
            "Value":       u,
            "Source File": "Sales (Input 1)",
            "Issue":       "Unit exists in Sales but NOT in Collections",
            "Severity":    "🟡 Medium",
            "Action":      "Verify unit status — may be a new booking without a collection demand raised yet"
        })

    for u in sorted(in_col_not_sales):
        issues.append({
            "Category":    "Unit Mismatch",
            "Field":       "Unit Number",
            "Value":       u,
            "Source File": "Collections (Input 3)",
            "Issue":       "Unit exists in Collections but NOT in Sales records",
            "Severity":    "🔴 High",
            "Action":      "Investigate — possible ghost unit or cancelled booking still in collections"
        })

    # ── 2. MILESTONE MISMATCH (Collections vs Construction) ─────────────────
    col_milestones   = set(collections["Milestone Linked"].dropna().astype(str).str.strip())
    con_milestones   = set(construction["Linked Collection Milestone"].dropna().astype(str).str.strip())

    in_col_not_con = col_milestones - con_milestones
    in_con_not_col = con_milestones - col_milestones

    for m in sorted(in_col_not_con):
        if m:
            issues.append({
                "Category":    "Milestone Mismatch",
                "Field":       "Milestone",
                "Value":       m,
                "Source File": "Collections (Input 3)",
                "Issue":       "Milestone in Collections has no matching Construction activity",
                "Severity":    "🔴 High",
                "Action":      "Construction team to verify if milestone has been defined in tracking sheet"
            })

    for m in sorted(in_con_not_col):
        if m:
            issues.append({
                "Category":    "Milestone Mismatch",
                "Field":       "Milestone",
                "Value":       m,
                "Source File": "Construction (Input 2)",
                "Issue":       "Construction milestone has no linked Collection demand",
                "Severity":    "🟡 Medium",
                "Action":      "Collections team to check if demand for this milestone has been raised"
            })

    # ── 3. MISSING DELAY REASON ──────────────────────────────────────────────
    delayed = construction[
        pd.to_numeric(construction["Delay Days"], errors="coerce") > 15
    ].copy()

    missing_reason = delayed[
        delayed["Delay Reason"].isna() |
        (delayed["Delay Reason"].astype(str).str.strip() == "") |
        (delayed["Delay Reason"].astype(str).str.lower() == "nan")
    ]

    for _, row in missing_reason.iterrows():
        issues.append({
            "Category":    "Missing Data — Delay Reason",
            "Field":       "Delay Reason",
            "Value":       row.get("Activity", "Unknown Activity"),
            "Source File": "Construction (Input 2)",
            "Issue":       f"Activity delayed {row.get('Delay Days', '?')} days but Delay Reason is MISSING",
            "Severity":    "🔴 High — Clarification Required",
            "Action":      f"Responsible Owner ({row.get('Responsible Owner', 'Unknown')}) must submit delay reason by EOD"
        })

    # ── 4. MISSING SALES OWNER ───────────────────────────────────────────────
    if "Sales Owner" in sales.columns:
        no_owner = sales[
            sales["Sales Owner"].isna() |
            (sales["Sales Owner"].astype(str).str.strip() == "")
        ]
        for _, row in no_owner.iterrows():
            issues.append({
                "Category":    "Missing Owner",
                "Field":       "Sales Owner",
                "Value":       row.get("Unit Number", "Unknown"),
                "Source File": "Sales (Input 1)",
                "Issue":       "Booking has no Sales Owner assigned",
                "Severity":    "🟡 Medium",
                "Action":      "Sales Head to assign ownership for this unit immediately"
            })

    # ── 5. MISSING COLLECTIONS OWNER ─────────────────────────────────────────
    if "Collections Owner" in collections.columns:
        no_cowner = collections[
            collections["Collections Owner"].isna() |
            (collections["Collections Owner"].astype(str).str.strip() == "")
        ]
        for _, row in no_cowner.iterrows():
            issues.append({
                "Category":    "Missing Owner",
                "Field":       "Collections Owner",
                "Value":       row.get("Unit Number", "Unknown"),
                "Source File": "Collections (Input 3)",
                "Issue":       "Collection record has no Collections Owner assigned",
                "Severity":    "🟡 Medium",
                "Action":      "Collections Head to assign an owner for follow-up"
            })

    # ── 6. MISSING RESPONSIBLE OWNER in Construction ──────────────────────────
    if "Responsible Owner" in construction.columns:
        no_resp = construction[
            construction["Responsible Owner"].isna() |
            (construction["Responsible Owner"].astype(str).str.strip() == "")
        ]
        for _, row in no_resp.iterrows():
            issues.append({
                "Category":    "Missing Owner",
                "Field":       "Responsible Owner",
                "Value":       row.get("Activity", "Unknown"),
                "Source File": "Construction (Input 2)",
                "Issue":       "Construction activity has no Responsible Owner",
                "Severity":    "🟡 Medium",
                "Action":      "Construction Head to assign ownership for accountability"
            })

    # ── 7. CASH-FLOW LEAKAGE: Milestone complete but collection not received ──
    # Find milestones where Actual Progress % == 100 but Outstanding Amount > 0
    merged_check = pd.merge(
        collections[["Unit Number", "Milestone Linked", "Amount Collected",
                      "Outstanding Amount", "Customer Name"]],
        construction[["Linked Collection Milestone", "Actual Progress %"]],
        left_on="Milestone Linked",
        right_on="Linked Collection Milestone",
        how="left"
    )

    leakage = merged_check[
        (pd.to_numeric(merged_check["Actual Progress %"], errors="coerce") >= 100) &
        (pd.to_numeric(merged_check["Outstanding Amount"], errors="coerce") > 0)
    ]

    for _, row in leakage.iterrows():
        issues.append({
            "Category":    "Cash Flow Leakage",
            "Field":       "Milestone Collection",
            "Value":       row.get("Milestone Linked", "Unknown"),
            "Source File": "Collections + Construction",
            "Issue":       (
                f"Milestone '{row.get('Milestone Linked', '?')}' is 100% complete "
                f"but ₹{pd.to_numeric(row.get('Outstanding Amount', 0), errors='coerce'):,.0f} "
                f"outstanding for {row.get('Customer Name', 'Unknown Customer')}"
            ),
            "Severity":    "🔴 High — Cash Flow Leakage",
            "Action":      "Collections team to raise demand notice and follow up for immediate collection"
        })

    # ── 8. CUSTOMER CODE MISMATCH (Sales vs Collections) ─────────────────────
    if "SAP Customer Code" in sales.columns and "SAP Customer Code" in collections.columns:
        sales_codes = sales.dropna(subset=["Unit Number", "SAP Customer Code"])
        col_codes   = collections.dropna(subset=["Unit Number", "SAP Customer Code"])

        merged_codes = pd.merge(
            sales_codes[["Unit Number", "SAP Customer Code"]],
            col_codes[["Unit Number", "SAP Customer Code"]],
            on="Unit Number",
            how="inner",
            suffixes=("_sales", "_col")
        )

        mismatch_codes = merged_codes[
            merged_codes["SAP Customer Code_sales"].astype(str).str.strip() !=
            merged_codes["SAP Customer Code_col"].astype(str).str.strip()
        ]

        for _, row in mismatch_codes.iterrows():
            issues.append({
                "Category":    "Customer Code Mismatch",
                "Field":       "SAP Customer Code",
                "Value":       row["Unit Number"],
                "Source File": "Sales vs Collections",
                "Issue":       (
                    f"Unit {row['Unit Number']}: Sales has code "
                    f"'{row['SAP Customer Code_sales']}' but Collections has "
                    f"'{row['SAP Customer Code_col']}'"
                ),
                "Severity":    "🔴 High",
                "Action":      "Finance / SAP team to reconcile and correct customer code discrepancy"
            })

    # ── 9. NEGATIVE / IMPLAUSIBLE VALUES ─────────────────────────────────────
    for col_name in ["Amount Collected", "Outstanding Amount", "Demand Amount"]:
        if col_name in collections.columns:
            neg_rows = collections[
                pd.to_numeric(collections[col_name], errors="coerce") < 0
            ]
            for _, row in neg_rows.iterrows():
                issues.append({
                    "Category":    "Data Integrity",
                    "Field":       col_name,
                    "Value":       row.get("Unit Number", "Unknown"),
                    "Source File": "Collections (Input 3)",
                    "Issue":       f"Negative value found in '{col_name}' — likely data entry error",
                    "Severity":    "🔴 High",
                    "Action":      "Finance team to verify and correct in source system"
                })

    # ── 10. AOP TARGET vs ACTUAL POPULATION SCALE MISMATCH ───────────────────
    # The AOP Collections target ("Expected Demand Value") is defined per
    # tower/milestone for the WHOLE inventory, while the Collections tracker
    # only contains records for units that are ALREADY sold. If the AOP
    # target implies a much larger sold base than Sales actually shows,
    # Achievement % against that target is not meaningful and needs a
    # human decision on how to scope it (e.g. pro-rate AOP by % sold).
    try:
        aop_collections_df = aop.get("collections", pd.DataFrame())
        if not aop_collections_df.empty and "Expected Demand Value" in aop_collections_df.columns:
            aop_target_cr = pd.to_numeric(
                aop_collections_df["Expected Demand Value"], errors="coerce"
            ).sum()
            actual_demand_cr = pd.to_numeric(
                collections.get("Demand Amount", pd.Series(dtype=float)), errors="coerce"
            ).sum() / 1e7
            units_sold = sales["Unit Number"].nunique() if "Unit Number" in sales.columns else None
            units_in_collections = (
                collections["Unit Number"].nunique() if "Unit Number" in collections.columns else None
            )

            if aop_target_cr > 0 and actual_demand_cr > 0 and (aop_target_cr / actual_demand_cr) > 5:
                issues.append({
                    "Category":    "AOP Scale Mismatch",
                    "Field":       "Expected Demand Value vs Demand Amount",
                    "Value":       "Portfolio-wide",
                    "Source File": "AOP (Input 4) vs Collections (Input 3)",
                    "Issue": (
                        f"AOP Collections target (₹{aop_target_cr:.1f} Cr) implies demand across the "
                        f"full tower/portfolio inventory, but actual demand raised in the Collections "
                        f"tracker is only ₹{actual_demand_cr:.1f} Cr for {units_in_collections} sold "
                        f"unit(s) out of {units_sold} unit(s) currently in Sales. Achievement % against "
                        f"the raw AOP figure will look artificially low because the two figures are not "
                        f"on the same population/base."
                    ),
                    "Severity":    "🔴 High — Clarification Required",
                    "Action": (
                        "Finance/Sales leadership to confirm whether AOP Collections target should be "
                        "pro-rated to the current % of inventory sold before computing Achievement %, "
                        "or whether the raw portfolio-wide target is intentional."
                    ),
                })
    except Exception:
        pass

    # ── BUILD FINAL DATAFRAME ────────────────────────────────────────────────
    issues_df = pd.DataFrame(issues)

    if issues_df.empty:
        issues_df = pd.DataFrame(columns=[
            "Category", "Field", "Value", "Source File", "Issue", "Severity", "Action"
        ])

    # Summary by category
    if not issues_df.empty:
        summary_df = issues_df.groupby(["Category", "Severity"]).size().reset_index(name="Count")
        summary_df = summary_df.sort_values("Count", ascending=False)
    else:
        summary_df = pd.DataFrame(columns=["Category", "Severity", "Count"])

    return {
        "all_issues": issues_df,
        "summary":    summary_df
    }
