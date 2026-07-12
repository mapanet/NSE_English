# INEGI Notes & Territorial Considerations

This document summarizes important territorial and geometric considerations when working with INEGI datasets for NSE calculation.

---

## 1. INEGI MG 2025 — AGEB Notes

### 1.1 Urban vs Rural AGEBs
- Urban AGEBs have full census data  
- Rural AGEEBs do **not** include socioeconomic census tables  
- AMAI NSE is only published for urban AGEBs

### 1.2 CVEGEO Structure
CVEGEO is composed of:

- State (2 digits)  
- Municipality (3 digits)  
- Locality (4 digits)  
- AGEB (4 digits)  

Normalization is required for joins.

### 1.3 Geometry Quality
MG 2025 polygons are generally high quality but may include:

- Minor slivers  
- Boundary overlaps  
- Topology inconsistencies in rural areas

---

## 2. INEGI DCAH 2025 — Neighborhood Notes

### 2.1 Colonia Boundaries
Neighborhoods are administrative boundaries defined by municipalities.  
They do **not** always align with AGEB boundaries.

### 2.2 Missing Colonias
Some municipalities do not publish complete colonia datasets.  
Examples include:

- Edomex  
- Las Arboledas  
- Certain rural municipalities

### 2.3 Geometry Issues
Common issues:

- Self‑intersections  
- Multi‑polygons with holes  
- Overlapping colonias  
- Unclosed rings

These must be validated before intersection.

---

## 3. Territorial Considerations

### 3.1 AGEB ↔ Colonia Misalignment
Colonias often cross multiple AGEBs.  
This is why area‑weighted interpolation is required.

### 3.2 Rural Fallback
Since rural AGEBs lack census data:

- Use INE locality indicators  
- Apply AMAI rural classification rules  
- Ensure all colonias receive valid NSE values

### 3.3 Municipality Boundary Changes
Municipalities may update boundaries between MG 2020 → MG 2025.  
Always use the latest MG dataset.

---

## 4. Recommended Validations

- `ST_IsValid` on all geometries  
- Area consistency checks  
- CVEGEO normalization  
- Topology repair (`ST_MakeValid`)  
- Intersection area sum checks  
- Detection of missing colonias

---

## 5. Notes for Production Use

- Always store normalized CVEGEO  
- Maintain versioned INEGI datasets  
- Document territorial anomalies  
- Keep audit logs for geometry repairs
