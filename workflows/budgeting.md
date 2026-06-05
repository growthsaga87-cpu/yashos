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
- `data/income.json`       — income ledger. Holds personal income on PNB 3382 (affiliate, interest, dividend, startup) AND **business income on the GrowthSaga company account (COG, account=`growthsaga_current_0512`, category=`business_income`)**. Feeds the P&L. Has `pending_classification` + `excluded_internal`. Owner's draws from GrowthSaga to personal are NOT income here (they live in `internal_register`).
- `data/internal_register.json` — money movements NOT in the budget: internal/family transfers, credit-card bill settlements, third-party-borne costs (e.g. Gopipura repair to be billed to Anita), and **GrowthSaga business charges** (`business_expenses`, e.g. bank SMS charge — not a personal head).
- `data/balances.json`     — opening/closing balance snapshots per account (assets +, liabilities -). Feeds the Balances tab / net position. Investments to be added later.
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
- Dashboard columns: Monthly Budget | for each FY month a pair {<month> actual,
  <month> vs Bud} | YTD Actual | Budget (Apr-now) = monthly_equiv x #months |
  YTD Variance | Status.
- "<Mon> vs Bud" = that month's actual - monthly budget. The variance cell is
  highlighted **red when the month overspent**, **green when under**, blank when
  there was no spend that month (build_workbook + sync_gsheets apply the colour).
  Lumpy heads (insurance, etc.) will show a big red spike in their due month —
  judge those against Cash-Due-This-Month, not the flat monthly budget.
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

## Workbook tabs (build_workbook.py / sync_gsheets.py)
Dashboard, **P&L** (income vs recorded expenses, month-wise), **Balances** (latest
position per account + net), Plan, Monthly Actuals, **Income**, Transactions.
`sync_gsheets.ensure_tabs()` adds any missing tab to the existing spreadsheet.

## Bank statements (vs card statements)
- Parse with `pdfplumber` `extract_table()` (clean cols: Date, Withdrawal, Deposit,
  Balance, Narration). Rows are reverse-chronological; use the Balance column to
  reconcile (opening + deposits - withdrawals = closing).
- Separate into: **expenses** (-> budget heads), **income** (-> income.json),
  **internal/settlement** (-> internal_register.json), and capture opening/closing
  (-> balances.json). NEVER let transfers / cc-bill payments hit the budget.
- Tag every expense note with payment mode: **"cash expense"** (ATM) vs
  **"online payment"** (UPI/GPay) so cash-vs-online is reportable per head.
- PNB savings 3382 is GPay-linked (all GPay UPI lands here). PDF opens WITHOUT a
  password.

## Special heads / rules (confirmed by Yash 2026-06-05)
- **Gold Kitty (5g gold/month)** -> head `gold_kitty` (Investment). ~Rs 15,790/mo, varies.
- **Gullak Gold** (digital gold via "gullakmoney") -> head `gullak_gold` (Investment),
  ~Rs 8,000/mo, recurring. SEPARATE from gold_kitty. Confirmed by Yash 2026-06-05; no
  dedicated tab (Yash declined) — it flows through the normal heads/tabs.
- **ICICI credit card** exists (bill paid from PNB via BillDesk). Get its statements
  to track real spends; the PNB bill payment stays in internal_register (no double count).
- **Axis credit card** (NEW, first seen May-2026; bill paid from PNB via BillDesk
  "AXIS CC PAYMEN"). Treat the PNB payment as internal settlement (like ICICI). Get the
  Axis statement to track real spends.
- **Growth Saga draws** (From:XXXX0512 / NEFT) = owner's draw from Yash's own business ->
  **internal_register.internal_transfers (in)**, NOT personal income (avoids double-count;
  real income is recognized at the Growth Saga company account — see below). Same treatment as April.
- **Growth Saga company current account (`growthsaga_current_0512`) — LIVE since 2026-06-05.**
  PNB current a/c 0910102100000512 (folder `account statements/GrowthSaga Current 0512/`). This
  is where Yash's **full-time-job income from Circle of Greatness (COG)** lands, via inbound
  foreign remittance: **NIUM PTE** (Singapore IMPS-IN) and **Citi "GLOBAL REMITTANCE-OTHERS"**
  (NEFT_IN). It's a **pass-through**: COG pays in, then almost the whole amount is drawn to
  personal PNB 3382 (`To:XXXX3382` = owner's draw). Processing rules:
  - Each COG inbound deposit -> `income.json` (account=`growthsaga_current_0512`,
    category=`business_income`, source="Circle of Greatness (COG)"). **Recognize income HERE**,
    once. The matching `To:XXXX3382` draw stays an internal transfer (don't double-count).
  - GrowthSaga bank charges (SMS chrg etc.) -> `internal_register.business_expenses` (business
    cost, NOT a personal budget head — keep them out of `transactions.json`).
  - Add opening/closing snapshots to `balances.json` (asset). Reconcile opening + income -
    draws - charges = closing; consecutive statements should chain (one's closing = next's opening).
  - Yash chose a **combined-but-tagged P&L** (2026-06-05): COG business income shows in the same
    Income/P&L as personal income, distinguishable by the Account column. P&L Net will swing large
    until more expense accounts (ICICI/Axis) are added — that's timing, not a real loss.
- **Gopipura property** maintenance + light bills (UPI payee "PRADIPKU"/"pradipshah 6971",
  BARB) -> **third_party_borne, billed to Anita Agarwal**, NOT Yash's budget. (Corrected by
  Yash 2026-06-05: PRADIPKU/pradipshah 6971 is the **Gopipura** property payee, NOT Yenpure
  — earlier entries were mislabelled Yenpure and have been relabelled Gopipura.) NOTE: a
  separate UPI payee literally named "YENPURE" (787425031...@ptsb) is Yash's own **medical**
  (kept as April) — don't conflate the two.
- **Gopipura repair** (JAG MOHA 9662992503@axl) -> third_party_borne, billed to
  **Anita Agarwal**, NOT Yash's budget.
- Income sources: **Circle of Greatness (COG)** = Yash's full-time job, recognized at the
  Growth Saga company account (`business_income`); Ambient United (startup); PayPal (affiliate);
  SGB interest; dividends. Growth Saga *draws* to personal = internal (not income).
  Anitadevi (a/c 3368) = internal, ignore.

## Mapping memory (merchant/keyword -> head)  — confirmed by Yash 2026-06-05
- Groceries/supermarket: Blinkit, "Blinkit Money", JioMart, DMart, Reliance Retail
  (grocery), Magson, M S Store, vegetable/kirana UPI (Mahesh Mannubhai, Kisanawati
  Devi, Jay Bajrangbali, etc.) -> **household**
- Restaurants / eating out: Zomato, restaurant & food-vendor UPI, The Bros Creamery,
  Rajhans Cine World (food court), Chai Naka, bakeries -> **food**
- Fuel: Krishna Petroleum + "FUEL SURCHARGE AND GST" -> **car_petrol**
- Pharmacy / clinics: Dr Agarwal's Health, Mayur Pharma -> **medical**
- Mobile: Vodafone Idea / "UPI VI", **Reliance Retail Ltd "Utilities" = phone recharge**, **Airtel** -> **phone**
- **Shaili K / UPI handle 7878972129** -> **gold_kitty** (the 5g gold kitty payee).
- **Gullak Money / "gullakmoney@yes"** -> **gullak_gold** (separate digital-gold investment).
- **AESOP TU** (mallucanvai@axl) and **BillDesk "FX Email Payme"** -> **business** (confirmed Yash 2026-06-05).
- Bakeries (e.g. "ATUL BAK"), creameries ("CREAMY S") -> **food**. Magson, Blinkit/"Blink Co" -> **household**.
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
  password.
- **PNB Savings 3382** (primary personal bank, GPay-linked; PDF opens without password).
- **GrowthSaga Current 0512** (company current a/c; COG income source — see Special heads).
  PDF opens without password.
- Still pending from Yash: **ICICI + Axis credit-card** statements (bills paid from PNB via
  BillDesk — get them to track real spends).

## Statement filing (since 2026-06-05)
- One folder per account under `account statements/<account folder>/`. IndusInd 9000 ->
  `account statements/IndusInd Platinum RuPay CC 9000/`. Each account's `statements_folder`
  is recorded in `data/accounts.json`. Naming: `<account> <period start> to <period end>.pdf`.
- **Capture state (per account):** `data/accounts.json` carries a `capture_state` block per
  account (`last_captured_date`, `captured_through_period_end`, `next_needed_from`). After
  processing a statement, UPDATE it. When Yash asks to process a new statement for an account,
  tell him to share data starting from that account's `next_needed_from`. As of 2026-06-05:
  PNB 3382 captured through 2026-06-05 (next from 2026-06-06); IndusInd 9000 through 2026-06-04
  (next from 2026-06-05); GrowthSaga 0512 through 2026-06-03 (next from 2026-06-04 — Jun is a
  partial month).

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
