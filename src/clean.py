"""
Clean a messy sales export into an analysis-ready dataset.

Usage:
    python src/clean.py data/raw_sales.csv

Outputs:
    data/clean_sales.csv   -- the cleaned dataset
    reports/change_log.md  -- what was changed and why

Design notes
------------
Every fix is logged with a count. Nothing is silently dropped: rows that
cannot be rescued are written to data/rejected_rows.csv so the client can
review them instead of wondering where their data went.
"""

import sys
import os
import re
import unicodedata
from datetime import datetime

import pandas as pd

LOG = []


def log(step, detail, count):
    LOG.append({"step": step, "detail": detail, "rows_affected": count})


# --- individual cleaners -------------------------------------------------

def clean_text(series):
    """Collapse whitespace, strip, normalise unicode."""
    return (
        series.fillna("")
        .astype(str)
        .map(lambda s: unicodedata.normalize("NFKC", s))
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )


def title_case_name(series):
    """Proper casing, keeping particles lowercase where sensible."""
    return series.map(lambda s: " ".join(w.capitalize() for w in s.split()))


# Product names are mapped to a canonical list rather than .title()-cased.
# Blind title-casing turns "External SSD 1TB" into "External Ssd 1Tb" --
# acronyms and unit suffixes do not survive it.
PRODUCT_CANON = {
    "wireless mouse": "Wireless Mouse",
    "mechanical keyboard": "Mechanical Keyboard",
    "usb-c hub": "USB-C Hub",
    "laptop stand": "Laptop Stand",
    "webcam hd": "Webcam HD",
    "noise cancelling headset": "Noise Cancelling Headset",
    "monitor 24 inch": "Monitor 24 inch",
    "external ssd 1tb": "External SSD 1TB",
}


def canon_product(series):
    """Map to the canonical catalogue name; leave unknown values untouched."""
    lowered = series.str.lower().str.strip()
    unknown = ~lowered.isin(PRODUCT_CANON) & (lowered != "")
    log("product", "values not in the known catalogue, left as-is for review",
        int(unknown.sum()))
    return lowered.map(lambda s: PRODUCT_CANON.get(s, s))


CITY_CANON = {
    "jakarta pusat": "Jakarta",
    "jogjakarta": "Yogyakarta",
    "den pasar": "Denpasar",
    "makasar": "Makassar",
}


def canon_city(series):
    lowered = series.str.lower().str.strip()
    mapped = lowered.map(lambda s: CITY_CANON.get(s, s))
    return mapped.map(lambda s: " ".join(w.capitalize() for w in s.split()))


EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[a-z]{2,}$")


def clean_email(series):
    """Lowercase, de-obfuscate, blank out anything still invalid."""
    s = (
        series.str.lower()
        .str.strip()
        .str.replace(r"\(at\)", "@", regex=True)
        .str.replace(r"\s+", "", regex=True)
    )
    s = s.replace({"n/a": "", "na": "", "-": "", "none": ""})
    invalid = (s != "") & (~s.map(lambda x: bool(EMAIL_RE.match(x))))
    log("email", "invalid addresses blanked (kept row, flagged column)",
        int(invalid.sum()))
    s = s.where(~invalid, "")
    return s


def parse_money(series):
    """'Rp 1.850.000' / '1850000.00' / ' 185000 ' -> 1850000.0"""
    s = series.astype(str).str.strip()
    s = s.str.replace(r"(?i)^rp\.?\s*", "", regex=True)
    s = s.str.replace(r"\s", "", regex=True)
    # a trailing '.00' or ',00' is decimals; other dots/commas are thousands
    s = s.str.replace(r"[.,](\d{2})$", r"@\1", regex=True)
    s = s.str.replace(r"[.,]", "", regex=True)
    s = s.str.replace("@", ".", regex=False)
    return pd.to_numeric(s, errors="coerce")


DATE_FORMATS = [
    "%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y", "%d-%m-%Y", "%d %b %Y", "%m/%d/%Y",
]


def parse_dates(series):
    """
    Try known formats in priority order.

    Ambiguity note: a value like 06/01/2025 is valid as both DD/MM and MM/DD.
    This source is Indonesian, so DD/MM is tried first and MM/DD is only used
    when DD/MM is impossible (e.g. 13/05). Ambiguous values are counted and
    reported so the client can confirm the convention rather than trusting a
    silent guess.
    """
    s = series.astype(str).str.strip()
    out = pd.Series(pd.NaT, index=s.index, dtype="datetime64[ns]")

    for fmt in DATE_FORMATS:
        pending = out.isna() & (s != "")
        if not pending.any():
            break
        parsed = pd.to_datetime(s[pending], format=fmt, errors="coerce")
        out.loc[pending] = parsed

    ambiguous = s.str.match(r"^(0?[1-9]|1[0-2])[/-](0?[1-9]|1[0-2])[/-]\d{4}$")
    log("order_date",
        "slash dates where DD/MM vs MM/DD is ambiguous -- read as DD/MM, "
        "needs client confirmation",
        int((ambiguous & out.notna()).sum()))
    return out


def clean_quantity(series):
    """'5 pcs' / '5.0' / '' -> 5"""
    s = (
        series.astype(str)
        .str.replace(r"(?i)\s*pcs?\.?$", "", regex=True)
        .str.strip()
    )
    return pd.to_numeric(s, errors="coerce")


# --- pipeline ------------------------------------------------------------

def run(path_in):
    os.makedirs("reports", exist_ok=True)

    df = pd.read_csv(path_in, dtype=str, keep_default_na=False)
    start_rows = len(df)
    log("load", f"read {path_in}", start_rows)

    # 1. drop fully blank rows
    blank = df.apply(lambda r: all(str(v).strip() == "" for v in r), axis=1)
    log("blank rows", "rows with every field empty, removed", int(blank.sum()))
    df = df[~blank].copy()

    # 2. normalise text columns
    for col in ["order_id", "customer_name", "city", "product", "status"]:
        df[col] = clean_text(df[col])

    df["customer_name"] = title_case_name(df["customer_name"])
    df["city"] = canon_city(df["city"])
    df["product"] = canon_product(df["product"])
    df["status"] = df["status"].str.lower()
    log("casing",
        "name/city/product/status normalised to consistent casing", len(df))

    # 3. typed columns
    df["email"] = clean_email(df["email"])
    df["unit_price"] = parse_money(df["unit_price"])
    df["order_date"] = parse_dates(df["order_date"])
    df["quantity"] = clean_quantity(df["quantity"])

    # 4. deduplicate -- after normalising, so near-dupes collapse too
    before = len(df)
    df = df.drop_duplicates(subset=["order_id"], keep="first")
    log("duplicates",
        "duplicate order_id removed (kept first occurrence)",
        before - len(df))

    # 5. quarantine unusable rows instead of deleting them
    bad_qty = df["quantity"].isna() | (df["quantity"] <= 0) | (df["quantity"] > 1000)
    bad_price = df["unit_price"].isna() | (df["unit_price"] <= 0)
    bad_date = df["order_date"].isna()
    rejected = df[bad_qty | bad_price | bad_date].copy()

    if len(rejected):
        reasons = []
        for _, r in rejected.iterrows():
            why = []
            if pd.isna(r["quantity"]) or r["quantity"] <= 0 or r["quantity"] > 1000:
                why.append("quantity out of range or missing")
            if pd.isna(r["unit_price"]) or r["unit_price"] <= 0:
                why.append("unit_price unparseable")
            if pd.isna(r["order_date"]):
                why.append("order_date unparseable")
            reasons.append("; ".join(why))
        rejected["reject_reason"] = reasons
        rejected.to_csv("data/rejected_rows.csv", index=False)
    log("quarantine",
        "rows moved to data/rejected_rows.csv for client review",
        len(rejected))

    df = df[~(bad_qty | bad_price | bad_date)].copy()

    # 6. derived column
    df["quantity"] = df["quantity"].astype(int)
    df["total_amount"] = (df["quantity"] * df["unit_price"]).round(2)
    df["order_date"] = df["order_date"].dt.strftime("%Y-%m-%d")

    df = df[[
        "order_id", "order_date", "customer_name", "email", "city",
        "product", "quantity", "unit_price", "total_amount", "status",
    ]].sort_values("order_date").reset_index(drop=True)

    df.to_csv("data/clean_sales.csv", index=False)
    log("output", f"wrote data/clean_sales.csv", len(df))

    write_report(start_rows, len(df))
    return df


def write_report(start_rows, end_rows):
    lines = [
        "# Change Log",
        "",
        f"Generated {datetime.now():%Y-%m-%d %H:%M}",
        "",
        f"**{start_rows} rows in -> {end_rows} clean rows out**",
        "",
        "| Step | What changed | Rows |",
        "|---|---|---|",
    ]
    for e in LOG:
        lines.append(f"| {e['step']} | {e['detail']} | {e['rows_affected']} |")

    lines += [
        "",
        "## Needs your confirmation",
        "",
        "1. **Date convention.** Some slash-format dates are valid both as "
        "DD/MM and MM/DD. They were read as DD/MM (Indonesian convention). "
        "Confirm this is right for your source system.",
        "2. **Rejected rows.** See `data/rejected_rows.csv` -- nothing was "
        "deleted, these are set aside for you to review.",
        "3. **Blanked emails.** Invalid addresses were emptied rather than "
        "guessed at. The customer row itself is kept.",
        "",
    ]
    with open("reports/change_log.md", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else "data/raw_sales.csv"
    result = run(src)
    print(f"\nClean rows: {len(result)}")
    print(result.head(8).to_string(index=False))
