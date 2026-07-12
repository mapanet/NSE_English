# STEP 2 — Marco Geoestadístico 2025 geometries

Objective: Build table `Boundaries_AGEB_2025` with the official AGEB geometries from INEGI MG 2025.  

This table will be used for:  

- Intersecting neighborhoods (colonias) with AGEB area geometries
- Calculating area proportions
- Weighting AMAI population by neighborhood (colonia)

## Suggested work directories

- D:\AXSI\INEGI\MG_2025 (work files)
- D:\AXSI\INEGI\MG_2025\Download (downloaded file and unzipped content to load into QGIS)
- D:\AXSI\INEGI\MG_2025\AGEB (save the processed AGEB shape MG_AGEB_2025.SHP as EPSG:4023)

## 1 — Official Download of Marco Geoestadístico 2025

The Marco Geoestadístico 2025 can be downloaded from INEGI:

https://www.inegi.org.mx/app/biblioteca/ficha.html?upc=889463807469

Download file:

**794551163061_s.zip**

**Page looks like this:**

[<img src="/docs/images/MG_2025.png" width="1000">](/docs/images/MG_2025.png)

### Save as

D:\AXSI\INEGI\MG_2025\Download\794551163061_s.zip

Inside the ZIP you will find:

- mg_2025_integrado.zip  
  - conjunto_de_datos/  
    - 00a.shp **← main AGEB areas file**

Contect of files inside the dataset (informational):

- 00_ent = State (polygons)  
- 00_mun = Municipality (polygons)
- 00_a = Urban and Rural AGEB (polygons **← AGEB areas**  
- 00_lpr = Locality (point)  
- 00_l = Locality Urban and Rural (polygons)  

## 2 — Contents of the file 00a.shp

Load `00a.shp` in QGIS, ch eck the layer contains the following fields:


| Field     | Description                          |
|-----------|--------------------------------------|
| CVE_ENT   | State code (2 digits)                |
| CVE_MUN   | Municipality code (3 digits)         |
| CVE_LOC   | Locality code (4 digits)             |
| CVE_AGEB  | AGEB code (4 digits)                 |
| CVEGEO    | Full geographic key (13 digits)      |
| AMBITO    | Urbano / Rural                       |
| geom      | Geometry (Polygon / MultiPolygon)    |

Total records: **82,263 AGEB**  
Original CRS: **MEXICO_IRF‑2008_LLC** 


## 3 — Export from QGIS to CRS EPSG:4326)

Export the layer `00a.shp` as:

**D:\AXSI\INEGI\MG_2025\AGEB\MG_AGEB_2025.shp**  
Make sure select CRS: **EPSG:4326** (very important)

From this new layer MG_AGEB_2025, export to CSV as:

**D:\AXSI\INEGI\MG_2025\Boundaries_AGEB_2025_WKT.csv**

- UTF‑8 encoding  
- TAB delimiter
- WKT as EPSG:4326 coordinates

| Column   | Description |
|----------|-------------|
| WKT      | Geometry in WKT format |
| CVE_ENT  | State code |
| CVE_MUN  | Municipality code |
| CVE_LOC  | Locality code |
| CVE_AGEB | AGEB code |
| CVEGEO   | Full geographic key |
| AMBITO   | Urbano / Rural |

If you edit the CSV you should see something like this:

| WKT | CVE_ENT |CVE_MUN | CVE_LOC | CVE_AGEB | CVEGEO | AMBITO |
|---------------------------------------------------|---------|---------|---------|---------|--------------|-------|
|MULTIPOLYGON (((-102.27 21.87, ... -102.27 21.87)))| 01 | 001 | 0001 | 216A | 010010001216A | Urbano |
|MULTIPOLYGON (((-102.24 21.86, ... -102.24 21.86)))	| 01 | 001 | 0001 | 2649 | 0100100012649 | Urbano |

## 4 — Create the MS SQL Staging table

We create a staging table to import the data as since QGIS creates the CSV with WKT geometry in 1st position.
Then we will create and copy the imported data to the final table.

* check file path you used to store CSV file

```sql
------------------------------
-- 4 Create the taging Table
------------------------------
DROP TABLE IF EXISTS dbo.Boundaries_AGEB_2025_IMPORT;

CREATE TABLE Boundaries_AGEB_2025_IMPORT (
    WKT        nvarchar(MAX),
    CVE_ENT    char(2),
    CVE_MUN    char(3),
    CVE_LOC    char(4),
    CVE_AGEB   char(4),
    CVEGEO     nvarchar(13),
    AMBITO     char(10)
);

------------------------
-- Import CSV (TSV) file
------------------------
BULK INSERT Boundaries_AGEB_2025_IMPORT 
FROM 'D:\AXSI\INEGI\MG_2025\Boundaries_AGEB_2025_WKT.csv' 
WITH ( 
    FIRSTROW = 2,
    FIELDTERMINATOR = '\t', 
    ROWTERMINATOR = '\n', 
    CODEPAGE = '65001'
);
```

#### Expected result

(82283 rows affected)   
Completion time: 2026-05-24T18:16:03.7467723-05:00   

## 5 — Create Final Table: Boundaries_AGEB_2025

```sql
-----------------------------------------------
-- 5 Create Final Table: Boundaries_AGEB_2025
-----------------------------------------------
DROP TABLE IF EXISTS dbo.Boundaries_AGEB_2025;

CREATE TABLE dbo.Boundaries_AGEB_2025
(
    ID            BIGINT IDENTITY(1,1) PRIMARY KEY,
    CVEGEO        NVARCHAR(13) NOT NULL UNIQUE,

    -- Components of CVEGEO key
    CVE_ENT       CHAR(2)  NULL,
    CVE_MUN       CHAR(3)  NULL,
    CVE_LOC       CHAR(4)  NULL,
    CVE_AGEB      CHAR(4)  NULL,

    -- Type (Ámbito): Urbano, Rural (urban or rural)
    Type          CHAR(10)  NULL,

    -- Population and Dwellings (will be filled with Census 2020)
    Population	int	NULL,
    Dwellings	int	NULL,
    Occupied_Dwellings	int	NULL

    -- Geometries
    geom          GEOMETRY NOT NULL,
    geog          GEOGRAPHY NULL,
);

-- Spatial indexes
CREATE SPATIAL INDEX SIDX_Boundaries_AGEB_2025_geog
ON dbo.Boundaries_AGEB_2025(geog)
USING GEOGRAPHY_AUTO_GRID;

CREATE SPATIAL INDEX SIDX_Boundaries_AGEB_2025_geom
ON dbo.Boundaries_AGEB_2025(geom)
WITH (BOUNDING_BOX = (-180, -90, 180, 90));
```

#### Expect results

Commands completed successfully.   


## 6 — Insert Data from the Staging Table

```sql
-----------------------------------------
-- 6 Insert Data from the Staging Table
-----------------------------------------
INSERT INTO Boundaries_AGEB_2025 (
    CVEGEO, CVE_ENT, CVE_MUN, CVE_LOC, CVE_AGEB, Type, geom
)
SELECT
    CVEGEO,
    CVE_ENT,
    CVE_MUN,
    CVE_LOC,
    CVE_AGEB,
    AMBITO,
    geometry::STGeomFromText(WKT, 4326)
FROM Boundaries_AGEB_2025_IMPORT;

--------------------
-- Valite geometries
--------------------
UPDATE Boundaries_AGEB_2025 SET geom = geom.MakeValid() WHERE geom.STIsValid() = 0;

-------------------------
-- drop the staging table
-------------------------
DROP TABLE dbo.Boundaries_AGEB_2025_IMPORT;
```

#### Expected results

(82283 rows affected)   


## 8 — Geometry Validation and Correction

### Validate invalid geometries

✅ Querys should return nothing

```sql
-----------------------------------------
-- 2.8 Geometry Validation and Correction
-----------------------------------------
SELECT ID, CVEGEO
FROM Boundaries_AGEB_2025
WHERE geom.STIsValid() = 0;
```

#### Expected results

ID	CVEGEO   
None  
(all geometries are valid)   

### Correct invalid geometries using MakeValid

If query returns results, it indicates a problem that must be fixed, use the next step to correct them.

1️⃣ Only if Invalid geometries run:
This SQL should make all invalid to valid and return zero rows:

```sql
-----------------------------------------------
-- 1 Correct invalid geometries using MakeValid
-----------------------------------------------
UPDATE Boundaries_AGEB_2025
SET geom = geom.MakeValid()
WHERE geom.STIsValid() = 0;
```

#### Expected results

(0 rows affected)   


## 9 — Copy geometry: geom column to geography: geog column

```sql
-----------------------------------------------------------
-- 9 Copy geometry: geom column to geography: geog column
-----------------------------------------------------------
UPDATE Boundaries_AGEB_2025
SET geog = geography::STGeomFromText(geom.STAsText(), 4326);
```

#### Expected results

(82283 rows affected)   

---

### Validate geog (geography)

2️⃣ Missing geography check
This should also return zero rows:

```sql
------------------------------
-- 2 - Missing geography check
------------------------------
SELECT ID
FROM Boundaries_AGEB_2025
WHERE geog IS NULL;
```

#### Expected results

ID  
None  
(all geography fields have a geometry)  

---

## Final Result

The table `Boundaries_AGEB_2025` now contains:

- 82,263 AGEB
- Valid geometries
- Complete CVEGEO
- Urban/Rural scope
- Population and Dwellings fields ready to be filled later

It is used for:

- Intersecting neighborhood (colonias) with AGEB geometries
- Calculating area proportions
- Weighting AMAI population by neighborhood (colonia)
- Serving as the base for NSE calculation per Neighborhood (colonia)


