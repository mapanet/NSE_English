---  
title: "NSE Calculation for Boundaries Layer 6"   
description: "Area-weighted AMAI NSE calculation using INEGI MG 2025 and DCAH 2025 datasets."   
---  

# 4 NSE calculation for Boundaries layer = 6 (Neighborhoods)

> **Reference:** See [Methodology Overview](methodology.md) for the complete conceptual description of the NSE calculation process, including dataset relationships, weighting logic, and audit steps.  
> This page documents the **implementation** — the SQL and GIS workflow used to calculate NSE for Boundaries Layer 6 (Neighborhoods).

## Purpose in the NSE Pipeline

This dataset is used to:

- Build **Boundaries Layer 6** (Neighborhoods)  
- Perform **spatial intersection** with AGEB polygons  
- Calculate **area‑weighted NSE** values per neighborhood  


## Why Area Weighting Is Required

Neighborhoods often cross multiple AGEB boundaries.  
Each AGEB has its own AMAI NSE classification, so the neighborhood inherits a **weighted NSE** based on the proportion of its area that falls within each AGEB.

### Example

| AGEB | % Area in Neighborhood | C+ | C | D+ | E |
|------|------------------------|----|---|----|---|
| A | 70 % | 40 | 30 | 20 | 10 |
| B | 30 % | 10 | 20 | 40 | 30 |

The neighborhood’s weighted values are:

C+ = 0.7 × 40 + 0.3 × 10
C  = 0.7 × 30 + 0.3 × 20

This ensures that the NSE assigned to each neighborhood accurately reflects the socioeconomic composition of the AGEBs it overlaps.


---

# 1 — Check geometries

```sql
------------------------------------------------------
-- NSE Step 4.0 — Validate geometries
-- Boundaries layer 6 (neighborhoods) and MG 2025 AGEB
-- Neighborhoods: Boundaries Layer = 6
-- AGEB:          Boundaries_AGEB_2025
------------------------------------------------------

-------------------------------------
-- Boundaries Layer 6 (neighborhoods)
-- Expected: Nothing = OK
-------------------------------------

-------------------------
-- Invalidd Geometries
-------------------------

SELECT ID, CVEGEO 
FROM Boundaries
WHERE Layer = 6
  AND geom.STIsValid() = 0;

---------------------------
-- Empty or null Geometries
---------------------------

SELECT ID, CVEGEO 
FROM Boundaries
WHERE Layer = 6
  AND (geom IS NULL OR geom.STIsEmpty() = 1);

-----------
-- Area = 0
-----------

SELECT ID, CVEGEO 
FROM Boundaries
WHERE Layer = 6
  AND geom.STArea() = 0;

--------------------------
-- Incorrect geometry type
--------------------------

SELECT ID, CVEGEO, geom.STGeometryType()
FROM Boundaries
WHERE Layer = 6
  AND geom.STGeometryType() NOT IN ('Polygon','MultiPolygon');

----------------------------------------------
-- Bounding box suspicious (weird coordinates)
----------------------------------------------

SELECT ID, CVEGEO 
FROM Boundaries
WHERE Layer = 6
  AND (geom.STEnvelope().ToString() LIKE '%E+%' OR geom.STEnvelope().ToString() LIKE '%E-%');

----------------------------------------
-- Inconsitent SRID (must be EPSG: 4326)
----------------------------------------

SELECT DISTINCT geom.STSrid AS SRID
FROM Boundaries
WHERE Layer = 6;


------------------------------
-- AGEB (Boundaries_AGEB_2025)
------------------------------

---------------------
-- Invalid Geometries
---------------------

SELECT ID, CVEGEO 
FROM Boundaries_AGEB_2025
WHERE geom.STIsValid() = 0;

---------------------------
-- Empty or null Geometries
---------------------------

SELECT ID, CVEGEO 
FROM Boundaries_AGEB_2025
WHERE geom IS NULL OR geom.STIsEmpty() = 1;

-----------
-- Area = 0
-----------

SELECT ID, CVEGEO 
FROM Boundaries_AGEB_2025
WHERE geom.STArea() = 0;

--------------------------
-- Incorrect geometry type
--------------------------

SELECT ID, CVEGEO, geom.STGeometryType()
FROM Boundaries_AGEB_2025
WHERE geom.STGeometryType() NOT IN ('Polygon','MultiPolygon');

-----------------------------------
-- Suspicious Bounding box E+ or E-
-----------------------------------

SELECT ID, CVEGEO 
FROM Boundaries_AGEB_2025
WHERE geom.STEnvelope().ToString() LIKE '%E+%' 
   OR geom.STEnvelope().ToString() LIKE '%E-%';

------------------------------------
-- SRID inconsistente (must be 4326)
------------------------------------

SELECT DISTINCT geom.STSrid AS SRID
FROM Boundaries_AGEB_2025;
```

# 2 — Create Intersection Boundaries (layer=6) ↔ AGEB

Overlay AGEB polygons with neighborhood polygons to establish spatial relationships.

- Use Boundaries_AGEB_2025 (AGEB polygons)
- Use Boundaries with Layer = 6 (Neighborhoods)
- Apply ST_Intersects or ST_Intersection to generate overlaps
- Store results in COLONIA_AGEB_INTERSECT

```sql
USE INMO;
GO

----------------------------------------------------------
-- NSE Step 4.2 — Intersection Boundaries (layer=6) ↔ AGEB
----------------------------------------------------------

-- Creates COLONIA_AGEB_INTERSECT
-- Expected result: ~267,718 records

DROP TABLE IF EXISTS COLONIA_AGEB_INTERSECT;
GO

SELECT 
    B.ID AS ID_COLONIA,
    B.CVEGEO AS CVE_COLONIA,
    A.CVEGEO AS CVE_AGEB,
    B.geom.STIntersection(A.geom) AS geom_inter,
    B.geom.STIntersection(A.geom).STArea() / B.geom.STArea() AS pct_area
INTO COLONIA_AGEB_INTERSECT
FROM Boundaries B
JOIN Boundaries_AGEB_2025 A
    ON B.geom.STIntersects(A.geom) = 1
WHERE B.layer = 6;
GO

------------------------------------------------------------------------
-- Validation: How many records were generated in COLONIA_AGEB_INTERSECT
-- Expected result: ~267,718 records
-- Time to run: ~1 seconds
-------------------------------------------------------------------------

SELECT COUNT(*) AS Records FROM COLONIA_AGEB_INTERSECT;

---------------------------------------------------------------------------
-- Validation: Check that no neighborhoods exist without AGEB intersections
-- Expected result: 0
---------------------------------------------------------------------------

SELECT COUNT(*) 
FROM Boundaries B
LEFT JOIN COLONIA_AGEB_INTERSECT I
    ON B.CVEGEO = I.CVE_COLONIA
WHERE B.layer = 6
  AND I.CVE_COLONIA IS NULL;
```

# 3 — Create COLONIA_NSE (weighted population)

```sql
USE INMO;
GO

-- NSE Step 4.3 — Create COLONIA_NSE (weighted population)
-- Corrected version: excludes AGEBs without AMAI population

-- Why this table is necessary:
-- Each neighborhood (colonia) intersects multiple AGEBs
-- Each AGEB has different AMAI population values
-- Each neighborhood covers a different percentage of each AGEB
-- We need to weight population by intersection area

-- This is required to next steps:
-- Sum by neighborhood
-- Calculate percentages
-- Calculate NSE_SCORE
-- Determine dominant NSE
-- Assign NSE_LABEL
-- Copy COLONIA_NSE results to Boundaries layer 6

-- Exclusions:
-- ✔ AGEBs without population
-- ✔ Prevents one intersection with NSE_TOTAL = 0 from breaking the whole neighborhood
-- ✔ AMAI-compatible
-- ✔ 100% robust

DROP TABLE IF EXISTS COLONIA_NSE;
GO

SELECT
    I.CVE_COLONIA,
    SUM(CASE WHEN A.NSE_TOTAL IS NOT NULL THEN I.pct_area * A.NSE_AB     ELSE 0 END) AS NSE_AB,
    SUM(CASE WHEN A.NSE_TOTAL IS NOT NULL THEN I.pct_area * A.NSE_CPLUS  ELSE 0 END) AS NSE_CPLUS,
    SUM(CASE WHEN A.NSE_TOTAL IS NOT NULL THEN I.pct_area * A.NSE_C      ELSE 0 END) AS NSE_C,
    SUM(CASE WHEN A.NSE_TOTAL IS NOT NULL THEN I.pct_area * A.NSE_CMINUS ELSE 0 END) AS NSE_CMINUS,
    SUM(CASE WHEN A.NSE_TOTAL IS NOT NULL THEN I.pct_area * A.NSE_DPLUS  ELSE 0 END) AS NSE_DPLUS,
    SUM(CASE WHEN A.NSE_TOTAL IS NOT NULL THEN I.pct_area * A.NSE_D      ELSE 0 END) AS NSE_D,
    SUM(CASE WHEN A.NSE_TOTAL IS NOT NULL THEN I.pct_area * A.NSE_E      ELSE 0 END) AS NSE_E,
    SUM(CASE WHEN A.NSE_TOTAL IS NOT NULL THEN I.pct_area * A.NSE_TOTAL  ELSE 0 END) AS NSE_TOTAL
INTO COLONIA_NSE
FROM COLONIA_AGEB_INTERSECT I
LEFT JOIN AMAI_AGEB_2024 A
    ON I.CVE_AGEB = A.CVEGEO
GROUP BY I.CVE_COLONIA;
GO

---------------------------------------
-- Validation: Expected ~79,775 records
-- same number of records as Boundaries
---------------------------------------

SELECT COUNT(*) AS Records_NSE_COLONIA FROM COLONIA_NSE;

-----------------------------------------------
-- Validation: Neighborhoods with NSE_TOTAL = 0
-- Must return ~12708 Colonias_No_Pop 
-----------------------------------------------

SELECT COUNT(*) AS Neighborhood_No_Pop
FROM COLONIA_NSE
WHERE NSE_TOTAL = 0;

------------------------------------------------------
-- Validation example: 
-- Neighborhood El Cielo (CVE_COLONIA = 2300800010017)
-- CVE_COLONIA   NSE_AB  NSE_PLUS NSE_C   NSE_DPLUS NSE_DE  NSE_TOTAL
-- 2300800010017	6.69871	7.95565	6.69931	2.09404	0.00045	0.00018	0	23.448389
------------------------------------------------------

SELECT *
FROM COLONIA_NSE
WHERE CVE_COLONIA = '2300800010017';
```

# 4 — Calculate percentages by neighborhood (colonia)

This generates percentages per level and prepares everything for NSE_SCORE, dominant NSE, and NSE_LABEL:

- NSE_AB_PCT   
- NSE_CPLUS_PCT   
- NSE_C_PCT   
- NSE_CMINUS_PCT   
- NSE_DPLUS_PCT   
- NSE_D_PCT   
- NSE_E_PCT   

```sql
USE INMO;
GO

-- NSE Step 4.4 — Calculate percentages by neighborhood (colonia)

-- This generates:
-- NSE_AB_PCT
-- NSE_CPLUS_PCT
-- NSE_C_PCT   (C + C-)
-- NSE_DPLUS_PCT
-- NSE_DE_PCT  (D + E)
-- Prepares everything for NSE_SCORE, dominant NSE, and NSE_LABEL

-- We already have:
-- Boundaries ✔
-- COLONIA_AGEB_INTERSECT ✔
-- COLONIA_NSE ✔ (79,775 colonias with weighted population)

-- This step is critical because it converts weighted population into percentages,
-- which then feed into NSE_SCORE, dominant NSE, and NSE_LABEL.

--------------------------------------------
-- 1 Add the percentage columns to the table
--------------------------------------------

ALTER TABLE COLONIA_NSE
ADD NSE_AB_PCT      numeric(10,4),
    NSE_CPLUS_PCT   numeric(10,4),
    NSE_CMINUS_PCT  numeric(10,4),
    NSE_C_PCT       numeric(10,4),
    NSE_DPLUS_PCT   numeric(10,4),
    NSE_D_PCT       numeric(10,4),
    NSE_E_PCT       numeric(10,4);
GO

--------------------------
-- 2 Calculate percentages
--------------------------

UPDATE COLONIA_NSE
SET
    NSE_AB_PCT      = CASE WHEN NSE_TOTAL > 0 THEN ROUND(NSE_AB     * 100.0 / NSE_TOTAL, 4) END,
    NSE_CPLUS_PCT   = CASE WHEN NSE_TOTAL > 0 THEN ROUND(NSE_CPLUS  * 100.0 / NSE_TOTAL, 4) END,
    NSE_C_PCT       = CASE WHEN NSE_TOTAL > 0 THEN ROUND(NSE_C      * 100.0 / NSE_TOTAL, 4) END,
    NSE_CMINUS_PCT  = CASE WHEN NSE_TOTAL > 0 THEN ROUND(NSE_CMINUS * 100.0 / NSE_TOTAL, 4) END,
    NSE_DPLUS_PCT   = CASE WHEN NSE_TOTAL > 0 THEN ROUND(NSE_DPLUS  * 100.0 / NSE_TOTAL, 4) END,
    NSE_D_PCT       = CASE WHEN NSE_TOTAL > 0 THEN ROUND(NSE_D      * 100.0 / NSE_TOTAL, 4) END,
    NSE_E_PCT       = CASE WHEN NSE_TOTAL > 0 THEN ROUND(NSE_E      * 100.0 / NSE_TOTAL, 4) END;
GO

----------------------------------------------------------------------
-- Validation 1: Check that no percentages are NULL when NSE_TOTAL > 0
----------------------------------------------------------------------

SELECT CVE_COLONIA, NSE_TOTAL, NSE_AB_PCT, NSE_CPLUS_PCT, NSE_C_PCT, NSE_CMINUS_PCT, NSE_DPLUS_PCT, NSE_D_PCT, NSE_E_PCT
FROM COLONIA_NSE
WHERE NSE_TOTAL > 0
  AND (NSE_AB_PCT IS NULL OR NSE_CPLUS_PCT IS NULL OR NSE_C_PCT IS NULL OR NSE_CMINUS_PCT IS NULL OR NSE_DPLUS_PCT IS NULL OR NSE_D_PCT IS NULL OR NSE_E_PCT IS NULL);

----------------------------------------------------
-- Validation 2: Check that percentages sum to ~100%
----------------------------------------------------

SELECT TOP 20
    CVE_COLONIA,
    NSE_AB_PCT + NSE_CPLUS_PCT + NSE_C_PCT  + NSE_CMINUS_PCT + NSE_DPLUS_PCT + NSE_D_PCT + NSE_E_PCT AS SUM_PCT
FROM COLONIA_NSE;

---------------------------------------------------------------------------------
-- Validation 3: Confirm no colonias with NSE_TOTAL > 0 have all percentages NULL
---------------------------------------------------------------------------------

SELECT *
FROM COLONIA_NSE
WHERE NSE_TOTAL > 0
  AND NSE_AB_PCT IS NULL
  AND NSE_CPLUS_PCT IS NULL
  AND NSE_C_PCT IS NULL
  AND NSE_CMINUS_PCT IS NULL
  AND NSE_DPLUS_PCT IS NULL
  AND NSE_D_PCT IS NULL
  AND NSE_E_PCT IS NULL;

-----------------------------------------------------
-- Validation 4: Distribution of neighborhoods by NSE
-----------------------------------------------------

SELECT NSE_LABEL, COUNT(*) AS Neighborhoods
FROM (
    SELECT 
        CVE_COLONIA,
        CASE 
            WHEN NSE_AB_PCT     = (SELECT MAX(val) FROM (VALUES (NSE_AB_PCT),(NSE_CPLUS_PCT),(NSE_C_PCT),(NSE_CMINUS_PCT),(NSE_DPLUS_PCT),(NSE_D_PCT),(NSE_E_PCT)) AS t(val)) THEN 'AB'
            WHEN NSE_CPLUS_PCT  = (SELECT MAX(val) FROM (VALUES (NSE_AB_PCT),(NSE_CPLUS_PCT),(NSE_C_PCT),(NSE_CMINUS_PCT),(NSE_DPLUS_PCT),(NSE_D_PCT),(NSE_E_PCT)) AS t(val)) THEN 'C+'
            WHEN NSE_C_PCT      = (SELECT MAX(val) FROM (VALUES (NSE_AB_PCT),(NSE_CPLUS_PCT),(NSE_C_PCT),(NSE_CMINUS_PCT),(NSE_DPLUS_PCT),(NSE_D_PCT),(NSE_E_PCT)) AS t(val)) THEN 'C'
            WHEN NSE_CMINUS_PCT = (SELECT MAX(val) FROM (VALUES (NSE_AB_PCT),(NSE_CPLUS_PCT),(NSE_C_PCT),(NSE_CMINUS_PCT),(NSE_DPLUS_PCT),(NSE_D_PCT),(NSE_E_PCT)) AS t(val)) THEN 'C-'
            WHEN NSE_DPLUS_PCT  = (SELECT MAX(val) FROM (VALUES (NSE_AB_PCT),(NSE_CPLUS_PCT),(NSE_C_PCT),(NSE_CMINUS_PCT),(NSE_DPLUS_PCT),(NSE_D_PCT),(NSE_E_PCT)) AS t(val)) THEN 'D+'
            WHEN NSE_D_PCT      = (SELECT MAX(val) FROM (VALUES (NSE_AB_PCT),(NSE_CPLUS_PCT),(NSE_C_PCT),(NSE_CMINUS_PCT),(NSE_DPLUS_PCT),(NSE_D_PCT),(NSE_E_PCT)) AS t(val)) THEN 'D'
            WHEN NSE_E_PCT      = (SELECT MAX(val) FROM (VALUES (NSE_AB_PCT),(NSE_CPLUS_PCT),(NSE_C_PCT),(NSE_CMINUS_PCT),(NSE_DPLUS_PCT),(NSE_D_PCT),(NSE_E_PCT)) AS t(val)) THEN 'E'
        END AS NSE_LABEL
    FROM COLONIA_NSE
    WHERE NSE_TOTAL > 0
) AS Labels
GROUP BY NSE_LABEL
ORDER BY NSE_LABEL ASC;
```

### Expected results

#### Validation 1

Displays a table with percentages, check visually not all percentages _PCT fields are NULL when NSE_TOTAL > 0
If NSE_TOTAL > 0, at least one _PCT must have a value, but typically several must have a value.

#### Validation 2

|CVE_COLONIA  |SUM_PCT|
|-------------|-------|
|1307400010027|100.00|
|1205000010002|100.00|
|1000500010024|100.01|
|1400800010079|100.00|
|1305600010031|99.99|
|1205000010030|94.23|
|1202900010201|99.95|
|1305100260003|99.99|
|1200100010246|99.97|
|1000500010698|99.90|
|1304800010046|100.01|
|0710100010324|100.01|
|1403900010192|99.95|
|1412002310013|100.00|
|1902900010002|100.00|
|2107100010033|100.01|
|2111400011362|NULL|
|1605300010760|100.00|
|1607700670001|99.99|
|0400200010041|100.01|

#### Validation 3

NONE (Confirm no colonias with NSE_TOTAL > 0 have all percentages NULL)

#### Validation 4

|NSE_LABEL|Neighborhoods|
|--------|-------------|
|AB      |6317|
|C+      |11569|
|C       |7240|
|C-      |3073|
|D+      |756|
|D       |37718|
|E       |394|

# 5 — Calculate IDS_PROM and NSE_SCORE

```sql
USE INMO;
GO

---------------------------------------------------------
-- NSE Step 4.5 — Calculate IDS_PROM and NSE_SCORE
-- IDS_PROM  = weighted raw index (0–700)
-- NSE_SCORE = normalized index (1–7 scale)
---------------------------------------------------------

-- This is the weighted AMAI index, using simplified categories:
--
-- IDS_PROM:
-- Category   Weight
-- A/B        7
-- C+         6
-- C          5
-- C-         4
-- D+         3
-- D          2
-- E          1
--
-- NSE_SCORE = IDS_PROM / 100 (scale 1–7)

-----------------------------------------
-- 1. Drop previous columns if they exist
-----------------------------------------

IF EXISTS (SELECT 1 FROM sys.columns 
           WHERE Name = N'IDS_PROM' AND Object_ID = Object_ID(N'COLONIA_NSE'))
BEGIN
    ALTER TABLE COLONIA_NSE DROP COLUMN IDS_PROM;
END;

IF EXISTS (SELECT 1 FROM sys.columns 
           WHERE Name = N'NSE_SCORE' AND Object_ID = Object_ID(N'COLONIA_NSE'))
BEGIN
    ALTER TABLE COLONIA_NSE DROP COLUMN NSE_SCORE;
END;
GO

-----------------------
-- 2. Add clean columns
-----------------------
ALTER TABLE COLONIA_NSE
ADD IDS_PROM  numeric(10,4),
    NSE_SCORE numeric(10,4);
GO

---------------------------------------------------------------
-- 3. Calculate IDS_PROM (raw index) and NSE_SCORE (normalized)
---------------------------------------------------------------
UPDATE COLONIA_NSE
SET 
    IDS_PROM =
          ISNULL(NSE_AB_PCT,0)     * 7
        + ISNULL(NSE_CPLUS_PCT,0)  * 6
        + ISNULL(NSE_C_PCT,0)      * 5
        + ISNULL(NSE_CMINUS_PCT,0) * 4
        + ISNULL(NSE_DPLUS_PCT,0)  * 3
        + ISNULL(NSE_D_PCT,0)      * 2
        + ISNULL(NSE_E_PCT,0)      * 1,

    NSE_SCORE =
    (
          ISNULL(NSE_AB_PCT,0)     * 7
        + ISNULL(NSE_CPLUS_PCT,0)  * 6
        + ISNULL(NSE_C_PCT,0)      * 5
        + ISNULL(NSE_CMINUS_PCT,0) * 4
        + ISNULL(NSE_DPLUS_PCT,0)  * 3
        + ISNULL(NSE_D_PCT,0)      * 2
        + ISNULL(NSE_E_PCT,0)      * 1
    ) / 100.0;


---------------------------------------------------------
-- Validation
---------------------------------------------------------

-- 1. Verify NSE_SCORE is not NULL when NSE_TOTAL > 0
SELECT *
FROM COLONIA_NSE
WHERE NSE_TOTAL > 0 AND NSE_SCORE IS NULL;

-- 2. Inspect typical values
SELECT TOP 40 CVE_COLONIA, IDS_PROM, NSE_SCORE
FROM COLONIA_NSE
ORDER BY NSE_SCORE DESC;
```

### Expected results

#### Validation 1

- No records should appear if NSE_TOTAL > 0 and NSE_SCORE is not null

#### Validation 1

- Typical values IDS_PROM: 677.3900 (means is almost 7, the highest) and NSE_SCORE represents that in % as 6.7776   
- This query is NSE_SCORE Descending order so it is pislying the higuest ranked, you **ASC** to display the lower.  

|CVE_COLONIA  |IDS_PROM|NSE_SCORE|
|-------------|--------|---------|
|3110200010059|699.9992|7.0000|
|1904800010254|683.9540|6.8395|
|1904800010273|677.7567|6.7776|
|1903900011171|677.3900|6.7739|
|1901900010234|676.9549|6.7695|
|1901900010076|676.9533|6.7695|
|1901900010075|676.9539|6.7695|
|1901900010074|676.9531|6.7695|
|1901900010003|676.9513|6.7695|
|1901900010435|676.8476|6.7685|

# 6 — Calculate dominant NSE (A/B, C+, C, D+, DE)

```sql
USE INMO;
GO

-------------------------------------------------------------------
-- NSE Step 4.6 — Calculate dominant NSE (A/B, C+, C, C-, D+, D, E)
-- Select the category with the highest percentage
-------------------------------------------------------------------

-- 1. Drop NSE column if it exists
IF EXISTS (SELECT 1 FROM sys.columns 
           WHERE Name = N'NSE' AND Object_ID = Object_ID(N'COLONIA_NSE'))
BEGIN
    ALTER TABLE COLONIA_NSE DROP COLUMN NSE;
END;
GO

-- 2. Add clean NSE column
ALTER TABLE COLONIA_NSE
ADD NSE varchar(5);
GO

-- 3. Calculate dominant NSE using VALUES()
UPDATE COLONIA_NSE
SET NSE =
(
    SELECT TOP 1 Nivel
    FROM
    (
        VALUES
            ('A/B', NSE_AB_PCT),
            ('C+',  NSE_CPLUS_PCT),
            ('C',   NSE_C_PCT),
            ('C-',  NSE_CMINUS_PCT),
            ('D+',  NSE_DPLUS_PCT),
            ('D',   NSE_D_PCT),
            ('E',   NSE_E_PCT)
    ) AS X(Nivel, Valor)
    WHERE Valor IS NOT NULL
    ORDER BY Valor DESC
)
WHERE NSE_TOTAL > 0;
GO

-- 4. Colonias with no population → NSE = 'N/A'
UPDATE COLONIA_NSE
SET NSE = 'N/A'
WHERE NSE_TOTAL = 0;
GO

---------------------------------------------------------
-- Validation
---------------------------------------------------------

-- 1. No colonias with NSE_TOTAL > 0 should have NSE = NULL

SELECT *
FROM COLONIA_NSE
WHERE NSE_TOTAL > 0 AND NSE IS NULL;

-- 2. General distribution

SELECT NSE, COUNT(*) AS Colonias
FROM COLONIA_NSE
GROUP BY NSE
ORDER BY NSE ASC;
GO
```

### Expected results

#### Validation 1

Just headers, no records if there is no NSE = NULL.   

CVE_COLONIA	NSE_AB	NSE_CPLUS	NSE_C	NSE_CMINUS	NSE_DPLUS	NSE_D	NSE_E	NSE_TOTAL	NSE_AB_PCT	NSE_CPLUS_PCT	NSE_CMINUS_PCT	NSE_C_PCT	NSE_DPLUS_PCT	NSE_D_PCT	NSE_E_PCT	IDS_PROM	NSE_SCORE	NSE

#### Validation 2

|NSE|Colonias|
|---|--------|
|A/B|6087|
|C+|11747|
|C|7242|
|C-|3069|
|D+|758|
|D|37770|
|E|394|
|N/A|12708|

# 7 — Create NSE_LABEL 

Create NSE_LABEL with letter and percentage, example "A/B (57%)"

```sql
USE INMO
GO

---------------------------------------------------------
-- NSE Step 4.7 — Create NSE_LABEL
---------------------------------------------------------

-- Logic:
-- Add a column NSE_LABEL
-- Build a string with the dominant NSE + rounded percentage
-- Example: "A/B (47%)", "C+ (32%)", "N/A (0%)"

-- 1. Add NSE_LABEL column
ALTER TABLE COLONIA_NSE
ADD NSE_LABEL varchar(15);
GO

-- 2. Generate NSE_LABEL text
UPDATE COLONIA_NSE
SET NSE_LABEL = 
    CASE 
        WHEN NSE = 'A/B' THEN CONCAT('A/B (', CAST(ROUND(NSE_AB_PCT,0) AS INT), '%)')
        WHEN NSE = 'C+'  THEN CONCAT('C+ (',  CAST(ROUND(NSE_CPLUS_PCT,0) AS INT), '%)')
        WHEN NSE = 'C'   THEN CONCAT('C (',   CAST(ROUND(NSE_C_PCT,0) AS INT), '%)')
        WHEN NSE = 'C-'  THEN CONCAT('C- (',  CAST(ROUND(NSE_CMINUS_PCT,0) AS INT), '%)')
        WHEN NSE = 'D+'  THEN CONCAT('D+ (',  CAST(ROUND(NSE_DPLUS_PCT,0) AS INT), '%)')
        WHEN NSE = 'D'   THEN CONCAT('D (', CAST(ROUND(NSE_D_PCT,0) AS INT), '%)')
        WHEN NSE = 'E'   THEN CONCAT('E (', CAST(ROUND(NSE_E_PCT,0) AS INT), '%)')
        WHEN NSE = 'N/A' THEN 'N/A (0%)'
    END
WHERE NSE IS NOT NULL;
GO

---------------------------------------------------------
-- Validation
---------------------------------------------------------

-- 1. Sample results

SELECT TOP 20 CVE_COLONIA, NSE, NSE_LABEL
FROM COLONIA_NSE;

-- 2. Count colonias with NSE_LABEL
-- Expected: 79,775 total colonias
-- Minus ~12,708 with NSE_TOTAL = 0
-- ≈ 67,067 with valid NSE_LABEL

SELECT COUNT(*) AS Colonias_With_Label
FROM COLONIA_NSE
WHERE NSE_LABEL IS NOT NULL;
```

### Expected results

#### Validation 1

|CVE_COLONIA  |NSE|NSE_LABEL|
|-------------|---|---------|
|1307400010027|D|D (24%)|
|1205000010002|D|D (27%)|
|1000500010024|D|D (22%)|
|1400800010079|C-|C- (22%)|
|1305600010031|D|D (23%)|
|1205000010030|D|D (27%)|
|1202900010201|D|D (25%)|
|1305100260003|A/B|A/B (30%)|
|1200100010246|D|D (40%)|
|1000500010698|C+|C+ (29%)|
|1304800010046|C|C (20%)|
|0710100010324|D|D (24%)|
|1403900010192|C+|C+ (28%)|
|1412002310013|C-|C- (23%)|
|1902900010002|D|D (26%)|
|2107100010033|D|D (42%)|
|2111400011362|A/B|A/B (42%)|
|1605300010760|C|C (19%)|
|1607700670001|D|D (37%)|
|0400200010041|D|D (33%)|

#### Validation 2

Colonias_With_Label  
79775  
This means all Neighborhoods have a NSE_LABEL

# 8 — Copy COLONIAS_NSE calculations to Boundaries layer = 6

```sql
USE INMO;
GO

---------------------------------------------------------
-- NSE Step 4.8 — Update Boundaries Layer 6 with final values
-- Requires that Steps 4.5, 4.6, and 4.7 have already been executed
---------------------------------------------------------

-- 1. Validate that required columns exist in COLONIA_NSE
--    If any are missing → ABORT
IF NOT EXISTS (SELECT 1 FROM sys.columns 
               WHERE Name = 'NSE' AND Object_ID = OBJECT_ID('COLONIA_NSE'))
BEGIN
    RAISERROR('ERROR: Missing column NSE. Step 4.6 not executed.', 16, 1);
    RETURN;
END;

IF NOT EXISTS (SELECT 1 FROM sys.columns 
               WHERE Name = 'NSE_LABEL' AND Object_ID = OBJECT_ID('COLONIA_NSE'))
BEGIN
    RAISERROR('ERROR: Missing column NSE_LABEL. Step 4.7 not executed.', 16, 1);
    RETURN;
END;

IF NOT EXISTS (SELECT 1 FROM sys.columns 
               WHERE Name = 'NSE_SCORE' AND Object_ID = OBJECT_ID('COLONIA_NSE'))
BEGIN
    RAISERROR('ERROR: Missing column NSE_SCORE. Step 4.5 not executed.', 16, 1);
    RETURN;
END;

IF NOT EXISTS (SELECT 1 FROM sys.columns 
               WHERE Name = 'IDS_PROM' AND Object_ID = OBJECT_ID('COLONIA_NSE'))
BEGIN
    RAISERROR('ERROR: Missing column IDS_PROM. Step 4.5 not executed.', 16, 1);
    RETURN;
END;

PRINT 'Validation OK: All required columns exist.';
GO

---------------------------------------------------------
-- 2. Clear previous values in Boundaries Layer 6
---------------------------------------------------------
UPDATE Boundaries
SET 
    NSE        = NULL,
    NSE_LABEL  = NULL,
    NSE_SCORE  = NULL,
    IDS_PROM   = NULL,
    NSE_TOTAL  = NULL,

    NSE_AB     = NULL,
    NSE_CPLUS  = NULL,
    NSE_C      = NULL,
    NSE_CMINUS = NULL,
    NSE_DPLUS  = NULL,
    NSE_D      = NULL,
    NSE_E      = NULL,

    NSE_AB_PCT     = NULL,
    NSE_CPLUS_PCT  = NULL,
    NSE_C_PCT      = NULL,
    NSE_CMINUS_PCT = NULL,
    NSE_DPLUS_PCT  = NULL,
    NSE_D_PCT      = NULL,
    NSE_E_PCT      = NULL
WHERE Layer = 6;
GO

PRINT 'Previous values cleared successfully.';
GO

---------------------------------------------------------
-- 3. Copy final data from COLONIA_NSE into Boundaries Layer 6
---------------------------------------------------------
UPDATE B
SET
    B.NSE            = C.NSE,
    B.NSE_LABEL      = C.NSE_LABEL,
    B.NSE_SCORE      = C.NSE_SCORE,
    B.IDS_PROM       = C.IDS_PROM,

    B.NSE_TOTAL      = C.NSE_TOTAL,

    B.NSE_AB         = C.NSE_AB,
    B.NSE_CPLUS      = C.NSE_CPLUS,
    B.NSE_C          = C.NSE_C,
    B.NSE_CMINUS     = C.NSE_CMINUS,
    B.NSE_DPLUS      = C.NSE_DPLUS,
    B.NSE_D          = C.NSE_D,
    B.NSE_E          = C.NSE_E,

    B.NSE_AB_PCT     = C.NSE_AB_PCT,
    B.NSE_CPLUS_PCT  = C.NSE_CPLUS_PCT,
    B.NSE_C_PCT      = C.NSE_C_PCT,
    B.NSE_CMINUS_PCT = C.NSE_CMINUS_PCT,
    B.NSE_DPLUS_PCT  = C.NSE_DPLUS_PCT,
    B.NSE_D_PCT      = C.NSE_D_PCT,
    B.NSE_E_PCT     = C.NSE_E_PCT
FROM Boundaries B
JOIN COLONIA_NSE C
    ON B.CVEGEO = C.CVE_COLONIA
WHERE B.Layer = 6;
GO

PRINT 'Boundaries Layer 6 updated successfully.';
GO

---------------------------------------------------------
-- 4. Final validations
---------------------------------------------------------

-- Distribution of NSE categories
SELECT NSE, COUNT(*) AS Records
FROM Boundaries
WHERE Layer = 6
GROUP BY NSE
ORDER BY NSE ASC, COUNT(*) DESC;

-- Colonias with population > 0 should not have NSE_SCORE = NULL
-- Should retun NONE
SELECT *
FROM Boundaries
WHERE Layer = 6
  AND NSE_TOTAL > 0
  AND NSE_SCORE IS NULL;

-- Colonias with no population should not have NSE assigned
-- Must return ~13859 that didn't have NSE_TOTAL and NSE values
SELECT 
 State, 
 Municipality, 
 City, 
 Neighborhood, 
 NSE, 
 NSE_LABEL, 
 NSE_SCORE,
 IDS_PROM,
 NSE_TOTAL,
 NSE_AB,
 NSE_CPLUS,
 NSE_C,
 NSE_CMINUS,
 NSE_DPLUS,
 NSE_D,
 NSE_E,
 NSE_AB_PCT,
 NSE_CPLUS_PCT,
 NSE_C_PCT,
 NSE_CMINUS_PCT,
 NSE_DPLUS_PCT,
 NSE_D_PCT,
 NSE_E_PCT
FROM Boundaries
WHERE Layer = 6
  AND NSE_TOTAL = 0
  AND NSE IS NOT NULL;

-- Sample results
SELECT TOP 20 CVEGEO, NSE, NSE_LABEL, NSE_SCORE, NSE_TOTAL
FROM Boundaries
WHERE Layer = 6;
GO
```

### Expected results

#### Validation 1

|NSE|Records|
|---|-------|
|A/B|   6087|
|C  |   7242|
|C+ |  11747|
|C- |   3069|
|D  |  37770|
|D+ |    758|
|E  |    394|
|N/A|  12708|

#### Validation 2

None as if NSE_TOTAL > 0 AND NSE_SCORE IS NULL

#### Validation 3

14,162 records where NSE_TOTAL = 0 (as original file has no data for those)
