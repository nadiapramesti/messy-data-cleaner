"""
Generate a realistically messy sales CSV.

This simulates the kind of export a small business actually sends you:
spreadsheet edited by five different people over two years.
Run once to regenerate data/raw_sales.csv.
"""

import random
import csv

random.seed(42)

FIRST = ["Andi", "Budi", "Citra", "Dewi", "Eko", "Fitri", "Gilang",
         "Hana", "Indra", "Joko", "Kiki", "Lina", "Maya", "Nanda",
         "Oka", "Putri", "Rizky", "Sari", "Tono", "Umi"]
LAST = ["Santoso", "Wijaya", "Pratama", "Lestari", "Nugroho",
        "Hidayat", "Permata", "Saputra", "Anggraini", "Kusuma"]

PRODUCTS = [
    ("Wireless Mouse", 150000),
    ("Mechanical Keyboard", 750000),
    ("USB-C Hub", 320000),
    ("Laptop Stand", 185000),
    ("Webcam HD", 450000),
    ("Noise Cancelling Headset", 1250000),
    ("Monitor 24 inch", 1850000),
    ("External SSD 1TB", 980000),
]

CITIES = ["Jakarta", "Bandung", "Surabaya", "Semarang", "Medan",
          "Makassar", "Denpasar", "Yogyakarta"]

# --- the mess generators -----------------------------------------------

def messy_date(y, m, d):
    """Same date, six different formats. Classic multi-user spreadsheet."""
    fmts = [
        f"{y}-{m:02d}-{d:02d}",
        f"{d:02d}/{m:02d}/{y}",
        f"{m:02d}/{d:02d}/{y}",
        f"{d} {['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][m-1]} {y}",
        f"{y}/{m:02d}/{d:02d}",
        f"{d:02d}-{m:02d}-{y}",
    ]
    return random.choice(fmts)

def messy_price(value):
    """Currency typed by humans: symbols, separators, spaces, decimals."""
    style = random.random()
    if style < 0.25:
        return f"Rp {value:,}".replace(",", ".")
    if style < 0.45:
        return f"Rp{value}"
    if style < 0.60:
        return f"{value:,}".replace(",", ".")
    if style < 0.70:
        return f" {value} "
    if style < 0.78:
        return f"{value}.00"
    return str(value)

def messy_name(first, last):
    """Casing and whitespace chaos."""
    full = f"{first} {last}"
    style = random.random()
    if style < 0.18:
        return full.upper()
    if style < 0.34:
        return full.lower()
    if style < 0.46:
        return f"  {full}  "
    if style < 0.56:
        return full.replace(" ", "  ")
    return full

def messy_email(first, last):
    """Some valid, some broken, some missing entirely."""
    base = f"{first.lower()}.{last.lower()}"
    style = random.random()
    if style < 0.08:
        return ""
    if style < 0.14:
        return f"{base}@gmail"            # missing TLD
    if style < 0.19:
        return f"{base}(at)gmail.com"     # obfuscated
    if style < 0.24:
        return f" {base.upper()}@GMAIL.COM "
    if style < 0.28:
        return "n/a"
    return f"{base}@{random.choice(['gmail.com','yahoo.com','outlook.com'])}"

def messy_qty(q):
    style = random.random()
    if style < 0.05:
        return ""
    if style < 0.09:
        return f"{q} pcs"
    if style < 0.12:
        return f"{q}.0"
    return str(q)

def messy_city(city):
    style = random.random()
    if style < 0.10:
        return city.upper()
    if style < 0.18:
        return city.lower()
    if style < 0.24:
        return f"{city} "
    # common misspellings / alternates
    alt = {"Jakarta": "Jakarta Pusat", "Yogyakarta": "Jogjakarta",
           "Denpasar": "Den Pasar", "Makassar": "Makasar"}
    if style < 0.32 and city in alt:
        return alt[city]
    return city

# --- build rows ---------------------------------------------------------

rows = []
order_id = 1000

for _ in range(950):
    order_id += 1
    first = random.choice(FIRST)
    last = random.choice(LAST)
    product, unit = random.choice(PRODUCTS)
    qty = random.randint(1, 8)

    year = random.choice([2024, 2024, 2025, 2025, 2026])
    month = random.randint(1, 12)
    day = random.randint(1, 28)

    rows.append({
        "order_id": f"ORD-{order_id}",
        "customer_name": messy_name(first, last),
        "email": messy_email(first, last),
        "city": messy_city(random.choice(CITIES)),
        "product": product if random.random() > 0.15 else product.upper(),
        "quantity": messy_qty(qty),
        "unit_price": messy_price(unit),
        "order_date": messy_date(year, month, day),
        "status": random.choice(["completed", "Completed", "COMPLETED",
                                 "shipped", "Shipped", "pending",
                                 "Pending", "cancelled", "Cancelled"]),
    })

# inject exact duplicates (someone pasted the same block twice)
for _ in range(60):
    rows.append(dict(random.choice(rows)))

# inject near-duplicates: same order_id, slightly different formatting
for _ in range(35):
    src = dict(random.choice(rows))
    src["customer_name"] = src["customer_name"].upper()
    src["status"] = src["status"].lower()
    rows.append(src)

# inject fully blank rows (spreadsheet padding)
for _ in range(12):
    rows.append({k: "" for k in rows[0]})

# inject a few rows with impossible values
for _ in range(8):
    src = dict(random.choice(rows[:900]))
    src["quantity"] = random.choice(["-3", "0", "9999"])
    rows.append(src)

random.shuffle(rows)

with open("data/raw_sales.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)

print(f"Wrote data/raw_sales.csv with {len(rows)} rows")
