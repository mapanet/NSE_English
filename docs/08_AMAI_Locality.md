# 08 AMAI LOCALIDAD 2024 Data Ingestion (NSE by LOC)

Objective: Convert the official AMAI file NSE_por_localidad_AMAI_2024.xlsx into a normalized SQL table ready for the NSE pipeline.

## Suggested work directories

- D:\AXSI\AMAI — working files
- D:\AXSI\AMAI\Download  — downloaded source files

---

## 1. — Official Source File

AMAI publishes the dataset in its downloads section:

https://www.amai.org/NSE/index.php?queVeo=NSEDES&Logeado=s (download NSE por localidad)


Important characteristics of the file:

- The filename does not include a year.
- It corresponds to the NSE 2024 methodology.

[<img src="/docs/images/AMAI_2024.png" width="1000">](/docs/images/AMAI_2024.png)

---

## 2. — Original File Contents

The file contains one row per urban AGEB from Census 2020.

Original columns:

| Column | Meaning |
|--------|---------|
| CLAVE LOCALIDAD | CVEGEO code |
| ENTIDAD | State code |
| NOMBRE ENTIDAD | State name |
| MUNICIPIO | Municipality code |
| NOMBRE MUNICIPIO | Municipality name |
| LOCALIDAD | Locality code |
| NOMBRE LOCALIDAD | Locality name |
| AB | Dwellings in socioeconomic level AB |
| C+ | Dwellings in socioeconomic level C+ |
| C | Dwellings in socioeconomic level C |
| C- | Dwellings in socioeconomic level C- |
| D+ | Dwellings in socioeconomic level D+ |
| D | Dwellings in socioeconomic level D |
| E | Dwellings in socioeconomic level E |
| NIVEL_PREDOMINANTE | Dominant socioeconomic level (NSE) |
| VIVIENDAS | Total occupied private dwellings |
| TAMAÑO_DE_LOCALIDAD | Population range |

#### Save the file

Directory: D:\AXSI\AMAI\Download   
File name: NSE_por_localidad_AMAI_2024.xlsx   

### Copy the file to the working directory

Directory: D:\AXSI\AMAI\
Saves as : NSE_por_localidad_AMAI_2024-IMPORT.xlsx


## 3. — Edit the Excel File to Produce an Importable CSV

Although the next section provides a **PYTHON SCRIPT** that automates the entire process,   
the manual steps are documented here for clarity, auditing, and reproducibility.

#### 3.1 — Delete unnecessary column

- Remove the column TAMAÑO_DE_LOCALIDAD.

#### 3.2 — Fix merged header rows

- The file contains merged header cells:

```text
 TOTAL DE VIVIENDAS POR NIVEL SOCIOECONÓMICO   
 AB     C+    C     C-     D+     D     E
 ```

To standardize the structure:

- Add the following headers in row 3:

```code
CVEGEO	CVE_ENT	NOM_ENT	CVE_MUN	NOM_MUN	CVE_LOC	NOM_LOC	NSE_AB	NSE_CPLUS	NSE_C	NSE_CMINUS	NSE_DPLUS	NSE_D	NSE_E	NSE	NSE_TOTAL	POPULATION_RANGE
```

- Delete row 1 and 2



#### 3.4 — Replace N/D values

Replace all *N/D* values *with empty* cells so they import as *NULL* in SQL Server.

This prevents errors in:

- SUM()
- Percentage calculations
- Validation scripts
- Pipeline consistency checks

Excel now should look like this:

[<img src="/docs/images/NSE_6.png" width="1000">](/docs/NSE_6.png)

#### 3.5 — Generate a clean CSV

Excel exports CSV only as **UTF‑8 with commas**, which causes some locality names to include double quotes.  
  
The simplest way to obtain a clean, tab‑separated file:   

1. Select all Excel data
2. Paste into **Editpad Pro** (or similar)
3. This produces a **TAB-separated** dataset without Excel quoting issues

#### 3.6 — Save the final CSV

Save the cleaned file as:

```code
D:\AXSI\AMAI\NSE_por_AGEB_AMAI_2024_IMPORT.csv
```
Encoding: UTF‑8 (No BOM)

---

## Phyton script

Save the following script to: **D:\AXSI\AMAI\Convert_Excel_to_CSV.py**

This script requires **pandas** and **openpyxl**.  
In Windows CMD (with administrator rights), run: 

```code
pip install pandas   
pip install openpyxl
```

Open the script in **Visual Studio Code** and run it.  
(Verify the path and filenames if you used different ones.)   

```phyton
import pandas as pd

# 1. Read Excel file without headers
df = pd.read_excel(r"D:\AXSI\AMAI\NSE_por_localidad_AMAI_2024_IMPORT.xlsx", header=None)

# 2. Drop the first two rows (original headers)
df = df.drop([0, 1]).reset_index(drop=True)

# 3. Define new headers
headers = [
    "CVEGEO", "CVE_ENT","NOM_ENT","CVE_MUN","NOM_MUN","CVE_LOC","NOM_LOC",
    "NSE_AB","NSE_CPLUS","NSE_C","NSE_CMINUS","NSE_DPLUS","NSE_D","NSE_E","NSE",
    "NSE_TOTAL","POPULATION_RANGE"
]
df.columns = headers

# 4. Drop HABITANTES column
#df = df.drop(columns=["POPULATION_RANGE"])

# 5. Format ENTIDAD, MUN, LOC with leading zeros
df["CVE_ENT"] = df["CVE_ENT"].astype(str).str.zfill(2)
df["CVE_MUN"] = df["CVE_MUN"].astype(str).str.zfill(3)
df["CVE_LOC"] = df["CVE_LOC"].astype(str).str.zfill(4)

# 6. Insert CVEGEO column at position 0
# df.insert(0, "CVEGEO", "")

# 7. Build CVEGEO = ENTIDAD + MUN + LOC + AGEB
#df["CVEGEO"] = (
#    df["CVE_ENT"].astype(str).str.zfill(2) +
#    df["CVE_MUN"].astype(str).str.zfill(3) +
#3    df["CVE_LOC"].astype(str).str.zfill(4)
#)

# 8. Replace "N/D" with empty string
df = df.replace("N/D", "")

# 8. Remove all double quotes
df = df.replace('"', '', regex=True)

# 9. Save as TSV (tab-separated), UTF-8 without BOM
df.to_csv(r"D:\AXSI\AMAI\NSE_por_localidad_AMAI_2024_IMPORT.csv",
    sep="\t",
    index=False,
    encoding="utf-8"
)
```

### Expected result

```code
D:\AXSI\AMAI\NSE_por_localidad_AMAI_2024_IMPORT.csv
```

The CSV file should look like this:   

| CVEGEO    |CVE_ENT| ENT_NOM       |CVE_MUN| MUN_NOM      |CVE_LOC | LOC_NOM              |NSE_AB |NSE_CPLUS|NSE_C  |NSE_CMINUS|NSE_DPLUS|NSE_D  |NSE_E  |NSE| NSE_TOTAL | POPULATION_RANGE |
|-----------|-------|---------------|-------|--------------|--------|----------------------|-------|---------|-------|----------|---------|-------|-------|---|-----------|------------------|
| 010010102 |01     |Aguascalientes |001    |Aguascalientes|0001    |Los Arbolitos [Rancho]|      0|       12|     39|       111|      153|    331|       |D  |        648|500,000 a 999,999 |
| 010010204 |01     |Aguascalientes |001    |Aguascalientes|0001    |Ardillas de Abajo     |    178|      124|     60|        24|        9|      4|      0|A/B|        399|500,000 a 999,999 |
| 010010106 |01     |Aguascalientes |001    |Aguascalientes|0001    |Arellano              |    183|      375|    247|       128|       62|     32|       |C+ |       1028|500,000 a 999,999 |
| 010010112 |01     |Aguascalientes |001    |Aguascalientes|0001    |Bajío los Vázquez     |     35|      157|    228|       167|      124|     78|      0|C  |        789|500,000 a 999,999 |
| 010010120 |01     |Aguascalientes |001    |Aguascalientes|0001    |Buenavista de Peñuelas|    345|      187|     63|        46|       13|      6|      0|A/B|        660|500,000 a 999,999 |
| 010010121 |01     |Aguascalientes |001    |Aguascalientes|0001    |Cabecita 3 Marías     |    25 |       36|     14|        20|        9|      7|      0|C+ |        111|500,000 a 999,999 |


## 4 — Create Final table in MS SQL Server

```sql
------------------------------------------
-- Create table in SQL: AMAI_LOC_2024
------------------------------------------

USE INMO
GO

SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

DROP TABLE IF EXISTS dbo.AMAI_LOC_2024;

CREATE TABLE [dbo].[AMAI_LOC_2024](
	[CVEGEO] [nvarchar](20) NOT NULL,
	[CVE_ENT] [varchar](2) NOT NULL,
	[NOM_ENT] [nvarchar](85) NOT NULL,
	[CVE_MUN] [varchar](3) NOT NULL,
	[NOM_MUN] [nvarchar](85) NOT NULL,
	[CVE_LOC] [varchar](4) NOT NULL,
	[NOM_LOC] [nvarchar](110) NOT NULL,
	[NSE_AB] [int] NULL,
	[NSE_CPLUS] [int] NULL,
	[NSE_C] [int] NULL,
	[NSE_CMINUS] [int] NULL,
	[NSE_DPLUS] [int] NULL,
	[NSE_D] [int] NULL,
	[NSE_E] [int] NULL,
	[NSE] [nvarchar](10) NULL,
	[NSE_TOTAL] [int] NULL,
	[POPULATION_RANGE] [varchar](30) NULL,
 CONSTRAINT [PK_AMAI_LOC_2024] PRIMARY KEY CLUSTERED 
(
	[CVEGEO] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO

------------------------------------------------
-- Import CSV: NSE_por_AGEB_LOC_2024_IMPORT.csv
-- Asumes: CSV is TAB
-- File is UTF-8 NO BOM
-- Make sure the directory path matches where you saved the AMAI CSV file.
------------------------------------------------
BULK INSERT AMAI_LOC_2024
FROM 'D:\AXSI\AMAI\NSE_por_localidad_AMAI_2024_IMPORT.csv'
WITH (
    FIRSTROW = 2,
    FIELDTERMINATOR = '\t',
    ROWTERMINATOR = '\n',
    CODEPAGE = '65001'
);
```

### Expected result

(189432 rows affected)   



## 5 — Post‑Import Validations

```sql
----------------------------------------------------
-- Validate that TOTAL = sum of socioeconomic levels
-- Exprected result
-- CVEGEO | NSE_AB | NSE_CPLUS | NSE_C | NSE_CMINUS | NSE_DPLUS | NSE_D | NSE_E | NSE | NSE_TOTAL |
-- No records: This means there is no difference between total vs sum of components   

SELECT *
FROM AMAI_LOC_2024
WHERE NSE_TOTAL <> (NSE_AB + NSE_CPLUS + NSE_C + NSE_CMINUS + NSE_DPLUS + NSE_D + NSE_E);

------------------------------------------------
-- Validate correct CVEGEO length (9 characters)
-- Exprected result
-- CVEGEO | NSE_AB | NSE_CPLUS | NSE_C | NSE_CMINUS | NSE_DPLUS | NSE_D | NSE_E | NSE | NSE_TOTAL |
-- No records: This means all CVEGEO are 9 characters: EEMMMLLLL

SELECT *
FROM AMAI_LOC_2024
WHERE LEN(CVEGEO) <> 13;

------------------------------------------------
-- Final Result
-- SQL to display top 6 records to verify data:
-- Show top 6 rows

SELECT TOP (6) 
  CVEGEO, 
  CVE_ENT,
  NOM_ENT,
  CVE_MUN,
  NOM_MUN,
  CVE_LOC,
  NOM_LOC,
  NSE_AB, 
  NSE_CPLUS, 
  NSE_C, 
  NSE_CMINUS, 
  NSE_DPLUS, 
  NSE_D, 
  NSE_E, 
  NSE, 
  NSE_TOTAL,
  POPULATION_RANGE
FROM dbo.AMAI_LOC_2024
```

Your final table in SQL should look like this:  

| CVEGEO        | CVE_ENT | NOM_ENT      | CVE_MUN | NOM_MUN      | CVE_LOC | NOM_LOC        | NSE_AB | NSE_CPLUS | NSE_C | NSE_CMINUS | NSE_DPLUS | NSE_D   | NSE_E  | NSE | NSE_TOTAL | POPULATION_RANGE |
|---------------|---------|--------------|---------|--------------|---------|----------------|--------|-----------|-------|------------|-----------|---------|--------|-----|-----------|------------------|
| 0100100010017 | 01	  |Aguascalientes| 001     |Aguascalientes|0001	    | Aguascalientes |      0 |        12 |    39 |        111 |       153 |     331 |        | D   |        648| 500,000 a 999,999|
| 010010001006A | 01	  |Aguascalientes| 001     |Aguascalientes|0001	    | Aguascalientes |    178 |       124 |    60 |         24 |         9 |       4 |      0 | A/B |        399| 500,000 a 999,999|
| 0100100010106 | 01	  |Aguascalientes| 001     |Aguascalientes|0001	    | Aguascalientes |    183 |       375 |   247 |        128 |        62 |      32 |        | C+  |       1028| 500,000 a 999,999|
| 0100100010163 | 01	  |Aguascalientes| 001     |Aguascalientes|0001	    | Aguascalientes |    35  |       157 |   228 |        167 |       124 |      78 |      0 | C   |        789| 500,000 a 999,999|
| 0100100010182 | 01	  |Aguascalientes| 001     |Aguascalientes|0001	    | Aguascalientes |    345 |       187 |    63 |         46 |        13 |       6 |      0 | A/B |        660| 500,000 a 999,999|
| 0100100010229 | 01	  |Aguascalientes| 001     |Aguascalientes|0001	    | Aguascalientes |    25  |       36  |    14 |         20 |         9 |       7 |      0 | C+  |        111| 500,000 a 999,999|

This table is the official AMAI source for the **NSE calculation steps**.  
