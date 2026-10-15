---
name: comparar-planilhas
description: Use to find out what changed between two spreadsheets (old and new version, two months, two systems): rows that were added, removed or changed, using a column as the key.
---

# Compare spreadsheets

1. Read both and find the **key column**, which identifies each row (code, tax ID, order number). If there isn't an obvious one, ask. Without a key, the comparison becomes a guess.
2. Check whether the columns have the same names; if not, say how you matched one to the other.
3. Compare and split into three groups:
   - **Added:** the key only exists in the new one.
   - **Removed:** the key only exists in the old one.
   - **Changed:** the key exists in both, but some value is different (say which column, the old value and the new one).
4. Ignore differences that aren't real: extra spaces, upper and lower case, `10` and `10.00`. Say that you ignored them.
5. Deliver:
   - a summary with the count of each group;
   - a new spreadsheet (e.g. `comparacao.xlsx`) with one sheet per group and the changed cells highlighted.
6. Never touch the two original spreadsheets.
