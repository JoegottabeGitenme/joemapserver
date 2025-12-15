from locust import HttpUser, task, between
import random, datetime


class GfsWmsUser(HttpUser):
    wait_time = between(0.5, 2)
    host = "http://nginx"  # internal docker name

    @task(10)
    def getmap(self):
        bbox = random.choice(["-125,25,-65,50", "-10,35,40,70"])
        t = (
            datetime.datetime.utcnow()
            - datetime.timedelta(hours=random.randint(0, 240))
        ).strftime("%Y-%m-%dT%H:00:00Z")
        self.client.get(
            "/cgi-bin/mapserv",
            params={
                "MAP": "GFS",
                "SERVICE": "WMS",
                "VERSION": "1.3.0",
                "REQUEST": "GetMap",
                "LAYERS": random.choice(["t2m", "pwat", "rh2m", "gust", "mslp", "cape", "vis"]),
                "CRS": "EPSG:4326",
                "BBOX": bbox,
                "WIDTH": "512",
                "HEIGHT": "512",
                "FORMAT": "image/png",
                "TIME": t,
                "RUN": t,
                "ISOTHERM": str(random.choice(range(200, 321, 5))),
            },
        )

    @task(3)
    def gettile(self):
        z = random.randint(0, 8)
        x = random.randint(0, 2**z - 1)
        y = random.randint(0, 2**z - 1)
        self.client.get(f"/mapcache/gfs-t2m/{z}/{x}/{y}.png")
