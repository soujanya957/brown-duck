"""Build BOM.md from BOM.csv and compute the totals.

BOM.csv is the source of truth: edit it (add us_source links, update status), then run

    python hardware/make_bom_md.py

Line total = unit price x qty when qty is a whole number; otherwise (e.g. "1 kit", "~500 g")
the unit price is already the price of the lot. Rows without a price are left out of the totals.
"""

import csv
from pathlib import Path

HERE = Path(__file__).resolve().parent


def line_total(row):
    if not row["unit_price_eur_upstream"]:
        return None
    price = float(row["unit_price_eur_upstream"])
    qty = row["qty"]
    return price * int(qty) if qty.isdigit() else price


def main():
    with open(HERE / "BOM.csv", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    core = sum(t for r in rows if not r["category"].endswith("(optional)") and (t := line_total(r)) is not None)
    optional = sum(t for r in rows if r["category"].endswith("(optional)") and (t := line_total(r)) is not None)
    unpriced = [r["part"] for r in rows if line_total(r) is None]

    out = [
        "# Bill of materials",
        "",
        "Generated from [`BOM.csv`](BOM.csv) by `python hardware/make_bom_md.py`. Edit the CSV, not this file.",
        "Source: the [official Open Duck Mini v2 BOM spreadsheet]"
        "(https://docs.google.com/spreadsheets/d/1gq4iWWHEJVgAA_eemkTEsshXqrYlFxXAPwO515KpCJc),",
        "plus items the [assembly guide](../Open_Duck_Mini/docs/assembly_guide.md) needs but the sheet leaves out.",
        "",
        f"| | EUR |",
        f"|---|---:|",
        f"| **Robot total** | **{core:.2f}** |",
        f"| Expression package (optional) | {optional:.2f} |",
        f"| Robot + expression package | {core + optional:.2f} |",
        "",
        "Prices are **upstream EU prices** (mostly amazon.fr / AliExpress) from the spreadsheet, per unit"
        " unless noted. **Shipping, tax and US prices are extra**: fill in `us_source` as you find US sellers.",
        f"Not priced yet: {', '.join(unpriced)}.",
        "",
        "| Category | Part | Qty | Unit € | Line € | Notes | US source | Status |",
        "|---|---|---:|---:|---:|---|---|---|",
    ]
    for r in rows:
        t = line_total(r)
        out.append(
            f"| {r['category']} | {r['part']} | {r['qty']} | {r['unit_price_eur_upstream']} | "
            f"{'' if t is None else f'{t:.2f}'} | {r['notes']} | {r['us_source']} | {r['status']} |"
        )
    (HERE / "BOM.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"robot total {core:.2f} EUR, expression package {optional:.2f} EUR, {len(rows)} rows")


if __name__ == "__main__":
    main()
