# Methodology — AMAI Socioeconomic Level (NSE) for INEGI Neighborhoods

This document describes the complete methodology used to generate **Layer 6 — NSE by colonia**, integrating AMAI socioeconomic indicators with INEGI territorial datasets.  
It covers ingestion, normalization, spatial processing, interpolation, classification, and audit steps.

---

## 1. Overview

AMAI publishes socioeconomic indicators (NSE) at the **AGEB** level.  
INEGI provides two key territorial datasets:

- **MG 2025** — official AGEB geometries  
- **DCAH 2025** — neighborhood (colonia) geometries  

To obtain NSE at the colonia level, we perform:

1. **Ingestion** of AMAI + INEGI datasets  
2. **Normalization** of keys and identifiers  
3. **Spatial intersection** between AGEB and colonia polygons  
4. **Area‑weighted interpolation** of socioeconomic indicators  
5. **AMAI‑compliant classification**  
6. **Generation of final layers**  
7. **Geometric + territorial audits**

---

## 2. Datasets

### 2.1 AMAI 2024 — NSE by AGEB
AMAI provides socioeconomic indicators for each AGEB:

- Household characteristics  
- Education  
- Assets  
- Services  
- Composite NSE score  
- Final NSE category (A/B, C+, C, C-, D+, D)

### 2.2 INEGI MG 2025 — AGEB Geometries
Official polygon boundaries for:

- **AGEB urban**  
- **AGEEB rural**

Includes:

- CVEGEO  
- Municipality code  
- State code  
- Geometry (polygon)

### 2.3 INEGI DCAH 2025 — Neighborhood Geometries
Neighborhood boundaries (colonias) for all municipalities/alcaldías.

Includes:

- CVEGEO  
- Neighborhood name  
- Municipality code  
- Geometry (polygon)

### 2.4 INE 2025 Localities (Rural Fallback)
Used when rural AGEB census data is unavailable.

---

## 3. Key Normalization

Before any spatial processing, all keys must be normalized:

- `LTRIM(RTRIM())` on all text fields  
- Convert CHAR → VARCHAR  
- Normalize CVEGEO formats  
- Standardize municipality and state codes  
- Remove trailing spaces  
- Uppercase all locality and colonia names  

This prevents join mismatches and NULL propagation.

---

## 4. Spatial Intersection (AGEB × Colonia)

The core of the methodology is the **polygon intersection** between:

- AGEB polygons (MG 2025)  
- Colonia polygons (DCAH 2025)

### 4.1 Intersection Output

For each pair of intersecting polygons:

- Intersection geometry  
- Intersection area  
- Percentage of AGEB area contributing to the colonia  
- Weighted socioeconomic indicators  

### 4.2 Area‑Weighted Contribution

For each socioeconomic variable:

**WeightedValue** = (IntersectionArea / AGEB_TotalArea) * AMAI_Value


This ensures that AGEBs contribute proportionally to the colonia based on spatial overlap.

---

## 5. NSE Calculation

After interpolation, each colonia has weighted socioeconomic indicators.

### 5.1 Composite Score

AMAI’s composite score is recalculated using weighted variables:

**NSE_Score** = Σ (WeightedIndicators × AMAI_Weights)


### 5.2 Final NSE Category

The score is mapped to AMAI’s categories:

- **A/B**  
- **C+**  
- **C**  
- **C-**  
- **D+**  
- **D**

These thresholds follow AMAI’s official methodology.

---

## 6. Layer Generation

### 6.1 Layer 6 — NSE by Colonia
Final output:

- CVEGEO  
- Colonia name  
- Municipality  
- State  
- NSE score  
- NSE category  
- Geometry  

### 6.2 Layer 5 — City
Aggregation of Layer 6 by city boundaries.

### 6.3 Layer 2 — Municipality
Aggregation by municipality code.

### 6.4 Layer 1 — State
Aggregation by state code.

---

## 7. Rural Fallback Logic (ITER)

INEGI does not publish rural AGEB census data.  
To avoid NULL propagation:

- Use **INE 2025 locality indicators**  
- Assign rural NSE based on locality characteristics  
- Apply AMAI rules for rural classification  
- Ensure all colonias (urban + rural) receive valid NSE values

---

## 8. Geometry & Territorial Audits

To ensure data quality:

### 8.1 Geometry Validity
- Check for self‑intersections  
- Validate polygon topology  
- Repair invalid geometries

### 8.2 Territorial Consistency
- Verify CVEGEO alignment  
- Check municipality/state codes  
- Detect missing colonias  
- Compare MG 2025 vs DCAH 2025 boundaries

### 8.3 Area Checks
- Ensure intersection areas sum correctly  
- Detect anomalies (tiny slivers, overlaps, gaps)

---

## 9. Output Format

Final NSE datasets are exported as:

- GeoJSON  
- Shapefile  
- SQL tables  
- API‑ready JSON layers  

Used in production at:

**AXSI Real Estate Platform**  
https://axsi.io/es

---

## 10. Related Documentation

- [Data Requirements](00_Data_Requirements.md)  
- [Import AMAI NSE 2024](01_Import_AMAI.md)  
- [Import INEGI MG 2025 AGEB geometries](02_Import_INEGI_MG_2025_AGEB.md)  
- [Import INEGI DCAH 2025 Neighborhood geometries](03_Import_INEGI_DCAH_2025.md)  
- [AGEB × Neighborhood Spatial Intersection](04_NSE_Intersections.md)  
- [Pipeline Overview](pipeline.md)  
- [INEGI Notes](inegi.md)  
- [AMAI Notes](amai.md)

---

## Author

**Juan Carlos Alcaide Blanco**  
AXSI / Divex Turismo, S.L.  
Playa del Carmen, Quintana Roo
