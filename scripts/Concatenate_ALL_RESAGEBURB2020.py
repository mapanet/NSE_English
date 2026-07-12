import pandas as pd
import glob

# List all CSV files
csv_files = glob.glob(r"D:\AXSI\INEGI\Censo_2020\Tabulados_AGEB_Manzana\RESAGEBURB2020 - *.csv")

dfs = []
for i, f in enumerate(csv_files):
    print("Reading:", f)
    # Force codes to be strings
    df = pd.read_csv(f, dtype={
        "ENTIDAD": str,
        "MUN": str,
        "LOC": str,
        "AGEB": str,
        "MZA": str
    })
    dfs.append(df)

merged = pd.concat(dfs, ignore_index=True)

# Save as comma-separated
# merged.to_csv(r"D:\AXSI\INEGI\Censo_2020\Tabulados_AGEB_Manzana\RESAGEBURB2020_ALL_COMA.csv", index=False)
# Save tab separated
merged.to_csv(r"D:\AXSI\INEGI\Censo_2020\Tabulados_AGEB_Manzana\RESAGEBURB2020_ALL_TAB.csv", index=False, sep="\t")
