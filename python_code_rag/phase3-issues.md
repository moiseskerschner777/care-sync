# Phase 3 — Implementation Log: Issues & Resolutions

## 1. `intersystems_irispython` import path incorrect

**Task:** 3.4
**Error:** `ModuleNotFoundError: No module named 'intersystems_irispython'`
**Context:** The design spec specified `import intersystems_irispython.intersystems.iris as iris`. The pip package is named `intersystems_irispython` (underscore), but the importable Python module is simply `iris` — not `intersystems_irispython.intersystems.iris`.
**Fix:** Changed import to `import iris` (matching `health.py` which already used this pattern).

---

## 2. `MODULE` is a reserved word in IRIS SQL

**Task:** 3.6
**Error:** `SQLCODE: <-1>:<Invalid SQL statement> — IDENTIFIER expected, reserved word MODULE found`
**Context:** `CREATE TABLE` used `module` as a column name, which is a reserved word in IRIS SQL.
**Fix:** Quoted the column name as `"module"` in the DDL. Also applied the same quoting in INSERT and SELECT statements.

---

## 3. `CREATE INDEX IF NOT EXISTS` not supported by IRIS

**Task:** 3.6
**Error:** `SQLCODE: <-1>:<Invalid SQL statement> — ON expected, NOT found`
**Context:** The design spec assumed `CREATE INDEX IF NOT EXISTS` would work and that "IRIS silently ignores this if the index already exists." IRIS does NOT support `IF NOT EXISTS` clause on `CREATE INDEX`.
**Fix:** Wrapped the `CREATE INDEX` in a `try/except` block. The index creation is still idempotent — attempting to create an already-existing index silently raises an exception which is caught and ignored.

---

## 4. `TO_VECTOR(?)` parameterized in INSERT stores as VARCHAR, not VECTOR

**Task:** 3.10, 3.14
**Error:** `SQLCODE: <-259>:<Cannot perform vector operation on vectors of different datatypes>`
**Context:** When using parameterized queries (`TO_VECTOR(?)`), the IRIS Python dbapi driver passes the vector string as a VARCHAR parameter. IRIS then stores it as a VARCHAR instead of converting it to the VECTOR column type. The INFORMATION_SCHEMA always reports VECTOR columns as `varchar` type, regardless of the actual column definition, making this hard to debug.
**Fix (insert):** Inline the comma-separated vector string directly in the SQL string (e.g., `TO_VECTOR('0.1,0.2,...')`) rather than using a `?` parameter. The format must be comma-separated values WITHOUT brackets — NOT `str(list)` which produces `[0.1, 0.2, ...]`.
**Fix (search):** Wrap the stored `embedding` column with `TO_VECTOR` in the SELECT query: `VECTOR_COSINE(TO_VECTOR(embedding), TO_VECTOR('{vec_str}'))`. Without wrapping, the column is returned as a string (VARCHAR) and can't be compared with the query VECTOR. Inline the query vector string rather than parameterizing it.

---

## 5. `DataRow` type printed as object repr instead of tuple

**Task:** 3.4 (test verification)
**Observation:** `cursor.fetchone()` returns `iris.dbapi.DataRow` objects. When printed, they display as `<iris.dbapi.DataRow object at 0x...>` instead of the expected `(1,)`. Indexed access (`row[0]`) works correctly. This is a cosmetic difference in the test output — the test expectations in the spec showed tuple output, but the actual IRIS Python driver returns DataRow objects.

---

## Summary of design spec issues

| Design assumption | Actual behavior |
|---|---|
| `import intersystems_irispython.intersystems.iris` | Should be `import iris` |
| `CREATE INDEX IF NOT EXISTS` supported | IRIS does not support this syntax |
| `TO_VECTOR(?)` parameterized works for INSERT | Must be inlined in the SQL string |
| `VECTOR_COSINE(embedding, TO_VECTOR(?))` | Must wrap embedding column: `TO_VECTOR(embedding)` |
| `str(vector_list)` format works | Must be comma-separated without brackets |
| Column `module` unquoted | Must be quoted as `"module"` |
