"""Compute true terrain horizon profiles from a NASA LOLA digital elevation model.
Usage: python tools/horizon.py LDEM_85S_20M.tif [--radius-km 100] [--height 2]
Download the polar LOLA DEM (south pole, e.g. LDEM_80S_20M or LDEM_85S_10M) from the NASA PDS Geosciences Node
(https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/) or the LOLA mosaic pages, convert to GeoTIFF if needed
(gdal_translate). DEM must be south-polar stereographic, lunar sphere R=1737400 m, central meridian 0 deg.
Output: docs/data/masks.json  {site name: [elevation deg for azimuth 0..359]}"""
import json, sys, argparse, numpy as np
RM = 1737400.0

def stereo_xy(lat, lon, lon0=0.0):
    """South-polar stereographic (true scale at the pole), metres from the pole."""
    rho = 2 * RM * np.tan(np.pi / 4 + np.radians(lat) / 2)
    d = np.radians(lon - lon0)
    return rho * np.sin(d), rho * np.cos(d)

def bilinear(dem, c, r):
    c0 = np.clip(np.floor(c).astype(int), 0, dem.shape[1] - 2); r0 = np.clip(np.floor(r).astype(int), 0, dem.shape[0] - 2)
    fc, fr = np.clip(c - c0, 0, 1), np.clip(r - r0, 0, 1)
    return (dem[r0, c0] * (1 - fc) * (1 - fr) + dem[r0, c0 + 1] * fc * (1 - fr) + dem[r0 + 1, c0] * (1 - fc) * fr + dem[r0 + 1, c0 + 1] * fc * fr)

def horizon(dem, to_px, x0, y0, res, radius_m, north_dir, h=2.0):
    """north_dir: unit map vector pointing to local geographic north at the observer."""
    z0 = bilinear(dem, *to_px(np.array([x0]), np.array([y0])))[0] + h
    d = np.arange(res, radius_m, res)
    nx, ny = north_dir; ex, ey = ny, -nx                  # east is 90 deg clockwise from north in map view (x right, y up)
    prof = np.zeros(360)
    for az in range(360):
        a = np.radians(az); ux, uy = np.cos(a) * nx + np.sin(a) * ex, np.cos(a) * ny + np.sin(a) * ey
        c, r = to_px(x0 + ux * d, y0 + uy * d)
        z = bilinear(dem, c, r)
        drop = d ** 2 / (2 * RM)                           # lunar curvature
        prof[az] = np.degrees(np.max(np.arctan2(z - z0 - drop, d)))
    return prof

def main():
    import rasterio
    ap = argparse.ArgumentParser(); ap.add_argument('dem'); ap.add_argument('--radius-km', type=float, default=100); ap.add_argument('--height', type=float, default=2.0)
    ap.add_argument('--lon0', type=float, default=0.0); a = ap.parse_args()
    sites = json.load(open('tools/sites.json')); res_out = {}
    with rasterio.open(a.dem) as src:
        dem = src.read(1).astype('float64') * (src.scales[0] or 1) + (src.offsets[0] or 0)
        T = src.transform; inv = ~T; res = abs(T.a)
        to_px = lambda x, y: (inv.a * x + inv.b * y + inv.c, inv.d * x + inv.e * y + inv.f)
        for name, lat, lon in sites:
            x0, y0 = stereo_xy(lat, lon, a.lon0)
            c, r = to_px(np.array([x0]), np.array([y0]))
            if not (0 <= c[0] < dem.shape[1] and 0 <= r[0] < dem.shape[0]): print('skip (outside DEM):', name); continue
            # local north on the map: direction of increasing latitude (toward the pole is 'south'), measured numerically
            e = 1e-4; xa, ya = stereo_xy(lat + e, lon, a.lon0); n = np.array([xa - x0, ya - y0]); n /= np.hypot(*n)
            res_out[name] = [round(float(v), 2) for v in horizon(dem, to_px, x0, y0, res, a.radius_km * 1000, n, a.height)]
            print(name, 'max horizon %.1f deg' % max(res_out[name]))
    json.dump({'source': 'NASA LRO LOLA DEM ' + a.dem, 'radius_km': a.radius_km, 'observer_height_m': a.height, 'masks': res_out}, open('docs/data/masks.json', 'w'))
if __name__ == '__main__': main()
