# Workflow: Personal Budgeting & Expense Tracking (Yash)

## Objective
Maintain Yash's monthly budget plan and track actual expenses against it,
head-wise and month-wise, flagging where he is over / under / on track. Act as
his financial guide on top of the raw numbers.

## Key files
- `data/budget_plan.json`  — source-of-truth plan (27 heads, amounts, frequency, due months). EDIT ONLY when Yash changes a budget; ask before changing.
- `data/transactions.json` — append-only ledger of actual expenses, each mapped to a `head_id`.
- `data/accounts.json`     — registry of Yash's payment accounts (cards/banks). Map every statement to the right account; grow as new accounts arrive.
- `data/statement_register.json` — per-statement dues (period, total/min due, due date) so we can answer "what's still due this month".
- `data/Yash_Budget.xlsx`  — generated master workbook (Dashboard, Plan, Monthly Actuals, Transactions).
- `data/monthly_actuals.csv` — CSV mirror of the heads x months matrix (for cloud upload).
- `tools/budget_summary.py` — prints monthly-equivalent + bare-minimum total.
- `tools/record_expenses.py` — validates + appends a staging file of mapped expenses.
- `tools/build_workbook.py` — regenerates the workbook + CSV from plan + ledger.
- NOTE: `data/` and `account statements/` are gitignored (repo is PUBLIC). Financial data lives local + Google Sheet only; only code/tools/workflows go to GitHub.

## Core numbers (v1, 2026-06-05)
- Bare-minimum monthly (all heads, monthly-equivalent): **Rs 2,78,667**.
- Pure lifestyle/bills burn (excludes Investment, Travelling-to-fund, IT-Tax-to-fund, EMI, Loan): ~Rs 1,48,667.
- Annualized: Rs 33,44,000.

## Normalization rules
- monthly -> x12/yr ; yearly -> /12 ; half-yearly -> x2/yr then /12.
- Monthly-equivalent = budget * occurrences_per_year / 12  (accrual / sinking-fund view).
- Cash-due-this-month = full budget in due_months, else 0 for lumpy heads (cash view).

## Dashboard layout (FY-aware, since 2026-06-05)
- Tracking the Indian financial year **FY 2026-27 (April -> March)**.
- Dashboard + Monthly Actuals show one column **per FY month from April through the
  current month** (auto-extends each month; empty months show 0). Helpers live in
  `lib_budget.py` (`fy_months`, `dashboard_matrix`, `current_month`).
- Dashboard columns: Monthly Budget | <each month actual> | YTD Actual |
  Budget (Apr-now) = monthly_equiv x #months | Variance | Status.
- Run `python tools/build_workbook.py [YYYY-MM]` — the optional arg sets the
  "as-of" month the axis runs up to (default = current month).

## Recurring task: logging expenses (weekly/monthly)
Yash sends expenses as a typed list OR bank statement files (CSV/PDF) — handle both.

1. Parse the input into individual expenses (date, description, amount, account).
   - For statement files, drop into `.tmp/`, parse, and extract debit lines.
2. Map each expense to a `head_id` from `budget_plan.json`. Use description keywords.
   - If unsure which head, ASK Yash rather than guessing. Keep a note of recurring
     merchant -> head mappings here as they're confirmed (see Mapping memory below).
3. Write the mapped rows to `.tmp/staging_expenses.json` (see record_expenses.py format).
4. Run `python tools/record_expenses.py .tmp/staging_expenses.json`.
5. Run `python tools/build_workbook.py` (optionally with a `YYYY-MM` as-of month; default = current month — see Dashboard layout below).
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

## Mapping memory (merchant/keyword -> head)  — confirmed by Yash 2026-06-05
- Groceries/supermarket: Blinkit, "Blinkit Money", JioMart, DMart, Reliance Retail
  (grocery), Magson, M S Store, vegetable/kirana UPI (Mahesh Mannubhai, Kisanawati
  Devi, Jay Bajrangbali, etc.) -> **household**
- Restaurants / eating out: Zomato, restaurant & food-vendor UPI, The Bros Creamery,
  Rajhans Cine World (food court), Chai Naka, bakeries -> **food**
- Fuel: Krishna Petroleum + "FUEL SURCHARGE AND GST" -> **car_petrol**
- Pharmacy / clinics: Dr Agarwal's Health, Mayur Pharma -> **medical**
- Mobile: Vodafone Idea / "UPI VI", **Reliance Retail Ltd "Utilities" = phone recharge** -> **phone**
- Apparel: Landmark/EasyBuy, Maximal Ventures -> **shopping**
- Recreation/clubs/cinema: Avadh Clubs, Imagicaa, **Paraizo Club**, **PVR**, Chhaba -> **entertainment**
- School: Fountainhead -> **school_fees** (Saisha's school)
- Zillion Analytics -> **business**
- **CRED** ("Merchandise" debits) -> **misc** (confirmed park-in-misc)
- **Ola Financial Services** (cab/Ola Money) -> **misc**
- **IRCTC** = dad's card -> **misc** (not Yash's own travel; park here for now)
- Personal care (e.g. Satyveer Sain) -> **misc** (no dedicated head)

## Refund / credit handling (confirmed approach)
- Record refunds/reversals as **negative** rows to the SAME head so a charged-then-
  refunded item (e.g. Imagicaa) nets to zero. Surcharge waivers offset fuel surcharge.
- **Skip** card payments (BBPS PAYMENT) — they aren't expenses.
- Statement reconciliation: staged DR total must equal the statement's
  "Purchases & Other Charges"; recorded credits (excl. BBPS) + BBPS = "Payment & Other Credits".

## Accounts on file
- **IndusInd Platinum RuPay Credit Card ending 9000** (Yash's main UPI/spending card).
  Cycle ~5th-to-4th, statement day 4, due day 24. Statements decrypt with Yash's PDF
  password. Still pending from Yash: other cards + primary bank account(s).

## Statement filing (since 2026-06-05)
- One folder per account under `account statements/<account folder>/`. IndusInd 9000 ->
  `account statements/IndusInd Platinum RuPay CC 9000/`. Each account's `statements_folder`
  is recorded in `data/accounts.json`. Naming: `<account> <period start> to <period end>.pdf`.

## Git (since 2026-06-05)
- Remote: https://github.com/growthsaga87-cpu/yashos (PUBLIC). Push as owner
  `growthsaga87-cpu`. After any code/tool/workflow change, commit + push.
- `data/` & `account statements/` are gitignored — never force-add them.

## Edge cases / learnings
- Lumpy heads (SP Maintenance Apr/Oct, Life Insurance May, Car Insurance Nov,
  Mediclaim Dec, Internet July, Vera annual) will show big spikes in their months.
  That's expected — judge them against Cash-Due-This-Month, not monthly-equiv.
- SP Maintenance = Rs 42,800 EACH occurrence (twice/yr), confirmed by Yash 2026-06-05.
- Never overwrite budget_plan.json without confirming the change with Yash.
- A single statement can straddle two calendar months (e.g. 05/04-04/05): map each
  txn to its own date's month. Watch consecutive statements for clean period
  boundaries (no overlap) — verify closing balance of one = opening of the next.
