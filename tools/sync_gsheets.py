"""
sync_gsheets.py — Mirror the budget workbook to Google Sheets.

Auth (one-time): place your OAuth client as credentials.json in the project root
(from your own Google Cloud project, signed in with the account you want to use).
First run opens a browser to sign in and writes token.json. The account you sign
in with is the account this tool uses from then on.

On first sync it creates a spreadsheet named "Yash Budget" and saves its id in
data/gsheet_config.json. Later runs update that same spreadsheet.

Builds the same four tabs as the local xlsx: Dashboard, Plan, Monthly Actuals,
Transactions.

Usage:
    python tools/sync_gsheets.py                 # dashboard = latest month
    python tools/sync_gsheets.py 2026-06         # dashboard for a specific month
"""
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

from lib_budget import (load_plan, load_ledger, load_income, load_balances,
                        monthly_equivalent, actuals_by_head_month, dashboard_matrix,
                        fy_months, current_month, income_matrix, pnl_matrix,
                        balances_matrix, ROOT)

CONFIG = ROOT / "data" / "gsheet_config.json"
CREDS = ROOT / "credentials.json"
TOKEN = ROOT / "token.json"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets",
          "https://www.googleapis.com/auth/drive.file"]
SHEET_TITLE = "Yash Budget"


# ---------------------------------------------------------------- auth
def get_service():
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    if not CREDS.exists():
        sys.exit(f"Missing {CREDS}. Download your OAuth client from Google Cloud "
                 f"and save it there. See workflows/budgeting.md.")

    creds = None
    if TOKEN.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDS), SCOPES)
            creds = flow.run_local_server(port=0)
        TOKEN.write_text(creds.to_json(), encoding="utf-8")
    return build("sheets", "v4", credentials=creds)


# ---------------------------------------------------------------- data
def dashboard_rows(plan, ledger, months):
    span = f"{months[0]} to {months[-1]}" if months else "no data yet"
    headers, body, total = dashboard_matrix(plan, ledger, months)
    rows = [[f"BUDGET DASHBOARD  —  FY 2026-27  ({span})"], [], headers]
    rows.extend(body)
    rows.append(total)
    return rows


def plan_rows(plan):
    rows = [["Particulars", "Per Occurrence", "Frequency", "Due Months",
             "Monthly Equivalent", "Remarks"]]
    total = 0.0
    for h in plan["heads"]:
        me = monthly_equivalent(plan, h); total += me
        due = ", ".join(str(m) for m in h.get("due_months", [])) or "-"
        rows.append([h["particulars"], h["budget"], h["frequency"], due,
                     round(me), h["remarks"]])
    rows.append(["TOTAL (bare-minimum monthly)", "", "", "", round(total), ""])
    return rows


def monthly_actuals_rows(plan, ledger, months):
    abm = actuals_by_head_month(ledger)
    rows = [["Particulars", "Monthly Budget"] + months]
    col_tot = defaultdict(float)
    for h in plan["heads"]:
        me = monthly_equivalent(plan, h)
        r = [h["particulars"], round(me)]
        for m in months:
            v = abm.get(h["id"], {}).get(m, 0.0)
            r.append(round(v)); col_tot[m] += v
        rows.append(r)
    rows.append(["TOTAL", round(sum(monthly_equivalent(plan, h) for h in plan["heads"]))]
                + [round(col_tot[m]) for m in months])
    return rows


def income_rows(income, months):
    headers, body, total = income_matrix(income, months)
    rows = [headers] + body + [total]
    for title, key in [("OTHER INFLOWS - not income (asset sale / capital refund)", "other_inflows"),
                       ("PENDING CLASSIFICATION (not counted yet)", "pending_classification")]:
        items = income.get(key, [])
        if items:
            rows += [[], [title]]
            rows += [[r["date"], r["source"], r.get("category", ""),
                      round(float(r["amount"])), "", r.get("note", "")] for r in items]
    return rows


def pnl_rows(ledger, income, months):
    headers, body = pnl_matrix(ledger, income, months)
    return [["PROFIT & LOSS  —  FY 2026-27  (income vs recorded expenses)"], [], headers] + body


def balances_rows(balances):
    headers, body, net = balances_matrix(balances)
    return [["ACCOUNT BALANCES  —  latest known position"], [], headers] + body + [net]


def transaction_rows(ledger):
    rows = [["Date", "Month", "Description", "Amount", "Account", "Head", "Note"]]
    for t in sorted(ledger["transactions"], key=lambda x: x["date"]):
        rows.append([t["date"], t["month"], t["description"], t["amount"],
                     t["account"], t["head_id"], t["note"]])
    return rows


# ---------------------------------------------------------------- sheets ops
def ensure_spreadsheet(svc):
    if CONFIG.exists():
        return json.loads(CONFIG.read_text(encoding="utf-8"))["spreadsheet_id"]
    ss = svc.spreadsheets().create(body={
        "properties": {"title": SHEET_TITLE},
        "sheets": [{"properties": {"title": t}} for t in
                   ("Dashboard", "Plan", "Monthly Actuals", "Transactions")],
    }).execute()
    sid = ss["spreadsheetId"]
    CONFIG.write_text(json.dumps(
        {"spreadsheet_id": sid, "url": ss["spreadsheetUrl"]}, indent=2),
        encoding="utf-8")
    print(f"Created spreadsheet: {ss['spreadsheetUrl']}")
    return sid


def ensure_tabs(svc, sid, tab_names):
    """Add any missing tabs to an existing spreadsheet."""
    meta = svc.spreadsheets().get(spreadsheetId=sid).execute()
    existing = {s["properties"]["title"] for s in meta["sheets"]}
    requests = [{"addSheet": {"properties": {"title": t}}}
                for t in tab_names if t not in existing]
    if requests:
        svc.spreadsheets().batchUpdate(
            spreadsheetId=sid, body={"requests": requests}).execute()


def write_tab(svc, sid, tab, rows):
    svc.spreadsheets().values().clear(
        spreadsheetId=sid, range=f"'{tab}'").execute()
    svc.spreadsheets().values().update(
        spreadsheetId=sid, range=f"'{tab}'!A1",
        valueInputOption="RAW", body={"values": rows}).execute()


def main(as_of=None):
    plan = load_plan()
    ledger = load_ledger()
    income = load_income()
    balances = load_balances()
    if as_of is None:
        as_of = current_month()
    months = fy_months(as_of)

    svc = get_service()
    sid = ensure_spreadsheet(svc)
    ensure_tabs(svc, sid, ["Dashboard", "P&L", "Balances", "Plan",
                           "Monthly Actuals", "Income", "Transactions"])
    write_tab(svc, sid, "Dashboard", dashboard_rows(plan, ledger, months))
    write_tab(svc, sid, "P&L", pnl_rows(ledger, income, months))
    write_tab(svc, sid, "Balances", balances_rows(balances))
    write_tab(svc, sid, "Plan", plan_rows(plan))
    write_tab(svc, sid, "Monthly Actuals", monthly_actuals_rows(plan, ledger, months))
    write_tab(svc, sid, "Income", income_rows(income, months))
    write_tab(svc, sid, "Transactions", transaction_rows(ledger))

    url = json.loads(CONFIG.read_text(encoding="utf-8")).get("url", "")
    print(f"Synced to Google Sheets. FY axis: {', '.join(months)}")
    print(url)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
