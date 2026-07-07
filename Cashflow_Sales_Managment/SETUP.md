# 🏢 AI Site Performance & Cash Flow Agent
### Godrej Properties — Executive Analytics Platform

> An **agentic AI workflow** that automates the monthly site performance review across Sales, Collections, Construction, Cost and Cash Flow — generating **leadership-ready reports** directly from raw Excel inputs.

---

## ⚡ How to Run

### Step 1 — Install Dependencies
```bash
pip install pandas openpyxl streamlit plotly
```

### Step 2 — Run the Agent Pipeline (generates all outputs)
```bash
python app.py
```

### Step 3 — Launch the Executive Dashboard
```bash
python -m streamlit run dashboard.py
```
Open: **http://localhost:8501**

---

## 📁 Project Structure

```
Goorej_properties/
│
├── app.py                          ← Main orchestration (run this first)
├── dashboard.py                    ← Streamlit executive dashboard
│
├── data/                           ← Input Excel files (do not modify)
│   ├── AI_Assignment_Input_1_Sales_SANITIZED.xlsx
│   ├── AI_Assignment_Input_2_Construction_Tracking.xlsx
│   ├── AI_Assignment_Input_3_Collections_Tracker.xlsx
│   └── AI_Assignment_Input_4_AOP_Targets.xlsx
│
├── modules/                        ← AI Agent modules
│   ├── sales_loader.py             ← Load sales data
│   ├── construction_loader.py      ← Load construction data
│   ├── collections_loader.py       ← Load collections data
│   ├── aop_loader.py               ← Load AOP targets (6 sheets)
│   ├── data_cleaner.py             ← Remove nulls/dupes/unnamed cols
│   ├── validator.py                ← Dataset shape validation
│   ├── data_quality.py             ← Cross-file mismatch detection
│   ├── merger.py                   ← Sales <-> Collections <-> Construction
│   ├── aop_compare.py              ← Actual vs AOP target comparisons
│   ├── business_rules.py           ← All 10 business rules
│   ├── risk_detector.py            ← Risk level classification
│   ├── escalation_engine.py        ← Escalation routing + summary
│   ├── cash_flow_engine.py         ← NCF, CoC, inflows, variances
│   ├── action_plan.py              ← Owner-wise action plan
│   ├── ai_summary.py               ← AI text summary
│   ├── draft_comms.py              ← Draft emails/Teams messages
│   └── performance_report.py       ← Leadership CBE-style report
│
└── output/                         ← All generated reports
    ├── performance_report.xlsx      ← MAIN LEADERSHIP REPORT
    ├── cash_flow_report.xlsx        ← NCF, inflows, outflows, top risks
    ├── escalation_report.xlsx       ← Red/Amber table with owners + actions
    ├── action_plan.xlsx             ← Owner-wise action plan by department
    ├── draft_communications.xlsx    ← Draft emails (table)
    ├── draft_communications.txt     ← Draft emails (copy-paste text)
    ├── data_quality_report.xlsx     ← Human review: mismatches, gaps
    ├── final_merged_dataset.xlsx    ← Master linked dataset
    ├── business_rule_report.xlsx    ← Business rules applied per unit
    ├── risk_report.xlsx             ← Risk level per unit
    ├── sales_vs_aop.xlsx
    ├── collections_vs_aop.xlsx
    ├── construction_vs_aop.xlsx
    └── ai_summary.txt
```

---

## 🔄 Pipeline Architecture — 13 Stages

```
4 EXCEL INPUT FILES
        |
        v
Stage  1: DATA INGESTION
          Load Sales / Construction / Collections / AOP (6 sheets)
        |
        v
Stage  2: CLEAN & VALIDATE
          Strip nulls, unnamed columns, duplicate rows
        |
        v
Stage  3: DATA QUALITY DETECTION  [Human-in-the-Loop]
          Unit mismatches (Sales vs Collections)
          Milestone mismatches (Collections vs Construction)
          Missing Delay Reasons, Missing Owners
          Cash-flow leakage flags
          Customer SAP code conflicts
          --> data_quality_report.xlsx
        |
        v
Stage  4: DATA LINKING
          Sales <-> Collections  (key: Unit Number)
          + Construction         (key: Milestone Linked)
          --> final_merged_dataset.xlsx
        |
        v
Stage  5: AOP COMPARISON
          Sales / Collections / Construction vs AOP targets
          --> sales/collections/construction_vs_aop.xlsx
        |
        v
Stage  6: BUSINESS RULE ENGINE  (10 Rules)
          Rules 1-7: Row-level per unit
          Rules 8-9: Aggregate (Sales <80%, Collections <85%)
          Rule 10:   Cross-functional (same project failing multiple areas)
          --> business_rule_report.xlsx
        |
        v
Stage  7: RISK DETECTION
          Critical / High / Medium / Low per unit
          --> risk_report.xlsx
        |
        v
Stage  8: ESCALATION ENGINE
          CEO/Site Head  -> Critical / Cross-functional
          Project Head   -> High risk
          Site Manager   -> Medium risk, delays
          + Reason, Action, Due Date per item
          --> escalation_report.xlsx
        |
        v
Stage  9: CASH FLOW ENGINE
          Inflow  = Amount Collected
          CoC Out = Actual Cost + Additional Expected Cost
          NCF     = Inflow - CoC - Other Costs (AOP proxy)
          Variance vs GPL Pre-BD NCF Target
          --> cash_flow_report.xlsx
        |
        v
Stage 10: ACTION PLAN
          Sales Head / Collections / Construction / Finance / CEO
          With Priority, Due Date, Supporting Data
          --> action_plan.xlsx
        |
        v
Stage 11: AI SUMMARY
          Rule-based text synthesis of all metrics
          --> ai_summary.txt
        |
        v
Stage 12: DRAFT COMMUNICATIONS
          Email drafts for each risk category, stakeholder-specific
          --> draft_communications.txt / .xlsx
        |
        v
Stage 13: LEADERSHIP PERFORMANCE REPORT
          8-sheet Excel: Scorecard, Escalation, Product Mix,
          Action Plan, Decision Items, AI Recs, Cash Flow
          --> performance_report.xlsx
        |
        v
14 OUTPUT FILES IN /output/
```

---

## 📊 Business Rules — All 10 Implemented

| # | Area | Rule | Threshold |
|---|------|------|-----------|
| 1 | Collections | Customer overdue | >30 days |
| 2 | Construction | Milestone delay | >15 days |
| 3 | Collections | High outstanding | >Rs.10 Lakh |
| 4 | Collections | Low payment received | Paid % <50% |
| 5 | Cash Flow | Milestone done + collection pending | 100% progress + outstanding >0 |
| 6 | Data Quality | Missing delay reason | Delay >15d + no reason recorded |
| 7 | Cost | CoC overrun | Actual >110% of Planned |
| 8 | Sales | Monthly booking shortfall | <80% of AOP target |
| 9 | Collections | Monthly collection shortfall | <85% of AOP target |
| 10 | Escalation | Cross-functional failure | Same project: Sales Risk + Col/Con Risk |

---

## 🤖 AI Usage — Where AI Adds Value

| Task | Approach |
|------|----------|
| Data ingestion & merge | Deterministic — Pandas joins on exact keys |
| Business rules | Deterministic — Hard-coded thresholds from brief |
| Cash flow calculation | Deterministic — NCF = Inflows - CoC - Other Costs |
| Risk classification | Deterministic — Rule-based scoring |
| AI Summary text | Rule-based synthesis from computed metrics |
| Draft communications | Context-filled templates with real values |
| AI Recommendations | Fire from specific rule conditions |

> AI is used for **interpretation and synthesis**, not for calculations.
> Calculations use deterministic code/formulas for accuracy and auditability.

---

## ⚠️ Assumptions

- **Unit Number** is the primary key linking Sales <-> Collections
- **Milestone Linked** (Collections) maps to **Linked Collection Milestone** (Construction)
- AOP monetary values are in **Crores** (x 10,000,000 to convert to Rs.)
- CoC actuals = Actual Cost INR + Additional Cost Expected INR
- "Other Costs" for NCF (Marketing, Tax, Interest) use AOP targets as proxy
  since actuals are not in the 4 input files
- **Sales vs AOP** is restricted to the exact months the AOP sales sheet
  covers (matched on `Booking Date`'s month). Without this, actual bookings
  spanning a wider date range than the AOP target were being summed against
  a fixed 3-month target, producing a meaningless Achievement %.
- **Collections vs AOP** is restricted the same way (matched on `Due Date`'s
  month against the AOP `Month` column), and a **monthly breakdown sheet**
  is now included in `collections_vs_aop.xlsx` / `sales_vs_aop.xlsx` so the
  "monthly booking/collections below threshold" rules can be verified
  month-by-month, not just as one blended figure.

## 🔴 Known Data Limitation — Flagged, Not Silently Fixed

The AOP **Collections** target (`Expected Demand Value`) is defined at the
full tower/portfolio level (i.e. assumes the entire tower's inventory has
been sold), while the Collections tracker only contains records for the
41 units that are currently sold (out of 80 units in the Sales file). This
means the AOP figure (~₹1,110 Cr) and the actual figure (~₹14.7 Cr demand
raised) are not on the same population, and a raw Achievement % against it
will always look extremely low — even after correcting the date-window
issue above.

Rather than guess a pro-rating formula, this is deliberately surfaced as an
**"AOP Scale Mismatch"** entry in `data_quality_report.xlsx`, with a
recommended action for Finance/Sales leadership to confirm whether the AOP
target should be pro-rated to % of inventory sold. This is consistent with
the brief's instruction to "flag the mismatch rather than ignoring it"
instead of hard-coding an assumption that could mislead leadership.

## 🔁 Reusability

The solution is fully reusable. Replace any input file with updated data
(same column structure) and rerun `python app.py` — all 14 outputs regenerate.
No results are hardcoded.

---

## 🛠 Tech Stack

| Component | Tool |
|-----------|------|
| Language | Python 3.10+ |
| Data Processing | Pandas, OpenPyXL |
| Dashboard | Streamlit |
| Charts | Plotly |
| Business Rules | Custom Python rule engine |
| Output | Excel (openpyxl), Plain text |

---

## ✅ Evaluation Rubric — Self-Assessment

| Criterion | Weight | Implementation |
|-----------|--------|----------------|
| File ingestion & data linking | 15% | All 4 files, cross-linked on Unit Number + Milestone |
| Business rule application | 10% | All 10 rules, deterministic, documented |
| Workflow / agentic design | 20% | 13 pipeline stages, error routing, human-in-the-loop |
| Handling messy data | 5% | data_quality.py: 10 detection checks, flagged for human review |
| Output quality | 25% | 14 outputs — scorecard, cash flow, escalation, action plan, drafts |
| Code quality & reusability | 10% | Modular, no hardcoding, reusable on new inputs |
| Architecture & explanation | 10% | This document + pipeline diagram |
| Demo effectiveness | 5% | Streamlit dashboard with 8 tabs |
