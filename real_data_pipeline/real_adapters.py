"""
Thin subclasses that let the existing pipeline classes (src/preprocessing.py,
src/clustering.py) run on the real-data tables. The files in src/ are NOT modified.

Why subclasses are needed
  * The real tables have no income, peak-hour volume, water supply or electricity columns,
    so the engineered-feature step and the clustering feature list are adjusted.
  * The original cluster labelling compares raw averages with 0-1 thresholds (it expects
    scaled values), so on real data every cluster would get the same label. Here clusters are
    described relative to the overall mean instead.
"""

import os
import sys

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from preprocessing import UrbanDataPreprocessor  # noqa: E402
from clustering import UrbanClusteringAnalyzer  # noqa: E402

CLUSTER_FEATURES = [
    "Population_Density_Calc", "Pollution_Load_Index_Calc", "Infrastructure_Density_Calc",
    "Traffic_Stress_Index", "Environmental_Quality_Score", "Green_Cover_Percentage",
    "AQI", "Road_Network_Density", "Literacy_Rate", "Total_Amenities",
]


class RealDataPreprocessor(UrbanDataPreprocessor):
    """Same stages as the original; features limited to what the real sources provide."""

    def engineer_features(self, datasets: dict) -> pd.DataFrame:
        print("Engineering features (real data)...")
        df = datasets["wards"].copy()
        for key in ("demographics", "traffic", "pollution", "green_cover", "infrastructure"):
            df = df.merge(datasets[key], on=["Ward_ID", "Ward_Name"], how="left")
        df = self.handle_missing_values(df)

        df["Population_Density_Calc"] = df["Population"] / df["Area_sqkm"]
        df["Pollution_Load_Index_Calc"] = df["PM2_5"] + df["PM10"] + df["NO2"]
        df["Infrastructure_Density_Calc"] = df["Total_Amenities"] / df["Area_sqkm"]
        df["Green_Space_Per_Capita"] = df["Open_Spaces_sqkm"] * 1_000_000 / df["Population"]
        # Congestion_Index is already a proxy (people per road-km); no volume column exists
        df["Traffic_Stress_Index"] = df["Congestion_Index"]
        df["Environmental_Quality_Score"] = (100 - df["AQI"]) * 0.5 + df["Green_Cover_Percentage"] * 0.5
        # Reduced index: only the three components that can be computed from real data,
        # re-weighted to sum to 1 (the simulated version also used water and electricity).
        df["Quality_of_Life_Index"] = (
            df["Environmental_Quality_Score"] * 0.3
            + (100 - df["Traffic_Stress_Index"]) * 0.2
            + df["Green_Space_Per_Capita"] / 10 * 0.2
        ) / 0.7
        print(f"Feature engineering completed. Total columns: {len(df.columns)}")
        return df

    def prepare_clustering_features(self, df: pd.DataFrame):
        print("Preparing features for clustering (real data)...")
        feats = [f for f in CLUSTER_FEATURES if f in df.columns]
        out = df[["Ward_ID", "Ward_Name"] + feats].copy()
        out = self.handle_missing_values(out)
        scaler = MinMaxScaler()
        out[feats] = scaler.fit_transform(out[feats])
        import joblib
        joblib.dump(scaler, os.path.join(self.processed_dir, "clustering_scaler.pkl"))
        print(f"Prepared {len(feats)} features for clustering")
        return out, feats


class RealClusteringAnalyzer(UrbanClusteringAnalyzer):
    """Clustering identical to the original; cluster description made relative to the mean."""

    STRESS_UP = ("Population_Density_Calc", "Pollution_Load_Index_Calc", "Traffic_Stress_Index")
    STRESS_DOWN = ("Green_Cover_Percentage",)

    def interpret_clusters(self, clustering_df, main_df, cluster_labels, feature_names):
        cols = [c for c in (*self.STRESS_UP, *self.STRESS_DOWN, "Infrastructure_Density_Calc") if c in main_df]
        self._mu, self._sd = main_df[cols].mean(), main_df[cols].std(ddof=0).replace(0, 1)
        return super().interpret_clusters(clustering_df, main_df, cluster_labels, feature_names)

    def _z(self, features: dict) -> dict:
        return {k: (features[k] - self._mu[k]) / self._sd[k] for k in self._mu.index if k in features}

    def _interpret_cluster_type(self, feature_means: dict) -> dict:
        z = self._z(feature_means)
        notes = []
        for k, label in (("Population_Density_Calc", "population density"),
                         ("Pollution_Load_Index_Calc", "pollution load"),
                         ("Traffic_Stress_Index", "congestion proxy"),
                         ("Green_Cover_Percentage", "green cover"),
                         ("Infrastructure_Density_Calc", "amenity density")):
            if k in z and abs(z[k]) >= 0.5:
                notes.append(f"{'high' if z[k] > 0 else 'low'} {label}")
        return {"type": "Cluster (described relative to the ward mean)",
                "characteristics": notes or ["close to the mean on all indicators"],
                "description": "Auto-generated from z-scores against the overall mean."}

    def _get_key_characteristics(self, features: dict) -> list:
        return self._interpret_cluster_type(features)["characteristics"]

    def _get_planning_recommendations(self, features: dict) -> list:
        z, recs = self._z(features), []
        if z.get("Pollution_Load_Index_Calc", 0) > 0.5:
            recs.append("Higher-than-average pollution load: prioritise air-quality monitoring and controls")
        if z.get("Traffic_Stress_Index", 0) > 0.5:
            recs.append("High demand on the road network: prioritise public transport and traffic management")
        if z.get("Green_Cover_Percentage", 0) < -0.5:
            recs.append("Low green cover: prioritise parks and tree planting")
        if z.get("Infrastructure_Density_Calc", 0) < -0.5:
            recs.append("Low amenity density: prioritise schools, clinics and services")
        return recs

    def _create_cluster_profiles(self, result_df, key_features):
        # the radar chart axis is fixed to 0-1, so scale each indicator across wards first
        feats = [f for f in key_features if f in result_df.columns]
        scaled = result_df.copy()
        rng = (scaled[feats].max() - scaled[feats].min()).replace(0, 1)
        scaled[feats] = (scaled[feats] - scaled[feats].min()) / rng
        super()._create_cluster_profiles(scaled, feats)
