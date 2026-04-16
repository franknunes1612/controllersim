# ControllerSim — Design Spec

**Date:** 2026-04-16
**Status:** Approved

---

## Overview

ControllerSim is a beginner-friendly, portfolio-first web app that teaches the core skill set of a business controller through interactive scenarios. The user plays as a junior business controller at a fictional company (Nexova Ltd) and completes real-world tasks: reading financial statements, building budgets, analysing variances, and updating forecasts.

Built with Python and Streamlit. Deployed publicly on Streamlit Cloud as both a learning tool and a career portfolio piece.

---

## Narrative & Concept

**Company:** Nexova Ltd — a fictional mid-size company with realistic financials across departments (Marketing, Operations, Sales, HR).

**Player role:** Junior Business Controller, newly hired. The CFO assigns tasks each week via scenario prompts.

**Learning philosophy:** Learn by doing exactly what the job requires. No abstract theory — every exercise mirrors a real controller task.

---

## Skill Modules

Four modules, unlocked progressively. Each module contains 3–5 scenarios.

| # | Module | Core Skills Covered |
|---|--------|---------------------|
| 1 | Financial Statements | Read and interpret P&L, balance sheet, cash flow statement |
| 2 | Budgeting | Build a department annual budget from provided assumptions |
| 3 | Variance Analysis | Compare actuals vs. budget, quantify gaps, write CFO-ready explanations |
| 4 | Forecasting | Update rolling forecast based on new actuals and business context |

Completing all scenarios in a module unlocks the next one. A **Controller Readiness Score** (0–100) is calculated on completion and is shareable.

---

## Architecture

### Project Structure

```
controllersim/
├── app.py                  # Streamlit entry point, routing, sidebar nav
├── modules/
│   ├── statements.py       # Module 1 UI and logic
│   ├── budgeting.py        # Module 2 UI and logic
│   ├── variance.py         # Module 3 UI and logic
│   └── forecasting.py      # Module 4 UI and logic
├── scenarios/
│   ├── statements.json     # Scenario data for Module 1
│   ├── budgeting.json      # Scenario data for Module 2
│   ├── variance.json       # Scenario data for Module 3
│   └── forecasting.json    # Scenario data for Module 4
├── components/
│   ├── feedback.py         # Claude API integration — grades answers, returns feedback
│   └── progress.py         # Progress tracking, scoring, session state management
└── .streamlit/
    └── config.toml         # Theme and branding config
```

### Data Flow

1. Streamlit renders the scenario UI (financial tables, charts, input fields)
2. Scenario content (financial data, questions, rubric, model answer) is loaded from JSON
3. User submits their answer
4. `feedback.py` sends the scenario context + rubric + user answer to Claude API
5. Claude returns: pass/partial/fail signal + 2–4 sentence plain-English explanation + one improvement tip
6. Progress is stored in Streamlit session state (in-memory, no database)

### State Management

No database. Streamlit session state stores:
- Current module and scenario index
- Per-scenario scores (pass / partial / fail)
- Overall Controller Readiness Score

Progress resets on page refresh. Acceptable for v1.

---

## Scenario Design

### JSON Schema (per scenario)

```json
{
  "id": "variance_001",
  "title": "Q2 Marketing Overspend",
  "prompt": "Nexova's Q2 marketing budget was €50,000. Actuals came in at €63,500. The team ran two unplanned campaigns in June. In 2–3 sentences, explain this variance to the CFO.",
  "financial_data": { },
  "answer_type": "text",
  "rubric": [
    "Identifies the variance as unfavourable",
    "Quantifies the gap (€13,500 or +27%)",
    "Explains the cause (unplanned campaigns)"
  ],
  "model_answer": "Nexova's Q2 marketing spend came in at €63,500, €13,500 (27%) above the €50,000 budget — an unfavourable variance. The overspend was driven by two unplanned campaigns executed in June that were not included in the original budget."
}
```

### Answer Types by Module

| Module | Answer Type | Grading Method |
|--------|-------------|----------------|
| Financial Statements | Multiple choice + number inputs | Exact match |
| Budgeting | Fill-in budget table (numbers) | Tolerance-based numeric check |
| Variance Analysis | Written explanation (text) | Claude grades against rubric |
| Forecasting | Number inputs + written rationale | Hybrid: numeric check + Claude |

---

## AI Feedback Layer

**Model:** Claude API (claude-sonnet-4-6 or latest available)

**Prompt structure sent to Claude:**
- Scenario description and financial data
- The rubric (key points a correct answer must cover)
- The user's submitted answer

**Claude responds with:**
- Signal: `pass` / `partial` / `fail`
- 2–4 sentences of plain-English feedback referencing the user's specific answer
- One concrete improvement tip

**Example feedback (partial):**
> "You correctly identified the variance as unfavourable — good instinct. However, you didn't quantify it. A CFO always wants the number: €13,500 over budget, or +27%. Next time, lead with the figure before explaining the cause."

Claude API key is stored as a Streamlit secret, never in source code.

---

## UX & Portfolio Design

### Two Modes

- **Learn mode** — full interactive experience, user works through scenarios
- **Demo mode** — auto-plays a completed scenario with sample answers, allowing recruiters to see the full experience without completing exercises

Mode is toggled in the sidebar.

### Sidebar Navigation

- Nexova Ltd logo + branding
- Module list with completion indicators (locked / in progress / complete)
- Mode toggle (Learn / Demo)
- About this project link

### "About This Project" Page

Always visible. Serves as an in-app cover letter:

> Built by [name] as part of a self-directed transition into finance. Covers the core skill set of a business controller: financial reporting, budgeting, variance analysis, and forecasting. Built with Python, Streamlit, and Claude AI.

### Visual Components

- Financial tables: Streamlit native dataframe
- Budget vs. actuals charts: Plotly bar/line charts
- Nexova Ltd colour scheme applied via `.streamlit/config.toml`
- No custom CSS or complex animations required

---

## Deployment

- **Platform:** Streamlit Cloud (free tier)
- **Repository:** GitHub (public, part of portfolio)
- **URL:** Public, shareable link
- **Secrets:** Claude API key stored in Streamlit Cloud secrets manager

---

## Out of Scope (v1)

- User accounts or persistent progress across sessions
- Mobile-optimised layout
- More than 4 modules
- Real company financial data
- Multiplayer or leaderboard features
