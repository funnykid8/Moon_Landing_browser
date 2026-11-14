// Fetch NASA JPL Horizons Sun/Earth azimuth+elevation for every site and save docs/data/ephem.json (Node 18+, no deps).
// Usage: node tools/fetch-horizons.js [days=120]   (start = yesterday 00:00 UTC, hourly). No API key needed.
const fs = require('fs'), path = require('path');
const sites = JSON.parse(fs.readFileSync(path.join(__dirname, 'sites.json'), 'utf8'));
const days = +process.argv[2] || 120, H = 3600e3;
const start = Math.floor(Date.now() / 864e5) * 864e5 - 864e5, stop = start + days * 24 * H;
const fmt = ms => new Date(ms).toISOString().slice(0, 16).replace('T', ' ');
const sleep = ms => new Promise(r => setTimeout(r, ms));

function parse(text) {
  const m = text.match(/\$\$SOE([\s\S]*?)\$\$EOE/);
  if (!m) throw new Error('no ephemeris: ' + text.slice(0, 300));
  return m[1].trim().split('\n').map(l => {
    const p = l.split(',').map(s => s.trim()), n = p.slice(1).filter(s => s !== '' && !isNaN(+s)).map(Number);
    return [Math.round(n[0] * 100) / 100, Math.round(n[1] * 1000) / 1000];
  });
}
async function get(cmd, lat, lon) {
  const q = new URLSearchParams({ format: 'json', COMMAND: `'${cmd}'`, OBJ_DATA: "'NO'", MAKE_EPHEM: "'YES'", EPHEM_TYPE: "'OBSERVER'",
    CENTER: "'coord@301'", COORD_TYPE: "'GEODETIC'", SITE_COORD: `'${((lon % 360) + 360) % 360},${lat},0'`,
    START_TIME: `'${fmt(start)}'`, STOP_TIME: `'${fmt(stop)}'`, STEP_SIZE: "'1h'", QUANTITIES: "'4'", ANG_FORMAT: "'DEG'", CSV_FORMAT: "'YES'", APPARENT: "'AIRLESS'" });
  for (let t = 0; t < 3; t++) {
    try { const r = await fetch('https://ssd.jpl.nasa.gov/api/horizons.api?' + q); if (!r.ok) throw new Error('HTTP ' + r.status);
      const rows = parse((await r.json()).result || ''); if (rows.length !== days * 24 + 1) throw new Error('expected ' + (days * 24 + 1) + ' rows, got ' + rows.length); return rows; }
    catch (e) { if (t == 2) throw e; await sleep(3000); }
  }
}
module.exports = { parse };
if (require.main === module) (async () => {
  const out = { source: 'NASA JPL Horizons (ssd.jpl.nasa.gov/api/horizons.api), observer on the Moon, airless', generated: new Date().toISOString(), start, hours: days * 24, sites: {} };
  for (const [n, lat, lon] of sites) {
    console.log('fetching', n);
    out.sites[n] = { lat, lon, s: await get('10', lat, lon), e: await get('399', lat, lon) };
    await sleep(1000);
  }
  fs.writeFileSync(path.join(__dirname, '..', 'docs', 'data', 'ephem.json'), JSON.stringify(out));
  console.log('saved docs/data/ephem.json');
})().catch(e => { console.error(e); process.exit(1); });
