# 3.0 INEGI DCAH 2025 (Neighborhood Polygons)

This document describes the process to import the **INEGI DCAH 2025** dataset, which contains the official polygon boundaries of neighborhoods (*colonias*) and other human settlements in Mexico.  
These geometries are used to build **Boundaries Layer 6**, where the AMAI Socioeconomic Level (NSE) is calculated for each neighborhood.

Suggested working directories  

Working : D:\AXSI\INEGI\DCAH_2025  
Download: D:\AXSI\INEGI\DCAH_2025\Download  

---

## Dataset Description

**Source:** INEGI — *Delimitación de colonias y otros asentamientos humanos (DCAH)*  
**Edition (edicion):** 2025  
**Coverage (cobertura):** 2025‑01‑01 to 2025‑12‑31  
**Datum:** ITRF2008, Ellipsoid GRS80  
**File type (tipo de archivo):** SHP (530.26 MB)  
**Download URL:** [https://www.inegi.org.mx/programas/dcah/#descargas](https://www.inegi.org.mx/programas/dcah/#descargas)

**Page looks like this:**

[<img src="/docs/images/DCAH_2025.png" width="1000">](/docs/images/DCAH_2025.png)

---

## 3.1 Download data

1. Open the INEGI DCAH download page:  
   [https://www.inegi.org.mx/programas/dcah/#descargas](https://www.inegi.org.mx/programas/dcah/#descargas)

Cartografía geoestadística histórica de México
=> https://www.inegi.org.mx/app/biblioteca/ficha.html?upc=794551131954

Información Topográfica a escala 1:50,000 y sus actualizaciones
=> https://www.inegi.org.mx/programas/topografia/50000/#descargas

2. In the **Filters** section, leave all options as default:
   - **Entity:** Estados Unidos Mexicanos  
   - **Scale:** Sin escala  
   - **Edition:** (leave blank)

3. Click **Consultar** or **Buscar** to display available editions.

4. From the results table, select:
   - **Delimitación de colonias y otros asentamientos humanos 2025**  
   - File type: **SHP**  
   - Size: **530.26 MB**

5. Download the ZIP file and extract the contents into:

Directory: D:\INEGI\DCAH_2025\Download
File name: **794551163078_s.zip** 2025 edition

Inside you will find a series of zip's by state and one named: 00_integrado.zip that contain data of all states.
Extract the files is BOLD:

- 00_integrado.zip
  - conjunto_de_datos
      - **00as.shp** (SHP file main) Datum: ITRF2008
      - **00as.cpg** (SHP file accesory)
      - **00as.dbf** (SHP file accesory)
      - **00as.prj** (SHP file accesory)
      - **00as.sbn** (SHP file accesory)
      - **00as.sbx** (SHP file accesory)
      - **00as.shx** (SHP file accesory)

Dataset include:

| Field | Description |
|-------|--------------|
| **CVEGEO** | cvegeo code 13 digits EEMMMLLLLAAAA (EE state, MMM municipality, LLLL Locality, AAAA Neighborhood |
| **CVE_ENT** | State code |
| **CVE_MUN** | Municipality code |
| **CVE_LOC** | Locality code |
| **CVE_ASEN** | Locality code |
| **CP** | Postal code |
| **FECHA_ACT** | Last Update MM/YYYY |
| **INSTITUCIO** | Source name |
| **NOM_ASEN** | Neighborhood name |
| **TIPO** | Category name (Fraccionamiento, Colonia, etc. (Urbanization type) |
| **geom** | Neighborhood boundary polygon |

---

## 3.2 Load the 00as.shp into QGIS

Verify NOM_ASEN is legible (accents) data originally is Windows-1252 but file may be loaded as UTF-8)
(if needed, use layer Properties > Source > Windows-1252 to set encoding, check accents in Attributes table)

### Export it as

Directory: D:\AXSI\INEGI\DCAH_2025  
File name: Boundaries_INEGI_DCAH_2025.shp  
CRS: **ESPG:4023**  
Encoding: **UTF-8**  

- Delete source 00as.shp layer in QGIS

---

# 3.3 Save as CSV with WKT geometries

Export Boundaries_INEGI_DCAH_2025 layer to CSV with WKT geometries

- Directory: D:\AXSI\INEGI\DCAH_2025
- File name: Boundaries_INEGI_DCAH_2025.CSV
- CRS: **ESPG:4023**
- Encoding: **UTF-8**
- Geometry: **As WKT**
- Delimiter: **TAB**
- String quting: **IF_NEEDED**
- Write BOM: **NO**
- Add saved file to MAP: **Uncheck**

Save "OK"

----

Edit Boundaries_INEGI_DCAH_2025.CSV with EditPad Pro or Notepad+

Replace all doune quotes (") created in the geometries "MULTIPOLYGON ((( ... )))"

Save file, making sure is **UTF-8** and **No BOM**

### Result file

| Field | Description |
|-------|--------------|
| **WTK** | Neighborhood boundary polygon |
| **CVEGEO** | cvegeo code 13 digits
| **CVE_ENT** | State code |
| **CVE_MUN** | Municipality code |
| **CVE_LOC** | Locality code |
| **CVE_ASEN** | Locality code |
| **CP** | Postal code |
| **FECHA_ACT** | Last Update MM/YYYY |
| **INSTITUCIO** | Source name |
| **NOM_ASEN** | Neighborhood name |
| **TIPO** | Category name (Fraccionamiento, Colonia, etc. (Urbanization type) |

---

# 3.4 Upload CSV geometries to SQL

```sql
--------------------------------------------
-- 3.4 — Upload Upload CSV geometries to SQL
--------------------------------------------

-----------------------------
-- 3.4.1 Create staging table
-----------------------------
DROP TABLE IF EXISTS INEGI_DCAH_Staging;
GO

CREATE TABLE INEGI_DCAH_Staging (
    WKT varchar(MAX) NOT NULL,
    CVEGEO varchar(16) NOT NULL,
    CVE_ENT varchar(2) NULL,
    CVE_MUN varchar(3) NOT NULL,
    CVE_LOC varchar(4) NOT NULL,
    CVE_ASEN varchar(4) NOT NULL,
    CP varchar(5) NOT NULL,
    FECHA_ACT varchar(10) NULL,
    INSTITICIO nvarchar(500) NULL,
    NOM_ASEN nvarchar(115) NOT NULL,
    TIPO nvarchar(100) NOT NULL
);
GO

--------------------
-- 3.4.2 Bulk Insert
--------------------
BULK INSERT INEGI_DCAH_Staging
FROM 'D:\AXSI\INEGI\DCAH_2025\Boundaries_INEGI_DCAH_2025.csv'
WITH (
    FIRSTROW = 2,
    FIELDTERMINATOR = '\t',
    ROWTERMINATOR = '\n',
    CODEPAGE = '65001',  -- UTF-8
    TABLOCK
);
GO
```
### Expected results

(79775 rows affected)

### Check results on INEGI_DCAH_Staging

```sql
SELECT TOP (5) WKT, GVEGEO, CVE_ENT, CVE_MUN, CVE_LOC, CVE_ASEN, CP, FECHA_ACT, INSTITICIO, NOM_ASEN, TIPO
FROM  dbo.INEGI_DCAH_Staging
```

|WKT|GVEGEO|CVE_ENT|CVE_MUN|CVE_LOC|CVE_ASEN|CP|FECHA_ACT|INSTITICIO|NOM_ASEN|TIPO|
|---|------|-------|-------|-------|--------|--|---------|----------|--------|----|
MULTIPOLYGON|0503300010076|05|033|0001|0076|27810|11/2022|AYUNTAMIENTO|VILLAS DEL AMÉRICA|FRACCIONAMIENTO|
MULTIPOLYGON|0503300010077|05|033|0001|0077|27810|11/2022|AYUNTAMIENTO|NINGUNO|COLONIA|
MULTIPOLYGON|0503300010079|05|033|0001|0079|00000|11/2022|AYUNTAMIENTO|LOS NOGALES|FRACCIONAMIENTO|
MULTIPOLYGON|0503300010081|05|033|0001|0081|00000|11/2022|AYUNTAMIENTO|SAN JOSÉ|COLONIA|
MULTIPOLYGON|0503300010084|05|033|0001|0084|00000|11/2022|AYUNTAMIENTO|EJIDAL VALPARAISO|COLONIA|

---

# 3.5 Create Boundaries table

```sql
CREATE TABLE [dbo].[Boundaries](
	[ID] [bigint] IDENTITY(1,1) NOT NULL,
	[CVEGEO] [varchar](16) NULL,
	[Layer] [int] NOT NULL,
	[ISO] [nvarchar](2) NULL,
	[Country] [nvarchar](25) NULL,
	[State] [nvarchar](85) NULL,
	[Municipality] [nvarchar](85) NULL,
	[City] [nvarchar](110) NULL,
	[Neighborhood] [nvarchar](115) NULL,
	[Category] [nvarchar](85) NULL,
	[PostalCode] [varchar](5) NULL,
	[Population] [int] NULL,
	[Dwelings] [int] NULL,
    [Occupied_Dwelings] [int] NULL,
	[Type] [varchar](10) NULL,
	[AreaM2] [float] NULL,
	[geog] [geography] NULL,
	[geom] [geometry] NULL,
	[minLat] [decimal](12, 6) NULL,
	[maxLat] [decimal](12, 6) NULL,
	[minLon] [decimal](12, 6) NULL,
	[maxLon] [decimal](12, 6) NULL,
	[IDS_PROM] [numeric](6, 3) NULL,
	[NSE] [varchar](5) NULL,
	[NSE_LABEL] [varchar](15) NULL,
	[NSE_AB_PCT] [numeric](5, 2) NULL,
	[NSE_CPLUS_PCT] [numeric](5, 2) NULL,
	[NSE_C_PCT] [numeric](5, 2) NULL,
	[NSE_DPLUS_PCT] [numeric](5, 2) NULL,
	[NSE_DE_PCT] [numeric](5, 2) NULL,
	[NSE_AB] [int] NULL,
	[NSE_CPLUS] [int] NULL,
	[NSE_C] [int] NULL,
	[NSE_DPLUS] [int] NULL,
	[NSE_DE] [int] NULL,
	[NSE_TOTAL] [int] NULL,
	[NSE_SCORE] [numeric](6, 3) NULL,
	[LastUpdate] [varchar](10) NULL,
	[Source] [nvarchar](400) NULL
 CONSTRAINT [PK_Boundaries] PRIMARY KEY CLUSTERED 
(
	[ID] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO

ALTER TABLE [dbo].[Boundaries] ADD  CONSTRAINT [DF_Boundaries_Layer]  DEFAULT ((6)) FOR [Layer]
GO

ALTER TABLE [dbo].[Boundaries] ADD  CONSTRAINT [DF_Boundaries_ISO]  DEFAULT ('MX') FOR [ISO]
GO

ALTER TABLE [dbo].[Boundaries] ADD  CONSTRAINT [DF_Boundaries_Country]  DEFAULT ('México') FOR [Country]
GO
```

--- 

## 3.6 Copy DCAH Staging Data into Boundaries (Layer = 6)

```sql
------------------------------------------------------------
-- 3.6 — Copy DCAH Staging Data into Boundaries (Layer = 6)
------------------------------------------------------------

INSERT INTO dbo.Boundaries (
    CVEGEO,
    Layer,
    Neighborhood,
    Category,
    PostalCode,
    geom,
    LastUpdate,
    Source
)
SELECT
    CVEGEO,                              -- Unique geographic key
    6 AS Layer,                          -- Neighborhood layer
    NOM_ASEN AS Neighborhood,            -- Neighborhood name (Colonia)
    TIPO AS Category,                    -- Settlement type
    CP AS PostalCode,                    -- Postal code
    geometry::STGeomFromText(WKT, 4326), -- Convert WKT to geometry (EPSG:4326)
    RIGHT(FECHA_ACT, 4) + '-' + LEFT(FECHA_ACT, 2) AS LastUpdate, -- Convert MM/YYYY → YYYY-MM
    INSTITICIO AS Source                 -- Data source
FROM dbo.INEGI_DCAH_Staging;
GO
```

### Expected result

(79775 rows affected)

### Delete staging if copy was sucessfull

```sql
DROP TABLE IF EXISTS dbo.INEGI_DCAH_Staging;
```

---

## 3.8 Validate geomtery (geom)

The imported WKT geometries must be checked for validity.  
Invalid geometries are repaired using `MakeValid()`.

```sql
----------------------------------
-- 3.8.0 Detect invalid geometries
----------------------------------

SELECT ID, CVEGEO
FROM dbo.Boundaries
WHERE geom.STIsValid() = 0;
```

### Expected result

ID CVEGEO   
None  
If other than None, run next process, otherwise run next step 8.9  

```sql

-------------------------------------------
-- 3.8.1 Fix invalid geometries (MakeValid)
-------------------------------------------

UPDATE dbo.Boundaries
SET geom = geom.MakeValid()
WHERE geom.STIsValid() = 0;
```

----

## 3.9 Generate Geography (geog) from Geometry

The geog column stores the same geometry in SQL Server’s geography type (EPSG:4326).  
This enables distance calculations and geodesic operations.  

```sql
UPDATE dbo.Boundaries
SET geog = geography::STGeomFromText(geom.STAsText(), 4326);
```

### Excepcted result

(79775 rows affected)

Validation:

```sql
SELECT ID, CVEGEO
FROM dbo.Boundaries
WHERE geog IS NULL;
```

### Excepcted result

IS CVEGEO   
None  

---

## 3.10 Compute Bounding Box Fields

Bounding box values are derived from the geom envelope:  

- minLat
- maxLat
- minLon
- maxLon

```sql
UPDATE dbo.Boundaries
SET 
    minLat = geom.STEnvelope().STPointN(1).STY,
    minLon = geom.STEnvelope().STPointN(1).STX,
    maxLat = geom.STEnvelope().STPointN(3).STY,
    maxLon = geom.STEnvelope().STPointN(3).STX;
```

### Excepcted result

(79775 rows affected)

Validation:

```sql
SELECT TOP 20 CVEGEO, minLat, maxLat, minLon, maxLon
FROM dbo.Boundaries;
```

You should see valid numeric values.

---

## 3.11 Create Spatial Indexes

Spatial indexes significantly improve performance for intersection, containment, and proximity queries.

```sql
------------------------------------------
-- 3.11.1 Spatial Index for geom (geometry)
------------------------------------------
CREATE SPATIAL INDEX SIDX_Boundaries_geom
ON dbo.Boundaries_TEMP(geom)
WITH (BOUNDING_BOX = (-180, -90, 180, 90));

--------------------------------------------
-- 3.11.2 Spatial Index for geog (geography)
--------------------------------------------

CREATE SPATIAL INDEX SIDX_Boundaries_geog
ON dbo.Boundaries_TEMP(geog);
```

### Excepcted result

Commands completed successfully.

---


## Next Steps to calculate NSE (socioeconomic levels)

1. Validate geometries integrity of **Boundaries_AGEB_2025** and **Boundaries** layer 6 (no empty or self‑intersecting polygons).  
2. Check and normalize Boundaries_AGEB_2025 keys **CVEGEO** = CVE_ENT + CVE_MUN + CVE_LOC + CVE_ASEN  
3. Intersect with AGEB geometries from **Boundaries_AGEB_2025** (INEGI MG 2025).  
4. Apply area‑weighted NSE aggregation using **AMAI 2024** and **Census 2020** data.  
5. Enrich **Boundaries Layer 6 NSE dataset** with NSE calculations.

---

**Result:**  
A complete, validated neighborhood‑level dataset ready for NSE calculation, mapping, and API integration.
