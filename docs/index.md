# AMAI NSE English Documentation

## Socioeconomic Level for INEGI Neighborhoods

This site contains the complete technical documentation for the **NSE (Nivel Socioeconómico AMAI)** pipeline developed by mapanet / AXSI.  
It explains the datasets, methodology, spatial processing, SQL workflow, and validation steps required to generate **Layer 6 — NSE by colonia** for all of Mexico.

---

## 📘 Overview

The NSE pipeline integrates:

- **AMAI 2024 NSE values** (by AGEB)
- **INEGI MG 2025 geometries** (AGEB / AGEEB)
- **INEGI DCAH 2025 neighborhood boundaries** (colonias)
- **INE 2025 localities** (rural fallback)
- Area‑weighted interpolation from AGEB → colonia

The result is a reproducible, audit‑ready socioeconomic dataset used in production at AXSI Real Estate.

---

## 📁 Documentation Index

### 0. [Data Requirements](00_Data_Requirements.md)
### 1. [Import AMAI NSE 2024](01_Import_AMAI.md)
### 2. [Import INEGI MG 2025 AGEB geometries](02_Import_INEGI_MG_2025_AGEB.md)
### 3. [Import INEGI DCAH 2025 Neighborhood geometries](03_Import_INEGI_DCAH_2025.md)
### 4. [AGEB × Neighborhood Spatial Intersection](04_NSE_Intersections.md)
### 5. [NSE Calculation Methodology](methodology.md)
### 6. [Pipeline Overview](pipeline.md)
### 7. [INEGI Notes & Territorial Considerations](inegi.md)
### 8. [AMAI Notes & Classification Rules](amai.md)

---

## 🗺️ Live NSE Map (CDMX)

The final NSE dataset is used in production at:

**AXSI Real Estate Platform**  
https://axsi.io/es

---

## 🧩 About this project

Repository:  
https://github.com/mapanet/NSE_English/

Author: **Juan Carlos Alcaide Blanco**  
Organization: **AXSI / Divex Turismo, S.L.**  
Location: **Playa del Carmen, Quintana Roo**
