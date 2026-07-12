# Pipeline Overview — NSE AMAI for INEGI Neighborhoods

This page summarizes the complete end‑to‑end workflow used to generate **NSE AMAI by colonia** (Boundaries Layer 6).  
It connects all datasets, SQL steps, geospatial operations, and validation procedures into a single reproducible pipeline.

---

## 1. Data Ingestion

### 1.1 AMAI NSE 2024
- Socioeconomic indicators by AGEB  
- Composite NSE score  
- Final AMAI category (A/B, C+, C, C-, D+, D)

### 1.2 INEGI MG 2025 (AGEB geometries)
- Urban AGEB polygons  
- Rural AGEEB polygons  
- CVEGEO codes  
- Municipality and state identifiers

### 1.3 INEGI DCAH 2025 (Neighborhood geometries)
- Colonia polygons  
- CVEGEO  
- Municipality and locality metadata

### 1.4 INE 2025 Localities (Rural fallback)
- Used when rural AGEB census data is unavailable

---

## 2. Key Normalization

Before joining datasets:

- Normalize CVEGEO formats  
- LTRIM/RTRIM all text fields  
- Convert CHAR → VARCHAR  
- Uppercase colonia names  
- Standardize municipality/state codes  

This prevents NULL propagation and join mismatches.

---

## 3. Spatial Intersection (AGEB ↔ Colonia)

Core geospatial step:

- Intersect AGEB polygons with colonia polygons  
- Compute intersection area  
- Compute percentage contribution of each AGEB  
- Generate weighted socioeconomic indicators

This produces the **AGEB × Colonia intersection table**.

---

## 4. Area‑Weighted Interpolation

For each socioeconomic variable:

**WeightedValue** = (IntersectionArea / AGEB_TotalArea) * AMAI_Value


This ensures each colonia inherits NSE values proportionally.

---

## 5. NSE Calculation

### 5.1 Weighted Indicators
Sum weighted contributions from all intersecting AGEBs.

### 5.2 Composite Score
Recalculate AMAI’s composite score using weighted variables.

### 5.3 Final NSE Category
Assign AMAI category based on score thresholds.

---

## 6. Layer Generation

### Layer 6 — Neighborhoods (Colonias)
Final output includes:

- CVEGEO  
- Colonia name  
- Municipality  
- NSE score  
- NSE category  
- Geometry  

### Layer 5 — Cities  
Aggregation of Layer 6.

### Layer 2 — Municipalities  
Aggregation by municipality code.

### Layer 1 — States  
Aggregation by state code.

---

## 7. Geometry & Territorial Audits

- Validate polygon topology  
- Detect self‑intersections  
- Compare MG 2025 vs DCAH 2025 boundaries  
- Check area consistency  
- Identify missing colonias  
- Validate CVEGEO alignment

---

## 8. Export & API Integration

Final datasets exported as:

- GeoJSON  
- Shapefile  
- SQL tables  
- API‑ready JSON layers

Used in production at:

**AXSI Real Estate Platform**  
https://axsi.io/es
