# Use official MapServer image with GDAL support
FROM camptocamp/mapserver:8.2

# Install fonts for label rendering
RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# Create directories and set up fonts
RUN mkdir -p /etc/mapserver/maps /etc/mapserver/fonts /var/log/mapserver && \
    chown www-data:www-data /var/log/mapserver && \
    echo "dejavu /usr/share/fonts/truetype/dejavu/DejaVuSans.ttf" > /etc/mapserver/fonts/fonts.txt && \
    echo "dejavu-bold /usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" >> /etc/mapserver/fonts/fonts.txt

# Copy map files
COPY gfs.map /etc/mapserver/maps/gfs.map
COPY mrms.map /etc/mapserver/maps/mrms.map
COPY goes.map /etc/mapserver/maps/goes.map

# Override the mapserver config to allow full paths and enable debugging
# MS_DEBUGLEVEL: 0=errors, 1=notices, 2=timing, 3=verbose, 4=very verbose, 5=all
RUN printf 'CONFIG\n  ENV\n    MS_MAP_NO_PATH "0"\n    MS_DEBUGLEVEL "5"\n  END\n  MAPS\n    GFS "/etc/mapserver/maps/gfs.map"\n    MRMS "/etc/mapserver/maps/mrms.map"\n    GOES "/etc/mapserver/maps/goes.map"\n  END\nEND\n' > /etc/mapserver.conf

# Enable Apache error logging to stderr (which goes to docker logs)
RUN sed -i 's/ErrorLog .*/ErrorLog \/dev\/stderr/' /etc/apache2/sites-enabled/000-default.conf 2>/dev/null || true

# The camptocamp image runs Apache with mod_fcgid on port 80
EXPOSE 80
