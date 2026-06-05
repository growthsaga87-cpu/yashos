"""
lib_budget.py — Shared helpers for the budgeting tools.

Loads the plan and ledger, and computes monthly-equivalent and
"cash due this month" figures per head. Also provides the Indian
financial-year month axis (April -> March) used by the dashboard.
"""
import datetime
import json
from collections import defaultdict
from pathlib import Path

MONTH_NAMES = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

ROOT = Path(__file__).resolve().parent.parent
PLAN_PATH = ROOT / "data" / "budget_plan.json"
LEDGER_PATH = ROOT / "data" / "transactions.json"
INCOME_PATH = ROOT / "data" / "income.json"
BALANCES_PATH = ROOT / "data" / "balances.json"


def load_plan():
    return json.loads(PLAN_PATH.read_text(encoding="utf-8"))


def load_ledger():
    return json.loads(LEDGER_PATH.read_text(encoding="utf-8"))


def load_income():
    if not INCOME_PATH.exists():
        return {"income": [], "pending_classification": [], "excluded_internal": []}
    return json.loads(INCOME_PATH.read_text(encoding="utf-8"))


def load_balances():
    if not BALANCES_PATH.exists():
        return {"accounts": []}
    return json.loads(BALANCES_PATH.read_text(encoding="utf-8"))


def save_ledger(ledger):
    LEDGER_PATH.write_text(json.dumps(ledger, indent=2, ensure_ascii=False),
                           encoding="utf-8")


def occurrences(plan, frequency):
    return plan["frequency_rules"][frequency]["occurrences_per_year"]


def monthly_equivalent(plan, head):
    return head["budget"] * occurrences(plan, head["frequency"]) / 12.0


def cash_due(head, month_num):
    """Actual cash the bill demands in a given calendar month (1-12).
    Monthly heads are due every month; lumpy heads only in their due_months."""
    if head["frequency"] == "monthly":
        return head["budget"]
    if month_num in head.get("due_months", []):
        return head["budget"]
    return 0.0


def head_index(plan):
    return {h["id"]: h for h in plan["heads"]}


def valid_head_ids(plan):
    return {h["id"] for h in plan["heads"]}


# ---------------------------------------------------------------- FY axis
def current_month():
    """Today's month as 'YYYY-MM' (Indian local context)."""
    return datetime.date.today().strftime("%Y-%m")


def fy_start_year(year, month):
    """Indian financial year starts in April. Return the FY's starting year."""
    return year if month >= 4 else year - 1


def month_label(ym):
    """'2026-04' -> 'Apr 2026'."""
    y, m = ym.split("-")
    return f"{MONTH_NAMES[int(m)]} {y}"


def fy_months(as_of=None):
    """FY month axis: every 'YYYY-MM' from April of the as_of month's financial
    year up to and including as_of. e.g. as_of='2026-06' -> Apr,May,Jun 2026."""
    if as_of is None:
        as_of = current_month()
    y, m = int(as_of[:4]), int(as_of[5:7])
    sy = fy_start_year(y, m)
    out = []
    yy, mm = sy, 4
    while (yy, mm) <= (y, m):
        out.append(f"{yy:04d}-{mm:02d}")
        mm += 1
        if mm == 13:
            mm, yy = 1, yy + 1
    return out


def actuals_by_head_month(ledger):
    """head_id -> month -> summed actual spend."""
    d = defaultdict(lambda: defaultdict(float))
    for t in ledger["transactions"]:
        d[t["head_id"]][t["month"]] += t["amount"]
    return d


def dashboard_matrix(plan, ledger, months):
    """Multi-month FY dashboard as plain data (no styling).

    Returns (headers, body_rows, total_row). Each body row is:
      [particulars, monthly_budget, <actual per month...>, ytd, period_budget,
       variance, status]
    period_budget = monthly_equivalent * number_of_months (accrual benchmark);
    variance = ytd - period_budget; status flags OVER / Under / On Track.
    """
    abm = actuals_by_head_month(ledger)
    n = len(months)
    headers = (["Particulars", "Monthly Budget"]
               + [month_label(m) for m in months]
               + ["YTD Actual", "Budget (Apr-now)", "Variance", "Status"])
    body = []
    tot_me = tot_ytd = 0.0
    tot_month = [0.0] * n
    for h in plan["heads"]:
        me = monthly_equivalent(plan, h)
        vals = [abm.get(h["id"], {}).get(m, 0.0) for m in months]
        ytd = sum(vals)
        pbudget = me * n
        var = ytd - pbudget
        if ytd == 0:
            status = "No spend logged"
        elif var > 0.05 * pbudget:
            status = "OVER"
        elif var < -0.05 * pbudget:
            status = "Under"
        else:
            status = "On Track"
        body.append([h["particulars"], round(me)] + [round(v) for v in vals]
                    + [round(ytd), round(pbudget), round(var), status])
        tot_me += me
        tot_ytd += ytd
        for i, v in enumerate(vals):
            tot_month[i] += v
    total = (["TOTAL", round(tot_me)] + [round(x) for x in tot_month]
             + [round(tot_ytd), round(tot_me * n), round(tot_ytd - tot_me * n), ""])
    return headers, body, total


# ---------------------------------------------------------------- income / P&L
def income_by_month(income):
    d = defaultdict(float)
    for r in income.get("income", []):
        d[r["date"][:7]] += float(r["amount"])
    return d


def expense_by_month(ledger):
    d = defaultdict(float)
    for t in ledger["transactions"]:
        d[t["month"]] += float(t["amount"])
    return d


def income_matrix(income, months):
    """Income tab as plain data: (headers, body_rows, total_row)."""
    headers = ["Date", "Source", "Category", "Amount", "Account", "Note"]
    body = [[r["date"], r["source"], r.get("category", ""), round(float(r["amount"])),
             r.get("account", ""), r.get("note", "")]
            for r in sorted(income.get("income", []), key=lambda x: x["date"])]
    total = ["TOTAL", "", "", round(sum(float(r["amount"]) for r in income.get("income", []))), "", ""]
    return headers, body, total


def pnl_matrix(ledger, income, months):
    """Month-on-month P&L: (headers, body_rows). Rows: Income, Expenses, Net."""
    inc = income_by_month(income)
    exp = expense_by_month(ledger)
    headers = ["Line"] + [month_label(m) for m in months] + ["YTD"]
    inc_row = ["Total Income"] + [round(inc.get(m, 0.0)) for m in months] + [round(sum(inc.get(m, 0.0) for m in months))]
    exp_row = ["Total Expenses (recorded)"] + [round(exp.get(m, 0.0)) for m in months] + [round(sum(exp.get(m, 0.0) for m in months))]
    net_row = ["Net (Income - Expenses)"] + [round(inc.get(m, 0.0) - exp.get(m, 0.0)) for m in months] + [round(sum(inc.get(m, 0.0) - exp.get(m, 0.0) for m in months))]
    return headers, [inc_row, exp_row, net_row]


# ---------------------------------------------------------------- balances
def balances_matrix(balances):
    """Latest balance per account + net position.
    Returns (headers, body_rows, net_row). Liabilities are shown negative."""
    headers = ["Account", "Type", "Latest Balance", "As Of", "Source"]
    body = []
    net = 0.0
    for a in balances.get("accounts", []):
        snaps = sorted(a.get("snapshots", []), key=lambda s: s["date"])
        if not snaps:
            continue
        last = snaps[-1]
        signed = last["balance"] if a["kind"] == "asset" else -last["balance"]
        net += signed
        body.append([a["name"], a["kind"], round(signed), last["date"], last.get("source", "")])
    net_row = ["NET POSITION (assets - liabilities)", "", round(net), "", ""]
    return headers, body, net_row
