from locust import HttpUser, task, between, events
import random
import datetime
import time

# ============================================================================
# GFS LAYERS
# ============================================================================
# Layers with multiple style variants
STYLED_LAYERS = {
    "t2m": ["t2m", "t2m_contour", "t2m_numbers"],
    "mslp": ["mslp", "mslp_contour", "mslp_numbers"],
    "cape": ["cape", "cape_contour", "cape_numbers"],
    "pwat": ["pwat", "pwat_contour", "pwat_numbers"],
}

# Base layers (gradient only)
BASE_LAYERS = ["t2m", "pwat", "rh2m", "gust", "mslp", "cape", "vis", "refc"]

# All layers including styled variants
ALL_LAYERS = BASE_LAYERS + [
    "t2m_contour",
    "t2m_numbers",
    "mslp_contour",
    "mslp_numbers",
    "cape_contour",
    "cape_numbers",
    "pwat_contour",
    "pwat_numbers",
]

# ============================================================================
# MRMS LAYERS
# ============================================================================
MRMS_LAYERS = {
    "refl": ["refl", "refl_contour"],
    "precip_rate": ["precip_rate", "precip_rate_contour"],
    "qpe_01h": ["qpe_01h", "qpe_01h_contour"],
    "base_refl": ["base_refl"],
}

MRMS_ALL_LAYERS = [
    "refl",
    "refl_contour",
    "precip_rate",
    "precip_rate_contour",
    "qpe_01h",
    "qpe_01h_contour",
    "base_refl",
]

# ============================================================================
# GOES LAYERS
# ============================================================================
GOES_LAYERS = {
    "vis": ["vis", "vis_enhanced"],
    "ir": ["ir", "ir_gray", "ir_contour"],
    "wv": ["wv", "wv_gray"],
    "swir": ["swir", "swir_gray"],
}

GOES_ALL_LAYERS = [
    "vis",
    "vis_enhanced",
    "ir",
    "ir_gray",
    "ir_contour",
    "wv",
    "wv_gray",
    "swir",
    "swir_gray",
]

# ============================================================================
# BOUNDING BOXES
# ============================================================================
# Various geographic bounding boxes (global)
BBOXES = [
    "-125,25,-65,50",  # Continental US
    "-10,35,40,70",  # Europe
    "-80,20,-30,50",  # North Atlantic
    "-130,40,-115,55",  # Pacific Northwest
    "-100,18,-80,32",  # Gulf of Mexico
    "-105,35,-85,50",  # Midwest US
    "-90,35,-85,40",  # Small region (high detail)
    "-180,-90,180,90",  # Global
]

# CONUS bounding boxes (for MRMS and GOES)
CONUS_BBOXES = [
    "-125,25,-65,50",  # Full CONUS
    "-130,40,-115,55",  # Pacific Northwest
    "-100,25,-75,50",  # Eastern US
    "-105,35,-85,45",  # Midwest
    "-100,25,-85,35",  # Gulf Coast/South
    "-95,35,-90,40",  # Small region (high detail)
    "-120,30,-100,45",  # Western US
]

# Image sizes
SIZES = [
    (256, 256),
    (512, 512),
    (1024, 1024),
    (2048, 2048),
]


# ============================================================================
# GFS USERS (existing)
# ============================================================================
class StyleComparisonUser(HttpUser):
    """Test different rendering styles: gradient, contour, numbers"""

    wait_time = between(0.2, 0.8)
    host = "http://nginx"

    @task(10)
    def getmap_gradient(self):
        """Gradient (raster) style - fastest"""
        layer = random.choice(["t2m", "mslp", "cape", "pwat"])
        self.client.get(
            "/cgi-bin/mapserv",
            params={
                "MAP": "GFS",
                "SERVICE": "WMS",
                "VERSION": "1.3.0",
                "REQUEST": "GetMap",
                "LAYERS": layer,
                "CRS": "EPSG:4326",
                "BBOX": random.choice(BBOXES),
                "WIDTH": "512",
                "HEIGHT": "512",
                "FORMAT": "image/png",
            },
            name=f"/wms/gfs?style=gradient&layer={layer}",
        )

    @task(8)
    def getmap_contour(self):
        """Contour style - CPU intensive"""
        layer = random.choice(
            ["t2m_contour", "mslp_contour", "cape_contour", "pwat_contour"]
        )
        base_layer = layer.replace("_contour", "")
        self.client.get(
            "/cgi-bin/mapserv",
            params={
                "MAP": "GFS",
                "SERVICE": "WMS",
                "VERSION": "1.3.0",
                "REQUEST": "GetMap",
                "LAYERS": layer,
                "CRS": "EPSG:4326",
                "BBOX": random.choice(BBOXES),
                "WIDTH": "512",
                "HEIGHT": "512",
                "FORMAT": "image/png",
            },
            name=f"/wms/gfs?style=contour&layer={base_layer}",
        )

    @task(5)
    def getmap_numbers(self):
        """Numbers style - text rendering"""
        layer = random.choice(
            ["t2m_numbers", "mslp_numbers", "cape_numbers", "pwat_numbers"]
        )
        base_layer = layer.replace("_numbers", "")
        self.client.get(
            "/cgi-bin/mapserv",
            params={
                "MAP": "GFS",
                "SERVICE": "WMS",
                "VERSION": "1.3.0",
                "REQUEST": "GetMap",
                "LAYERS": layer,
                "CRS": "EPSG:4326",
                "BBOX": random.choice(BBOXES),
                "WIDTH": "512",
                "HEIGHT": "512",
                "FORMAT": "image/png",
            },
            name=f"/wms/gfs?style=numbers&layer={base_layer}",
        )

    @task(3)
    def getmap_combined(self):
        """Combined: gradient + contour overlay"""
        base = random.choice(["t2m", "mslp", "cape", "pwat"])
        layers = f"{base},{base}_contour"
        self.client.get(
            "/cgi-bin/mapserv",
            params={
                "MAP": "GFS",
                "SERVICE": "WMS",
                "VERSION": "1.3.0",
                "REQUEST": "GetMap",
                "LAYERS": layers,
                "CRS": "EPSG:4326",
                "BBOX": random.choice(BBOXES),
                "WIDTH": "512",
                "HEIGHT": "512",
                "FORMAT": "image/png",
            },
            name=f"/wms/gfs?style=combined&layer={base}",
        )


class AggressiveWmsUser(HttpUser):
    """High-frequency WMS user for stress testing"""

    wait_time = between(0.1, 0.5)
    host = "http://nginx"

    @task(20)
    def getmap_random(self):
        """Random GetMap requests with various styles"""
        layer = random.choice(ALL_LAYERS)
        width, height = random.choice(SIZES[:3])

        # Determine style from layer name for naming
        if "_contour" in layer:
            style = "contour"
        elif "_numbers" in layer:
            style = "numbers"
        else:
            style = "gradient"

        self.client.get(
            "/cgi-bin/mapserv",
            params={
                "MAP": "GFS",
                "SERVICE": "WMS",
                "VERSION": "1.3.0",
                "REQUEST": "GetMap",
                "LAYERS": layer,
                "CRS": random.choice(["EPSG:4326", "EPSG:3857"]),
                "BBOX": random.choice(BBOXES),
                "WIDTH": str(width),
                "HEIGHT": str(height),
                "FORMAT": random.choice(["image/png", "image/jpeg"]),
            },
            name=f"/wms/gfs?GetMap_{style}",
        )

    @task(5)
    def getmap_large_contour(self):
        """Large contour image - very CPU intensive"""
        layer = random.choice(["t2m_contour", "mslp_contour"])
        self.client.get(
            "/cgi-bin/mapserv",
            params={
                "MAP": "GFS",
                "SERVICE": "WMS",
                "VERSION": "1.3.0",
                "REQUEST": "GetMap",
                "LAYERS": layer,
                "CRS": "EPSG:4326",
                "BBOX": "-180,-90,180,90",
                "WIDTH": "2048",
                "HEIGHT": "1024",
                "FORMAT": "image/png",
            },
            name="/wms/gfs?GetMap_large_contour",
        )

    @task(3)
    def getmap_multilayer_styled(self):
        """Multi-layer with mixed styles"""
        base = random.choice(["t2m", "mslp", "cape"])
        # Gradient base + contour overlay
        layers = f"{base},{base}_contour"
        self.client.get(
            "/cgi-bin/mapserv",
            params={
                "MAP": "GFS",
                "SERVICE": "WMS",
                "VERSION": "1.3.0",
                "REQUEST": "GetMap",
                "LAYERS": layers,
                "CRS": "EPSG:4326",
                "BBOX": random.choice(BBOXES),
                "WIDTH": "512",
                "HEIGHT": "512",
                "FORMAT": "image/png",
            },
            name="/wms/gfs?GetMap_multi_styled",
        )

    @task(2)
    def getcapabilities(self):
        """GetCapabilities"""
        self.client.get(
            "/cgi-bin/mapserv",
            params={
                "MAP": "GFS",
                "SERVICE": "WMS",
                "VERSION": "1.3.0",
                "REQUEST": "GetCapabilities",
            },
            name="/wms/gfs?GetCapabilities",
        )


class TileUser(HttpUser):
    """MapCache tile user"""

    wait_time = between(0.05, 0.2)
    host = "http://nginx"

    TILE_BBOXES = [
        ["-180,-90,0,90", "0,-90,180,90"],
        ["-180,0,0,90", "0,0,180,90", "-180,-90,0,0", "0,-90,180,0"],
        ["-90,0,0,45", "0,0,90,45", "-180,45,-90,90", "-90,45,0,90"],
    ]

    @task(10)
    def gettile_wms(self):
        """Tile requests via WMS to mapcache"""
        layer = random.choice(["gfs-t2m", "gfs-pwat", "gfs-cape"])
        z = random.randint(0, 2)
        bboxes = self.TILE_BBOXES[z]
        bbox = random.choice(bboxes)
        self.client.get(
            "/mapcache/",
            params={
                "SERVICE": "WMS",
                "VERSION": "1.1.1",
                "REQUEST": "GetMap",
                "LAYERS": layer,
                "STYLES": "",
                "SRS": "EPSG:4326",
                "BBOX": bbox,
                "WIDTH": "256",
                "HEIGHT": "256",
                "FORMAT": "image/png",
            },
            name=f"/mapcache?tile_{layer}",
        )

    @task(5)
    def gettile_repeated(self):
        """Repeated tile request - cache HIT"""
        self.client.get(
            "/mapcache/",
            params={
                "SERVICE": "WMS",
                "VERSION": "1.1.1",
                "REQUEST": "GetMap",
                "LAYERS": "gfs-t2m",
                "STYLES": "",
                "SRS": "EPSG:4326",
                "BBOX": "-180,-90,0,90",
                "WIDTH": "256",
                "HEIGHT": "256",
                "FORMAT": "image/png",
            },
            name="/mapcache?tile_cached",
        )


class GfsWmsUser(HttpUser):
    """Balanced user for baseline testing"""

    wait_time = between(0.5, 2)
    host = "http://nginx"

    @task(10)
    def getmap_gradient(self):
        """Standard gradient map"""
        bbox = random.choice(["-125,25,-65,50", "-10,35,40,70"])
        self.client.get(
            "/cgi-bin/mapserv",
            params={
                "MAP": "GFS",
                "SERVICE": "WMS",
                "VERSION": "1.3.0",
                "REQUEST": "GetMap",
                "LAYERS": random.choice(BASE_LAYERS),
                "CRS": "EPSG:4326",
                "BBOX": bbox,
                "WIDTH": "512",
                "HEIGHT": "512",
                "FORMAT": "image/png",
            },
            name="/wms/gfs?GetMap_gradient",
        )

    @task(5)
    def getmap_contour(self):
        """Contour overlay"""
        bbox = random.choice(["-125,25,-65,50", "-10,35,40,70"])
        layer = random.choice(["t2m_contour", "mslp_contour"])
        self.client.get(
            "/cgi-bin/mapserv",
            params={
                "MAP": "GFS",
                "SERVICE": "WMS",
                "VERSION": "1.3.0",
                "REQUEST": "GetMap",
                "LAYERS": layer,
                "CRS": "EPSG:4326",
                "BBOX": bbox,
                "WIDTH": "512",
                "HEIGHT": "512",
                "FORMAT": "image/png",
            },
            name="/wms/gfs?GetMap_contour",
        )

    @task(3)
    def getmap_numbers(self):
        """Numbers overlay"""
        bbox = random.choice(["-125,25,-65,50", "-10,35,40,70"])
        layer = random.choice(["t2m_numbers", "mslp_numbers"])
        self.client.get(
            "/cgi-bin/mapserv",
            params={
                "MAP": "GFS",
                "SERVICE": "WMS",
                "VERSION": "1.3.0",
                "REQUEST": "GetMap",
                "LAYERS": layer,
                "CRS": "EPSG:4326",
                "BBOX": bbox,
                "WIDTH": "512",
                "HEIGHT": "512",
                "FORMAT": "image/png",
            },
            name="/wms/gfs?GetMap_numbers",
        )

    @task(3)
    def gettile(self):
        """Tile request via mapcache"""
        self.client.get(
            "/mapcache/",
            params={
                "SERVICE": "WMS",
                "VERSION": "1.1.1",
                "REQUEST": "GetMap",
                "LAYERS": "gfs-t2m",
                "STYLES": "",
                "SRS": "EPSG:4326",
                "BBOX": random.choice(["-180,-90,0,90", "0,-90,180,90"]),
                "WIDTH": "256",
                "HEIGHT": "256",
                "FORMAT": "image/png",
            },
            name="/mapcache?tile",
        )


# ============================================================================
# MRMS USERS (NEW)
# ============================================================================
class MrmsWmsUser(HttpUser):
    """MRMS radar WMS user - CONUS coverage"""

    wait_time = between(0.3, 1.0)
    host = "http://nginx"

    @task(15)
    def getmap_reflectivity(self):
        """Composite reflectivity - most common radar product"""
        self.client.get(
            "/cgi-bin/mapserv",
            params={
                "MAP": "MRMS",
                "SERVICE": "WMS",
                "VERSION": "1.3.0",
                "REQUEST": "GetMap",
                "LAYERS": "refl",
                "CRS": "EPSG:4326",
                "BBOX": random.choice(CONUS_BBOXES),
                "WIDTH": "512",
                "HEIGHT": "512",
                "FORMAT": "image/png",
            },
            name="/wms/mrms?layer=refl",
        )

    @task(8)
    def getmap_reflectivity_contour(self):
        """Reflectivity contours"""
        self.client.get(
            "/cgi-bin/mapserv",
            params={
                "MAP": "MRMS",
                "SERVICE": "WMS",
                "VERSION": "1.3.0",
                "REQUEST": "GetMap",
                "LAYERS": "refl_contour",
                "CRS": "EPSG:4326",
                "BBOX": random.choice(CONUS_BBOXES),
                "WIDTH": "512",
                "HEIGHT": "512",
                "FORMAT": "image/png",
            },
            name="/wms/mrms?layer=refl_contour",
        )

    @task(10)
    def getmap_precip_rate(self):
        """Precipitation rate"""
        self.client.get(
            "/cgi-bin/mapserv",
            params={
                "MAP": "MRMS",
                "SERVICE": "WMS",
                "VERSION": "1.3.0",
                "REQUEST": "GetMap",
                "LAYERS": "precip_rate",
                "CRS": "EPSG:4326",
                "BBOX": random.choice(CONUS_BBOXES),
                "WIDTH": "512",
                "HEIGHT": "512",
                "FORMAT": "image/png",
            },
            name="/wms/mrms?layer=precip_rate",
        )

    @task(8)
    def getmap_qpe(self):
        """1-hour QPE"""
        self.client.get(
            "/cgi-bin/mapserv",
            params={
                "MAP": "MRMS",
                "SERVICE": "WMS",
                "VERSION": "1.3.0",
                "REQUEST": "GetMap",
                "LAYERS": "qpe_01h",
                "CRS": "EPSG:4326",
                "BBOX": random.choice(CONUS_BBOXES),
                "WIDTH": "512",
                "HEIGHT": "512",
                "FORMAT": "image/png",
            },
            name="/wms/mrms?layer=qpe_01h",
        )

    @task(5)
    def getmap_base_refl(self):
        """Base reflectivity"""
        self.client.get(
            "/cgi-bin/mapserv",
            params={
                "MAP": "MRMS",
                "SERVICE": "WMS",
                "VERSION": "1.3.0",
                "REQUEST": "GetMap",
                "LAYERS": "base_refl",
                "CRS": "EPSG:4326",
                "BBOX": random.choice(CONUS_BBOXES),
                "WIDTH": "512",
                "HEIGHT": "512",
                "FORMAT": "image/png",
            },
            name="/wms/mrms?layer=base_refl",
        )

    @task(5)
    def getmap_large(self):
        """Large MRMS image - full CONUS"""
        layer = random.choice(["refl", "precip_rate"])
        self.client.get(
            "/cgi-bin/mapserv",
            params={
                "MAP": "MRMS",
                "SERVICE": "WMS",
                "VERSION": "1.3.0",
                "REQUEST": "GetMap",
                "LAYERS": layer,
                "CRS": "EPSG:4326",
                "BBOX": "-130,20,-60,55",
                "WIDTH": "1400",
                "HEIGHT": "700",
                "FORMAT": "image/png",
            },
            name=f"/wms/mrms?large_{layer}",
        )

    @task(2)
    def getcapabilities(self):
        """MRMS GetCapabilities"""
        self.client.get(
            "/cgi-bin/mapserv",
            params={
                "MAP": "MRMS",
                "SERVICE": "WMS",
                "VERSION": "1.3.0",
                "REQUEST": "GetCapabilities",
            },
            name="/wms/mrms?GetCapabilities",
        )


class MrmsAggressiveUser(HttpUser):
    """High-frequency MRMS radar user"""

    wait_time = between(0.1, 0.4)
    host = "http://nginx"

    @task(20)
    def getmap_random(self):
        """Random MRMS layer requests"""
        layer = random.choice(MRMS_ALL_LAYERS)
        width, height = random.choice(SIZES[:3])

        style = "contour" if "_contour" in layer else "gradient"

        self.client.get(
            "/cgi-bin/mapserv",
            params={
                "MAP": "MRMS",
                "SERVICE": "WMS",
                "VERSION": "1.3.0",
                "REQUEST": "GetMap",
                "LAYERS": layer,
                "CRS": random.choice(["EPSG:4326", "EPSG:3857"]),
                "BBOX": random.choice(CONUS_BBOXES),
                "WIDTH": str(width),
                "HEIGHT": str(height),
                "FORMAT": random.choice(["image/png", "image/jpeg"]),
            },
            name=f"/wms/mrms?GetMap_{style}",
        )

    @task(5)
    def getmap_combined(self):
        """Reflectivity + contour overlay"""
        self.client.get(
            "/cgi-bin/mapserv",
            params={
                "MAP": "MRMS",
                "SERVICE": "WMS",
                "VERSION": "1.3.0",
                "REQUEST": "GetMap",
                "LAYERS": "refl,refl_contour",
                "CRS": "EPSG:4326",
                "BBOX": random.choice(CONUS_BBOXES),
                "WIDTH": "512",
                "HEIGHT": "512",
                "FORMAT": "image/png",
            },
            name="/wms/mrms?combined",
        )


# ============================================================================
# GOES USERS (NEW)
# ============================================================================
class GoesWmsUser(HttpUser):
    """GOES satellite WMS user - CONUS coverage"""

    wait_time = between(0.3, 1.0)
    host = "http://nginx"

    @task(12)
    def getmap_visible(self):
        """Visible imagery (daytime)"""
        layer = random.choice(["vis", "vis_enhanced"])
        self.client.get(
            "/cgi-bin/mapserv",
            params={
                "MAP": "GOES",
                "SERVICE": "WMS",
                "VERSION": "1.3.0",
                "REQUEST": "GetMap",
                "LAYERS": layer,
                "CRS": "EPSG:4326",
                "BBOX": random.choice(CONUS_BBOXES),
                "WIDTH": "512",
                "HEIGHT": "512",
                "FORMAT": "image/png",
            },
            name=f"/wms/goes?layer={layer}",
        )

    @task(15)
    def getmap_infrared(self):
        """Infrared imagery - most common"""
        layer = random.choice(["ir", "ir_gray"])
        self.client.get(
            "/cgi-bin/mapserv",
            params={
                "MAP": "GOES",
                "SERVICE": "WMS",
                "VERSION": "1.3.0",
                "REQUEST": "GetMap",
                "LAYERS": layer,
                "CRS": "EPSG:4326",
                "BBOX": random.choice(CONUS_BBOXES),
                "WIDTH": "512",
                "HEIGHT": "512",
                "FORMAT": "image/png",
            },
            name=f"/wms/goes?layer={layer}",
        )

    @task(8)
    def getmap_ir_contour(self):
        """IR with temperature contours"""
        self.client.get(
            "/cgi-bin/mapserv",
            params={
                "MAP": "GOES",
                "SERVICE": "WMS",
                "VERSION": "1.3.0",
                "REQUEST": "GetMap",
                "LAYERS": "ir_contour",
                "CRS": "EPSG:4326",
                "BBOX": random.choice(CONUS_BBOXES),
                "WIDTH": "512",
                "HEIGHT": "512",
                "FORMAT": "image/png",
            },
            name="/wms/goes?layer=ir_contour",
        )

    @task(10)
    def getmap_water_vapor(self):
        """Water vapor imagery"""
        layer = random.choice(["wv", "wv_gray"])
        self.client.get(
            "/cgi-bin/mapserv",
            params={
                "MAP": "GOES",
                "SERVICE": "WMS",
                "VERSION": "1.3.0",
                "REQUEST": "GetMap",
                "LAYERS": layer,
                "CRS": "EPSG:4326",
                "BBOX": random.choice(CONUS_BBOXES),
                "WIDTH": "512",
                "HEIGHT": "512",
                "FORMAT": "image/png",
            },
            name=f"/wms/goes?layer={layer}",
        )

    @task(6)
    def getmap_swir(self):
        """Shortwave IR (fire/fog detection)"""
        layer = random.choice(["swir", "swir_gray"])
        self.client.get(
            "/cgi-bin/mapserv",
            params={
                "MAP": "GOES",
                "SERVICE": "WMS",
                "VERSION": "1.3.0",
                "REQUEST": "GetMap",
                "LAYERS": layer,
                "CRS": "EPSG:4326",
                "BBOX": random.choice(CONUS_BBOXES),
                "WIDTH": "512",
                "HEIGHT": "512",
                "FORMAT": "image/png",
            },
            name=f"/wms/goes?layer={layer}",
        )

    @task(5)
    def getmap_large(self):
        """Large GOES image"""
        layer = random.choice(["ir", "vis", "wv"])
        self.client.get(
            "/cgi-bin/mapserv",
            params={
                "MAP": "GOES",
                "SERVICE": "WMS",
                "VERSION": "1.3.0",
                "REQUEST": "GetMap",
                "LAYERS": layer,
                "CRS": "EPSG:4326",
                "BBOX": "-135,15,-60,55",
                "WIDTH": "1500",
                "HEIGHT": "800",
                "FORMAT": "image/png",
            },
            name=f"/wms/goes?large_{layer}",
        )

    @task(2)
    def getcapabilities(self):
        """GOES GetCapabilities"""
        self.client.get(
            "/cgi-bin/mapserv",
            params={
                "MAP": "GOES",
                "SERVICE": "WMS",
                "VERSION": "1.3.0",
                "REQUEST": "GetCapabilities",
            },
            name="/wms/goes?GetCapabilities",
        )


class GoesAggressiveUser(HttpUser):
    """High-frequency GOES satellite user"""

    wait_time = between(0.1, 0.4)
    host = "http://nginx"

    @task(25)
    def getmap_random(self):
        """Random GOES layer requests"""
        layer = random.choice(GOES_ALL_LAYERS)
        width, height = random.choice(SIZES[:3])

        style = (
            "contour"
            if "_contour" in layer
            else ("gray" if "_gray" in layer else "color")
        )

        self.client.get(
            "/cgi-bin/mapserv",
            params={
                "MAP": "GOES",
                "SERVICE": "WMS",
                "VERSION": "1.3.0",
                "REQUEST": "GetMap",
                "LAYERS": layer,
                "CRS": random.choice(["EPSG:4326", "EPSG:3857"]),
                "BBOX": random.choice(CONUS_BBOXES),
                "WIDTH": str(width),
                "HEIGHT": str(height),
                "FORMAT": random.choice(["image/png", "image/jpeg"]),
            },
            name=f"/wms/goes?GetMap_{style}",
        )

    @task(5)
    def getmap_combined(self):
        """IR + contour overlay"""
        self.client.get(
            "/cgi-bin/mapserv",
            params={
                "MAP": "GOES",
                "SERVICE": "WMS",
                "VERSION": "1.3.0",
                "REQUEST": "GetMap",
                "LAYERS": "ir,ir_contour",
                "CRS": "EPSG:4326",
                "BBOX": random.choice(CONUS_BBOXES),
                "WIDTH": "512",
                "HEIGHT": "512",
                "FORMAT": "image/png",
            },
            name="/wms/goes?combined_ir",
        )


# ============================================================================
# MIXED USER - Tests all data sources together
# ============================================================================
class MixedDataUser(HttpUser):
    """Simulates a user viewing multiple data sources"""

    wait_time = between(0.5, 1.5)
    host = "http://nginx"

    @task(10)
    def getmap_gfs(self):
        """GFS model data"""
        layer = random.choice(["t2m", "mslp", "cape", "pwat"])
        self.client.get(
            "/cgi-bin/mapserv",
            params={
                "MAP": "GFS",
                "SERVICE": "WMS",
                "VERSION": "1.3.0",
                "REQUEST": "GetMap",
                "LAYERS": layer,
                "CRS": "EPSG:4326",
                "BBOX": random.choice(CONUS_BBOXES),
                "WIDTH": "512",
                "HEIGHT": "512",
                "FORMAT": "image/png",
            },
            name="/wms/mixed?gfs",
        )

    @task(10)
    def getmap_mrms(self):
        """MRMS radar data"""
        layer = random.choice(["refl", "precip_rate", "qpe_01h"])
        self.client.get(
            "/cgi-bin/mapserv",
            params={
                "MAP": "MRMS",
                "SERVICE": "WMS",
                "VERSION": "1.3.0",
                "REQUEST": "GetMap",
                "LAYERS": layer,
                "CRS": "EPSG:4326",
                "BBOX": random.choice(CONUS_BBOXES),
                "WIDTH": "512",
                "HEIGHT": "512",
                "FORMAT": "image/png",
            },
            name="/wms/mixed?mrms",
        )

    @task(10)
    def getmap_goes(self):
        """GOES satellite data"""
        layer = random.choice(["ir", "vis", "wv"])
        self.client.get(
            "/cgi-bin/mapserv",
            params={
                "MAP": "GOES",
                "SERVICE": "WMS",
                "VERSION": "1.3.0",
                "REQUEST": "GetMap",
                "LAYERS": layer,
                "CRS": "EPSG:4326",
                "BBOX": random.choice(CONUS_BBOXES),
                "WIDTH": "512",
                "HEIGHT": "512",
                "FORMAT": "image/png",
            },
            name="/wms/mixed?goes",
        )

    @task(3)
    def rapid_switch(self):
        """Rapid switching between data sources (simulates user browsing)"""
        # GFS
        self.client.get(
            "/cgi-bin/mapserv",
            params={
                "MAP": "GFS",
                "SERVICE": "WMS",
                "VERSION": "1.3.0",
                "REQUEST": "GetMap",
                "LAYERS": "t2m",
                "CRS": "EPSG:4326",
                "BBOX": "-100,30,-80,45",
                "WIDTH": "512",
                "HEIGHT": "512",
                "FORMAT": "image/png",
            },
            name="/wms/mixed?rapid_gfs",
        )
        # MRMS
        self.client.get(
            "/cgi-bin/mapserv",
            params={
                "MAP": "MRMS",
                "SERVICE": "WMS",
                "VERSION": "1.3.0",
                "REQUEST": "GetMap",
                "LAYERS": "refl",
                "CRS": "EPSG:4326",
                "BBOX": "-100,30,-80,45",
                "WIDTH": "512",
                "HEIGHT": "512",
                "FORMAT": "image/png",
            },
            name="/wms/mixed?rapid_mrms",
        )
        # GOES
        self.client.get(
            "/cgi-bin/mapserv",
            params={
                "MAP": "GOES",
                "SERVICE": "WMS",
                "VERSION": "1.3.0",
                "REQUEST": "GetMap",
                "LAYERS": "ir",
                "CRS": "EPSG:4326",
                "BBOX": "-100,30,-80,45",
                "WIDTH": "512",
                "HEIGHT": "512",
                "FORMAT": "image/png",
            },
            name="/wms/mixed?rapid_goes",
        )
