#!/bin/bash
# Cold-cache load test script
# Clears all caches, enables maximum debug logging, and runs load test

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

# Parse arguments
USERS=${1:-10}
SPAWN_RATE=${2:-2}
DURATION=${3:-60}

echo "=== MapServer Cold-Cache Load Test ==="
echo "Users: $USERS, Spawn Rate: $SPAWN_RATE/s, Duration: ${DURATION}s"
echo ""

# Step 1: Stop services and clear caches
echo "[1/5] Stopping services and clearing caches..."
docker compose down -v 2>/dev/null || true

# Remove cache volume completely
docker volume rm joemapserver_cache 2>/dev/null || true

# Create reports directory if it doesn't exist
mkdir -p reports

echo "[2/5] Starting services with fresh cache..."
docker compose up -d --build

# Wait for services to be ready
echo "[3/5] Waiting for services to be ready..."
sleep 10

# Health check - wait for MapServer
for i in {1..30}; do
    if curl -sf "http://localhost:8080/cgi-bin/mapserv?MAP=GFS&SERVICE=WMS&REQUEST=GetCapabilities" > /dev/null 2>&1; then
        echo "MapServer is ready!"
        break
    fi
    echo "Waiting for MapServer... ($i/30)"
    sleep 2
done

# Step 2: Run load test
echo "[4/5] Starting Locust load test..."
echo "  -> UI available at http://localhost:8089"
echo "  -> Grafana at http://localhost:3000 (admin/admin)"
echo ""

# Generate timestamped report filename
REPORT_FILE="report-$(date +%Y%m%d-%H%M%S).html"

# Start headless load test
docker compose exec -T locust locust \
    -f /mnt/locustfile.py \
    --headless \
    --users $USERS \
    --spawn-rate $SPAWN_RATE \
    --run-time ${DURATION}s \
    --host http://nginx \
    --html /mnt/reports/$REPORT_FILE \
    --csv /mnt/reports/stats \
    2>&1 | tee loadtest-output.log &

LOCUST_PID=$!

echo "[5/5] Load test running... (PID: $LOCUST_PID)"
echo ""
echo "=== Quick Links ==="
echo "  Locust UI:    http://localhost:8089"
echo "  Grafana:      http://localhost:3000 (admin/admin)"
echo "  Prometheus:   http://localhost:9090"
echo "  WMS Viewer:   http://localhost:8080/viewer.html"
echo ""
echo "=== Debug Commands ==="
echo "  MapServer logs:  docker compose logs -f mapserver"
echo "  nginx access:    docker compose exec nginx tail -f /var/log/nginx/access.log"
echo "  perf profiling:  docker compose exec mapserver perf top -p \$(pgrep mapserv)"
echo ""

# Wait for load test to complete
wait $LOCUST_PID

echo ""
echo "=== Load Test Complete ==="
echo ""
echo "Reports saved to:"
echo "  HTML Report:  reports/$REPORT_FILE"
echo "  CSV Stats:    reports/stats_*.csv"
echo "  Console Log:  loadtest-output.log"
echo ""

# Show summary stats from Prometheus if available
echo "Fetching metrics summary..."
curl -s "http://localhost:9090/api/v1/query?query=nginx_http_requests_total" 2>/dev/null | jq -r '.data.result[0].value[1] // "N/A"' | xargs -I {} echo "Total requests: {}"

echo ""
echo "Open the HTML report:"
echo "  xdg-open reports/$REPORT_FILE"
