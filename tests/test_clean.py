"""Unit tests for the individual cleaners. Run: pytest -q"""

import sys
import os
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import clean  # noqa: E402


def test_parse_money_handles_rupiah_formats():
    s = pd.Series(["Rp 1.850.000", "Rp1850000", "1850000.00", " 1850000 "])
    out = clean.parse_money(s)
    assert (out == 1850000.0).all()


def test_parse_money_rejects_garbage():
    out = clean.parse_money(pd.Series(["", "n/a", "abc"]))
    assert out.isna().all()


def test_parse_dates_prefers_day_first():
    # 06/01/2025 is ambiguous; Indonesian convention reads it as 6 January
    out = clean.parse_dates(pd.Series(["06/01/2025"]))
    assert out.iloc[0].month == 1 and out.iloc[0].day == 6


def test_parse_dates_falls_back_when_day_first_impossible():
    # 13 cannot be a month, so this must resolve as 12 November
    out = clean.parse_dates(pd.Series(["13-11-2025"]))
    assert out.iloc[0].month == 11 and out.iloc[0].day == 13


def test_clean_email_blanks_invalid():
    s = pd.Series(["A.B@GMAIL.COM ", "broken@gmail", "n/a", "x.y(at)mail.com"])
    out = clean.clean_email(s)
    assert out.iloc[0] == "a.b@gmail.com"
    assert out.iloc[1] == ""
    assert out.iloc[2] == ""
    assert out.iloc[3] == "x.y@mail.com"


def test_clean_quantity_strips_units():
    out = clean.clean_quantity(pd.Series(["5 pcs", "5.0", "5", ""]))
    assert list(out[:3]) == [5.0, 5.0, 5.0]
    assert pd.isna(out.iloc[3])


def test_canon_city_merges_variants():
    out = clean.canon_city(pd.Series(["JOGJAKARTA", "yogyakarta", " Jogjakarta "]))
    assert set(out) == {"Yogyakarta"}


def test_canon_product_preserves_acronyms():
    out = clean.canon_product(pd.Series(["EXTERNAL SSD 1TB", "usb-c hub"]))
    assert list(out) == ["External SSD 1TB", "USB-C Hub"]
