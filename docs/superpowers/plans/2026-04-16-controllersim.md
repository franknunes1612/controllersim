# ControllerSim Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Streamlit web app that teaches business controller skills through interactive scenarios at a fictional company (Nexova Ltd), with Claude AI feedback.

**Architecture:** Four progressive skill modules (Financial Statements → Budgeting → Variance Analysis → Forecasting), each loading scenario data from JSON files. Rule-based grading for objective answers; Claude API for written explanations. Pure business-logic functions are tested with pytest; Streamlit UI is not unit-tested.

**Tech Stack:** Python 3.11+, Streamlit, Anthropic Python SDK, Plotly, pytest

---

## File Map

| File | Responsibility |
|------|---------------|
| `controllersim/app.py` | Entry point, sidebar nav, page routing |
| `controllersim/components/progress.py` | Pure functions for scoring and unlock logic |
| `controllersim/components/feedback.py` | Claude API call and JSON parsing |
| `controllersim/modules/statements.py` | Module 1 UI — financial statement scenarios |
| `controllersim/modules/budgeting.py` | Module 2 UI — budgeting scenarios |
| `controllersim/modules/variance.py` | Module 3 UI — variance analysis scenarios |
| `controllersim/modules/forecasting.py` | Module 4 UI — forecasting scenarios |
| `controllersim/scenarios/statements.json` | 3 financial statement scenarios |
| `controllersim/scenarios/budgeting.json` | 3 budgeting scenarios |
| `controllersim/scenarios/variance.json` | 3 variance analysis scenarios |
| `controllersim/scenarios/forecasting.json` | 3 forecasting scenarios |
| `controllersim/tests/test_progress.py` | Tests for progress pure functions |
| `controllersim/tests/test_feedback.py` | Tests for feedback with mocked Anthropic |
| `controllersim/.streamlit/config.toml` | Nexova Ltd theme |
| `controllersim/.streamlit/secrets.toml.example` | API key template |

---

## Task 1: Project Setup

**Files:**
- Create: `controllersim/requirements.txt`
- Create: `controllersim/app.py`
- Create: `controllersim/components/__init__.py`
- Create: `controllersim/modules/__init__.py`
- Create: `controllersim/tests/__init__.py`

- [ ] **Step 1: Create the project directory and folder structure**

```bash
mkdir -p controllersim/components controllersim/modules controllersim/scenarios controllersim/tests controllersim/.streamlit
touch controllersim/components/__init__.py controllersim/modules/__init__.py controllersim/tests/__init__.py
```

- [ ] **Step 2: Create `controllersim/requirements.txt`**

```
streamlit==1.33.0
anthropic==0.25.0
plotly==5.20.0
pytest==8.1.1
```

- [ ] **Step 3: Install dependencies**

```bash
cd controllersim && pip install -r requirements.txt
```

Expected: All packages installed without errors.

- [ ] **Step 4: Create a minimal `controllersim/app.py` to verify Streamlit works**

```python
import streamlit as st

st.set_page_config(page_title="ControllerSim", page_icon="📊", layout="wide")
st.title("ControllerSim")
st.write("Welcome to Nexova Ltd. Your controller training starts here.")
```

- [ ] **Step 5: Run the app**

```bash
streamlit run app.py
```

Expected: Browser opens showing "ControllerSim" title and welcome text.

- [ ] **Step 6: Commit**

```bash
git init
git add .
git commit -m "feat: project setup — Streamlit hello world"
```

---

## Task 2: Scenario JSON Data

**Files:**
- Create: `controllersim/scenarios/statements.json`
- Create: `controllersim/scenarios/budgeting.json`
- Create: `controllersim/scenarios/variance.json`
- Create: `controllersim/scenarios/forecasting.json`

- [ ] **Step 1: Create `controllersim/scenarios/statements.json`**

```json
[
  {
    "id": "stmt_001",
    "title": "Reading Nexova's Income Statement",
    "context": "Your first week at Nexova Ltd. The CFO hands you last year's income statement and asks you to demonstrate you can read it.",
    "financial_data": {
      "type": "table",
      "title": "Nexova Ltd — Income Statement FY2025 (€ thousands)",
      "columns": ["Line Item", "Amount (€k)"],
      "rows": [
        ["Revenue", 4200],
        ["Cost of Goods Sold", -1260],
        ["Gross Profit", 2940],
        ["Sales & Marketing", -840],
        ["Research & Development", -630],
        ["General & Administrative", -420],
        ["Operating Income (EBIT)", 1050],
        ["Interest Expense", -90],
        ["Earnings Before Tax", 960],
        ["Income Tax (25%)", -240],
        ["Net Income", 720]
      ]
    },
    "answer_type": "questions",
    "questions": [
      {
        "id": "q1",
        "text": "What is Nexova's gross margin? (enter as a whole number, e.g. 70 for 70%)",
        "type": "number",
        "unit": "%",
        "correct_answer": 70,
        "tolerance": 1
      },
      {
        "id": "q2",
        "text": "Which is the largest operating expense category?",
        "type": "multiple_choice",
        "options": ["Cost of Goods Sold", "Sales & Marketing", "Research & Development", "General & Administrative"],
        "correct_answer": "Sales & Marketing"
      },
      {
        "id": "q3",
        "text": "What is Nexova's net profit margin? (round to nearest whole number)",
        "type": "number",
        "unit": "%",
        "correct_answer": 17,
        "tolerance": 1
      }
    ]
  },
  {
    "id": "stmt_002",
    "title": "Analysing the Balance Sheet",
    "context": "The CFO wants to know if you can assess Nexova's financial health from the balance sheet.",
    "financial_data": {
      "type": "table",
      "title": "Nexova Ltd — Balance Sheet FY2025 (€ thousands)",
      "columns": ["Line Item", "Amount (€k)"],
      "rows": [
        ["ASSETS", ""],
        ["Cash & Equivalents", 650],
        ["Accounts Receivable", 380],
        ["Prepaid Expenses", 45],
        ["Total Current Assets", 1075],
        ["PP&E (net)", 420],
        ["Intangibles", 180],
        ["Total Assets", 1675],
        ["LIABILITIES", ""],
        ["Accounts Payable", 145],
        ["Accrued Expenses", 95],
        ["Deferred Revenue", 280],
        ["Total Current Liabilities", 520],
        ["Long-term Debt", 450],
        ["Total Liabilities", 970],
        ["EQUITY", ""],
        ["Shareholders' Equity", 705],
        ["Total Liabilities & Equity", 1675]
      ]
    },
    "answer_type": "questions",
    "questions": [
      {
        "id": "q1",
        "text": "What is Nexova's current ratio? (round to 1 decimal place, e.g. 2.1)",
        "type": "number",
        "unit": "",
        "correct_answer": 2.1,
        "tolerance": 0.1
      },
      {
        "id": "q2",
        "text": "What is Nexova's working capital? (in € thousands)",
        "type": "number",
        "unit": "€k",
        "correct_answer": 555,
        "tolerance": 5
      },
      {
        "id": "q3",
        "text": "What does a current ratio above 2.0 indicate?",
        "type": "multiple_choice",
        "options": [
          "The company is over-leveraged",
          "The company can comfortably cover short-term obligations",
          "The company has too much inventory",
          "The company is unprofitable"
        ],
        "correct_answer": "The company can comfortably cover short-term obligations"
      }
    ]
  },
  {
    "id": "stmt_003",
    "title": "Understanding the Cash Flow Statement",
    "context": "Net income is not the same as cash. The CFO tests whether you understand the difference.",
    "financial_data": {
      "type": "table",
      "title": "Nexova Ltd — Cash Flow Statement FY2025 (€ thousands)",
      "columns": ["Line Item", "Amount (€k)"],
      "rows": [
        ["OPERATING ACTIVITIES", ""],
        ["Net Income", 720],
        ["Depreciation & Amortisation", 95],
        ["Increase in Accounts Receivable", -45],
        ["Increase in Deferred Revenue", 60],
        ["Increase in Accounts Payable", 20],
        ["Net Cash from Operations", 850],
        ["INVESTING ACTIVITIES", ""],
        ["Purchase of Equipment", -120],
        ["Net Cash from Investing", -120],
        ["FINANCING ACTIVITIES", ""],
        ["Loan Repayment", -100],
        ["Net Cash from Financing", -100],
        ["Net Change in Cash", 630]
      ]
    },
    "answer_type": "questions",
    "questions": [
      {
        "id": "q1",
        "text": "What is Nexova's free cash flow? (Operating CF minus CapEx, in € thousands)",
        "type": "number",
        "unit": "€k",
        "correct_answer": 730,
        "tolerance": 5
      },
      {
        "id": "q2",
        "text": "Why is net cash from operations (€850k) higher than net income (€720k)?",
        "type": "multiple_choice",
        "options": [
          "The company recorded fictitious revenue",
          "Non-cash charges like depreciation are added back and working capital improved",
          "The company borrowed more money",
          "Tax was not paid"
        ],
        "correct_answer": "Non-cash charges like depreciation are added back and working capital improved"
      },
      {
        "id": "q3",
        "text": "Purchasing equipment (€120k) appears under which section of the cash flow statement?",
        "type": "multiple_choice",
        "options": ["Operating Activities", "Investing Activities", "Financing Activities", "Equity"],
        "correct_answer": "Investing Activities"
      }
    ]
  }
]
```

- [ ] **Step 2: Create `controllersim/scenarios/budgeting.json`**

```json
[
  {
    "id": "budg_001",
    "title": "Marketing Department Annual Budget",
    "context": "You are preparing the Marketing department's FY2026 budget. Use the assumptions below to fill in each line item.",
    "financial_data": {
      "type": "assumptions",
      "title": "Budget Assumptions",
      "items": [
        "3 marketing staff, average salary €55,000 each",
        "4 campaign activations planned, €12,000 per campaign",
        "Annual software licences: €8,000",
        "Travel & entertainment: €5,000"
      ]
    },
    "answer_type": "table_input",
    "fields": [
      {"id": "personnel", "label": "Personnel Costs (€)", "correct_answer": 165000, "tolerance_pct": 0},
      {"id": "campaigns", "label": "Campaign Costs (€)", "correct_answer": 48000, "tolerance_pct": 0},
      {"id": "software", "label": "Software Licences (€)", "correct_answer": 8000, "tolerance_pct": 0},
      {"id": "travel", "label": "Travel & Entertainment (€)", "correct_answer": 5000, "tolerance_pct": 0},
      {"id": "total", "label": "Total Budget (€)", "correct_answer": 226000, "tolerance_pct": 0}
    ]
  },
  {
    "id": "budg_002",
    "title": "Quarterly Revenue Budget",
    "context": "The annual revenue target for FY2026 is €4,500,000. Allocate it across quarters using the seasonal weighting factors provided.",
    "financial_data": {
      "type": "assumptions",
      "title": "Seasonal Weighting",
      "items": [
        "Q1: 22% of annual target",
        "Q2: 28% of annual target",
        "Q3: 25% of annual target",
        "Q4: 25% of annual target",
        "Annual target: €4,500,000"
      ]
    },
    "answer_type": "table_input",
    "fields": [
      {"id": "q1", "label": "Q1 Revenue Budget (€)", "correct_answer": 990000, "tolerance_pct": 0},
      {"id": "q2", "label": "Q2 Revenue Budget (€)", "correct_answer": 1260000, "tolerance_pct": 0},
      {"id": "q3", "label": "Q3 Revenue Budget (€)", "correct_answer": 1125000, "tolerance_pct": 0},
      {"id": "q4", "label": "Q4 Revenue Budget (€)", "correct_answer": 1125000, "tolerance_pct": 0},
      {"id": "total", "label": "Full Year Total (€)", "correct_answer": 4500000, "tolerance_pct": 0}
    ]
  },
  {
    "id": "budg_003",
    "title": "Finance Team Headcount Budget",
    "context": "Calculate the total people cost for the Finance team for FY2026. Remember: total cost = base salary + 20% benefits + 10% employer social contributions.",
    "financial_data": {
      "type": "assumptions",
      "title": "Finance Team Headcount",
      "items": [
        "Business Controller: €65,000",
        "Financial Analyst: €52,000",
        "Finance Assistant: €38,000",
        "FP&A Manager: €72,000",
        "Accountant: €48,000",
        "On-costs: 20% benefits + 10% employer social contributions on each salary"
      ]
    },
    "answer_type": "table_input",
    "fields": [
      {"id": "base_total", "label": "Total Base Salaries (€)", "correct_answer": 275000, "tolerance_pct": 0},
      {"id": "benefits", "label": "Benefits (20% of base) (€)", "correct_answer": 55000, "tolerance_pct": 0},
      {"id": "social", "label": "Employer Social Contributions (10% of base) (€)", "correct_answer": 27500, "tolerance_pct": 0},
      {"id": "total_people_cost", "label": "Total People Cost (€)", "correct_answer": 357500, "tolerance_pct": 0}
    ]
  }
]
```

- [ ] **Step 3: Create `controllersim/scenarios/variance.json`**

```json
[
  {
    "id": "var_001",
    "title": "Q2 Marketing Overspend",
    "context": "The CFO has asked you to explain last quarter's marketing spend. Budget was €50,000. Actuals came in at €63,500. Two unplanned digital campaigns were approved mid-quarter by the CMO.",
    "financial_data": {
      "type": "table",
      "title": "Q2 Marketing — Budget vs Actual (€)",
      "columns": ["", "Budget (€)", "Actual (€)", "Variance (€)"],
      "rows": [
        ["Digital Campaigns", 24000, 37500, -13500],
        ["Events", 14000, 14000, 0],
        ["Software Tools", 8000, 8000, 0],
        ["Travel", 4000, 4000, 0],
        ["Total", 50000, 63500, -13500]
      ]
    },
    "answer_type": "text",
    "prompt": "In 2–3 sentences, explain the Q2 marketing variance to the CFO. Your explanation should be professional and ready to present.",
    "rubric": [
      "Identifies the variance as unfavourable",
      "Quantifies the gap in absolute terms (€13,500) or percentage terms (+27%)",
      "Explains the cause (two unplanned digital campaigns approved mid-quarter)"
    ],
    "model_answer": "Q2 marketing spend came in at €63,500, €13,500 (27%) above the €50,000 budget — an unfavourable variance. The overspend was driven entirely by two unplanned digital campaigns approved by the CMO mid-quarter, which were not included in the original budget. All other line items were on-plan."
  },
  {
    "id": "var_002",
    "title": "Q2 Revenue Shortfall",
    "context": "Sales came in below plan in Q2. You need to explain the shortfall to the board before the quarterly review.",
    "financial_data": {
      "type": "table",
      "title": "Q2 Revenue — Budget vs Actual (€ thousands)",
      "columns": ["Segment", "Budget (€k)", "Actual (€k)", "Variance (€k)"],
      "rows": [
        ["Enterprise", 210, 158, -52],
        ["Mid-Market", 95, 95, 0],
        ["SMB", 45, 45, 0],
        ["Total", 350, 298, -52]
      ]
    },
    "answer_type": "text",
    "prompt": "In 2–3 sentences, explain the Q2 revenue variance to the board. Two enterprise deals (€26,000 each) were expected to close in June but slipped to Q3.",
    "rubric": [
      "Identifies the variance as unfavourable",
      "Quantifies the gap (€52,000 or approximately 15%)",
      "Explains the cause (two enterprise deals slipped to Q3)",
      "Indicates this is a timing issue, not lost revenue"
    ],
    "model_answer": "Q2 revenue came in at €298,000, €52,000 (15%) below the €350,000 budget — an unfavourable variance driven entirely by the Enterprise segment. Two enterprise deals worth €26,000 each that were expected to close in June slipped to Q3, representing a timing issue rather than lost revenue. Mid-Market and SMB performed in line with plan."
  },
  {
    "id": "var_003",
    "title": "Full Quarter Variance Summary",
    "context": "Quarter-end. The CFO needs a one-paragraph executive summary of Nexova's Q3 financial performance to share with the board. Review the full variance table below.",
    "financial_data": {
      "type": "table",
      "title": "Nexova Ltd — Q3 Variance Summary (€ thousands)",
      "columns": ["Line Item", "Budget (€k)", "Actual (€k)", "Variance (€k)", "Fav / Unfav"],
      "rows": [
        ["Revenue", 1050, 1098, 48, "Favourable"],
        ["Personnel Costs", -420, -408, 12, "Favourable"],
        ["Marketing", -150, -172, -22, "Unfavourable"],
        ["Software & Tools", -45, -45, 0, "On Plan"],
        ["Travel & Expenses", -30, -19, 11, "Favourable"],
        ["Other OpEx", -25, -28, -3, "Unfavourable"],
        ["EBIT", 380, 426, 46, "Favourable"]
      ]
    },
    "answer_type": "text",
    "prompt": "Write a one-paragraph executive summary of Q3 performance for the board. Cover: overall result, key drivers (positive and negative), and any items to watch.",
    "rubric": [
      "States the overall EBIT result and whether it was favourable or unfavourable vs budget",
      "Identifies revenue outperformance as a positive driver",
      "Flags marketing overspend as the main risk or negative driver",
      "Mentions at least one favourable item (personnel or travel)",
      "Written in professional, board-ready language"
    ],
    "model_answer": "Nexova delivered a strong Q3, with EBIT of €426,000 — €46,000 (12%) ahead of budget. Revenue outperformed by €48,000 driven by enterprise deal acceleration, and personnel costs came in €12,000 below plan due to two open roles not yet filled. The main area of concern was marketing, which overspent by €22,000 due to an unplanned brand campaign approved in August. Travel also underspent by €11,000 as several team offsites were postponed to Q4. Overall a positive quarter; the board should note that Q4 marketing and travel budgets may face pressure from Q3 deferrals."
  }
]
```

- [ ] **Step 4: Create `controllersim/scenarios/forecasting.json`**

```json
[
  {
    "id": "fore_001",
    "title": "Update the H2 Revenue Forecast",
    "context": "H1 is closed. Actuals came in ahead of budget. You need to update the H2 revenue forecast and explain your assumptions to the CFO.",
    "financial_data": {
      "type": "table",
      "title": "Nexova Ltd — Revenue Forecast (€ thousands)",
      "columns": ["Quarter", "Original Budget (€k)", "Actuals / Forecast (€k)"],
      "rows": [
        ["Q1 (Actual)", 945, 1050],
        ["Q2 (Actual)", 1155, 1155],
        ["Q3 (Forecast)", 1050, "?"],
        ["Q4 (Forecast)", 1050, "?"],
        ["Full Year", 4200, "?"]
      ]
    },
    "answer_type": "hybrid",
    "number_fields": [
      {"id": "q3_forecast", "label": "Q3 Revised Forecast (€k)", "correct_answer": 1100, "tolerance_pct": 5},
      {"id": "q4_forecast", "label": "Q4 Revised Forecast (€k)", "correct_answer": 1100, "tolerance_pct": 5},
      {"id": "fy_forecast", "label": "Full Year Revised Forecast (€k)", "correct_answer": 4305, "tolerance_pct": 3}
    ],
    "prompt": "In 2–3 sentences, explain the rationale behind your updated H2 forecast to the CFO.",
    "rubric": [
      "References the H1 outperformance as the basis for the revision",
      "Applies a reasonable and consistent logic to H2 (not just copying H1 beat)",
      "Acknowledges any uncertainty or risk in the forecast"
    ],
    "model_answer": "H1 came in €105,000 ahead of budget, with Q1 outperforming by €105,000 and Q2 on-plan. Given a healthy sales pipeline and no known headwinds, we are revising Q3 and Q4 forecasts up by €50,000 each — a conservative approach that reflects momentum without over-committing. The primary risk is enterprise deal slippage, which we will track weekly."
  },
  {
    "id": "fore_002",
    "title": "Reforecast OpEx After Headcount Changes",
    "context": "Two new analysts join in August. One accountant resigns effective end of September. Update the H2 monthly OpEx forecast and explain the impact.",
    "financial_data": {
      "type": "table",
      "title": "H2 OpEx Forecast (€ thousands) — Before Changes",
      "columns": ["Month", "Current Forecast (€k)"],
      "rows": [
        ["July", 150],
        ["August", 150],
        ["September", 150],
        ["October", 150],
        ["November", 150],
        ["December", 150],
        ["H2 Total", 900]
      ]
    },
    "answer_type": "hybrid",
    "number_fields": [
      {"id": "new_hire_cost", "label": "Additional cost from 2 new hires Aug–Dec (€k, combined)", "correct_answer": 45, "tolerance_pct": 10},
      {"id": "resignation_saving", "label": "Saving from resignation Oct–Dec (€k)", "correct_answer": 16, "tolerance_pct": 10},
      {"id": "revised_h2_total", "label": "Revised H2 OpEx Total (€k)", "correct_answer": 929, "tolerance_pct": 2}
    ],
    "prompt": "In 2–3 sentences, summarise the net impact of these headcount changes on H2 OpEx for the CFO. New hires: €9,000/month combined (on-costs included). Resignation saves: €5,500/month from October.",
    "rubric": [
      "Quantifies the net cost impact (approximately €29,000 net increase)",
      "Distinguishes between the additional cost (new hires) and the saving (resignation)",
      "States the revised H2 total or net change clearly"
    ],
    "model_answer": "The two new analyst hires add €9,000/month in combined on-cost from August, totalling €45,000 for the remaining 5 months of H2. The accountant resignation saves €5,500/month from October, reducing costs by €16,500 over 3 months — a net H2 increase of €28,500. The revised H2 OpEx forecast is therefore €928,500, up from the original €900,000."
  },
  {
    "id": "fore_003",
    "title": "Year-End Forecast Memo",
    "context": "It's October. With Q3 actuals in hand, write the year-end forecast memo that will go to the board. All numbers are provided — your job is the narrative.",
    "financial_data": {
      "type": "table",
      "title": "Nexova Ltd — Year-End Forecast (€ thousands)",
      "columns": ["", "Original Budget", "Q1–Q3 Actual", "Q4 Forecast", "Full Year Forecast", "vs Budget"],
      "rows": [
        ["Revenue", 4200, 3303, 1100, 4403, "+203"],
        ["Gross Profit", 2940, 2355, 770, 3125, "+185"],
        ["Total OpEx", 1890, 1490, 480, 1970, "-80"],
        ["EBIT", 1050, 865, 290, 1155, "+105"]
      ]
    },
    "answer_type": "text",
    "prompt": "Write a professional year-end forecast memo (3–4 sentences) for the board. Cover the expected full-year outcome vs budget, the key drivers, and any risks to the Q4 forecast.",
    "rubric": [
      "States the full-year EBIT forecast and the expected beat vs budget",
      "Explains at least one revenue driver for outperformance",
      "Mentions OpEx being over budget and why",
      "Identifies at least one Q4 risk",
      "Professional, board-ready tone"
    ],
    "model_answer": "Nexova is tracking to deliver full-year EBIT of €1,155,000 — €105,000 (10%) ahead of the original budget of €1,050,000. Revenue outperformance of €203,000 is the primary driver, reflecting strong enterprise deal conversion in Q2 and Q3. OpEx is forecast to exceed budget by €80,000, largely due to the two analyst hires in August and unplanned marketing spend in Q3. The key risk to Q4 is the €1.1M revenue forecast, which assumes two enterprise deals close before year-end; any slippage would reduce full-year EBIT by approximately €50,000–70,000."
  }
]
```

- [ ] **Step 5: Verify all JSON files parse correctly**

```bash
python -c "
import json, os
for f in ['statements','budgeting','variance','forecasting']:
    with open(f'scenarios/{f}.json') as fh:
        data = json.load(fh)
    print(f'{f}.json: {len(data)} scenarios OK')
"
```

Expected output:
```
statements.json: 3 scenarios OK
budgeting.json: 3 scenarios OK
variance.json: 3 scenarios OK
forecasting.json: 3 scenarios OK
```

- [ ] **Step 6: Commit**

```bash
git add scenarios/
git commit -m "feat: add scenario JSON data for all 4 modules"
```

---

## Task 3: Progress Component

**Files:**
- Create: `controllersim/components/progress.py`
- Create: `controllersim/tests/test_progress.py`

- [ ] **Step 1: Write the failing tests first**

Create `controllersim/tests/test_progress.py`:

```python
import pytest
from components.progress import (
    empty_progress,
    record_score,
    is_module_unlocked,
    mark_module_complete,
    get_readiness_score,
    MODULES,
)


def test_empty_progress_has_all_modules():
    p = empty_progress()
    assert set(p.keys()) == set(MODULES)


def test_empty_progress_all_incomplete():
    p = empty_progress()
    for module in MODULES:
        assert p[module]["completed"] is False
        assert p[module]["scores"] == []


def test_first_module_always_unlocked():
    p = empty_progress()
    assert is_module_unlocked(p, MODULES[0]) is True


def test_second_module_locked_until_first_complete():
    p = empty_progress()
    assert is_module_unlocked(p, MODULES[1]) is False
    p = mark_module_complete(p, MODULES[0])
    assert is_module_unlocked(p, MODULES[1]) is True


def test_record_score_appends_first_score():
    p = empty_progress()
    p = record_score(p, MODULES[0], 0, "pass")
    assert p[MODULES[0]]["scores"] == [1.0]


def test_record_score_overwrites_existing():
    p = empty_progress()
    p = record_score(p, MODULES[0], 0, "pass")
    p = record_score(p, MODULES[0], 0, "fail")
    assert p[MODULES[0]]["scores"] == [0.0]


def test_record_score_partial_is_half():
    p = empty_progress()
    p = record_score(p, MODULES[0], 0, "partial")
    assert p[MODULES[0]]["scores"] == [0.5]


def test_readiness_score_zero_when_empty():
    p = empty_progress()
    assert get_readiness_score(p) == 0


def test_readiness_score_100_all_pass():
    p = empty_progress()
    for i, module in enumerate(MODULES):
        for j in range(3):
            p = record_score(p, module, j, "pass")
    assert get_readiness_score(p) == 100


def test_readiness_score_50_all_partial():
    p = empty_progress()
    for module in MODULES:
        for j in range(3):
            p = record_score(p, module, j, "partial")
    assert get_readiness_score(p) == 50
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
pytest tests/test_progress.py -v
```

Expected: All tests FAIL with `ImportError: cannot import name 'empty_progress'`

- [ ] **Step 3: Implement `controllersim/components/progress.py`**

```python
import streamlit as st

MODULES = ["statements", "budgeting", "variance", "forecasting"]
SCORE_VALUES = {"pass": 1.0, "partial": 0.5, "fail": 0.0}


def empty_progress() -> dict:
    """Return a fresh progress dict with no scores."""
    return {module: {"scores": [], "completed": False} for module in MODULES}


def init_progress() -> None:
    """Initialise progress in Streamlit session state if not already present."""
    if "progress" not in st.session_state:
        st.session_state.progress = empty_progress()


def record_score(progress: dict, module: str, scenario_idx: int, signal: str) -> dict:
    """Record a scenario score. Overwrites if already scored."""
    score_value = SCORE_VALUES[signal]
    scores = progress[module]["scores"]
    if len(scores) <= scenario_idx:
        scores.append(score_value)
    else:
        scores[scenario_idx] = score_value
    return progress


def is_module_unlocked(progress: dict, module: str) -> bool:
    """Return True if the module is available to the user."""
    idx = MODULES.index(module)
    if idx == 0:
        return True
    prev_module = MODULES[idx - 1]
    return progress[prev_module]["completed"]


def mark_module_complete(progress: dict, module: str) -> dict:
    """Mark a module as completed."""
    progress[module]["completed"] = True
    return progress


def get_readiness_score(progress: dict) -> int:
    """Return overall Controller Readiness Score as an integer 0–100."""
    all_scores = []
    for module in MODULES:
        all_scores.extend(progress[module]["scores"])
    if not all_scores:
        return 0
    return int((sum(all_scores) / len(all_scores)) * 100)
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
pytest tests/test_progress.py -v
```

Expected: All 10 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add components/progress.py tests/test_progress.py
git commit -m "feat: add progress component with full test coverage"
```

---

## Task 4: Feedback Component

**Files:**
- Create: `controllersim/components/feedback.py`
- Create: `controllersim/tests/test_feedback.py`

- [ ] **Step 1: Write the failing tests**

Create `controllersim/tests/test_feedback.py`:

```python
import json
import pytest
from unittest.mock import MagicMock, patch
from components.feedback import get_ai_feedback, grade_questions, grade_table_input


# --- grade_questions (pure, no mock needed) ---

def test_grade_questions_all_correct_number():
    questions = [{"id": "q1", "type": "number", "text": "Gross margin?", "unit": "%", "correct_answer": 70, "tolerance": 1}]
    signal, feedback = grade_questions(questions, {"q1": 70})
    assert signal == "pass"


def test_grade_questions_number_within_tolerance():
    questions = [{"id": "q1", "type": "number", "text": "Gross margin?", "unit": "%", "correct_answer": 70, "tolerance": 1}]
    signal, feedback = grade_questions(questions, {"q1": 71})
    assert signal == "pass"


def test_grade_questions_number_out_of_tolerance():
    questions = [{"id": "q1", "type": "number", "text": "Gross margin?", "unit": "%", "correct_answer": 70, "tolerance": 1}]
    signal, feedback = grade_questions(questions, {"q1": 60})
    assert signal == "fail"


def test_grade_questions_multiple_choice_correct():
    questions = [{"id": "q1", "type": "multiple_choice", "text": "Largest expense?", "options": ["A", "B"], "correct_answer": "A"}]
    signal, feedback = grade_questions(questions, {"q1": "A"})
    assert signal == "pass"


def test_grade_questions_multiple_choice_wrong():
    questions = [{"id": "q1", "type": "multiple_choice", "text": "Largest expense?", "options": ["A", "B"], "correct_answer": "A"}]
    signal, feedback = grade_questions(questions, {"q1": "B"})
    assert signal == "fail"


def test_grade_questions_partial_score():
    questions = [
        {"id": "q1", "type": "number", "text": "Q1?", "unit": "%", "correct_answer": 70, "tolerance": 1},
        {"id": "q2", "type": "number", "text": "Q2?", "unit": "%", "correct_answer": 17, "tolerance": 1},
    ]
    signal, feedback = grade_questions(questions, {"q1": 70, "q2": 99})
    assert signal == "partial"


# --- grade_table_input (pure, no mock needed) ---

def test_grade_table_input_all_correct():
    fields = [{"id": "f1", "label": "Personnel (€)", "correct_answer": 165000, "tolerance_pct": 0}]
    signal, feedback = grade_table_input(fields, {"f1": 165000})
    assert signal == "pass"


def test_grade_table_input_wrong():
    fields = [{"id": "f1", "label": "Personnel (€)", "correct_answer": 165000, "tolerance_pct": 0}]
    signal, feedback = grade_table_input(fields, {"f1": 100000})
    assert signal == "fail"


# --- get_ai_feedback (mocked Anthropic) ---

def _mock_anthropic_response(json_str: str):
    mock_content = MagicMock()
    mock_content.text = json_str
    mock_message = MagicMock()
    mock_message.content = [mock_content]
    return mock_message


def test_get_ai_feedback_returns_parsed_dict():
    scenario = {
        "prompt": "Explain the variance.",
        "rubric": ["Identifies unfavourable variance", "Quantifies the gap"],
        "model_answer": "The variance was €13,500 unfavourable.",
    }
    response_json = json.dumps({
        "signal": "pass",
        "feedback": "Great explanation.",
        "tip": "Always lead with the number.",
    })

    with patch("components.feedback.anthropic.Anthropic") as MockClient:
        instance = MockClient.return_value
        instance.messages.create.return_value = _mock_anthropic_response(response_json)

        result = get_ai_feedback(scenario, "The marketing variance was €13,500 unfavourable.")

    assert result["signal"] == "pass"
    assert "feedback" in result
    assert "tip" in result


def test_get_ai_feedback_fallback_on_bad_json():
    scenario = {
        "prompt": "Explain the variance.",
        "rubric": ["Point A"],
        "model_answer": "Model answer.",
    }

    with patch("components.feedback.anthropic.Anthropic") as MockClient:
        instance = MockClient.return_value
        instance.messages.create.return_value = _mock_anthropic_response("not valid json {{")

        result = get_ai_feedback(scenario, "Some answer.")

    assert result["signal"] == "partial"
    assert "feedback" in result
    assert "tip" in result
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
pytest tests/test_feedback.py -v
```

Expected: FAIL with `ImportError`

- [ ] **Step 3: Implement `controllersim/components/feedback.py`**

```python
import json
import os
import anthropic
import streamlit as st


def _get_api_key() -> str:
    """Return API key from Streamlit secrets (production) or env var (local)."""
    try:
        return st.secrets["ANTHROPIC_API_KEY"]
    except (KeyError, FileNotFoundError):
        return os.environ.get("ANTHROPIC_API_KEY", "")


def get_ai_feedback(scenario: dict, user_answer: str) -> dict:
    """Send scenario + user answer to Claude. Return signal, feedback, tip."""
    client = anthropic.Anthropic(api_key=_get_api_key())
    rubric_str = "\n".join(f"- {point}" for point in scenario["rubric"])

    prompt = f"""You are a finance mentor grading a business controller exercise. Be encouraging but precise.

Scenario prompt given to the student:
{scenario["prompt"]}

Rubric — key points the answer must cover:
{rubric_str}

Student's answer:
{user_answer}

Respond ONLY with valid JSON in this exact format:
{{
  "signal": "pass" or "partial" or "fail",
  "feedback": "2-4 sentences referencing the student's specific answer",
  "tip": "one concrete improvement suggestion"
}}"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )

    try:
        return json.loads(message.content[0].text)
    except json.JSONDecodeError:
        return {
            "signal": "partial",
            "feedback": "Your answer was received but could not be fully evaluated. Please try again.",
            "tip": "Make sure your answer is clear and specific.",
        }


def grade_questions(questions: list, answers: dict) -> tuple:
    """Grade multiple-choice and number questions. Returns (signal, feedback)."""
    correct = 0
    wrong = []
    for q in questions:
        answer = answers.get(q["id"])
        if q["type"] == "number":
            if answer is not None and abs(float(answer) - q["correct_answer"]) <= q.get("tolerance", 0):
                correct += 1
            else:
                wrong.append(f"{q['text']} (correct: {q['correct_answer']}{q.get('unit','')})")
        elif q["type"] == "multiple_choice":
            if answer == q["correct_answer"]:
                correct += 1
            else:
                wrong.append(f"{q['text']} (correct: {q['correct_answer']})")

    total = len(questions)
    ratio = correct / total if total > 0 else 0

    if ratio == 1.0:
        return "pass", f"All {total} questions correct. Well done."
    elif ratio >= 0.5:
        return "partial", f"{correct}/{total} correct. Review: " + " | ".join(wrong)
    else:
        return "fail", f"{correct}/{total} correct. Review: " + " | ".join(wrong)


def grade_table_input(fields: list, answers: dict) -> tuple:
    """Grade budget table inputs. Returns (signal, feedback)."""
    correct = 0
    wrong = []
    for field in fields:
        answer = answers.get(field["id"], 0) or 0
        tolerance = field.get("tolerance_pct", 0) / 100 * field["correct_answer"]
        if abs(float(answer) - field["correct_answer"]) <= max(tolerance, 0.5):
            correct += 1
        else:
            wrong.append(f"{field['label']} (correct: €{field['correct_answer']:,})")

    total = len(fields)
    ratio = correct / total if total > 0 else 0

    if ratio == 1.0:
        return "pass", f"All {total} fields correct."
    elif ratio >= 0.5:
        return "partial", f"{correct}/{total} correct. Review: " + " | ".join(wrong)
    else:
        return "fail", f"{correct}/{total} correct. Review: " + " | ".join(wrong)
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
pytest tests/test_feedback.py -v
```

Expected: All 11 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add components/feedback.py tests/test_feedback.py
git commit -m "feat: add feedback component with grading logic and Claude API integration"
```

---

## Task 5: Module 1 — Financial Statements

**Files:**
- Create: `controllersim/modules/statements.py`

- [ ] **Step 1: Create `controllersim/modules/statements.py`**

```python
import json
import streamlit as st
import pandas as pd
from components.progress import init_progress, record_score, mark_module_complete, MODULES
from components.feedback import grade_questions

MODULE_KEY = "statements"


def _load_scenarios() -> list:
    with open("scenarios/statements.json") as f:
        return json.load(f)


def _render_table(financial_data: dict) -> None:
    st.markdown(f"**{financial_data['title']}**")
    rows = financial_data["rows"]
    columns = financial_data["columns"]
    df = pd.DataFrame(rows, columns=columns)
    st.dataframe(df, use_container_width=True, hide_index=True)


def _collect_answers(questions: list) -> dict:
    answers = {}
    for q in questions:
        if q["type"] == "number":
            val = st.number_input(q["text"], min_value=0.0, step=0.1, key=f"input_{q['id']}")
            answers[q["id"]] = val
        elif q["type"] == "multiple_choice":
            val = st.radio(q["text"], options=q["options"], key=f"input_{q['id']}", index=None)
            answers[q["id"]] = val
    return answers


def render() -> None:
    init_progress()
    progress = st.session_state.progress
    scenarios = _load_scenarios()

    st.header("Module 1: Financial Statements")
    st.caption("Learn to read and interpret P&L, balance sheet, and cash flow statements.")

    scenario_idx = st.session_state.get("stmt_scenario_idx", 0)
    if scenario_idx >= len(scenarios):
        st.success("Module complete! All scenarios finished.")
        progress = mark_module_complete(progress, MODULE_KEY)
        st.session_state.progress = progress
        return

    scenario = scenarios[scenario_idx]
    st.subheader(f"Scenario {scenario_idx + 1} of {len(scenarios)}: {scenario['title']}")
    st.info(scenario["context"])

    _render_table(scenario["financial_data"])
    st.markdown("---")
    st.markdown("**Your answers:**")
    answers = _collect_answers(scenario["questions"])

    if st.button("Submit", key="stmt_submit"):
        if None in answers.values():
            st.warning("Please answer all questions before submitting.")
            return
        signal, feedback = grade_questions(scenario["questions"], answers)
        progress = record_score(progress, MODULE_KEY, scenario_idx, signal)
        st.session_state.progress = progress

        if signal == "pass":
            st.success(f"Pass — {feedback}")
        elif signal == "partial":
            st.warning(f"Partial — {feedback}")
        else:
            st.error(f"Incorrect — {feedback}")

        if signal in ("pass", "partial"):
            if st.button("Next scenario →", key="stmt_next"):
                st.session_state.stmt_scenario_idx = scenario_idx + 1
                st.rerun()
        else:
            if st.button("Try again", key="stmt_retry"):
                st.rerun()
```

- [ ] **Step 2: Wire Module 1 into app.py to test it**

Replace the contents of `controllersim/app.py`:

```python
import streamlit as st
from components.progress import init_progress
from modules import statements

st.set_page_config(page_title="ControllerSim", page_icon="📊", layout="wide")

init_progress()

page = st.sidebar.selectbox("Navigate", ["Module 1: Financial Statements"])

if page == "Module 1: Financial Statements":
    statements.render()
```

- [ ] **Step 3: Run the app and test Module 1 manually**

```bash
streamlit run app.py
```

Verify:
- The P&L table renders correctly
- Number inputs and radio buttons appear
- Submitting correct answers shows "Pass"
- Submitting wrong answers shows "Incorrect" with what the correct answer was
- "Next scenario" button advances to the next scenario

- [ ] **Step 4: Commit**

```bash
git add modules/statements.py app.py
git commit -m "feat: add Module 1 — Financial Statements"
```

---

## Task 6: Module 2 — Budgeting

**Files:**
- Create: `controllersim/modules/budgeting.py`

- [ ] **Step 1: Create `controllersim/modules/budgeting.py`**

```python
import json
import streamlit as st
from components.progress import init_progress, record_score, mark_module_complete
from components.feedback import grade_table_input

MODULE_KEY = "budgeting"


def _load_scenarios() -> list:
    with open("scenarios/budgeting.json") as f:
        return json.load(f)


def _render_assumptions(financial_data: dict) -> None:
    st.markdown(f"**{financial_data['title']}**")
    for item in financial_data["items"]:
        st.markdown(f"- {item}")


def _collect_table_answers(fields: list) -> dict:
    answers = {}
    for field in fields:
        val = st.number_input(field["label"], min_value=0, step=1000, key=f"budg_{field['id']}")
        answers[field["id"]] = val
    return answers


def render() -> None:
    init_progress()
    progress = st.session_state.progress
    scenarios = _load_scenarios()

    st.header("Module 2: Budgeting")
    st.caption("Build department and headcount budgets from given assumptions.")

    scenario_idx = st.session_state.get("budg_scenario_idx", 0)
    if scenario_idx >= len(scenarios):
        st.success("Module complete! All scenarios finished.")
        from components.progress import mark_module_complete
        progress = mark_module_complete(progress, MODULE_KEY)
        st.session_state.progress = progress
        return

    scenario = scenarios[scenario_idx]
    st.subheader(f"Scenario {scenario_idx + 1} of {len(scenarios)}: {scenario['title']}")
    st.info(scenario["context"])

    _render_assumptions(scenario["financial_data"])
    st.markdown("---")
    st.markdown("**Fill in the budget:**")
    answers = _collect_table_answers(scenario["fields"])

    if st.button("Submit", key="budg_submit"):
        signal, feedback = grade_table_input(scenario["fields"], answers)
        progress = record_score(progress, MODULE_KEY, scenario_idx, signal)
        st.session_state.progress = progress

        if signal == "pass":
            st.success(f"Pass — {feedback}")
        elif signal == "partial":
            st.warning(f"Partial — {feedback}")
        else:
            st.error(f"Incorrect — {feedback}")

        if signal in ("pass", "partial"):
            if st.button("Next scenario →", key="budg_next"):
                st.session_state.budg_scenario_idx = scenario_idx + 1
                st.rerun()
        else:
            if st.button("Try again", key="budg_retry"):
                st.rerun()
```

- [ ] **Step 2: Add Module 2 to app.py navigation**

```python
import streamlit as st
from components.progress import init_progress
from modules import statements, budgeting

st.set_page_config(page_title="ControllerSim", page_icon="📊", layout="wide")

init_progress()

page = st.sidebar.selectbox(
    "Navigate",
    ["Module 1: Financial Statements", "Module 2: Budgeting"],
)

if page == "Module 1: Financial Statements":
    statements.render()
elif page == "Module 2: Budgeting":
    budgeting.render()
```

- [ ] **Step 3: Run and test Module 2 manually**

```bash
streamlit run app.py
```

Verify:
- Assumptions list renders correctly
- Number inputs appear for each budget field
- Correct totals produce a "Pass"
- Wrong totals show which fields were incorrect with the correct answer

- [ ] **Step 4: Commit**

```bash
git add modules/budgeting.py app.py
git commit -m "feat: add Module 2 — Budgeting"
```

---

## Task 7: Module 3 — Variance Analysis

**Files:**
- Create: `controllersim/modules/variance.py`

- [ ] **Step 1: Create `controllersim/modules/variance.py`**

```python
import json
import streamlit as st
import pandas as pd
from components.progress import init_progress, record_score, mark_module_complete
from components.feedback import get_ai_feedback

MODULE_KEY = "variance"


def _load_scenarios() -> list:
    with open("scenarios/variance.json") as f:
        return json.load(f)


def _render_variance_table(financial_data: dict) -> None:
    st.markdown(f"**{financial_data['title']}**")
    df = pd.DataFrame(financial_data["rows"], columns=financial_data["columns"])
    st.dataframe(df, use_container_width=True, hide_index=True)


def render() -> None:
    init_progress()
    progress = st.session_state.progress
    scenarios = _load_scenarios()

    st.header("Module 3: Variance Analysis")
    st.caption("Compare actuals vs. budget and write CFO-ready explanations.")

    scenario_idx = st.session_state.get("var_scenario_idx", 0)
    if scenario_idx >= len(scenarios):
        st.success("Module complete! All scenarios finished.")
        progress = mark_module_complete(progress, MODULE_KEY)
        st.session_state.progress = progress
        return

    scenario = scenarios[scenario_idx]
    st.subheader(f"Scenario {scenario_idx + 1} of {len(scenarios)}: {scenario['title']}")
    st.info(scenario["context"])

    _render_variance_table(scenario["financial_data"])
    st.markdown("---")
    st.markdown(f"**Task:** {scenario['prompt']}")

    answer = st.text_area(
        "Your explanation:",
        height=150,
        key=f"var_answer_{scenario_idx}",
        placeholder="Write your variance explanation here...",
    )

    if st.button("Submit", key="var_submit"):
        if not answer.strip():
            st.warning("Please write an explanation before submitting.")
            return

        with st.spinner("Evaluating your answer..."):
            result = get_ai_feedback(scenario, answer)

        signal = result["signal"]
        progress = record_score(progress, MODULE_KEY, scenario_idx, signal)
        st.session_state.progress = progress

        if signal == "pass":
            st.success(f"Pass")
        elif signal == "partial":
            st.warning(f"Partial")
        else:
            st.error(f"Not quite")

        st.markdown(f"**Feedback:** {result['feedback']}")
        st.markdown(f"**Tip:** {result['tip']}")

        if signal in ("pass", "partial"):
            if st.button("Next scenario →", key="var_next"):
                st.session_state.var_scenario_idx = scenario_idx + 1
                st.rerun()
        else:
            if st.button("Try again", key="var_retry"):
                st.rerun()
```

- [ ] **Step 2: Add Module 3 to app.py**

```python
import streamlit as st
from components.progress import init_progress
from modules import statements, budgeting, variance

st.set_page_config(page_title="ControllerSim", page_icon="📊", layout="wide")

init_progress()

page = st.sidebar.selectbox(
    "Navigate",
    [
        "Module 1: Financial Statements",
        "Module 2: Budgeting",
        "Module 3: Variance Analysis",
    ],
)

if page == "Module 1: Financial Statements":
    statements.render()
elif page == "Module 2: Budgeting":
    budgeting.render()
elif page == "Module 3: Variance Analysis":
    variance.render()
```

- [ ] **Step 3: Set the ANTHROPIC_API_KEY environment variable and test**

```bash
export ANTHROPIC_API_KEY=your_key_here
streamlit run app.py
```

Navigate to Module 3. Submit a written variance explanation. Verify Claude returns feedback and a tip.

- [ ] **Step 4: Commit**

```bash
git add modules/variance.py app.py
git commit -m "feat: add Module 3 — Variance Analysis with Claude AI feedback"
```

---

## Task 8: Module 4 — Forecasting

**Files:**
- Create: `controllersim/modules/forecasting.py`

- [ ] **Step 1: Create `controllersim/modules/forecasting.py`**

```python
import json
import streamlit as st
import pandas as pd
from components.progress import init_progress, record_score, mark_module_complete
from components.feedback import get_ai_feedback, grade_table_input

MODULE_KEY = "forecasting"
SCORE_VALUES = {"pass": 2, "partial": 1, "fail": 0}


def _load_scenarios() -> list:
    with open("scenarios/forecasting.json") as f:
        return json.load(f)


def _render_table(financial_data: dict) -> None:
    st.markdown(f"**{financial_data['title']}**")
    df = pd.DataFrame(financial_data["rows"], columns=financial_data["columns"])
    st.dataframe(df, use_container_width=True, hide_index=True)


def _combined_signal(number_signal: str, ai_signal: str) -> str:
    combined = (SCORE_VALUES[number_signal] + SCORE_VALUES[ai_signal]) / 2
    if combined >= 1.5:
        return "pass"
    elif combined >= 0.75:
        return "partial"
    return "fail"


def render() -> None:
    init_progress()
    progress = st.session_state.progress
    scenarios = _load_scenarios()

    st.header("Module 4: Forecasting")
    st.caption("Update rolling forecasts and explain your assumptions.")

    scenario_idx = st.session_state.get("fore_scenario_idx", 0)
    if scenario_idx >= len(scenarios):
        st.success("Module complete! All scenarios finished.")
        progress = mark_module_complete(progress, MODULE_KEY)
        st.session_state.progress = progress
        return

    scenario = scenarios[scenario_idx]
    st.subheader(f"Scenario {scenario_idx + 1} of {len(scenarios)}: {scenario['title']}")
    st.info(scenario["context"])

    _render_table(scenario["financial_data"])
    st.markdown("---")

    answer_type = scenario.get("answer_type", "text")

    number_answers = {}
    if answer_type == "hybrid":
        st.markdown("**Update the forecast numbers:**")
        for field in scenario["number_fields"]:
            val = st.number_input(field["label"], min_value=0, step=10, key=f"fore_num_{field['id']}")
            number_answers[field["id"]] = val
        st.markdown("---")

    st.markdown(f"**Task:** {scenario['prompt']}")
    text_answer = st.text_area(
        "Your explanation:",
        height=150,
        key=f"fore_text_{scenario_idx}",
        placeholder="Write your rationale here...",
    )

    if st.button("Submit", key="fore_submit"):
        if not text_answer.strip():
            st.warning("Please write an explanation before submitting.")
            return

        with st.spinner("Evaluating your answer..."):
            ai_result = get_ai_feedback(scenario, text_answer)

        if answer_type == "hybrid":
            number_signal, number_feedback = grade_table_input(scenario["number_fields"], number_answers)
            final_signal = _combined_signal(number_signal, ai_result["signal"])
            st.markdown(f"**Numbers:** {number_feedback}")
        else:
            final_signal = ai_result["signal"]

        progress = record_score(progress, MODULE_KEY, scenario_idx, final_signal)
        st.session_state.progress = progress

        if final_signal == "pass":
            st.success("Pass")
        elif final_signal == "partial":
            st.warning("Partial")
        else:
            st.error("Not quite")

        st.markdown(f"**Feedback:** {ai_result['feedback']}")
        st.markdown(f"**Tip:** {ai_result['tip']}")

        if final_signal in ("pass", "partial"):
            if st.button("Next scenario →", key="fore_next"):
                st.session_state.fore_scenario_idx = scenario_idx + 1
                st.rerun()
        else:
            if st.button("Try again", key="fore_retry"):
                st.rerun()
```

- [ ] **Step 2: Add Module 4 to app.py**

```python
import streamlit as st
from components.progress import init_progress
from modules import statements, budgeting, variance, forecasting

st.set_page_config(page_title="ControllerSim", page_icon="📊", layout="wide")

init_progress()

page = st.sidebar.selectbox(
    "Navigate",
    [
        "Module 1: Financial Statements",
        "Module 2: Budgeting",
        "Module 3: Variance Analysis",
        "Module 4: Forecasting",
    ],
)

if page == "Module 1: Financial Statements":
    statements.render()
elif page == "Module 2: Budgeting":
    budgeting.render()
elif page == "Module 3: Variance Analysis":
    variance.render()
elif page == "Module 4: Forecasting":
    forecasting.render()
```

- [ ] **Step 3: Run and test Module 4 manually**

```bash
streamlit run app.py
```

Navigate to Module 4. For scenario 1 (hybrid), enter numbers and a written rationale. Verify both are evaluated and a combined signal is returned.

- [ ] **Step 4: Commit**

```bash
git add modules/forecasting.py app.py
git commit -m "feat: add Module 4 — Forecasting with hybrid grading"
```

---

## Task 9: Main App — Sidebar, Progress, and Module Locking

**Files:**
- Modify: `controllersim/app.py`

- [ ] **Step 1: Replace `controllersim/app.py` with the full sidebar and routing**

```python
import streamlit as st
from components.progress import init_progress, is_module_unlocked, get_readiness_score, MODULES
from modules import statements, budgeting, variance, forecasting

st.set_page_config(page_title="ControllerSim — Nexova Ltd", page_icon="📊", layout="wide")

init_progress()
progress = st.session_state.progress

# --- Sidebar ---
with st.sidebar:
    st.markdown("## 📊 ControllerSim")
    st.caption("Nexova Ltd — Controller Training")
    st.markdown("---")

    MODULE_LABELS = {
        "statements": "Module 1: Financial Statements",
        "budgeting": "Module 2: Budgeting",
        "variance": "Module 3: Variance Analysis",
        "forecasting": "Module 4: Forecasting",
    }

    pages = ["Home"]
    for module_key in MODULES:
        label = MODULE_LABELS[module_key]
        if is_module_unlocked(progress, module_key):
            status = "✅" if progress[module_key]["completed"] else "▶️"
            pages.append(f"{status} {label}")
        else:
            pages.append(f"🔒 {label}")

    pages.append("About")
    page = st.radio("", pages, label_visibility="collapsed")

    st.markdown("---")
    score = get_readiness_score(progress)
    st.metric("Controller Readiness", f"{score}/100")

# --- Page routing ---
if page == "Home":
    st.title("Welcome to ControllerSim")
    st.markdown("""
You have just joined **Nexova Ltd** as a Junior Business Controller.

Your CFO has given you four training modules. Complete them in order to build your controller skill set.

| Module | Skills | Status |
|--------|--------|--------|
| 1 — Financial Statements | Read P&L, balance sheet, cash flow | Available |
| 2 — Budgeting | Build department and headcount budgets | Unlocks after Module 1 |
| 3 — Variance Analysis | Explain actuals vs. budget in writing | Unlocks after Module 2 |
| 4 — Forecasting | Update rolling forecasts with rationale | Unlocks after Module 3 |

Select a module from the sidebar to begin.
    """)

elif "Financial Statements" in page and "🔒" not in page:
    statements.render()

elif "Budgeting" in page and "🔒" not in page:
    budgeting.render()

elif "Variance Analysis" in page and "🔒" not in page:
    variance.render()

elif "Forecasting" in page and "🔒" not in page:
    forecasting.render()

elif "🔒" in page:
    st.warning("Complete the previous module to unlock this one.")

elif page == "About":
    st.title("About ControllerSim")
    st.markdown("""
Built as part of a self-directed transition into finance.

This tool covers the core skill set of a business controller:
- Financial reporting (P&L, balance sheet, cash flow)
- Budgeting (department and headcount budgets)
- Variance analysis (actuals vs. budget, CFO-ready explanations)
- Forecasting (rolling forecast updates with narrative rationale)

**Tech stack:** Python · Streamlit · Claude AI (Anthropic)

All scenarios are based on a fictional company — Nexova Ltd.
    """)
```

- [ ] **Step 2: Run the full app and test the locking logic**

```bash
streamlit run app.py
```

Verify:
- Home page renders the module table
- Module 2, 3, 4 show 🔒 in the sidebar initially
- Clicking a locked module shows the warning message
- After completing Module 1 scenarios, Module 2 unlocks
- Readiness score updates as scenarios are completed

- [ ] **Step 3: Commit**

```bash
git add app.py
git commit -m "feat: add full sidebar navigation, module locking, and readiness score"
```

---

## Task 10: Demo Mode

**Files:**
- Modify: `controllersim/app.py`

- [ ] **Step 1: Add demo mode toggle and demo scenario to app.py**

Add this block to the sidebar section (after the readiness score metric):

```python
    st.markdown("---")
    demo_mode = st.toggle("Demo Mode", value=False, help="Shows a completed scenario — useful for sharing with recruiters.")
    st.session_state.demo_mode = demo_mode
```

Then add this demo page at the end of the routing section in app.py:

```python
# Demo mode overlay
if st.session_state.get("demo_mode", False):
    st.info("**Demo Mode** — This shows a completed scenario so recruiters can see the full experience.")
    st.markdown("---")
    st.subheader("Demo: Variance Analysis — Q2 Marketing Overspend")
    st.markdown("""
**Context:** Your CFO asks you to explain why marketing overspent in Q2.

| Line Item | Budget (€) | Actual (€) | Variance (€) |
|-----------|-----------|-----------|-------------|
| Digital Campaigns | 24,000 | 37,500 | -13,500 |
| Events | 14,000 | 14,000 | 0 |
| Software Tools | 8,000 | 8,000 | 0 |
| Travel | 4,000 | 4,000 | 0 |
| **Total** | **50,000** | **63,500** | **-13,500** |

**Student answer:** Q2 marketing spend came in at €63,500, €13,500 (27%) above the €50,000 budget — an unfavourable variance. The overspend was driven by two unplanned digital campaigns approved by the CMO mid-quarter.

**AI Feedback:** Excellent explanation. You correctly identified the variance as unfavourable, quantified the gap in both absolute and percentage terms, and clearly explained the root cause. This is exactly what a CFO wants to see.

**Tip:** In future, you could also note which specific budget line drove the overspend (Digital Campaigns) for added precision.

**Result:** ✅ Pass
    """)
    st.stop()
```

Note: Place the demo mode check at the very top of the routing section (before the `if page == "Home":` block) so it overrides all other pages.

- [ ] **Step 2: Test demo mode**

```bash
streamlit run app.py
```

Toggle Demo Mode in the sidebar. Verify it shows the completed scenario and hides all other content. Toggle it off and verify normal navigation resumes.

- [ ] **Step 3: Commit**

```bash
git add app.py
git commit -m "feat: add demo mode for recruiter-friendly portfolio presentation"
```

---

## Task 11: Branding — Nexova Ltd Theme

**Files:**
- Create: `controllersim/.streamlit/config.toml`

- [ ] **Step 1: Create `controllersim/.streamlit/config.toml`**

```toml
[theme]
primaryColor = "#1B4F72"
backgroundColor = "#F8F9FA"
secondaryBackgroundColor = "#EAF2FF"
textColor = "#1C1C1C"
font = "sans serif"

[browser]
gatherUsageStats = false
```

- [ ] **Step 2: Restart app and verify theme**

```bash
streamlit run app.py
```

Verify the app uses the dark blue primary colour for buttons and the light grey background. The sidebar should have a slightly blue-tinted background.

- [ ] **Step 3: Commit**

```bash
git add .streamlit/config.toml
git commit -m "feat: add Nexova Ltd theme via Streamlit config"
```

---

## Task 12: Deployment Preparation

**Files:**
- Create: `controllersim/.streamlit/secrets.toml.example`
- Modify: `controllersim/requirements.txt`

- [ ] **Step 1: Create `controllersim/.streamlit/secrets.toml.example`**

```toml
# Copy this file to .streamlit/secrets.toml and fill in your key.
# Never commit secrets.toml to git.
ANTHROPIC_API_KEY = "your-anthropic-api-key-here"
```

- [ ] **Step 2: Create `controllersim/.gitignore`**

```
.streamlit/secrets.toml
__pycache__/
*.pyc
.pytest_cache/
.env
```

- [ ] **Step 3: Run the full test suite one final time**

```bash
pytest tests/ -v
```

Expected: All tests pass.

- [ ] **Step 4: Push to GitHub**

```bash
git add .gitignore .streamlit/secrets.toml.example
git commit -m "feat: add deployment config and gitignore"
git remote add origin https://github.com/YOUR_USERNAME/controllersim.git
git push -u origin main
```

- [ ] **Step 5: Deploy to Streamlit Cloud**

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click "New app"
3. Select your GitHub repo and set Main file path to `app.py`
4. Under "Advanced settings → Secrets", paste:
   ```
   ANTHROPIC_API_KEY = "your-key-here"
   ```
5. Click Deploy

Expected: App is live at a public URL within 2–3 minutes.

- [ ] **Step 6: Final commit**

```bash
git commit --allow-empty -m "chore: deployed to Streamlit Cloud"
```

---

## Self-Review

**Spec coverage check:**

| Spec requirement | Covered in task |
|-----------------|----------------|
| 4 modules (Statements, Budgeting, Variance, Forecasting) | Tasks 5–8 |
| 3 scenarios per module | Task 2 (JSON data) |
| Rule-based grading for statements and budgeting | Task 4 (grade_questions, grade_table_input) |
| Claude AI feedback for variance and forecasting | Task 4 (get_ai_feedback) |
| Hybrid grading for forecasting | Task 8 |
| Progressive module unlocking | Task 9 (is_module_unlocked) |
| Controller Readiness Score 0–100 | Task 9 (get_readiness_score) |
| Demo mode for recruiters | Task 10 |
| About page | Task 9 (routing) |
| Nexova Ltd branding and theme | Task 11 |
| Streamlit Cloud deployment | Task 12 |
| API key in secrets, never in code | Tasks 4 and 12 |
| Public GitHub repo as portfolio | Task 12 |

All spec requirements covered.
