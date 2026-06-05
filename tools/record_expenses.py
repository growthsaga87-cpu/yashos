"""
record_expenses.py — Append mapped expenses to the ledger.

The agent maps each raw expense to a head_id (from budget_plan.json), writes a
staging JSON file, then runs this tool to validate + append to the ledger.

Staging file format (a JSON list):
[
  {"date": "2026-06-03", "description": "Big Bazaar groceries",
   "amount": 4500, "account": "HDFC", "head_id": "household", "note": ""},
  ...
]

Usage:
    python tools/record_expenses.py .tmp/staging_expenses.json
"""
import json
import sys
from pathlib import Path

from lib_budget import load_plan, load_ledger, save_ledger, valid_head_ids


def normalize_month(date_str):
    # Expect YYYY-MM-DD; derive YYYY-MM
    return date_str[:7]


def main(staging_path):
    rows = json.loads(Path(staging_path).read_text(encoding="utf-8"))
    plan = load_plan()
    ledger = load_ledger()
    valid = valid_head_ids(plan)

    errors = []
    cleaned = []
    for i, r in enumerate(rows):
        missing = [k for k in ("date", "amount", "head_id") if k not in r]
        if missing:
            errors.append(f"row {i}: missing {missing}")
            continue
        if r["head_id"] not in valid:
            errors.append(f"row {i}: unknown head_id '{r['head_id']}'")
            continue
        cleaned.append({
            "date": r["date"],
            "month": normalize_month(r["date"]),
            "description": r.get("description", ""),
            "amount": float(r["amount"]),
            "account": r.get("account", ""),
            "head_id": r["head_id"],
            "note": r.get("note", ""),
        })

    if errors:
        print("VALIDATION FAILED — nothing recorded:")
        for e in errors:
            print("  -", e)
        sys.exit(1)

    ledger["transactions"].extend(cleaned)
    save_ledger(ledger)
    total = sum(r["amount"] for r in cleaned)
    print(f"Recorded {len(cleaned)} expense(s), total Rs {total:,.2f}.")
    print(f"Ledger now holds {len(ledger['transactions'])} transaction(s).")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python tools/record_expenses.py <staging_file.json>")
        sys.exit(2)
    main(sys.argv[1])
