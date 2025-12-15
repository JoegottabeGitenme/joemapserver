#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

echo "=== MapServer GFS Performance Lab ==="
echo ""

# Create data directory if it doesn't exist
if [ ! -d "data" ]; then
    echo "[1/4] Creating data directory..."
    mkdir -p data
else
    echo "[1/4] Data directory exists"
fi

# Check if we have any GFS data
if [ -z "$(ls -A data/*.grb2 2>/dev/null)" ]; then
    echo ""
    echo "WARNING: No GFS data found in ./data/"
    echo "Run './scripts/download-gfs.sh' to fetch sample GFS data"
    echo "Or manually place .grb2 files in the data/ directory"
    echo ""
fi

# Build and start services
echo "[2/4] Building MapServer image (this may take a while on first run)..."
docker compose build

echo "[3/4] Starting all services..."
docker compose up -d

echo "[4/4] Waiting for services to be ready..."
sleep 8

echo ""
echo "=== Services Started ==="
echo ""
echo "  Map Viewer:     http://localhost:8080/viewer.html"
echo "  MapServer WMS:  http://localhost:8080/cgi-bin/mapserv?MAP=GFS&SERVICE=WMS&REQUEST=GetCapabilities"
echo "  MapCache:       http://localhost:8080/mapcache/"
echo ""
echo "  --- Monitoring & Testing ---"
echo "  Grafana:        http://localhost:3000 (admin/admin)"
echo "    -> Dashboard: 'MapServer WMS Performance'"
echo "  Prometheus:     http://localhost:9090"
echo "  Loki:           http://localhost:3100"
echo "  Locust UI:      http://localhost:8089"
echo ""
echo "Available WMS layers: t2m, rh2m, gust, mslp, pwat, cape, refc, vis"
echo ""
echo "To view logs:     docker compose logs -f"
echo "To stop:          ./scripts/stop.sh"
echo "To run load test: Open Locust UI and start swarming"
echo ""
