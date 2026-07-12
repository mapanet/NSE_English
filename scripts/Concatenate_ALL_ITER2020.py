import pandas as pd
import glob

# List all locality-level CSV files
csv_files = glob.glob(r"D:\AXSI\INEGI\Censo_2020\Tabulados_AGEB_Localidad\ITER2020 - *.csv")

dfs = []
for f in csv_files:
    print("Reading:", f)
    # Force codes to be strings
    df = pd.read_csv(f, dtype={
        "ENTIDAD": str,
        "MUN": str,
        "LOC": str
    })
    # Remove asterisks
    df = df.replace(r"\*", "", regex=True)
    dfs.append(df)

# Merge all files
merged = pd.concat(dfs, ignore_index=True)

# Save tab-separated file
output_path = r"D:\AXSI\INEGI\Censo_2020\Tabulados_AGEB_Localidad\ITER2020_ALL_TAB.csv"
merged.to_csv(output_path, index=False, sep="\t")

print("Merged file saved to:", output_path)
