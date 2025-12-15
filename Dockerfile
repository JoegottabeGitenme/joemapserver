# Use official MapServer image with GDAL support
FROM camptocamp/mapserver:8.2

# Copy map file
RUN mkdir -p /etc/mapserver/maps /var/log/mapserver
COPY gfs.map /etc/mapserver/maps/gfs.map

# Override the mapserver config to allow full paths and enable debugging
# MS_DEBUGLEVEL: 0=errors, 1=notices, 2=timing, 3=verbose, 4=very verbose, 5=all
RUN printf 'CONFIG\n  ENV\n    MS_MAP_NO_PATH "0"\n    MS_ERRORFILE "stderr"\n  END\n  MAPS\n    GFS "/etc/mapserver/maps/gfs.map"\n  END\nEND\n' > /etc/mapserver.conf

# The camptocamp image runs Apache with mod_fcgid on port 80
EXPOSE 80
