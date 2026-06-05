# Workflow: Personal Budgeting & Expense Tracking (Yash)

## Objective
Maintain Yash's monthly budget plan and track actual expenses against it,
head-wise and month-wise, flagging where he is over / under / on track. Act as
his financial guide on top of the raw numbers.

## Key files
- `data/budget_plan.json`  — source-of-truth plan (27 heads, amounts, frequency, due months). EDIT ONLY when Yash changes a budget; ask before changing.
- `data/transactions.json` — append-only ledger of actual expenses, each mapped to a `head_id`.
- `data/Yash_Budget.xlsx`  — generated master workbook (Dashboard, Plan, Monthly Actuals, Transactions).
- `data/monthly_actuals.csv` — CSV mirror of the heads x months matrix (for cloud upload).
- `tools/budget_summary.py` — prints monthly-equivalent + bare-minimum total.
- `tools/record_expenses.py` — validates + appends a staging file of mapped expenses.
- `tools/build_workbook.py` — regenerates the workbook + CSV from plan + ledger.

## Core numbers (v1, 2026-06-05)
- Bare-minimum monthly (all heads, monthly-equivalent): **Rs 2,78,667**.
- Pure lifestyle/bills burn (excludes Investment, Travelling-to-fund, IT-Tax-to-fund, EMI, Loan): ~Rs 1,48,667.
- Annualized: Rs 33,44,000.

## Normalization rules
- monthly -> x12/yr ; yearly -> /12 ; half-yearly -> x2/yr then /12.
- Monthly-equivalent = budget * occurrences_per_year / 12  (accrual / sinking-fund view).
- Cash-due-this-month = full budget in due_months, else 0 for lumpy heads (cash view).
- Dashboard shows BOTH so Yash sees the even-spread plan and the real cash spike.

## Recurring task: logging expenses (weekly/monthly)
Yash sends expenses as a typed list OR bank statement files (CSV/PDF) — handle both.

1. Parse the input into individual expenses (date, description, amount, account).
   - For statement files, drop into `.tmp/`, parse, and extract debit lines.
2. Map each expense to a `head_id` from `budget_plan.json`. Use description keywords.
   - If unsure which head, ASK Yash rather than guessing. Keep a note of recurring
     merchant -> head mappings here as they're confirmed (see Mapping memory below).
3. Write the mapped rows to `.tmp/staging_expenses.json` (see record_expenses.py format).
4. Run `python tools/record_expenses.py .tmp/staging_expenses.json`.
5. Run `python tools/build_workbook.py` (optionally with a `YYYY-MM` to set dashboard month).
6. Mirror to Google Sheets (see Cloud sync below), then summarize for Yash:
   what's over/under, running month total vs Rs 2,78,667, any heads not yet touched.

## Cloud sync (Google Sheets) — LIVE
- DONE 2026-06-05: OAuth set up via Yash's own Google Cloud project
  (`basic-thinker-498507-k4`), Desktop app client. `credentials.json` + `token.json`
  in project root (gitignored). Re-syncs run silently (no browser) via refresh token.
- Tool: `tools/sync_gsheets.py` — creates/updates the "Yash Budget" spreadsheet,
  id stored in `data/gsheet_config.json`. Pushes 4 tabs: Dashboard, Plan,
  Monthly Actuals, Transactions.
- Spreadsheet: https://docs.google.com/spreadsheets/d/1aFIJpOKSCnhM4J7oXrJXbRbYjl9dkBhLC2ZMCXqKdG8/edit
- Run `python tools/sync_gsheets.py [YYYY-MM]` after every `build_workbook.py`.
- If token ever breaks: delete token.json and re-run to re-auth.

## Mapping memory (merchant/keyword -> head)
Add confirmed mappings here so categorization gets faster over time:
- (none yet)

## Edge cases / learnings
- Lumpy heads (SP Maintenance Apr/Oct, Life Insurance May, Car Insurance Nov,
  Mediclaim Dec, Internet July, Vera annual) will show big spikes in their months.
  That's expected — judge them against Cash-Due-This-Month, not monthly-equiv.
- SP Maintenance = Rs 42,800 EACH occurrence (twice/yr), confirmed by Yash 2026-06-05.
- Never overwrite budget_plan.json without confirming the change with Yash.
