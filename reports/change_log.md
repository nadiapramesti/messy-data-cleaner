# Change Log

Generated 2026-10-09 15:25

**1065 rows in -> 892 clean rows out**

| Step | What changed | Rows |
|---|---|---|
| load | read data/raw_sales.csv | 1065 |
| blank rows | rows with every field empty, removed | 12 |
| product | values not in the known catalogue, left as-is for review | 0 |
| casing | name/city/product/status normalised to consistent casing | 1053 |
| email | invalid addresses blanked (kept row, flagged column) | 52 |
| order_date | slash dates where DD/MM vs MM/DD is ambiguous -- read as DD/MM, needs client confirmation | 245 |
| duplicates | duplicate order_id removed (kept first occurrence) | 103 |
| quarantine | rows moved to data/rejected_rows.csv for client review | 58 |
| output | wrote data/clean_sales.csv | 892 |

## Needs your confirmation

1. **Date convention.** Some slash-format dates are valid both as DD/MM and MM/DD. They were read as DD/MM (Indonesian convention). Confirm this is right for your source system.
2. **Rejected rows.** See `data/rejected_rows.csv` -- nothing was deleted, these are set aside for you to review.
3. **Blanked emails.** Invalid addresses were emptied rather than guessed at. The customer row itself is kept.
