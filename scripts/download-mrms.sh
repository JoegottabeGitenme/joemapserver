#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
DATA_DIR="$PROJECT_DIR/data/mrms"

mkdir -p "$DATA_DIR"
cd "$DATA_DIR"

echo "=== Downloading MRMS Radar Data ==="
echo ""

# MRMS data from NCEP - using the .latest.grib2.gz files (always most recent)
# URL structure: https://mrms.ncep.noaa.gov/2D/{PRODUCT}/MRMS_{PRODUCT}.latest.grib2.gz
BASE_URL="https://mrms.ncep.noaa.gov/2D"

# Products to download
declare -A PRODUCTS=(
    ["refl"]="MergedReflectivityQCComposite"
    ["precip_rate"]="PrecipRate"
    ["qpe_01h"]="RadarOnly_QPE_01H"
    ["base_refl"]="MergedBaseReflectivity"
)

echo "Downloading latest MRMS products..."
echo ""

for KEY in "${!PRODUCTS[@]}"; do
    PRODUCT="${PRODUCTS[$KEY]}"
    OUTPUT_FILE="${KEY}_latest.grib2"
    
    echo "[$KEY] $PRODUCT"
    
    # Use the .latest file (always current)
    DOWNLOAD_URL="${BASE_URL}/${PRODUCT}/MRMS_${PRODUCT}.latest.grib2.gz"
    
    echo "  [download] MRMS_${PRODUCT}.latest.grib2.gz"
    
    if curl -sL -f "$DOWNLOAD_URL" 2>/dev/null | gunzip > "$OUTPUT_FILE" 2>/dev/null; then
        if [ -s "$OUTPUT_FILE" ]; then
            SIZE=$(ls -lh "$OUTPUT_FILE" | awk '{print $5}')
            echo "  [ok] Saved as $OUTPUT_FILE ($SIZE)"
        else
            echo "  [error] Downloaded file is empty"
            rm -f "$OUTPUT_FILE"
        fi
    else
        echo "  [error] Failed to download $PRODUCT"
        rm -f "$OUTPUT_FILE"
    fi
    
    echo ""
done

echo "=== MRMS Download Complete ==="
ls -la *.grib2 2>/dev/null || echo "No .grib2 files downloaded"
echo ""
