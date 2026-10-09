# Messy Data Cleaner

Turning a real-world messy sales export into an analysis-ready dataset — with a
repeatable script and an auditable change log, not manual spreadsheet edits.

**1,065 rows in → 892 clean rows out. 58 rows quarantined, 0 silently deleted.**

---

## The problem

This is what a small business export actually looks like after two years of
five different people editing the same spreadsheet:

| order_id | customer_name | email | city | product | quantity | unit_price | order_date | status |
|---|---|---|---|---|---|---|---|---|
| ORD-1263 | `Indra Pratama` | indra.pratama@outlook.com | Jakarta | Laptop Stand | 5 | `Rp 185.000` | `2024-12-03` | `Cancelled` |
| ORD-1839 | `MAYA PERMATA` | maya.permata@outlook.com | `Den Pasar` | Monitor 24 inch | 2 | `1850000.00` | `16-01-2025` | `completed` |
| ORD-1334 | `··Eko Permata··` | eko.permata@gmail.com | `YOGYAKARTA` | `MONITOR 24 INCH` | `6 pcs` | `Rp1850000` | `06/01/2025` | `Completed` |
| ORD-1200 | `joko pratama` | `joko.pratama@gmail` | `Jakarta Pusat` | `EXTERNAL SSD 1TB` | `-3` | `980000` | `2026/05/27` | `PENDING` |

Six date formats. Five currency formats. Nine spellings of four statuses.
Duplicates pasted twice. Invalid emails. Negative quantities.

## The result

| order_id | order_date | customer_name | email | city | product | quantity | unit_price | total_amount | status |
|---|---|---|---|---|---|---|---|---|---|
| ORD-1902 | 2024-01-01 | Gilang Anggraini | gilang.anggraini@gmail.com | Bandung | Mechanical Keyboard | 4 | 750000.0 | 3000000.0 | pending |
| ORD-1452 | 2024-01-03 | Maya Hidayat | maya.hidayat@yahoo.com | Yogyakarta | Mechanical Keyboard | 6 | 750000.0 | 4500000.0 | cancelled |
| ORD-1382 | 2024-01-06 | Fitri Santoso | fitri.santoso@outlook.com | Medan | External SSD 1TB | 2 | 980000.0 | 1960000.0 | completed |

One date format. Numeric currency. A `total_amount` column that didn't exist
before. Consistent casing throughout.

### What changed, measured

| Field | Before | After |
|---|---|---|
| Date formats | 6 | 1 (ISO `YYYY-MM-DD`) |
| Price formats | 5 | numeric |
| City spellings | 12 variants | 8 canonical |
| Status values | 9 variants | 4 canonical |
| Duplicate orders | 103 | 0 |
| Invalid emails | 52 | blanked, rows kept |
| Blank padding rows | 12 | 0 |

---

## Design decisions

These are the parts that separate a script from a deliverable a client can trust.

**Nothing is silently dropped.** 58 rows had unparseable prices, missing dates,
or impossible quantities. They go to `data/rejected_rows.csv` with a
`reject_reason` column — the client reviews them instead of wondering where
their data went.

**Ambiguity is reported, not guessed.** `06/01/2025` is valid as both 6 January
and 1 June. The parser applies the Indonesian DD/MM convention, counts how many
rows were ambiguous (245), and flags it in the change log for confirmation.
A cleaner that guesses silently is a cleaner that corrupts data quietly.

**Acronyms survive.** Blind `.title()` casing turns `External SSD 1TB` into
`External Ssd 1Tb`. Product names map to a canonical catalogue instead, and
anything not in the catalogue is left untouched and counted.

**Invalid emails are blanked, not deleted.** A customer with a broken email is
still a customer. The address is emptied; the order stays.

**Every run produces a change log.** `reports/change_log.md` lists each step,
what it changed, and how many rows it touched — so the work is auditable rather
than taken on faith.

---

## Running it

```bash
pip install -r requirements.txt

# regenerate the messy sample data (optional)
python src/make_messy_data.py

# clean it
python src/clean.py data/raw_sales.csv

# run the tests
pytest -q
```

### Output

| File | What it is |
|---|---|
| `data/clean_sales.csv` | The cleaned dataset |
| `data/rejected_rows.csv` | Rows needing human review, with reasons |
| `reports/change_log.md` | Step-by-step record of every change |

---

## Tests

8 unit tests covering the parsers individually — currency formats, date
ambiguity resolution, email validation, unit stripping, city and product
canonicalisation.

```
$ pytest -q
........                                    [100%]
8 passed in 0.54s
```

---

## Project layout

```
messy-data-cleaner/
├── data/
│   ├── raw_sales.csv         # messy input (generated)
│   ├── clean_sales.csv       # cleaned output
│   └── rejected_rows.csv     # quarantined rows + reasons
├── reports/
│   └── change_log.md         # auto-generated audit trail
├── src/
│   ├── make_messy_data.py    # sample data generator
│   └── clean.py              # the pipeline
├── tests/
│   └── test_clean.py
└── requirements.txt
```

## Stack

Python · pandas · pytest

---

**Nadia Pramesti** — [GitHub](https://github.com/nadiapramesti)

Available for data cleaning and automation work.
