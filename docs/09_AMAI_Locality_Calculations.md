# 9.1 — Load NSE values into Boundaries Layer 5 (Localities)

AMAI_LOC_2024 already contains CVEGEO at locality level  
(9-digit CVEGEO). No substring needed.  
Once we load NSE values into Boundaries Layer 5, we will summarize at level 2 (municipality), 1 (state)  

```sql
USE INMO;
GO

------------------------------------------------------------
-- STEP 1 — Clean AMAI_LOC_2024 (Locality-level NSE dataset)
------------------------------------------------------------
-- NSE_TOTAL = NULL when NSE_TOTAL = 0
-- This prevents invalid percentage calculations later.
-- Expected: 152 rows affected
---------------------------------------------------------

UPDATE AMAI_LOC_2024
SET NSE_TOTAL = NULL
WHERE NSE_TOTAL = 0;


---------------------------------------------------------
-- STEP 2 — Reset all NSE fields in Boundaries
---------------------------------------------------------
-- Layers affected:
-- Layer 1 = State
-- Layer 2 = Municipality
-- Layer 5 = Locality (City)
-- Result: 53789 rows affected
---------------------------------------------------------

UPDATE Boundaries
SET
    NSE = NULL,
    NSE_LABEL = NULL,
    NSE_AB_PCT = NULL,
    NSE_CPLUS_PCT = NULL,
    NSE_C_PCT = NULL,
    NSE_CMINUS_PCT = NULL,
    NSE_DPLUS_PCT = NULL,
    NSE_D_PCT = NULL,
    NSE_E_PCT = NULL,
    NSE_AB = NULL,
    NSE_CPLUS = NULL,
    NSE_C = NULL,
    NSE_CMINUS = NULL,
    NSE_DPLUS = NULL,
    NSE_D = NULL,
    NSE_E = NULL,
    NSE_TOTAL = NULL,
    NSE_SCORE = NULL
WHERE Layer IN (1, 2, 5);


---------------------------------------------------------
-- STEP 3 — Load NSE values into Layer 5 (Localities)
---------------------------------------------------------
-- AMAI_LOC_2024 already contains CVEGEO at locality level
-- (9-digit CVEGEO). No substring needed.
-- Results: 51279 rows affected
---------------------------------------------------------

UPDATE L5
SET 
    L5.NSE_AB      = S.NSE_AB,
    L5.NSE_CPLUS   = S.NSE_CPLUS,
    L5.NSE_C       = S.NSE_C,
    L5.NSE_CMINUS  = S.NSE_CMINUS,
    L5.NSE_DPLUS   = S.NSE_DPLUS,
    L5.NSE_D       = S.NSE_D,
    L5.NSE_E       = S.NSE_E,
    L5.NSE_TOTAL   = S.NSE_TOTAL
FROM Boundaries AS L5
LEFT JOIN (
    SELECT 
        CVEGEO AS CVE_LOC,
        SUM(NSE_AB)      AS NSE_AB,
        SUM(NSE_CPLUS)   AS NSE_CPLUS,
        SUM(NSE_C)       AS NSE_C,
        SUM(NSE_CMINUS)  AS NSE_CMINUS,
        SUM(NSE_DPLUS)   AS NSE_DPLUS,
        SUM(NSE_D)       AS NSE_D,
        SUM(NSE_E)       AS NSE_E,
        SUM(NSE_TOTAL)   AS NSE_TOTAL
    FROM AMAI_LOC_2024
    WHERE NSE_TOTAL IS NOT NULL
    GROUP BY CVEGEO
) AS S
    ON L5.CVEGEO = S.CVE_LOC
WHERE L5.Layer = 5;


---------------------------------------------------------------------
-- STEP 4 — Summarize Localities (Layer 5) → Municipalities (Layer 2)
---------------------------------------------------------------------
-- Municipality CVEGEO = first 5 digits
-- Results: 2478 rows affected
---------------------------------------------------------------------

UPDATE L2
SET 
    L2.NSE_AB      = S.NSE_AB,
    L2.NSE_CPLUS   = S.NSE_CPLUS,
    L2.NSE_C       = S.NSE_C,
    L2.NSE_CMINUS  = S.NSE_CMINUS,
    L2.NSE_DPLUS   = S.NSE_DPLUS,
    L2.NSE_D       = S.NSE_D,
    L2.NSE_E       = S.NSE_E,
    L2.NSE_TOTAL   = S.NSE_TOTAL
FROM Boundaries AS L2
LEFT JOIN (
    SELECT 
        LEFT(CVEGEO, 5) AS CVE_MUN,
        SUM(NSE_AB)      AS NSE_AB,
        SUM(NSE_CPLUS)   AS NSE_CPLUS,
        SUM(NSE_C)       AS NSE_C,
        SUM(NSE_CMINUS)  AS NSE_CMINUS,
        SUM(NSE_DPLUS)   AS NSE_DPLUS,
        SUM(NSE_D)       AS NSE_D,
        SUM(NSE_E)       AS NSE_E,
        SUM(NSE_TOTAL)   AS NSE_TOTAL
    FROM Boundaries
    WHERE Layer = 5
      AND NSE_TOTAL IS NOT NULL
    GROUP BY LEFT(CVEGEO, 5)
) AS S
    ON L2.CVEGEO = S.CVE_MUN
WHERE L2.Layer = 2;


-----------------------------------------------------------------
-- STEP 5 — Summarize Municipalities (Layer 2) → States (Layer 1)
-----------------------------------------------------------------
-- State CVEGEO = first 2 digits
-- Results: 32 rows affected
-----------------------------------------------------------------

UPDATE L1
SET 
    L1.NSE_AB      = S.NSE_AB,
    L1.NSE_CPLUS   = S.NSE_CPLUS,
    L1.NSE_C       = S.NSE_C,
    L1.NSE_CMINUS  = S.NSE_CMINUS,
    L1.NSE_DPLUS   = S.NSE_DPLUS,
    L1.NSE_D       = S.NSE_D,
    L1.NSE_E       = S.NSE_E,
    L1.NSE_TOTAL   = S.NSE_TOTAL
FROM Boundaries AS L1
LEFT JOIN (
    SELECT 
        LEFT(CVEGEO, 2) AS CVE_ENT,
        SUM(NSE_AB)      AS NSE_AB,
        SUM(NSE_CPLUS)   AS NSE_CPLUS,
        SUM(NSE_C)       AS NSE_C,
        SUM(NSE_CMINUS)  AS NSE_CMINUS,
        SUM(NSE_DPLUS)   AS NSE_DPLUS,
        SUM(NSE_D)       AS NSE_D,
        SUM(NSE_E)       AS NSE_E,
        SUM(NSE_TOTAL)   AS NSE_TOTAL
    FROM Boundaries
    WHERE Layer = 2
      AND NSE_TOTAL IS NOT NULL
    GROUP BY LEFT(CVEGEO, 2)
) AS S
    ON L1.CVEGEO = S.CVE_ENT
WHERE L1.Layer = 1;
```


# 9.2 — Calculate NSE percentage fields (_PCT)

IMPORTANT:
- Percentages must be calculated ONLY for Layers 1, 2, and 5.
- If NSE_TOTAL is NULL, all percentage fields must remain NULL.
- This prevents invalid divisions and keeps “N/D” logic intact.

```sql
USE INMO;
GO

----------------------------------------------------------------
-- STEP 9.2 — Calculate NSE percentage fields (_PCT)
----------------------------------------------------------------
-- IMPORTANT:
-- Percentages must be calculated ONLY for Layers 1, 2, and 5.
-- NSE_TOTAL must NOT be NULL, otherwise percentages remain NULL.
-- This prevents invalid divisions and preserves “N/D” logic.
-- Expected: 52586 rows affected
-----------------------------------------------------------------

UPDATE Boundaries
SET
    NSE_AB_PCT      = (NSE_AB      * 100.0 / NSE_TOTAL),
    NSE_CPLUS_PCT   = (NSE_CPLUS   * 100.0 / NSE_TOTAL),
    NSE_C_PCT       = (NSE_C       * 100.0 / NSE_TOTAL),
    NSE_CMINUS_PCT  = (NSE_CMINUS  * 100.0 / NSE_TOTAL),
    NSE_DPLUS_PCT   = (NSE_DPLUS   * 100.0 / NSE_TOTAL),
    NSE_D_PCT       = (NSE_D       * 100.0 / NSE_TOTAL),
    NSE_E_PCT       = (NSE_E       * 100.0 / NSE_TOTAL)
WHERE Layer IN (1, 2, 5)
  AND NSE_TOTAL IS NOT NULL;
```

# 9.3 — Calculate NSE_SCORE (AMAI IDS)

AMAI official scoring weights:  

|Level|Score|
|-----|-----|
|AB   |    7|
|C+   |    6|
|C    |    5|
|C−   |    4|
|D+   |    3|
|D    |    2|
|E    |    1|

Formula: **IDS = Σ (percentage_level * score_level)**

```sql
USE INMO;
GO

---------------------------------------------------------
--   STEP 9.3 — Calculate NSE_SCORE (AMAI IDS)
---------------------------------------------------------
--   AMAI official scoring weights:
--   Level   Score
--   AB      7
--   C+      6
--   C       5
--   C−      4
--   D+      3
--   D       2
--   E       1
--
--   Formula:
--   IDS = Σ (percentage_level * score_level)
--
--   Notes:
-- Missing levels must be treated as 0 (ISNULL).
-- Only calculate for Layers 1, 2, and 5.
-- Only calculate when NSE_TOTAL IS NOT NULL.
---------------------------------------------------------

UPDATE Boundaries
SET NSE_SCORE =
    (
          (ISNULL(NSE_AB_PCT,     0) * 7)
        + (ISNULL(NSE_CPLUS_PCT,  0) * 6)
        + (ISNULL(NSE_C_PCT,      0) * 5)
        + (ISNULL(NSE_CMINUS_PCT, 0) * 4)
        + (ISNULL(NSE_DPLUS_PCT,  0) * 3)
        + (ISNULL(NSE_D_PCT,      0) * 2)
        + (ISNULL(NSE_E_PCT,      0) * 1)
    ) / 100.0
WHERE Layer IN (1, 2, 5)
  AND NSE_TOTAL IS NOT NULL;


---------------------------------------------------------
-- STEP 8.3b — Calculate IDS_PROM
---------------------------------------------------------
UPDATE Boundaries
SET IDS_PROM =
(
      (ISNULL(NSE_AB,      0) * 7)
    + (ISNULL(NSE_CPLUS,   0) * 6)
    + (ISNULL(NSE_C,       0) * 5)
    + (ISNULL(NSE_CMINUS,  0) * 4)
    + (ISNULL(NSE_DPLUS,   0) * 3)
    + (ISNULL(NSE_D,       0) * 2)
    + (ISNULL(NSE_E,       0) * 1)
) / NULLIF(NSE_TOTAL, 0)
WHERE Layer IN (1, 2, 5)
  AND NSE_TOTAL IS NOT NULL;


---------------------------------------------------------
--   Validation Queries
---------------------------------------------------------

SELECT TOP 10 
    CVEGEO,
    NSE_TOTAL,
    NSE_AB_PCT,
    NSE_CPLUS_PCT,
    NSE_C_PCT,
    NSE_CMINUS_PCT,
    NSE_DPLUS_PCT,
    NSE_D_PCT,
    NSE_E_PCT
FROM Boundaries
WHERE Layer = 5
 AND NSE_TOTAL IS NOT NULL
ORDER BY CVEGEO;

SELECT TOP 10 CVEGEO, NSE_SCORE, IDS_PROM
FROM Boundaries
WHERE Layer = 5
 AND NSE_TOTAL IS NOT NULL
ORDER BY CVEGEO;
```

#### Validation 1

Display all percentages in Layer = 5

|CVEGEO   |NSE_TOTAL|NSE_AB_PCT|NSE_CPLUS_PCT|NSE_C_PCT|NSE_CMINUS_PCT|NSE_DPLUS_PCT|NSE_D_PCT|NSE_E_PCT|
|---------|---------|----------|-------------|---------|--------------|-------------|---------|---------|
|100010001|	   3395 |7.19	   |        11.52|    15.49|	     16.73|	       17.85|	 26.98|	    4.24|
|100010004|	    233 |0.00	   |         1.72|     3.00|	      8.58|	       20.17|	 47.21|	   19.31|
|100010005|	    192 |1.04	   |         5.21|	   4.17|	     10.94|	       21.88|	 44.27|	   12.50|
|100010010|	   87	|0.00	   |         3.45|	  16.09|	     18.39|	       22.99|	 35.63|	    3.45|
|100010012|	  226	|0.44	   |         1.33|	   4.42|	      7.52|	       30.09|	 45.58|	   10.62|
|100010022|	  37	|2.70	   |         0.00|    16.22|	      8.11|	       13.51|	 43.24|	   16.22|
|100010028|	  103	|1.94	   |         1.94|	   3.88|	     18.45|	       25.24|	 42.72|	    5.83|
|100010041|	  36	|2.78	   |         0.00|	   5.56|	      5.56|	       22.22|	 55.56|	    8.33|
|100010042|	  192	|0.52	   |         2.60|	   4.69|	     17.19|	       22.40|	 40.10|	   12.50|
|100010045|	  33	|12.12	   |        24.24|	  27.27|	     12.12|	       12.12|	 12.12|	    0.00|

#### Validation 2

|CVEGEO   |NSE_SCORE|
|---------|---------|
|100010001|	3.756|
|100010004|	2.339|
|100010005|	2.698|
|100010010|	3.184|
|100010012|	2.553|
|100010022|	2.757|
|100010028|	2.854|
|100010041|	2.556|
|100010042|	2.714|
|100010045|	4.757|

# 9.4 — Calculate NSE (dominant level) and NSE_LABEL

Applies to:
 - Layer 1 = State
 - Layer 2 = Municipality
 - Layer 5 = Locality (City)

Logic:
- NSE = dominant socioeconomic level based on highest percentage.
- If all percentages are NULL → NSE = NULL (no AMAI data).
- If all percentages are 0 → NSE = 'E' (lowest AMAI level).
- NSE_LABEL = NSE + rounded percentage (integer %).

```sql
USE INMO;
GO

------------------------------------------------------------
--   STEP 8.4 — Calculate NSE (dominant level) and NSE_LABEL
------------------------------------------------------------
--   Applies to:
--     - Layer 1 = State
--     - Layer 2 = Municipality
--     - Layer 5 = Locality (City)
--
--   Logic:
-- NSE = dominant socioeconomic level based on highest percentage.
-- If all percentages are NULL → NSE = NULL (no AMAI data).
-- If all percentages are 0 → NSE = 'E' (lowest AMAI level).
-- NSE_LABEL = NSE + rounded percentage (integer %).
-------------------------------------------------------------


---------------------------------------------------------
--  G0 — Reset NSE and NSE_LABEL for layers 1, 2, 5
---------------------------------------------------------
UPDATE Boundaries
SET NSE = NULL,
    NSE_LABEL = NULL
WHERE Layer IN (1, 2, 5);


---------------------------------------------------------
--  G1 — Assign NSE (dominant AMAI level)
--  Handles NULL and zero cases correctly
---------------------------------------------------------

UPDATE B
SET NSE =
    CASE 
        WHEN Dom.Level IS NOT NULL THEN Dom.Level
        WHEN Stats.NonNullCount = 0 THEN NULL      -- all NULL → no AMAI data
        ELSE 'E'                                   -- all 0 → lowest level
    END
FROM Boundaries B

OUTER APPLY (
    /* Dominant level among percentages > 0 */
    SELECT TOP 1 Level
    FROM (
        SELECT 'A/B' AS Level, B.NSE_AB_PCT      AS Value
        UNION ALL SELECT 'C+',  B.NSE_CPLUS_PCT
        UNION ALL SELECT 'C',   B.NSE_C_PCT
        UNION ALL SELECT 'C-',  B.NSE_CMINUS_PCT
        UNION ALL SELECT 'D+',  B.NSE_DPLUS_PCT
        UNION ALL SELECT 'D',   B.NSE_D_PCT
        UNION ALL SELECT 'E',   B.NSE_E_PCT
    ) X
    WHERE X.Value IS NOT NULL AND X.Value > 0
    ORDER BY X.Value DESC
) Dom

OUTER APPLY (
    /* Count non-null values to detect “no AMAI data” */
    SELECT 
        COUNT(Value) AS NonNullCount,
        MAX(Value)   AS MaxValue
    FROM (
        SELECT B.NSE_AB_PCT      AS Value
        UNION ALL SELECT B.NSE_CPLUS_PCT
        UNION ALL SELECT B.NSE_C_PCT
        UNION ALL SELECT B.NSE_CMINUS_PCT
        UNION ALL SELECT B.NSE_DPLUS_PCT
        UNION ALL SELECT B.NSE_D_PCT
        UNION ALL SELECT B.NSE_E_PCT
    ) Y
) Stats

WHERE B.Layer IN (1, 2, 5);



---------------------------------------------------------
--   G2 — Assign NSE_LABEL (level + integer percentage)
---------------------------------------------------------

UPDATE Boundaries
SET NSE_LABEL = 
    CASE 
        WHEN NSE IS NULL THEN 'N/A'

        WHEN NSE = 'A/B' THEN 
            'A/B (' + CAST(CAST(ISNULL(NSE_AB_PCT, 0) AS INT) AS VARCHAR(3)) + '%)'

        WHEN NSE = 'C+' THEN 
            'C+ (' + CAST(CAST(ISNULL(NSE_CPLUS_PCT, 0) AS INT) AS VARCHAR(3)) + '%)'

        WHEN NSE = 'C' THEN 
            'C (' + CAST(CAST(ISNULL(NSE_C_PCT, 0) AS INT) AS VARCHAR(3)) + '%)'

        WHEN NSE = 'C-' THEN 
            'C- (' + CAST(CAST(ISNULL(NSE_CMINUS_PCT, 0) AS INT) AS VARCHAR(3)) + '%)'

        WHEN NSE = 'D+' THEN 
            'D+ (' + CAST(CAST(ISNULL(NSE_DPLUS_PCT, 0) AS INT) AS VARCHAR(3)) + '%)'

        WHEN NSE = 'D' THEN 
            'D (' + CAST(CAST(ISNULL(NSE_D_PCT, 0) AS INT) AS VARCHAR(3)) + '%)'

        WHEN NSE = 'E' THEN 
            'E (' + CAST(CAST(ISNULL(NSE_E_PCT, 0) AS INT) AS VARCHAR(3)) + '%)'
    END
WHERE Layer IN (1, 2, 5);


-- Validations

SELECT TOP 10 CVEGEO, NSE_LABEL
FROM Boundaries
WHERE Layer = 5
 AND NSE_TOTAL IS NOT NULL
ORDER BY NSE_LABEL, CVEGEO;
```

#### Expected results

53789 rows affected

#### Validation

Display TOP 10 records from Boundaries layer = 5 (locality) with NSE_LABEL

|CVEGEO   |NSE_LABEL |
|---------|----------|
|100010001|	D/E (31%)|
|100010004|	D/E (66%)|
|100010005|	D/E (56%)|
|100010010|	D/E (39%)|
|100010012|	D/E (56%)|
|100010022|	D/E (59%)|
|100010028|	D/E (48%)|
|100010041|	D/E (63%)|
|100010042|	D/E (52%)|
|100010045|	C (27%)  |
