"""
Step 3 - Run the analysis on the real-data tables (data_real/) and write everything to
outputs_real/. Uses the existing preprocessing / clustering / visualization classes from
src/ (unchanged) through the adapters in real_adapters.py.

Run from the project root:   python real_data_pipeline/03_run_real_analysis.py
"""

import json
import os
import sys
import warnings
from datetime import datetime

import matplotlib

matplotlib.use("Agg")
import folium  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import plotly.express as px  # noqa: E402
import plotly.graph_objects as go  # noqa: E402
from scipy import stats  # noqa: E402
from sklearn.cluster import KMeans  # noqa: E402
from sklearn.metrics import adjusted_rand_score  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from real_adapters import RealClusteringAnalyzer, RealDataPreprocessor  # noqa: E402
from visualization import UrbanVisualizationEngine  # noqa: E402

warnings.filterwarnings("ignore")
# static PNG export of plotly figures needs a headless browser; the interactive HTML is kept
go.Figure.write_image = lambda self, *a, **k: None

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data_real")
OUT = os.path.join(ROOT, "outputs_real")
REPORTS = os.path.join(OUT, "reports")
MAPS = os.path.join(OUT, "maps")

STRESS_COLS = {"Population_Density_Calc": 1, "Pollution_Load_Index_Calc": 1,
               "Traffic_Stress_Index": 1, "Green_Cover_Percentage": -1}


def stress_score(df):
    z = pd.DataFrame({c: s * (df[c] - df[c].mean()) / df[c].std(ddof=0) for c, s in STRESS_COLS.items()})
    return z.mean(axis=1)


def polygon_map(df, geojson, value_col, title, path, cmap_name, categorical=False):
    m = folium.Map(location=[18.5204, 73.8567], zoom_start=11, tiles="CartoDB positron")
    lookup = df.set_index("Ward_ID")
    for f in geojson["features"]:
        f["properties"]["tip"] = f"{f['properties']['Ward_Name']}: {lookup.loc[f['properties']['Ward_ID'], value_col]}"
    if categorical:
        palette = ["#e15759", "#4e79a7", "#59a14f", "#f28e2b", "#b07aa1"]
        color = lambda wid: palette[int(lookup.loc[wid, value_col]) % len(palette)]
    else:
        vals = lookup[value_col].astype(float)
        lo, hi = vals.min(), vals.max()
        ramp = ["#ffffcc", "#fed976", "#fd8d3c", "#e31a1c", "#800026"]
        color = lambda wid: ramp[min(int((float(lookup.loc[wid, value_col]) - lo) / (hi - lo + 1e-9) * 5), 4)]
    folium.GeoJson(
        geojson,
        style_function=lambda f: {"fillColor": color(f["properties"]["Ward_ID"]), "color": "#333",
                                  "weight": 1, "fillOpacity": 0.7},
        tooltip=folium.GeoJsonTooltip(fields=["tip"], labels=False),
    ).add_to(m)
    m.get_root().html.add_child(folium.Element(
        f'<div style="position:fixed;top:12px;left:60px;z-index:9999;background:white;padding:6px 10px;'
        f'border:1px solid #888;font:14px sans-serif"><b>{title}</b></div>'))
    m.save(path)


def corr_row(df, a, b):
    r, p = stats.pearsonr(df[a], df[b])
    rho, ps = stats.spearmanr(df[a], df[b])
    return {"pair": f"{a} vs {b}", "pearson_r": round(r, 3), "pearson_p": round(p, 4),
            "spearman_rho": round(rho, 3), "spearman_p": round(ps, 4), "n": int(len(df))}


def main():
    for d in (REPORTS, MAPS, os.path.join(OUT, "charts")):
        os.makedirs(d, exist_ok=True)
    started = datetime.now()

    print("=" * 60, "\nSTEP 1: preprocessing (real data)\n" + "=" * 60)
    pre = RealDataPreprocessor(DATA)
    processed = pre.run_preprocessing_pipeline()
    if not processed:
        sys.exit("Preprocessing failed - run 01 and 02 first.")

    print("=" * 60, "\nSTEP 2: clustering\n" + "=" * 60)
    res = RealClusteringAnalyzer(DATA, OUT).run_clustering_pipeline()
    clustered = res["result_dataframe"].copy()
    clustered["Stress_Score"] = stress_score(clustered)
    clustered.to_csv(os.path.join(DATA, "processed", "clustered_wards.csv"), index=False)

    print("=" * 60, "\nSTEP 3: visualisation\n" + "=" * 60)
    viz = UrbanVisualizationEngine(DATA, OUT)
    ds = viz.load_processed_data()
    main_df = ds["main"]
    steps = [
        ("traffic heatmap", lambda: viz.create_traffic_heatmap(main_df)),
        ("pollution heatmap", lambda: viz.create_pollution_heatmap(main_df)),
        ("green cover heatmap", lambda: viz.create_green_cover_heatmap(main_df)),
        ("AQI time series", lambda: viz.create_aqi_timeseries_plot(ds["timeseries"])),
        ("correlation heatmap", lambda: viz.create_correlation_heatmap(main_df)),
        ("ward comparison", lambda: viz.create_ward_comparison_dashboard(
            main_df, focus_wards=clustered.nlargest(5, "Stress_Score")["Ward_Name"].tolist())),
    ]
    for name, fn in steps:
        try:
            fn()
        except Exception as e:  # keep going; report at the end
            print(f"  ! {name} failed: {e}")

    geo = json.load(open(os.path.join(DATA, "spatial", "pune_ward_boundaries.geojson"), encoding="utf-8"))
    polygon_map(clustered, json.loads(json.dumps(geo)), "Cluster", "Ward clusters (K-Means, k=3)",
                os.path.join(MAPS, "ward_clusters_polygon_map.html"), None, categorical=True)
    polygon_map(clustered.round({"Stress_Score": 2}), json.loads(json.dumps(geo)), "Stress_Score",
                "Composite stress score (z-score mean)", os.path.join(MAPS, "stress_score_map.html"), None)
    fig = px.scatter(clustered, x="Congestion_Index", y="PM2_5", color=clustered["Cluster"].astype(str),
                     size="Population", hover_name="Ward_Name",
                     labels={"Congestion_Index": "Congestion proxy (people per road-km, scaled)",
                             "PM2_5": "PM2.5 (ug/m3, 2024-25 mean)", "color": "Cluster"},
                     title="Road-network pressure vs PM2.5 by ward (real data)")
    fig.write_html(os.path.join(OUT, "charts", "congestion_proxy_vs_pm25.html"))

    print("=" * 60, "\nSTEP 4: statistics and report\n" + "=" * 60)
    X = pd.read_csv(os.path.join(DATA, "processed", "processed_clustering.csv")).drop(columns=["Ward_ID", "Ward_Name"]).values
    base = KMeans(n_clusters=3, random_state=42, n_init=10).fit_predict(X)
    ari = [adjusted_rand_score(base, KMeans(n_clusters=3, random_state=s, n_init=10).fit_predict(X)) for s in range(100, 130)]
    sil = dict(zip(res["k_range"], np.round(res["silhouette_scores"], 3)))

    ind = ["Population_Density_Calc", "Pollution_Load_Index_Calc", "Traffic_Stress_Index",
           "Green_Cover_Percentage", "Infrastructure_Density_Calc", "AQI", "PM2_5", "Literacy_Rate"]
    prof = clustered.groupby("Cluster")[ind].mean().round(1)
    prof["wards"] = clustered.groupby("Cluster")["Ward_Name"].apply(lambda s: ", ".join(s))
    prof["n"] = clustered.groupby("Cluster").size()
    prof["mean_stress"] = clustered.groupby("Cluster")["Stress_Score"].mean().round(2)
    order = prof["mean_stress"].sort_values(ascending=False).index.tolist()
    names = dict(zip(order, ["Highest-stress group", "Intermediate group", "Lowest-stress group"]))

    corr = [corr_row(clustered, "Congestion_Index", "PM2_5"), corr_row(clustered, "Congestion_Index", "AQI"),
            corr_row(clustered, "Population_Density_Calc", "Pollution_Load_Index_Calc"),
            corr_row(clustered, "Green_Cover_Percentage", "Pollution_Load_Index_Calc")]
    top = clustered.nlargest(5, "Stress_Score")[["Ward_Name", "Stress_Score", "Cluster"]]
    prov = json.load(open(os.path.join(DATA, "provenance.json"), encoding="utf-8"))

    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "wards": int(len(clustered)), "k": 3,
        "silhouette_by_k": {int(k): float(v) for k, v in sil.items()},
        "pca_components": int(res["n_components"]), "pca_variance": round(float(res["total_variance_explained"]), 4),
        "stability_ari_mean": round(float(np.mean(ari)), 3), "stability_ari_min": round(float(np.min(ari)), 3),
        "correlations": corr,
        "clusters": {int(c): {"label": names[c], **{k: (v.item() if hasattr(v, "item") else v) for k, v in prof.loc[c].items()}} for c in prof.index},
        "top_stress_wards": top.to_dict("records"),
    }
    json.dump(summary, open(os.path.join(REPORTS, "real_data_summary.json"), "w", encoding="utf-8"), indent=2, ensure_ascii=False)

    L = ["# Real-data analysis - Pune administrative wards", "",
         f"Generated {summary['generated_at']}. Unit: {prov['unit_of_analysis']}.", "",
         "## Data actually used", ""]
    L += [f"- **{k}**: {v}" for k, v in prov["measured_or_official"].items()]
    L += ["", "### Proxies (not measurements)", ""] + [f"- **{k}**: {v}" for k, v in prov["proxies_not_measurements"].items()]
    L += ["", "### Not available", "", ", ".join(prov["not_available"]), "", "## Clustering (K-Means, k = 3)", "",
          f"- Silhouette by k: {', '.join(f'k={k}: {v}' for k, v in sil.items())}",
          f"- PCA: {summary['pca_components']} components explain {summary['pca_variance']:.1%} of variance",
          f"- Stability over 30 re-seeded runs (adjusted Rand index vs. seed 42): mean {summary['stability_ari_mean']}, min {summary['stability_ari_min']}", ""]
    L += ["| Group | Wards | n | Pop. density | Pollution load | Congestion proxy | Green % | Mean stress z |", "|---|---|---|---|---|---|---|---|"]
    for c in order:
        r = prof.loc[c]
        L.append(f"| {names[c]} (cluster {c}) | {r['wards']} | {int(r['n'])} | {r['Population_Density_Calc']:.0f} | "
                 f"{r['Pollution_Load_Index_Calc']:.0f} | {r['Traffic_Stress_Index']:.0f} | {r['Green_Cover_Percentage']:.1f} | {r['mean_stress']} |")
    L += ["", "## Highest composite stress (z-score mean of density, pollution load, congestion proxy, low green)", ""]
    L += [f"{i}. {r.Ward_Name} ({r.Stress_Score:.2f}, cluster {r.Cluster})" for i, r in enumerate(top.itertuples(), 1)]
    L += ["", f"## Correlations (n = {len(clustered)})", "", "| Pair | Pearson r | p | Spearman rho | p |", "|---|---|---|---|---|"]
    L += [f"| {c['pair']} | {c['pearson_r']} | {c['pearson_p']} | {c['spearman_rho']} | {c['spearman_p']} |" for c in corr]
    L += ["", "## Limitations", ""] + [f"- {x}" for x in prov["limitations"]]
    L += ["- The congestion proxy is derived from population and road length, so its correlation with population density is partly built in.",
          "- Correlations on a small number of neighbouring wards are affected by spatial autocorrelation and are indicative only."]
    open(os.path.join(REPORTS, "real_data_report.md"), "w", encoding="utf-8").write("\n".join(L))

    print("\n".join(L))
    print(f"\nDone in {(datetime.now() - started).seconds}s. Outputs in outputs_real/ and data_real/processed/.")


if __name__ == "__main__":
    main()
