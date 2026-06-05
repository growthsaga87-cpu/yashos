"""
budget_summary.py — Normalize the budget plan to monthly-equivalent figures.

Reads data/budget_plan.json and prints, per head:
  - the amount per occurrence (as Yash entered it)
  - the frequency
  - the monthly-equivalent (budget * occurrences_per_year / 12)
plus the total monthly-equivalent = the "bare minimum monthly income" target.

Usage:
    python tools/budget_summary.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLAN = ROOT / "data" / "budget_plan.json"


def monthly_equivalent(head, rules):
    occ = rules[head["frequency"]]["occurrences_per_year"]
    return head["budget"] * occ / 12.0


def main():
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    rules = plan["frequency_rules"]
    heads = plan["heads"]

    rows = []
    for h in heads:
        rows.append((h["particulars"], h["budget"], h["frequency"],
                     monthly_equivalent(h, rules)))

    rows.sort(key=lambda r: r[3], reverse=True)

    w = max(len(r[0]) for r in rows)
    print(f"{'Particulars':<{w}}  {'Per Occurrence':>15}  {'Frequency':<12}  {'Monthly Equiv':>14}")
    print("-" * (w + 48))
    total_monthly = 0.0
    pure_monthly = 0.0
    for name, budget, freq, me in rows:
        print(f"{name:<{w}}  {budget:>15,.0f}  {freq:<12}  {me:>14,.2f}")
        total_monthly += me
        if freq == "monthly":
            pure_monthly += me

    print("-" * (w + 48))
    print(f"{'TOTAL MONTHLY-EQUIVALENT (bare minimum income)':<{w}}  "
          f"{'':>15}  {'':<12}  {total_monthly:>14,.2f}")
    print()
    print(f"  Pure monthly recurring outflow : Rs {pure_monthly:>14,.2f}")
    print(f"  Lumpy (annual/half-yearly) /12 : Rs {total_monthly - pure_monthly:>14,.2f}")
    print(f"  Annualized total               : Rs {total_monthly * 12:>14,.2f}")


if __name__ == "__main__":
    main()
