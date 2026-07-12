# Input and output paths
$inputFile  = "D:\AXSI\INEGI\AGEEML_2026\AGEEML_202651313653_utf.csv"
$outputFile = "D:\AXSI\INEGI\AGEEML_2026\AGEEML_2026.tsv"

# Load CSV using real CSV parser (handles quotes, commas, escapes)
$rows = Import-Csv -Path $inputFile

# Explicit column mapping: InputHeader -> OutputHeader
$map = [ordered]@{
    "CVEGEO"                         = "CVEGEO"
    "Estatus"                        = "Status"
    "CVE_ENT"                        = "CVE_ENT"
    "NOM_ENT"                        = "State"
    "CVE_MUN"                        = "CVE_MUN"
    "NOM_MUN"                        = "Municipality"
    "CVE_LOC"                        = "CVE_LOC"
    "NOM_LOC"                        = "City"
    "AMBITO"                         = "Type"
    "LAT_DECIMAL"                    = "Latitude"
    "LON_DECIMAL"                    = "Longitude"
    "ALTITUD"                        = "Altitude"
    "POB_TOTAL"                      = "Population"
    "POB_MASCULINA"                  = "Population_M"
    "POB_FEMENINA"                   = "Population_F"
    "TOTAL DE VIVIENDAS HABITADAS"   = "Occupied_Dwellings"
}

# Build header in the exact desired order
$inputCols  = $map.Keys
$outputCols = $map.Values
$headerLine = $outputCols -join "`t"

$lines = @($headerLine)

foreach ($row in $rows) {
    $vals = foreach ($inCol in $inputCols) {
        $val = $row.$inCol

        # Normalize NULL-like values
        if ($val -eq '-' -or $val -eq '*' -or $val -eq $null) {
            $val = ''
        }

        # Replace internal double quotes with two single quotes
        $val = $val -replace '"', "''"

        $val
    }

    $lines += ($vals -join "`t")
}

# Write UTF-8 output
[System.IO.File]::WriteAllLines($outputFile, $lines, [System.Text.Encoding]::UTF8)

Write-Host "DONE: $($lines.Count-1) records written to $outputFile"
