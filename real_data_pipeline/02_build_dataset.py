"""
Step 2 - Turn the downloaded real sources into the same table layout the existing pipeline
reads (pune_wards / demographics / traffic / pollution / green_cover / infrastructure /
timeseries + GeoJSON), written to data_real/ so data/ (simulated) is never touched.

Unit of analysis: the 15 PMC administrative ward offices (2017 boundaries).

What is measured and what is a proxy is written to data_real/provenance.json.

Run from the project root:   python real_data_pipeline/02_build_dataset.py
"""

import csv
import glob
import json
import os
import sys
from datetime import datetime

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import linemerge, polygonize, unary_union

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DL = os.path.join(ROOT, "data_real", "downloads")
RAW = os.path.join(ROOT, "data_real", "raw")
SPATIAL = os.path.join(ROOT, "data_real", "spatial")
UTM = "EPSG:32643"  # UTM zone 43N, metres - used for every area / length / distance

WARD_NAMES = {
    1: "Aundh", 2: "Ghole Road", 3: "Kothrud-Karve Road", 4: "Warje-Karve Nagar",
    5: "Dhole Patil Road", 6: "Yerawada-Sangamwadi", 7: "Nagar Road",
    8: "Kasba-Vishrambaugwada", 9: "Tilak Road", 10: "Sahakarnagar", 11: "Bibwewadi",
    12: "Bhavani Peth", 13: "Hadapsar", 14: "Dhankawadi", 15: "Kondhwa-Wanavdi",
}
# The 2011 "Bibvewadi" ward office contains the Kondhva Khurd / Kondhva Budrukh wards, which the 2017
# boundaries moved into "Kondhwa-Wanavdi". The two cannot be separated with 2011 census data, so they
# are analysed as one unit (ward 15 is folded into ward 11).
MERGE = {15: 11}
MERGED_NAME = {11: "Bibwewadi-Kondhwa"}
# census "Ward Name" (ward office) -> administrative ward number
CENSUS_TO_WARD = {
    "Aundh": 1, "Ghole Road": 2, "Kothrud": 3, "Warje": 4, "Dholepatil Road": 5,
    "Sangamwadi (Yerawada)": 6, "Nagar Road": 7, "Kasbavish-Rambaug": 8, "Tilak Road": 9,
    "Sahakarnagar": 10, "Bibvewadi": 11, "Bhavani Peth": 12, "Hadapsar": 13,
    "Dhankawadi": 14, "Yewalewadi": 15,   # Yewalewadi (census town) belongs to ward 15
}
STATION_FILES = {
    "revenue_colony_shivajinagar": "Revenue Colony-Shivajinagar (IITM)",
    "karve_road": "Karve Road (MPCB)", "sppu": "Savitribai Phule Pune University (MPCB)",
    "pashan": "Panchawati-Pashan (IITM)", "hadapsar": "Hadapsar (IITM)",
    "katraj_dairy": "Katraj Dairy (MPCB)", "dhankawadi": "Dhankawadi (IITM)",
}


# --------------------------------------------------------------------------- wards
def load_wards():
    """The 15 original 2017 administrative wards (used for OpenStreetMap extraction)."""
    g = gpd.read_file(os.path.join(DL, "boundaries", "admin_wards_2017.kml"))
    g["ward_no"] = g["Name"].str.extract(r"(\d+)").astype(int)
    g = g.sort_values("ward_no").reset_index(drop=True)
    g["geometry"] = g.geometry.make_valid()
    g["Ward_ID"] = g["ward_no"].map(lambda n: f"PMC_{n:02d}")
    g["Ward_Name"] = g["ward_no"].map(WARD_NAMES)
    g["Area_sqkm"] = (g.to_crs(UTM).area / 1e6).round(2)
    return g[["ward_no", "Ward_ID", "Ward_Name", "Area_sqkm", "geometry"]]


def make_units(orig):
    """Analysis units = original wards with the MERGE rules applied (14 units)."""
    g = orig.copy()
    g["unit_no"] = g["ward_no"].replace(MERGE)
    u = g.to_crs(UTM)[["unit_no", "geometry"]].dissolve(by="unit_no").reset_index()
    u["ward_no"] = u["unit_no"]
    u["Ward_ID"] = u["unit_no"].map(lambda n: f"PMC_{n:02d}")
    u["Ward_Name"] = u["unit_no"].map(lambda n: MERGED_NAME.get(n, WARD_NAMES[n]))
    u["Area_sqkm"] = (u.area / 1e6).round(2)
    cen = u.centroid.to_crs("EPSG:4326")
    u["Center_Latitude"], u["Center_Longitude"] = cen.y.round(6), cen.x.round(6)
    u["Ward_Type"] = "administrative_ward_office"
    u["Development_Level"] = "not_classified"
    u = u.to_crs("EPSG:4326")
    return u[["ward_no", "Ward_ID", "Ward_Name", "Area_sqkm", "Center_Latitude",
              "Center_Longitude", "Ward_Type", "Development_Level", "geometry"]]


# ------------------------------------------------------------------------ census
def load_demographics(wards):
    c = pd.read_csv(os.path.join(DL, "census_wardwise_2011.csv"), encoding="utf-8-sig")
    # the file mixes ward rows with "<office> Total" subtotal rows - keep ward rows only
    c["Census Ward Number"] = pd.to_numeric(c["Census Ward Number"], errors="coerce")
    c = c.dropna(subset=["Census Ward Number"]).copy()
    c["Census Ward Number"] = c["Census Ward Number"].astype(int)
    total = int(c["TOT_P"].sum())
    assert 3_100_000 < total < 3_150_000, f"census total {total} does not match PMC 2011 (3,124,458)"

    # literates come from the second census table (matched on ward number + population)
    rows = list(csv.reader(open(os.path.join(DL, "census_pune_2011.csv"), encoding="utf-8-sig")))
    lit = []
    for r in rows[3:]:
        label = r[0].strip()
        if label.lower().startswith("ward no"):
            lit.append({"Census Ward Number": int(label.split(".")[-1]),
                        "TOT_P": int(r[2]), "LITERATES": int(r[11])})
    c = c.merge(pd.DataFrame(lit), on=["Census Ward Number", "TOT_P"], how="left")
    missing = c["LITERATES"].isna().sum()
    if missing:
        print(f"  note: literacy not matched for {missing} census wards (excluded from literacy rate)")

    c["ward_no"] = c["Ward Name"].map(CENSUS_TO_WARD).replace(MERGE)
    agg = c.groupby("ward_no").apply(lambda d: pd.Series({
        "Population": d["TOT_P"].sum(), "Households": d["No of House Holds"].sum(),
        "P_06": d["P_06"].sum(), "P_SC": d["P_SC"].sum(), "P_ST": d["P_ST"].sum(),
        "lit_pop": d.loc[d["LITERATES"].notna(), "TOT_P"].sum(),
        "lit_06": d.loc[d["LITERATES"].notna(), "P_06"].sum(),
        "literates": d["LITERATES"].sum(),
    }), include_groups=False).reset_index()
    agg = wards[["ward_no", "Ward_ID", "Ward_Name", "Area_sqkm"]].merge(agg, on="ward_no")
    out = pd.DataFrame({
        "Ward_ID": agg["Ward_ID"], "Ward_Name": agg["Ward_Name"],
        "Population": agg["Population"].astype(int),
        "Population_Density": (agg["Population"] / agg["Area_sqkm"]).round(2),
        "Households": agg["Households"].astype(int),
        "Literacy_Rate": (agg["literates"] / (agg["lit_pop"] - agg["lit_06"]) * 100).round(1),
        "Children_Pct": (agg["P_06"] / agg["Population"] * 100).round(1),
        "SC_Pct": (agg["P_SC"] / agg["Population"] * 100).round(1),
        "ST_Pct": (agg["P_ST"] / agg["Population"] * 100).round(1),
    })
    return out, total


# ------------------------------------------------------------------- air quality
BREAKPOINTS = {  # CPCB National AQI, 24-hour averages: (conc_lo, conc_hi, idx_lo, idx_hi)
    "PM2_5": [(0, 30, 0, 50), (30, 60, 50, 100), (60, 90, 100, 200), (90, 120, 200, 300),
              (120, 250, 300, 400), (250, 500, 400, 500)],
    "PM10": [(0, 50, 0, 50), (50, 100, 50, 100), (100, 250, 100, 200), (250, 350, 200, 300),
             (350, 430, 300, 400), (430, 600, 400, 500)],
    "NO2": [(0, 40, 0, 50), (40, 80, 50, 100), (80, 180, 100, 200), (180, 280, 200, 300),
            (280, 400, 300, 400), (400, 800, 400, 500)],
}
PLAUSIBLE_MAX = {"PM2_5": 1000, "PM10": 2000, "NO2": 500}


def sub_index(pollutant, conc):
    if pd.isna(conc):
        return np.nan
    for lo, hi, ilo, ihi in BREAKPOINTS[pollutant]:
        if conc <= hi:
            return ilo + (conc - lo) * (ihi - ilo) / (hi - lo)
    return 500.0


def station_daily():
    """Daily station averages (IST) with basic QC; a day needs >= 48 of 96 readings."""
    locs = json.load(open(os.path.join(DL, "station_locations.json"), encoding="utf-8"))
    frames = []
    for key in STATION_FILES:
        df = pd.read_csv(os.path.join(DL, "aq", f"{key}.csv"), low_memory=False)
        df = df.rename(columns={"PM2.5 (µg/m³)": "PM2_5", "PM10 (µg/m³)": "PM10",
                                "NO2 (µg/m³)": "NO2", "AT (°C)": "Temperature", "RH (%)": "Humidity"})
        ts = pd.to_datetime(df["Timestamp"], utc=True).dt.tz_convert("Asia/Kolkata")
        df["Date"] = ts.dt.date
        for p, mx in PLAUSIBLE_MAX.items():
            df[p] = pd.to_numeric(df[p], errors="coerce")
            df.loc[(df[p] <= 0) | (df[p] > mx), p] = np.nan
        for p in ("Temperature", "Humidity"):
            df[p] = pd.to_numeric(df[p], errors="coerce") if p in df else np.nan
        g = df.groupby("Date")
        d = g[["PM2_5", "PM10", "NO2", "Temperature", "Humidity"]].mean()
        cnt = g[["PM2_5", "PM10", "NO2"]].count()
        for p in ("PM2_5", "PM10", "NO2"):
            d.loc[cnt[p] < 48, p] = np.nan
        d = d.reset_index()
        d["station"] = key
        d["lat"], d["lon"] = locs[key]["lat"], locs[key]["lon"]
        frames.append(d)
    out = pd.concat(frames, ignore_index=True)
    si = pd.DataFrame({p: out[p].map(lambda v, p=p: sub_index(p, v)) for p in BREAKPOINTS})
    out["AQI"] = si.max(axis=1, skipna=True)
    out.loc[out[["PM2_5", "PM10"]].isna().all(axis=1), "AQI"] = np.nan  # a PM reading is mandatory
    return out


def idw_wards(daily, wards, value_cols, power=2.0):
    """Inverse-distance weighting of station values to each ward centroid, per day."""
    cen = wards.to_crs(UTM).centroid
    wx, wy = cen.x.values, cen.y.values
    st = gpd.GeoSeries(gpd.points_from_xy(daily["lon"], daily["lat"]), crs="EPSG:4326").to_crs(UTM)
    daily = daily.assign(x=st.x.values, y=st.y.values)
    rows = []
    for date, d in daily.groupby("Date"):
        for i, w in enumerate(wards.itertuples()):
            dist = np.hypot(d["x"].values - wx[i], d["y"].values - wy[i]).clip(min=50)
            wgt = 1.0 / dist ** power
            rec = {"Date": date, "Ward_ID": w.Ward_ID, "Ward_Name": w.Ward_Name}
            for col in value_cols:
                ok = d[col].notna().values
                rec[col] = float((d[col].values[ok] * wgt[ok]).sum() / wgt[ok].sum()) if ok.any() else np.nan
            rows.append(rec)
    return pd.DataFrame(rows)


def build_pollution(wards):
    daily = station_daily()
    print(f"  station-days with data: {daily['AQI'].notna().sum()} across {daily['station'].nunique()} stations")
    wd = idw_wards(daily, wards, ["PM2_5", "PM10", "NO2", "AQI", "Temperature", "Humidity"])
    mean = wd.groupby(["Ward_ID", "Ward_Name"])[["PM2_5", "PM10", "NO2"]].mean().reset_index()
    # annual AQI = mean of the daily ward AQI values
    mean["AQI"] = wd.groupby("Ward_ID")["AQI"].mean().reindex(mean["Ward_ID"]).values
    mean["Pollution_Load_Index"] = mean["PM2_5"] + mean["PM10"] + mean["NO2"]
    # nearest station + distance, for transparency
    cen = wards.to_crs(UTM).centroid
    locs = json.load(open(os.path.join(DL, "station_locations.json"), encoding="utf-8"))
    sp = {k: gpd.GeoSeries([Point(v["lon"], v["lat"])], crs="EPSG:4326").to_crs(UTM).iloc[0] for k, v in locs.items()}
    near = []
    for i in range(len(wards)):
        k = min(sp, key=lambda s: cen.iloc[i].distance(sp[s]))
        near.append((STATION_FILES[k], round(cen.iloc[i].distance(sp[k]) / 1000, 2)))
    mean["Nearest_Station"] = [n[0] for n in near]
    mean["Nearest_Station_km"] = [n[1] for n in near]
    mean = mean.round({"PM2_5": 1, "PM10": 1, "NO2": 1, "AQI": 1, "Pollution_Load_Index": 1})
    ts = wd[["Date", "Ward_ID", "Ward_Name", "AQI", "PM2_5", "PM10", "Temperature", "Humidity"]].dropna(subset=["AQI"])
    ts = ts.round({"AQI": 1, "PM2_5": 1, "PM10": 1, "Temperature": 1, "Humidity": 1})
    return mean, ts


# ------------------------------------------------------------------ OpenStreetMap
def read_osm(ward_no, theme):
    path = os.path.join(DL, "osm", f"ward{ward_no:02d}_{theme}.json")
    return json.load(open(path, encoding="utf-8"))["elements"]


def points_in_ward(elements, poly, predicate):
    seen, n = set(), 0
    for el in elements:
        key = (el["type"], el["id"])
        if key in seen or not predicate(el.get("tags", {})):
            continue
        seen.add(key)
        c = el if el["type"] == "node" else el.get("center")
        if c and poly.contains(Point(c["lon"], c["lat"])):
            n += 1
    return n


def way_geom(el):
    pts = [(p["lon"], p["lat"]) for p in el.get("geometry", [])]
    return pts


def green_union(elements):
    polys = []
    for el in elements:
        if el["type"] == "way":
            pts = way_geom(el)
            if len(pts) >= 4 and pts[0] == pts[-1]:
                polys.append(Polygon(pts).buffer(0))
        elif el["type"] == "relation":
            outers, inners = [], []
            for m in el.get("members", []):
                pts = [(p["lon"], p["lat"]) for p in m.get("geometry", [])]
                if len(pts) >= 2:
                    (inners if m.get("role") == "inner" else outers).append(LineString(pts))
            if outers:
                shell = unary_union(list(polygonize(linemerge(outers))))
                hole = unary_union(list(polygonize(linemerge(inners)))) if inners else None
                polys.append(shell.difference(hole) if hole is not None and not hole.is_empty else shell)
    polys = [p for p in polys if p is not None and not p.is_empty]
    return unary_union(polys) if polys else Polygon()


def build_osm(units, orig, demo):
    """Count / measure per original 2017 ward, then roll up into the analysis units."""
    o_utm = orig.to_crs(UTM)
    raw = []
    for i, w in orig.iterrows():
        n, poly = int(w["ward_no"]), w.geometry
        am = read_osm(n, "amenity")
        rec = {
            "unit_no": MERGE.get(n, n),
            "Schools": points_in_ward(am, poly, lambda t: t.get("amenity") == "school"),
            "Hospitals": points_in_ward(am, poly, lambda t: t.get("amenity") == "hospital"),
            "Banks": points_in_ward(am, poly, lambda t: t.get("amenity") == "bank"),
            "Shopping_Malls": points_in_ward(am, poly, lambda t: t.get("shop") == "mall"),
            "Markets": points_in_ward(am, poly, lambda t: t.get("amenity") == "marketplace"),
            "Bus_Stops": points_in_ward(am, poly, lambda t: t.get("highway") == "bus_stop"),
            "Parks_Count": points_in_ward(am, poly, lambda t: t.get("leisure") == "park"),
        }
        g = gpd.GeoSeries([green_union(read_osm(n, "green"))], crs="EPSG:4326").to_crs(UTM).iloc[0]
        g = g.intersection(o_utm.geometry.iloc[i]) if not g.is_empty else g
        rec["green_km2"] = g.area / 1e6
        lines = [LineString(way_geom(el)) for el in read_osm(n, "roads") if len(way_geom(el)) >= 2]
        if lines:
            ln = gpd.GeoSeries(lines, crs="EPSG:4326").to_crs(UTM)
            rec["Road_Length_km"] = ln.intersection(o_utm.geometry.iloc[i]).length.sum() / 1000
        else:
            rec["Road_Length_km"] = 0.0
        raw.append(rec)
    raw = pd.DataFrame(raw).groupby("unit_no").sum().reset_index()
    u = units[["ward_no", "Ward_ID", "Ward_Name", "Area_sqkm"]].merge(raw, left_on="ward_no", right_on="unit_no")

    u["Total_Amenities"] = u["Schools"] + u["Hospitals"] + u["Banks"] + u["Shopping_Malls"]
    infra = pd.DataFrame({
        "Ward_ID": u["Ward_ID"], "Ward_Name": u["Ward_Name"], "Schools": u["Schools"], "Hospitals": u["Hospitals"],
        "Banks": u["Banks"], "Shopping_Malls": u["Shopping_Malls"], "Markets": u["Markets"], "Bus_Stops": u["Bus_Stops"],
        "Total_Amenities": u["Total_Amenities"], "Infrastructure_Density": (u["Total_Amenities"] / u["Area_sqkm"]).round(2)})
    green = pd.DataFrame({
        "Ward_ID": u["Ward_ID"], "Ward_Name": u["Ward_Name"],
        "Green_Cover_Percentage": (u["green_km2"] / u["Area_sqkm"] * 100).clip(upper=100).round(1),
        "Open_Spaces_sqkm": u["green_km2"].round(3), "Parks_Count": u["Parks_Count"]})

    t = u[["Ward_ID", "Ward_Name", "Area_sqkm", "Road_Length_km", "Bus_Stops"]].merge(demo[["Ward_ID", "Population"]], on="Ward_ID")
    t["Road_Length_km"] = t["Road_Length_km"].round(1)
    t["Road_Network_Density"] = (t["Road_Length_km"] / t["Area_sqkm"]).round(2)
    t["People_per_Road_km"] = (t["Population"] / t["Road_Length_km"]).round(0)
    pr = t["People_per_Road_km"]
    # PROXY: demand pressure on the road network, scaled 0-100 (no measured congestion exists)
    t["Congestion_Index"] = ((pr - pr.min()) / (pr.max() - pr.min()) * 100).round(1)
    t["Bus_Stops_per_sqkm"] = (t["Bus_Stops"] / t["Area_sqkm"]).round(2)
    traffic = t[["Ward_ID", "Ward_Name", "Congestion_Index", "Road_Length_km",
                 "Road_Network_Density", "People_per_Road_km", "Bus_Stops_per_sqkm"]]
    return infra, green, traffic


# ------------------------------------------------------------------------- main
def main():
    for d in (RAW, SPATIAL):
        os.makedirs(d, exist_ok=True)
    print("Wards")
    orig = load_wards()
    wards = make_units(orig)
    print(f"  {len(orig)} administrative wards -> {len(wards)} analysis units (ward 15 folded into ward 11)")
    print("Demographics (Census 2011)")
    demo, census_total = load_demographics(wards)
    print("Air quality (2024-25 station readings -> wards)")
    pollution, ts = build_pollution(wards)
    print("OpenStreetMap (amenities, roads, green space)")
    infra, green, traffic = build_osm(wards, orig, demo)

    wards.drop(columns=["ward_no", "geometry"]).to_csv(os.path.join(RAW, "pune_wards.csv"), index=False)
    demo.to_csv(os.path.join(RAW, "pune_demographics.csv"), index=False)
    traffic.to_csv(os.path.join(RAW, "pune_traffic.csv"), index=False)
    pollution.to_csv(os.path.join(RAW, "pune_pollution.csv"), index=False)
    green.to_csv(os.path.join(RAW, "pune_green_cover.csv"), index=False)
    infra.to_csv(os.path.join(RAW, "pune_infrastructure.csv"), index=False)
    ts.to_csv(os.path.join(RAW, "pune_timeseries.csv"), index=False)
    gj = wards[["Ward_ID", "Ward_Name", "Area_sqkm", "Ward_Type", "geometry"]]
    gj.to_file(os.path.join(SPATIAL, "pune_ward_boundaries.geojson"), driver="GeoJSON")

    provenance = {
        "built_at": datetime.now().isoformat(timespec="seconds"),
        "unit_of_analysis": "14 analysis units from the 15 PMC administrative wards (2017 boundaries, OpenCity KML); Kondhwa-Wanavdi is merged into Bibwewadi because the 2011 census office \"Bibvewadi\" contains the Kondhva wards",
        "census_total_population_check": census_total,
        "measured_or_official": {
            "Population, Households, Children_Pct, SC_Pct, ST_Pct, Literacy_Rate": "Census of India 2011, PMC ward-wise tables (OpenCity)",
            "Area_sqkm, Center_Latitude/Longitude": "computed from the PMC administrative ward polygons",
            "PM2_5, PM10, NO2": "IITM / MPCB station readings 2024-25 (OpenCity), daily means with QC, interpolated to ward centroids by inverse-distance weighting (power 2)",
            "AQI": "CPCB sub-index method on daily PM2.5, PM10 and NO2 (max sub-index), averaged over days",
            "Schools, Hospitals, Banks, Shopping_Malls, Markets, Bus_Stops, Parks_Count": "OpenStreetMap point counts inside each ward (Overpass API)",
            "Road_Length_km, Road_Network_Density": "OpenStreetMap highway lengths clipped to each ward",
        },
        "proxies_not_measurements": {
            "Congestion_Index": "NOT measured congestion. Population per km of OSM road, min-max scaled to 0-100 across the analysis units.",
            "Green_Cover_Percentage": "Share of ward area covered by OSM parks, gardens, forest, grass, scrub and meadow polygons. Depends on OSM completeness; not satellite NDVI.",
            "Open_Spaces_sqkm": "Same OSM green polygons, in km2.",
        },
        "not_available": ["Average_Income", "Peak_Hour_Volume", "Average_Speed_kmh", "Noise_Level_dB",
                         "SO2 (sensor values implausible)", "Water_Supply_Hours", "Electricity_Reliability_Pct", "Tree counts"],
        "limitations": [
            "Only 7 air-quality stations; most wards receive interpolated, not measured, values.",
            "Station coordinates come from geocoding the station's locality name and are approximate.",
            "Census is 2011 while air quality is 2024-25 and boundaries are 2017; population density therefore mixes years.",
            "Aundh and Bibwewadi-Kondhwa include areas merged into PMC after 2011, so their 2011-based density is understated.",
            "Fourteen units is a small sample for clustering.",
            "2011 census ward offices and 2017 administrative wards share names but not exact boundaries; apart from the Bibwewadi/Kondhwa merge, densities are approximate.",
        ],
    }
    with open(os.path.join(ROOT, "data_real", "provenance.json"), "w", encoding="utf-8") as f:
        json.dump(provenance, f, indent=2, ensure_ascii=False)

    print("\nBuilt data_real/raw/*.csv, data_real/spatial/pune_ward_boundaries.geojson, data_real/provenance.json")
    full = wards[["Ward_ID", "Ward_Name", "Area_sqkm"]].merge(demo, on=["Ward_ID", "Ward_Name"]) \
        .merge(pollution[["Ward_ID", "PM2_5", "AQI"]], on="Ward_ID") \
        .merge(traffic[["Ward_ID", "Congestion_Index"]], on="Ward_ID") \
        .merge(green[["Ward_ID", "Green_Cover_Percentage"]], on="Ward_ID") \
        .merge(infra[["Ward_ID", "Total_Amenities"]], on="Ward_ID")
    with pd.option_context("display.width", 220, "display.max_columns", 30):
        print(full.drop(columns="Ward_ID").to_string(index=False))


if __name__ == "__main__":
    sys.exit(main())
