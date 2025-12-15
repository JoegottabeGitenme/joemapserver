#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
DATA_DIR="$PROJECT_DIR/data"

mkdir -p "$DATA_DIR"
cd "$DATA_DIR"

echo "=== Downloading GFS Sample Data ==="
echo ""

# Get latest available GFS run (usually ~4-6 hours behind real time)
# Using NOMADS NOAA server
BASE_URL="https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod"

# Calculate the latest available run (round down to nearest 6 hours, minus 6 for availability)
CURRENT_HOUR=$(date -u +%H)
RUN_HOUR=$(( (CURRENT_HOUR / 6) * 6 - 6 ))
if [ $RUN_HOUR -lt 0 ]; then
    RUN_HOUR=$(( RUN_HOUR + 24 ))
    DATE=$(date -u -d "yesterday" +%Y%m%d)
else
    DATE=$(date -u +%Y%m%d)
fi
RUN_HOUR=$(printf "%02d" $RUN_HOUR)

echo "Attempting to download GFS run: ${DATE} ${RUN_HOUR}Z"
echo ""

# Download a few forecast hours for the t2m (2m temperature) variable
# Using the 0.25 degree resolution pgrb2 files
for FORECAST in 000 003 006; do
    FILENAME="gfs.t${RUN_HOUR}z.pgrb2.0p25.f${FORECAST}"
    URL="${BASE_URL}/gfs.${DATE}/${RUN_HOUR}/atmos/${FILENAME}"
    
    if [ -f "${FILENAME}.grb2" ]; then
        echo "  [skip] ${FILENAME}.grb2 already exists"
    else
        echo "  [download] ${FILENAME} ..."
        # Download only the TMP:2 m above ground variable to reduce file size
        # Full file would be ~300MB, filtered is ~1MB
        curl -s -f "${URL}" -o "${FILENAME}.grb2" 2>/dev/null || {
            echo "  [warn] Failed to download ${FILENAME}, trying alternate URL..."
            # Try alternate: filter for 2m temperature only using NOMADS filter
            FILTER_URL="https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl?file=${FILENAME}&var_TMP=on&lev_2_m_above_ground=on&dir=%2Fgfs.${DATE}%2F${RUN_HOUR}%2Fatmos"
            curl -s -f "${FILTER_URL}" -o "${FILENAME}.grb2" 2>/dev/null || {
                echo "  [error] Could not download ${FILENAME}"
            }
        }
    fi
done

echo ""
echo "=== Download Complete ==="
ls -la *.grb2 2>/dev/null || echo "No .grb2 files downloaded"
echo ""
echo "Tip: For better performance, create GDAL overviews:"
echo "  docker run --rm -v \$(pwd):/data osgeo/gdal gdaladdo -ro /data/*.grb2 2 4 8 16"
echo ""
