# Lunar South Pole Site Planner (NASA Space Apps)
Static site (GitHub Pages) comparing lunar south pole landing sites and dates: Sun/Earth elevation and azimuth against the terrain horizon, with power and direct-to-Earth windows.

## NASA data
- **JPL Horizons** (free, no API key): `tools/fetch-horizons.js` saves hourly Sun/Earth azimuth and elevation for every site to `docs/data/ephem.json`. A GitHub Action refreshes it daily.
- **LRO LOLA DEM** (PDS Geosciences Node): `tools/horizon.py` builds true terrain horizons into `docs/data/masks.json`.
- Offline fallback: built-in analytic engine (about 0.1-0.2 deg), also used to show a validation difference vs Horizons.

## Publish on GitHub Pages
1. Push this folder to a GitHub repo.
2. Generate the NASA data once, either:
   - locally: `node tools/fetch-horizons.js 120`, commit `docs/data/ephem.json`, or
   - on GitHub: Actions tab > "Refresh NASA Horizons data" > Run workflow (needs Settings > Actions > General > Workflow permissions > Read and write).
3. Settings > Pages > Source: "Deploy from a branch", Branch `main`, folder `/docs`. Your site: https://USERNAME.github.io/REPO/

## Terrain horizons (optional but recommended)
    pip install numpy rasterio
    # download a south-polar LOLA DEM (e.g. LDEM_80S_20M) from https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/
    gdal_translate LDEM_80S_20M.IMG ldem.tif      # if conversion is needed
    python tools/horizon.py ldem.tif --radius-km 100 --height 2
Commit `docs/data/masks.json`. Sites outside the DEM (69 S sites) keep a flat horizon.

Local preview: `python3 -m http.server -d docs 8000`.
Credits: NASA JPL Horizons, NASA LRO/LOLA. Planning use only, not for flight.
