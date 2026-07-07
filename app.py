"""
app.py — AI Site Performance & Cash Flow Agent
================================================
Main orchestration script. Runs the complete agentic workflow:

  Stage 1 : Data Ingestion
  Stage 2 : Data Cleaning & Validation
  Stage 3 : Data Linking (cross-file merging)
  Stage 4 : AOP Comparison (Sales / Collections / Construction)
  Stage 5 : Business Rule Engine (10 rules)
  Stage 6 : Risk Detection Engine
  Stage 7 : Escalation Engine
  Stage 8 : Cash Flow Engine
  Stage 9 : Data Quality Detector
  Stage 10: Action Plan Generator
  Stage 11: Draft Communications Generator
  Stage 12: Performance Report Generator
  Stage 13: AI Summary Generator
  Stage 14: Output — Write all Excel / text reports

Human-In-The-Loop:
  - Data quality issues are flagged and saved to data_quality_report.xlsx
    for human review before leadership presentation.
  - Missing delay reasons are flagged for construction team clarification.
  - All outputs are in /output/ — no data is auto-sent anywhere.
"""

import os
import sys
import traceback
import pandas as pd

pd.set_option("display.float_format", "{:,.2f}".format)

# ── Module imports ─────────────────────────────────────────────────────────
from modules.sales_loader         import load_sales_data
from modules.construction_loader  import load_construction_data
from modules.collections_loader   import load_collections_data
from modules.aop_loader           import load_aop_data
from modules.data_cleaner         import clean_dataframe
from modules.validator            import validate

from modules.merger import (
    merge_sales_collections,
    merge_with_construction,
)

from modules.aop_compare import (
    compare_sales,
    compare_collections,
    compare_construction,
    sales_monthly_breakdown,
    collections_monthly_breakdown,
)

from modules.business_rules   import generate_business_rules
from modules.risk_detector    import detect_risk
from modules.escalation_engine import generate_escalation, build_escalation_summary
from modules.cash_flow_engine  import build_cash_flow_report
from modules.data_quality      import detect_data_quality_issues
from modules.action_plan       import generate_action_plan
from modules.draft_comms       import generate_draft_communications
from modules.performance_report import generate_performance_report
from modules.ai_summary        import generate_ai_summary


# ═══════════════════════════════════════════════════════════════════════════
# UTILITIES
# ═══════════════════════════════════════════════════════════════════════════

def section(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def step(msg):
    print(f"  ✔  {msg}")

def warn(msg):
    print(f"  ⚠  {msg}")

def save_excel_multi(filepath, sheets: dict):
    """
    Save multiple DataFrames as sheets in one Excel file.
    Every named sheet is ALWAYS written, even if empty — downstream
    readers (e.g. dashboard.py) expect these sheet names to exist.
    An empty sheet gets a single "No data for this section" row
    instead of disappearing, so pd.read_excel(sheet_name=...) never
    raises a "Worksheet not found" error.
    """
    with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
        for sheet_name, df in sheets.items():
            if not isinstance(df, pd.DataFrame) or df.empty:
                df = pd.DataFrame({"Note": ["No data available for this section in the current input files."]})
            df.to_excel(writer, sheet_name=sheet_name[:31], index=False)
    step(f"Saved: {filepath}")

def save_excel(filepath, df):
    df.to_excel(filepath, index=False)
    step(f"Saved: {filepath}")


# ═══════════════════════════════════════════════════════════════════════════
# MAIN AGENT WORKFLOW
# ═══════════════════════════════════════════════════════════════════════════

def main():

    os.makedirs("output", exist_ok=True)

    print()
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║   AI SITE PERFORMANCE & CASH FLOW AGENT — v2.0                  ║")
    print("║   Godrej Properties — Executive Analytics Engine                ║")
    print("╚══════════════════════════════════════════════════════════════════╝")

    # ─────────────────────────────────────────────────────────────────────
    # STAGE 1: DATA INGESTION
    # ─────────────────────────────────────────────────────────────────────
    section("STAGE 1 — DATA INGESTION")

    try:
        sales        = load_sales_data()
        step("Sales data loaded")
    except Exception as e:
        warn(f"Sales data load FAILED: {e}")
        sys.exit(1)

    try:
        construction = load_construction_data()
        step("Construction data loaded")
    except Exception as e:
        warn(f"Construction data load FAILED: {e}")
        sys.exit(1)

    try:
        collections  = load_collections_data()
        step("Collections data loaded")
    except Exception as e:
        warn(f"Collections data load FAILED: {e}")
        sys.exit(1)

    try:
        aop          = load_aop_data()
        step("AOP targets loaded")
    except Exception as e:
        warn(f"AOP data load FAILED: {e}")
        sys.exit(1)

    print(f"\n  Summary:")
    print(f"    Sales        : {sales.shape[0]} records, {sales.shape[1]} columns")
    print(f"    Construction : {construction.shape[0]} records, {construction.shape[1]} columns")
    print(f"    Collections  : {collections.shape[0]} records, {collections.shape[1]} columns")
    print(f"    AOP Sheets   : {list(aop.keys())}")

    # ─────────────────────────────────────────────────────────────────────
    # STAGE 2: DATA CLEANING & VALIDATION
    # ─────────────────────────────────────────────────────────────────────
    section("STAGE 2 — DATA CLEANING & VALIDATION")

    sales        = clean_dataframe(sales)
    construction = clean_dataframe(construction)
    collections  = clean_dataframe(collections)

    for sheet in aop:
        try:
            aop[sheet] = clean_dataframe(aop[sheet])
        except Exception:
            pass

    step("All datasets cleaned")

    validate(sales,        "Sales")
    validate(construction, "Construction")
    validate(collections,  "Collections")
    for k, v in aop.items():
        validate(v, f"AOP — {k}")

    # ─────────────────────────────────────────────────────────────────────
    # STAGE 3: DATA QUALITY DETECTION (before merging)
    # ─────────────────────────────────────────────────────────────────────
    section("STAGE 3 — DATA QUALITY DETECTION")

    try:
        dq_result = detect_data_quality_issues(sales, construction, collections, aop)
        dq_all    = dq_result["all_issues"]
        dq_sum    = dq_result["summary"]

        print(f"\n  {len(dq_all)} data quality issue(s) detected:")
        if not dq_sum.empty:
            print(dq_sum.to_string(index=False))

        save_excel_multi("output/data_quality_report.xlsx", {
            "All Issues":        dq_all,
            "Summary by Category": dq_sum,
        })

    except Exception as e:
        warn(f"Data quality check error: {e}")
        dq_result = {"all_issues": pd.DataFrame(), "summary": pd.DataFrame()}

    # ─────────────────────────────────────────────────────────────────────
    # STAGE 4: DATA LINKING
    # ─────────────────────────────────────────────────────────────────────
    section("STAGE 4 — DATA LINKING")

    try:
        merged_sc = merge_sales_collections(sales, collections)
        step(f"Sales + Collections merged: {merged_sc.shape}")
    except Exception as e:
        warn(f"Sales-Collections merge failed: {e}. Using sales only.")
        merged_sc = sales.copy()

    try:
        final_dataset = merge_with_construction(merged_sc, construction)
        step(f"Construction linked: {final_dataset.shape}")
    except Exception as e:
        warn(f"Construction merge failed: {e}. Using sales+collections only.")
        final_dataset = merged_sc.copy()

    # ─────────────────────────────────────────────────────────────────────
    # STAGE 5: AOP COMPARISON
    # ─────────────────────────────────────────────────────────────────────
    section("STAGE 5 — AOP COMPARISON")

    try:
        sales_result = compare_sales(sales, aop["sales"])
        sales_monthly = sales_monthly_breakdown(sales, aop["sales"])
        step(f"Sales vs AOP ({sales_result['Period Compared'].iloc[0]}): "
             f"{float(sales_result['Achievement %'].iloc[0]):.1f}% achieved")
    except Exception as e:
        warn(f"Sales AOP comparison failed: {e}")
        sales_result = pd.DataFrame()
        sales_monthly = pd.DataFrame()

    try:
        collections_result = compare_collections(collections, aop["collections"])
        collections_monthly = collections_monthly_breakdown(collections, aop["collections"])
        step(f"Collections vs AOP ({collections_result['Period Compared'].iloc[0]}): "
             f"{float(collections_result['Achievement %'].iloc[0]):.1f}% achieved")
    except Exception as e:
        warn(f"Collections AOP comparison failed: {e}")
        collections_result = pd.DataFrame()
        collections_monthly = pd.DataFrame()

    try:
        construction_result = compare_construction(construction, aop["construction"])
        step(f"Construction vs AOP: {float(construction_result['Achievement %'].iloc[0]):.1f}% achieved")
    except Exception as e:
        warn(f"Construction AOP comparison failed: {e}")
        construction_result = pd.DataFrame()

    save_excel_multi("output/sales_vs_aop.xlsx", {
        "Period Summary": sales_result,
        "Monthly Breakdown": sales_monthly,
    })
    save_excel_multi("output/collections_vs_aop.xlsx", {
        "Period Summary": collections_result,
        "Monthly Breakdown": collections_monthly,
    })
    save_excel("output/construction_vs_aop.xlsx", construction_result)

    # ─────────────────────────────────────────────────────────────────────
    # STAGE 6: BUSINESS RULE ENGINE (all 10 rules)
    # ─────────────────────────────────────────────────────────────────────
    section("STAGE 6 — BUSINESS RULE ENGINE (10 Rules)")

    try:
        final_dataset = generate_business_rules(
            final_dataset,
            sales_result=sales_result,
            collections_result=collections_result,
            construction_agg=construction,
        )
        rule_summary = final_dataset["Business Rule"].value_counts()
        print("\n  Business Rule Distribution:")
        print(rule_summary.to_string())
        save_excel("output/business_rule_report.xlsx", final_dataset)
    except Exception as e:
        warn(f"Business Rule Engine error: {e}")
        traceback.print_exc()

    # ─────────────────────────────────────────────────────────────────────
    # STAGE 7: RISK DETECTION ENGINE
    # ─────────────────────────────────────────────────────────────────────
    section("STAGE 7 — RISK DETECTION ENGINE")

    try:
        final_dataset = detect_risk(final_dataset)
        risk_summary  = final_dataset["Risk Level"].value_counts()
        print("\n  Risk Summary:")
        print(risk_summary.to_string())
        save_excel("output/risk_report.xlsx", final_dataset)
    except Exception as e:
        warn(f"Risk Detection error: {e}")
        traceback.print_exc()

    # ─────────────────────────────────────────────────────────────────────
    # STAGE 8: ESCALATION ENGINE
    # ─────────────────────────────────────────────────────────────────────
    section("STAGE 8 — ESCALATION ENGINE")

    try:
        final_dataset    = generate_escalation(final_dataset)
        escalation_summary = build_escalation_summary(final_dataset)

        esc_counts = final_dataset["Escalation"].value_counts()
        print("\n  Escalation Summary:")
        print(esc_counts.to_string())

        save_excel_multi("output/escalation_report.xlsx", {
            "Escalation Summary":   escalation_summary,
            "Full Dataset":         final_dataset,
        })
    except Exception as e:
        warn(f"Escalation Engine error: {e}")
        traceback.print_exc()

    # ─────────────────────────────────────────────────────────────────────
    # STAGE 9: CASH FLOW ENGINE
    # ─────────────────────────────────────────────────────────────────────
    section("STAGE 9 — CASH FLOW ENGINE")

    try:
        cash_flow_report = build_cash_flow_report(collections, construction, aop)
        save_excel_multi("output/cash_flow_report.xlsx", {
            "Cash Flow Summary": cash_flow_report["summary"],
            "Monthly AOP Targets": cash_flow_report["monthly"],
            "Top Cash Flow Risks": cash_flow_report["top_risks"],
        })
        step("Cash Flow Report generated")
    except Exception as e:
        warn(f"Cash Flow Engine error: {e}")
        traceback.print_exc()
        cash_flow_report = {"summary": pd.DataFrame(), "monthly": pd.DataFrame(), "top_risks": pd.DataFrame()}

    # ─────────────────────────────────────────────────────────────────────
    # STAGE 10: ACTION PLAN GENERATOR
    # ─────────────────────────────────────────────────────────────────────
    section("STAGE 10 — OWNER-WISE ACTION PLAN")

    try:
        action_plan = generate_action_plan(
            final_dataset, sales, collections, construction, aop,
            sales_result, collections_result, construction_result,
        )
        print(f"\n  {len(action_plan['all_actions'])} action item(s) generated")
        if not action_plan["dept_summary"].empty:
            print(action_plan["dept_summary"].to_string(index=False))

        save_excel_multi("output/action_plan.xlsx", {
            "Action Plan":        action_plan["all_actions"],
            "By Department":      action_plan["dept_summary"],
        })
    except Exception as e:
        warn(f"Action Plan error: {e}")
        traceback.print_exc()
        action_plan = {"all_actions": pd.DataFrame(), "dept_summary": pd.DataFrame()}

    # ─────────────────────────────────────────────────────────────────────
    # STAGE 11: AI SUMMARY
    # ─────────────────────────────────────────────────────────────────────
    section("STAGE 11 — AI SUMMARY GENERATOR")

    try:
        ai_summary_text = generate_ai_summary(
            sales_result, collections_result, construction_result, final_dataset
        )
        print("\n" + ai_summary_text)
        with open("output/ai_summary.txt", "w", encoding="utf-8") as f:
            f.write(ai_summary_text)
        step("AI Summary saved")
    except Exception as e:
        warn(f"AI Summary error: {e}")
        ai_summary_text = "AI Summary generation failed."

    # ─────────────────────────────────────────────────────────────────────
    # STAGE 12: DRAFT COMMUNICATIONS
    # ─────────────────────────────────────────────────────────────────────
    section("STAGE 12 — DRAFT COMMUNICATIONS")

    try:
        draft_comms = generate_draft_communications(
            final_dataset, sales, collections, construction, aop,
            sales_result, collections_result, construction_result,
            cash_flow_report, dq_result,
        )
        step(f"{len(draft_comms['table'])} draft communication(s) generated")

        with open("output/draft_communications.txt", "w", encoding="utf-8") as f:
            f.write(draft_comms["text"])
        save_excel("output/draft_communications.xlsx", draft_comms["table"])
    except Exception as e:
        warn(f"Draft Comms error: {e}")
        traceback.print_exc()
        draft_comms = {"text": "", "table": pd.DataFrame()}

    # ─────────────────────────────────────────────────────────────────────
    # STAGE 13: MONTH-END PERFORMANCE REPORT (Leadership-Ready)
    # ─────────────────────────────────────────────────────────────────────
    section("STAGE 13 — MONTH-END PERFORMANCE REPORT")

    try:
        perf_report = generate_performance_report(
            final_dataset, sales, collections, construction, aop,
            sales_result, collections_result, construction_result,
            cash_flow_report, dq_result, action_plan, ai_summary_text,
        )

        save_excel_multi("output/performance_report.xlsx", {
            "Cover & Metadata":      perf_report["cover"],
            "Executive Scorecard":   perf_report["scorecard"],
            "Escalation Summary":    perf_report["escalation"],
            "Product Mix Analysis":  perf_report["product_mix"],
            "Action Plan":           perf_report["action_plan"],
            "Decision Items":        perf_report["decision"],
            "AI Recommendations":    perf_report["ai_recs"],
            "Cash Flow Summary":     perf_report["cash_flow"],
        })
        step("Month-End Performance Report generated")
    except Exception as e:
        warn(f"Performance Report error: {e}")
        traceback.print_exc()

    # ─────────────────────────────────────────────────────────────────────
    # STAGE 14: FINAL MERGED DATASET
    # ─────────────────────────────────────────────────────────────────────
    section("STAGE 14 — FINAL MERGED DATASET")
    save_excel("output/final_merged_dataset.xlsx", final_dataset)

    # ─────────────────────────────────────────────────────────────────────
    # COMPLETION SUMMARY
    # ─────────────────────────────────────────────────────────────────────
    section("AGENT COMPLETION — ALL OUTPUTS GENERATED")

    outputs = [
        ("output/final_merged_dataset.xlsx",  "Master dataset (all linked data)"),
        ("output/sales_vs_aop.xlsx",          "Sales vs AOP comparison"),
        ("output/collections_vs_aop.xlsx",    "Collections vs AOP comparison"),
        ("output/construction_vs_aop.xlsx",   "Construction vs AOP comparison"),
        ("output/business_rule_report.xlsx",  "Business Rule Engine output (10 rules)"),
        ("output/risk_report.xlsx",           "Risk Detection report"),
        ("output/escalation_report.xlsx",     "Escalation Summary (Red/Amber)"),
        ("output/cash_flow_report.xlsx",      "Cash Flow Report (inflows/outflows/NCF)"),
        ("output/data_quality_report.xlsx",   "Data Quality Report [Human Review]"),
        ("output/action_plan.xlsx",           "Owner-wise Action Plan"),
        ("output/draft_communications.xlsx",  "Draft Communications (table)"),
        ("output/draft_communications.txt",   "Draft Communications (email text)"),
        ("output/performance_report.xlsx",    "Month-End Leadership Performance Report"),
        ("output/ai_summary.txt",             "AI Management Summary"),
    ]

    print()
    for path, desc in outputs:
        exists = "✔" if os.path.exists(path) else "✗ MISSING"
        print(f"  {exists}  {path:<42}  {desc}")

    print("\n")
    print("  ✅ All stages complete. Open output/ folder to review all reports.")
    print("  ⚠  Review data_quality_report.xlsx before presenting to leadership.")
    print()


if __name__ == "__main__":
    main()