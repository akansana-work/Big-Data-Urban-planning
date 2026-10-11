"""
Step 1 - Download the real source files (nothing here touches the simulated pipeline).

Sources
  * Census of India 2011, PMC ward-wise tables        -> OpenCity (public domain)
  * PMC administrative ward boundaries (2017, KML)     -> OpenCity
  * Air quality, 15-minute readings 2024-25            -> OpenCity (IITM / MPCB stations)
  * Station locations                                  -> OpenStreetMap Nominatim geocoding
  * Amenities, roads, green areas                      -> OpenStreetMap Overpass API

Everything lands in data_real/downloads/. Already-downloaded files are skipped, so the
script can be re-run safely.

Run from the project root:   python real_data_pipeline/01_download_sources.py
"""

import json
import os
import sys
import time

import geopandas as gpd
import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DL = os.path.join(ROOT, "data_real", "downloads")
UA = {"User-Agent": "pune-urban-planning-dissertation/1.0 (academic research)"}

OPENCITY = "https://data.opencity.in/dataset"
FILES = {
    "census_wardwise_2011.csv": f"{OPENCITY}/ed14d426-552a-43eb-adfa-dbfd3afbd068/resource/49f1fca6-6904-48de-ad4c-199108048658/download/aa1addf9-77d6-4990-b65c-20f0439fa1f5.csv",
    "census_pune_2011.csv": f"{OPENCITY}/ed14d426-552a-43eb-adfa-dbfd3afbd068/resource/0418cf26-969c-4190-9542-70b1fc8500d2/download/fcaa315c-2d63-42ad-81b6-07e7c02debf4.csv",
    "boundaries/admin_wards_2017.kml": f"{OPENCITY}/98f28dac-9158-46ee-a91e-a514d9af427c/resource/686cd9cd-012f-4f97-913f-8c7003b3eb02/download/b26b0ee3-60a3-4f1a-a45c-94b24fb9434a.kml",
}

# Air-quality stations inside the PMC area (15-minute files, 2024-25).
# Stations in Pimpri-Chinchwad (Bhosari, Nigdi, Alandi, Bhumkar Nagar) are left out on purpose.
# Mhada Colony is left out because its location could not be confirmed.
B = f"{OPENCITY}/b16b4972-1d7e-4b7e-b1d6-23228cc63c83/resource"
AQ_FILES = {
    "revenue_colony_shivajinagar": (f"{B}/de7ed9dd-5be3-4e9d-b142-85a85f4d910d/download/pune-revenue-colony-shivajinagar-iitm-2024-25.csv", "Revenue Colony, Shivajinagar, Pune"),
    "karve_road": (f"{B}/42ae24da-8bd1-46ce-8acb-df2b3b5aa677/download/pune-karve-road-mpcb-2024-25.csv", "Karve Road, Pune"),
    "sppu": (f"{B}/bcd8e8ae-d0f7-466f-a502-913e4bca220b/download/pune-savitribai-phule-pune-university-mpcb-2024-25.csv", "Savitribai Phule Pune University"),
    "pashan": (f"{B}/da12ee9d-21bf-4f5d-98d4-052b3a85c216/download/pune-panchawati_pashan-iitm-2024-25.csv", "Panchawati, Pashan, Pune"),
    "hadapsar": (f"{B}/59a536da-dd4d-4597-b84e-bcfc85fa2fca/download/pune-hadapsar-iitm-2024-25.csv", "Hadapsar, Pune"),
    "katraj_dairy": (f"{B}/f427afcc-4e7d-4092-81ac-cd823584b325/download/pune-katraj-dairy-mpcb-2024-25.csv", "Katraj Dairy, Pune"),
    "dhankawadi": (f"{B}/d62efc0d-c847-4c24-a5aa-a4dd2cf8b925/download/pune-dhankawadi-iitm-2025.csv", "Dhankawadi, Pune"),
}

OVERPASS = ["https://overpass-api.de/api/interpreter", "https://maps.mail.ru/osm/tools/overpass/api/interpreter"]

# One Overpass query per theme; {b} is the ward bounding box (south,west,north,east).
Q_AMENITY = """[out:json][timeout:120];
(
  nwr["amenity"~"^(school|hospital|bank)$"]({b});
  nwr["shop"="mall"]({b});
  nwr["amenity"="marketplace"]({b});
  nwr["highway"="bus_stop"]({b});
  node["leisure"="park"]({b});
  way["leisure"="park"]({b});
);
out center tags;"""

Q_ROADS = """[out:json][timeout:180];
way["highway"~"^(motorway|trunk|primary|secondary|tertiary|unclassified|residential|living_street|motorway_link|trunk_link|primary_link|secondary_link|tertiary_link)$"]({b});
out geom;"""

Q_GREEN = """[out:json][timeout:180];
(
  way["leisure"~"^(park|garden|nature_reserve|recreation_ground)$"]({b});
  way["landuse"~"^(forest|grass|meadow|village_green|recreation_ground)$"]({b});
  way["natural"~"^(wood|scrub|grassland)$"]({b});
  relation["leisure"~"^(park|garden|nature_reserve|recreation_ground)$"]({b});
  relation["landuse"~"^(forest|grass|meadow|village_green|recreation_ground)$"]({b});
  relation["natural"~"^(wood|scrub|grassland)$"]({b});
);
out geom;"""

QUERIES = {"amenity": Q_AMENITY, "roads": Q_ROADS, "green": Q_GREEN}


def fetch_file(rel_path, url):
    dest = os.path.join(DL, rel_path)
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        print(f"  have  {rel_path}")
        return
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    r = requests.get(url, headers=UA, timeout=300)
    r.raise_for_status()
    with open(dest, "wb") as f:
        f.write(r.content)
    print(f"  got   {rel_path} ({len(r.content) / 1024:.0f} KB)")


def geocode_stations():
    dest = os.path.join(DL, "station_locations.json")
    if os.path.exists(dest):
        print("  have  station_locations.json")
        return
    out = {}
    for key, (_, query) in AQ_FILES.items():
        r = requests.get("https://nominatim.openstreetmap.org/search", headers=UA, timeout=60,
                         params={"q": query, "format": "json", "limit": 1})
        r.raise_for_status()
        hit = r.json()[0]
        out[key] = {"query": query, "lat": float(hit["lat"]), "lon": float(hit["lon"]),
                    "matched": hit["display_name"]}
        print(f"  geocoded {key}: {out[key]['lat']:.4f}, {out[key]['lon']:.4f}")
        time.sleep(1.5)  # Nominatim usage policy: max 1 request/second
    with open(dest, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)


def overpass(query, attempts=3):
    last = None
    for attempt in range(attempts):
        url = OVERPASS[attempt % len(OVERPASS)]
        try:
            r = requests.post(url, data={"data": query}, headers=UA, timeout=300)
            if r.status_code == 200 and r.text.lstrip().startswith("{"):
                return r.json()
            last = f"HTTP {r.status_code}"
        except requests.RequestException as e:
            last = str(e)
        time.sleep(15 * (attempt + 1))
    raise RuntimeError(f"Overpass failed: {last}")


def overpass_tiled(template, south, west, north, east, depth=0):
    """Query a bounding box; if the server refuses, split it into four tiles and merge."""
    bbox = f"{south:.5f},{west:.5f},{north:.5f},{east:.5f}"
    try:
        return overpass(template.format(b=bbox), attempts=3 if depth == 0 else 2)
    except RuntimeError:
        if depth >= 3:
            raise
        ms, mw = (south + north) / 2, (west + east) / 2
        merged = {}
        for s, n in ((south, ms), (ms, north)):
            for w, e in ((west, mw), (mw, east)):
                part = overpass_tiled(template, s, w, n, e, depth + 1)
                for el in part["elements"]:
                    merged[(el["type"], el["id"])] = el
                time.sleep(3)
        return {"elements": list(merged.values())}


def fetch_osm(wards):
    osm_dir = os.path.join(DL, "osm")
    os.makedirs(osm_dir, exist_ok=True)
    for _, w in wards.iterrows():
        minx, miny, maxx, maxy = w.geometry.bounds
        for theme, q in QUERIES.items():
            dest = os.path.join(osm_dir, f"ward{w['ward_no']:02d}_{theme}.json")
            if os.path.exists(dest):
                continue
            data = overpass_tiled(q, miny, minx, maxy, maxx)
            with open(dest, "w", encoding="utf-8") as f:
                json.dump(data, f)
            print(f"  ward {w['ward_no']:02d} {theme:8s} {len(data['elements']):6d} elements")
            time.sleep(3)


def main():
    os.makedirs(DL, exist_ok=True)
    print("Census and boundaries")
    for rel, url in FILES.items():
        fetch_file(rel, url)
    print("Air-quality files")
    for key, (url, _) in AQ_FILES.items():
        fetch_file(f"aq/{key}.csv", url)
    print("Station locations")
    geocode_stations()
    print("OpenStreetMap (Overpass)")
    wards = gpd.read_file(os.path.join(DL, "boundaries", "admin_wards_2017.kml"))
    wards["ward_no"] = wards["Name"].str.extract(r"(\d+)").astype(int)
    fetch_osm(wards)
    print("Done.")


if __name__ == "__main__":
    sys.exit(main())
