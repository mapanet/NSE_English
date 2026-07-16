import csv

input_file  = r"D:\AXSI\INEGI\AGEEML_2026\AGEEML_202651313653_utf.csv"
output_file = r"D:\AXSI\INEGI\AGEEML_2026\AGEEML_2026.tsv"

mapping = {
    "CVEGEO": "CVEGEO",
    "Estatus": "Status",
    "CVE_ENT": "CVE_ENT",
    "NOM_ENT": "State",
    "CVE_MUN": "CVE_MUN",
    "NOM_MUN": "Municipality",
    "CVE_LOC": "CVE_LOC",
    "NOM_LOC": "City",
    "AMBITO": "Type",
    "LAT_DECIMAL": "Latitude",
    "LON_DECIMAL": "Longitude",
    "ALTITUD": "Altitude",
    "POB_TOTAL": "Population",
    "POB_MASCULINA": "Population_M",
    "POB_FEMENINA": "Population_F",
    "TOTAL DE VIVIENDAS HABITADAS": "Occupied_Dwellings"
}

input_cols  = list(mapping.keys())
output_cols = list(mapping.values())

lines = []
lines.append("\t".join(output_cols))

with open(input_file, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)

    for row in reader:
        vals = []
        for col in input_cols:
            val = row.get(col, "")

            if val in ("-", "*", None):
                val = ""

            val = val.replace('"', "''")
            vals.append(val)

        lines.append("\t".join(vals))

with open(output_file, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print(f"DONE: {len(lines)-1} records written to {output_file}")
