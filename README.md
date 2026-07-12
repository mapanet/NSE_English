# NSE — AMAI Socioeconomic Level for INEGI Neighborhoods

<p align="center">
  <img src="/docs/images/INEGI.webp" alt="INEGI Logo" height="90">
  &nbsp;&nbsp;&nbsp;&nbsp;
  <img src="/docs/images/AMAI.webp" alt="AMAI Logo" height="90">
</p>

This repository documents the complete, reproducible, and auditable pipeline for calculating the AMAI Socioeconomic Level (NSE) across multiple territorial units in México:

- Neighborhood (colonia)
- Locality
- Municipality / Alcaldía
- State

The workflow integrates official datasets from AMAI, INEGI, and INE, producing standardized NSE layers suitable for GIS, APIs, real estate analytics, market segmentation, and territorial intelligence.

---

## 🎯 Purpose of this repository

To generate a final Layer 6 (NSE by colonia) dataset using:

- AMAI 2024 NSE values (by AGEB)
- INEGI MG 2025 AGEB geometries
- INEGI DCAH 2025 neighborhood geometries
- Spatial interpolation from AGEB → colonia boundaries

The resulting NSE dataset is used in production at:

### 🌐 AXSI Real Estate Platform  
Explore the interactive NSE map of cities or neighborhoods in México:  
**https://axsi.io/es**

---

## 📊 Official datasets used

### AMAI 2024 — NSE by AGEB  
Socioeconomic classification (A/B, C+, C, C-, D+, D) assigned to statistical units.

### INEGI Marco Geoestadístico 2025  
Official polygon geometries for AGEB / AGEEB units.

### INEGI DCAH 2025  
Neighborhood (colonia) boundaries for all municipalities and alcaldías.

### INE 2025 Localities  
Used for rural fallback logic when AGEB census data is unavailable.

### Spatial weighting  
Interpolation from AGEB polygons → colonia polygons using area‑weighted joins.

---

## 🗺️ Example: NSE Map of Mexico City

[<img src="/docs/images/CDMX_NSE_map.png" width="700">](/docs/images/CDMX_NSE_map.png)

This map is generated using the SQL + GIS pipeline documented in this repository.

---

## 🔗 Relationship between AMAI, MG 2025 AGEB geometries, and DCAH geometries

AMAI assigns NSE values to AGEB / AGEEB statistical units.  
INEGI MG 2025 provides the official boundaries for these units.  
INEGI DCAH 2025 provides neighborhood boundaries (colonias).

To obtain NSE at the colonia level, we perform:

- Spatial intersection  
- Area‑weighted interpolation  
- Normalization of keys  
- AMAI‑compliant aggregation rules  

### 📐 Diagram

```text
        AMAI (Socioeconomic Index - NSE)
                     │
                     ▼
          AGEB / AGEEB (Statistical Unit)
                     │
                     ▼
   MG 2025 Polygons (Official Boundaries)
                     │
          Interpolation / Spatial Join
                     ▼
   DCAH Boundaries (Neighborhood Units)
                     │
                     ▼
   NSE Assigned to DCAH Neighborhoods (Layer 6)
 ```

## 🧠 Methodology Overview

0. [Data Requirements](docs/00_Data_Requirements.md)   

1. [Import NSE_AMAI_AGEB_2024](docs/01_Import_AMAI.md)   
Import AMAI 2024 socioeconomic indicators for AGEBs.

2. [Import INEGI_MG 2025_AGEB geometries](docs/02_Import_INEGI_MG_2025_AGEB.md)   
Normalize keys, validate geometry, and prepare AGEB polygons.

3. [Import INEGI DCAH 2025 Neighborhood geometries](docs/03_Import_INEGI_DCAH_2025.md)   
Normalize colonia names, CVEGEO codes, and municipality identifiers.

4. [Neighbood boundaries × AGEB spatial intersection](docs/04_NSE_Intersections.md)   

- Calculate area‑weighted contributions from AGEB → colonia.
- Apply AMAI formulas: Compute weighted socioeconomic indicators per colonia.
- Assign NSE category: Determine final NSE class (A/B, C+, C, C-, D+, D).
- Generate Layer 6: Produce final colonia‑level NSE dataset.

8. Optional aggregation   

   Layer 5 — City  
   Layer 2 — Municipality   
   Layer 1 — State   

8. [Import_AMAI_Locality](docs/08_AMAI_Locality.md)

9. [AMAI_Locality_Calculations](docs/09_AMAI_Locality_Calculations.md)



## 📁 Repository Structure

- `/docs` — Step‑by‑step technical documentation (SQL, GIS, ETL, OSM)
- `/data` — CSV, SHP, and original source files (not public)
- `/scripts` — SQL scripts, PowerShell utilities, Python scripts, automation
- `/images` — Diagrams, maps, and reference figures



---

**Juan Carlos Alcaide Blanco**  
**Organization:** AXSI / Divex Turismo, S.L.  
**Location:** Playa del Carmen, Quintana Roo  
