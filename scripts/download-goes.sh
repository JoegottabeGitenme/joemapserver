#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
DATA_DIR="$PROJECT_DIR/data/goes"

mkdir -p "$DATA_DIR"
cd "$DATA_DIR"

echo "=== Downloading GOES-18 Satellite Data ==="
echo ""

# Use GOES-18 (West) - GOES-16 (East) S3 bucket appears to be stale
SATELLITE="goes18"
PRODUCT="ABI-L2-CMIPC"

# Calculate current date/hour
YEAR=$(date -u +%Y)
DAY_OF_YEAR=$(date -u +%j)

# Channels to download
declare -A CHANNELS=(
    ["vis"]="C02"
    ["swir"]="C07"
    ["wv"]="C08"
    ["ir"]="C13"
)

echo "Looking for GOES-18 ${PRODUCT} data..."
echo "Year: $YEAR, Day of Year: $DAY_OF_YEAR"
echo ""

# Try recent hours (data may be delayed)
for HOUR_OFFSET in 0 1 2 3; do
    CURRENT_HOUR=$(date -u +%H)
    CHECK_HOUR=$(printf "%02d" $(( (10#$CURRENT_HOUR - HOUR_OFFSET + 24) % 24 )))
    
    # Handle day rollover
    if [ $(( 10#$CURRENT_HOUR - HOUR_OFFSET )) -lt 0 ]; then
        CHECK_DAY=$(printf "%03d" $((10#$DAY_OF_YEAR - 1)))
    else
        CHECK_DAY=$DAY_OF_YEAR
    fi
    
    # AWS S3 bucket URL (public, no auth needed)
    LIST_URL="https://noaa-${SATELLITE}.s3.amazonaws.com/?list-type=2&prefix=${PRODUCT}/${YEAR}/${CHECK_DAY}/${CHECK_HOUR}/&delimiter=/"
    
    echo "Checking hour ${CHECK_HOUR} (day ${CHECK_DAY})..."
    
    # Get XML listing from S3
    LISTING=$(curl -s "$LIST_URL" 2>/dev/null)
    
    # Check if we have any files (look for <Key> elements)
    if echo "$LISTING" | grep -q "<Key>"; then
        echo "  Found data!"
        FOUND_HOUR=$CHECK_HOUR
        FOUND_DAY=$CHECK_DAY
        break
    fi
done

if [ -z "$FOUND_HOUR" ]; then
    echo "[error] Could not find any recent GOES data"
    exit 1
fi

echo ""
echo "Downloading from ${YEAR}/${FOUND_DAY}/${FOUND_HOUR}..."
echo ""

for KEY in "${!CHANNELS[@]}"; do
    CHANNEL="${CHANNELS[$KEY]}"
    OUTPUT_FILE="${KEY}_latest.nc"
    
    echo "[$KEY] Channel $CHANNEL"
    
    # Get file listing for this specific path
    PREFIX="${PRODUCT}/${YEAR}/${FOUND_DAY}/${FOUND_HOUR}/"
    LIST_URL="https://noaa-${SATELLITE}.s3.amazonaws.com/?list-type=2&prefix=${PREFIX}"
    
    # Extract filenames from S3 XML listing
    LISTING=$(curl -s "$LIST_URL" 2>/dev/null)
    
    # Find the latest file for this channel
    LATEST_FILE=$(echo "$LISTING" | grep -oP "<Key>[^<]*M6${CHANNEL}[^<]*\.nc</Key>" | sed 's/<Key>//;s/<\/Key>//' | sort -r | head -1)
    
    if [ -z "$LATEST_FILE" ]; then
        LATEST_FILE=$(echo "$LISTING" | grep -oP "<Key>[^<]*M3${CHANNEL}[^<]*\.nc</Key>" | sed 's/<Key>//;s/<\/Key>//' | sort -r | head -1)
    fi
    
    if [ -z "$LATEST_FILE" ]; then
        echo "  [warn] Could not find file for channel $CHANNEL"
        continue
    fi
    
    DOWNLOAD_URL="https://noaa-${SATELLITE}.s3.amazonaws.com/${LATEST_FILE}"
    FILENAME=$(basename "$LATEST_FILE")
    
    echo "  [download] $FILENAME"
    
    if curl -s -f "$DOWNLOAD_URL" -o "$OUTPUT_FILE" 2>/dev/null; then
        SIZE=$(ls -lh "$OUTPUT_FILE" 2>/dev/null | awk '{print $5}')
        echo "  [ok] Saved as $OUTPUT_FILE ($SIZE)"
    else
        echo "  [error] Failed to download"
        rm -f "$OUTPUT_FILE"
    fi
    
    echo ""
done

echo "=== GOES Download Complete ==="
ls -la *.nc 2>/dev/null || echo "No .nc files downloaded"
echo ""

# Convert NetCDF to GeoTIFF and reproject to EPSG:4326
echo "=== Converting to GeoTIFF and Reprojecting to EPSG:4326 ==="
echo ""

if command -v docker &> /dev/null; then
    for NC_FILE in *.nc; do
        if [ -f "$NC_FILE" ]; then
            BASE_NAME="${NC_FILE%.nc}"
            TIFF_FILE="${BASE_NAME}.tif"
            TIFF_4326="${BASE_NAME}_4326.tif"
            
            echo "Processing $NC_FILE..."
            
            # Step 1: Convert NetCDF to GeoTIFF (native projection)
            docker run --rm -v "$DATA_DIR:/data" \
                ghcr.io/osgeo/gdal:ubuntu-full-latest \
                gdal_translate -q -of GTiff \
                "NETCDF:/data/$NC_FILE:CMI" \
                "/data/$TIFF_FILE" 2>/dev/null || {
                    echo "  [error] NetCDF conversion failed for $NC_FILE"
                    continue
                }
            
            # Step 2: Reproject to EPSG:4326 for MapServer compatibility
            docker run --rm -v "$DATA_DIR:/data" \
                ghcr.io/osgeo/gdal:ubuntu-full-latest \
                gdalwarp -q -t_srs EPSG:4326 -r bilinear \
                "/data/$TIFF_FILE" \
                "/data/$TIFF_4326" 2>/dev/null || {
                    echo "  [error] Reprojection failed for $TIFF_FILE"
                    continue
                }
            
            SIZE=$(ls -lh "$TIFF_4326" 2>/dev/null | awk '{print $5}')
            echo "  [ok] $TIFF_4326 ($SIZE)"
            
            # Clean up intermediate file
            rm -f "$TIFF_FILE"
        fi
    done
else
    echo "[warn] Docker not available for GDAL conversion"
    echo "Install Docker or manually convert GOES files to GeoTIFF EPSG:4326"
fi

echo ""
echo "=== Final Files ==="
ls -la *_4326.tif 2>/dev/null || echo "No reprojected files created"
