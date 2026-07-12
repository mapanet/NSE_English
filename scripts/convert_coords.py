import csv
import os

def dms_to_decimal(dms_str):
    """
    Convert DMS (degrees°minutes'seconds"Direction) to decimal degrees.
    Example input: "102°17'45.768\" W"
    """
    try:
        parts = dms_str.replace("°"," ").replace("'"," ").replace('"'," ").split()
        deg, minutes, seconds, direction = parts
        decimal = float(deg) + float(minutes)/60 + float(seconds)/3600
        if direction.upper() in ['S','W']:
            decimal *= -1
        return round(decimal, 6)
    except Exception:
        return None

def process_file():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(base_dir, "ITER2020_ALL_TAB.csv")
    output_file = os.path.join(base_dir, "ITER2020_ALL_COORDS_TAB.csv")

    with open(input_file, newline='', encoding='utf-8') as infile, \
         open(output_file, 'w', newline='', encoding='utf-8') as outfile:

        reader = csv.DictReader(infile, delimiter='\t')

        # Build new header order: CVEGEO first
        fieldnames = ['CVEGEO'] + [fn for fn in reader.fieldnames if fn not in ['LATITUD','LONGITUD']]
        # Place LATITUD and LONGITUD together before ALTITUD
        alt_index = fieldnames.index('ALTITUD')
        fieldnames.insert(alt_index, 'LATITUD')
        fieldnames.insert(alt_index+1, 'LONGITUD')

        writer = csv.DictWriter(outfile, fieldnames=fieldnames, delimiter='\t')
        writer.writeheader()

        written, skipped = 0, 0

        for row in reader:
            loc = row.get('LOC','').strip()
            lat = row.get('LATITUD','').strip()
            lon = row.get('LONGITUD','').strip()
            alt = row.get('ALTITUD','').strip()

            if not lat or not lon or loc in ['0000','9998','9999']:
                skipped += 1
                continue

            # Build CVEGEO = ENTIDAD + MUN + LOC
            row['CVEGEO'] = f"{row.get('ENTIDAD','').strip()}{row.get('MUN','').strip()}{loc}"

            # Convert coordinates
            row['LATITUD'] = dms_to_decimal(lat)
            row['LONGITUD'] = dms_to_decimal(lon)

            # Clean and force ALTITUD to integer
            if alt:
                alt_clean = alt.replace('-', '')  # remove dashes
                try:
                    row['ALTITUD'] = int(float(alt_clean))
                except:
                    row['ALTITUD'] = None
            else:
                row['ALTITUD'] = None

            # Force population and housing counts to integers
            for col in ['POBTOT','VIVTOT','TVIVHAB']:
                try:
                    row[col] = int(float(row[col]))
                except:
                    pass

            writer.writerow(row)
            written += 1

    print(f"Finished. Written: {written} rows, Skipped: {skipped} rows.")

if __name__ == "__main__":
    process_file()
