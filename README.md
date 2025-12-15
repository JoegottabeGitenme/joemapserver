# MapServer-GFS-Perf-Lab
Spin up a **dimension-aware WMS** for GFS GRIB2 data and hammer it via browser.

1. Clone / empty folder → add the 3 files above.
2. Run:
   docker compose up -d
3. Grab a coffee while it downloads & seeds tiles.
4. Browse:
    - Locust UI → http://localhost:8089  (drag slider, watch latency)
    - Grafana → http://localhost:3000  (user/pass admin/admin)
5. Tweak:
    - Add more `mapserver` replicas in compose → nginx round-robins
    - Pre-create overviews: `gdaladdo -ro data/*.grb2 2 4 8 16`
    - Switch MapCache backend to RocksDB for > 10 M tile repos
6. Profile:
    - `perf top -p $(pgrep mapserv)` while Locust ramps → find hot GDAL symbols
    - Patch, re-build image, re-run.

Happy bottleneck hunting!


5. Next Bottlenecks You Will Probably Hit
   Symptom	Fastest Fix
   p99 > 250 ms, CPU low	GDAL open/seek → pre-create external overviews
   CPU 100 %	On-the-fly contour → pre-generate shape/FlatGeobuf layer
   Cache-hit < 90 %	Seed deeper (z=9) or add NVMe cache volume
   Single-core burn	Scale MapServer replicas (nginx already load-balances)