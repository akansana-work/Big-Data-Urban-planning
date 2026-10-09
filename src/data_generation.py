"""
Data Generation Module for Pune Urban Planning Analysis
Generates realistic simulated data for Pune city wards across multiple domains.
"""

import pandas as pd
import numpy as np
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

# Set random seed for reproducibility
np.random.seed(42)

class PuneDataGenerator:
    """Generate realistic simulated data for Pune city wards."""
    
    def __init__(self):
        # Pune ward names (34 major wards)
        self.pune_wards = [
            "Shivajinagar", "Kothrud", "Warje-Malwadi", "Bibwewadi", "Dhankawadi",
            "Sahakarnagar", "Baner", "Aundh", "Pune Cantonment", "Camp",
            "Koregaon Park", "Yerwada", "Kalyani Nagar", "Viman Nagar", "Hadapsar",
            "Kharadi", "Wagholi", "Mundhwa", "Undri", "Kondhwa",
            "Wanowrie", "Salisbury Park", "Gultekdi", "Dhayari", "Narhe",
            "Sus", "Pashan", "Bavdhan", "Hinjewadi", "Wakad",
            "Pimpri-Chinchwad", "Nigdi", "Akurdi", "Chinchwad"
        ]
        
        # Define ward characteristics for realistic data generation
        self.ward_profiles = {
            # Commercial/IT hubs - High traffic, moderate pollution, low green cover
            "Shivajinagar": {"type": "commercial", "development_level": "high"},
            "Hinjewadi": {"type": "it_hub", "development_level": "high"},
            "Baner": {"type": "it_hub", "development_level": "high"},
            "Aundh": {"type": "it_hub", "development_level": "medium"},
            "Viman Nagar": {"type": "commercial", "development_level": "high"},
            "Koregaon Park": {"type": "commercial", "development_level": "high"},
            
            # Residential planned areas - Moderate traffic, low pollution, high green cover
            "Kothrud": {"type": "residential_planned", "development_level": "medium"},
            "Wakad": {"type": "residential_planned", "development_level": "medium"},
            "Sus": {"type": "residential_planned", "development_level": "low"},
            "Pashan": {"type": "residential_planned", "development_level": "low"},
            "Bavdhan": {"type": "residential_planned", "development_level": "medium"},
            
            # Dense residential/mixed - High traffic, high pollution, low green cover
            "Camp": {"type": "dense_mixed", "development_level": "high"},
            "Pune Cantonment": {"type": "dense_mixed", "development_level": "high"},
            "Bibwewadi": {"type": "dense_mixed", "development_level": "medium"},
            "Sahakarnagar": {"type": "dense_mixed", "development_level": "medium"},
        }
        
        # Set default profile for wards not explicitly defined
        for ward in self.pune_wards:
            if ward not in self.ward_profiles:
                self.ward_profiles[ward] = {"type": "residential_mixed", "development_level": "medium"}
    
    def generate_ward_boundaries(self) -> pd.DataFrame:
        """Generate simulated ward boundary data with coordinates."""
        ward_data = []
        
        # Pune approximate bounds: 18.4088° N to 18.6298° N, 73.7394° E to 73.9617° E
        lat_min, lat_max = 18.4088, 18.6298
        lon_min, lon_max = 73.7394, 73.9617
        
        for i, ward in enumerate(self.pune_wards):
            # Generate random but realistic coordinates within Pune bounds
            center_lat = np.random.uniform(lat_min, lat_max)
            center_lon = np.random.uniform(lon_min, lon_max)
            
            # Generate area based on ward type
            profile = self.ward_profiles[ward]
            if profile["type"] == "commercial":
                area = np.random.uniform(2, 8)  # km²
            elif profile["type"] == "it_hub":
                area = np.random.uniform(5, 15)  # km²
            elif profile["type"] == "residential_planned":
                area = np.random.uniform(8, 20)  # km²
            else:
                area = np.random.uniform(3, 12)  # km²
            
            ward_data.append({
                "Ward_ID": f"PUN_{i+1:03d}",
                "Ward_Name": ward,
                "Center_Latitude": round(center_lat, 6),
                "Center_Longitude": round(center_lon, 6),
                "Area_sqkm": round(area, 2),
                "Ward_Type": profile["type"],
                "Development_Level": profile["development_level"]
            })
        
        return pd.DataFrame(ward_data)
    
    def generate_demographics_data(self, ward_df: pd.DataFrame) -> pd.DataFrame:
        """Generate demographic data for each ward."""
        demo_data = []
        
        for _, ward in ward_df.iterrows():
            profile = self.ward_profiles[ward["Ward_Name"]]
            area = ward["Area_sqkm"]
            
            # Population based on ward type and area
            if profile["type"] == "commercial":
                pop_density = np.random.uniform(15000, 25000)  # per km²
            elif profile["type"] == "it_hub":
                pop_density = np.random.uniform(8000, 15000)
            elif profile["type"] == "residential_planned":
                pop_density = np.random.uniform(5000, 12000)
            elif profile["type"] == "dense_mixed":
                pop_density = np.random.uniform(20000, 35000)
            else:
                pop_density = np.random.uniform(10000, 18000)
            
            population = int(pop_density * area)
            
            # Generate other demographic metrics
            demo_data.append({
                "Ward_ID": ward["Ward_ID"],
                "Ward_Name": ward["Ward_Name"],
                "Population": population,
                "Population_Density": round(population / area, 2),
                "Households": int(population / 4.2),  # Average household size in Maharashtra
                "Literacy_Rate": round(np.random.uniform(75, 95), 1),
                "Average_Income": int(np.random.uniform(25000, 80000)),
                "Senior_Citizens_Pct": round(np.random.uniform(8, 18), 1),
                "Children_Pct": round(np.random.uniform(15, 28), 1)
            })
        
        return pd.DataFrame(demo_data)
    
    def generate_traffic_data(self, ward_df: pd.DataFrame) -> pd.DataFrame:
        """Generate traffic and transportation data."""
        traffic_data = []
        
        for _, ward in ward_df.iterrows():
            profile = self.ward_profiles[ward["Ward_Name"]]
            
            # Traffic intensity based on ward type
            if profile["type"] in ["commercial", "it_hub"]:
                congestion_index = np.random.uniform(70, 95)
                peak_hour_volume = np.random.uniform(8000, 15000)
                avg_speed = np.random.uniform(15, 30)
            elif profile["type"] == "dense_mixed":
                congestion_index = np.random.uniform(60, 85)
                peak_hour_volume = np.random.uniform(5000, 10000)
                avg_speed = np.random.uniform(20, 35)
            else:
                congestion_index = np.random.uniform(30, 60)
                peak_hour_volume = np.random.uniform(2000, 6000)
                avg_speed = np.random.uniform(35, 50)
            
            traffic_data.append({
                "Ward_ID": ward["Ward_ID"],
                "Ward_Name": ward["Ward_Name"],
                "Congestion_Index": round(congestion_index, 1),
                "Peak_Hour_Volume": int(peak_hour_volume),
                "Average_Speed_kmh": round(avg_speed, 1),
                "Public_Transport_Access": round(np.random.uniform(3, 10), 1),
                "Parking_Availability": round(np.random.uniform(20, 80), 1),
                "Road_Network_Density": round(np.random.uniform(5, 25), 2)
            })
        
        return pd.DataFrame(traffic_data)
    
    def generate_pollution_data(self, ward_df: pd.DataFrame) -> pd.DataFrame:
        """Generate air and noise pollution data."""
        pollution_data = []
        
        for _, ward in ward_df.iterrows():
            profile = self.ward_profiles[ward["Ward_Name"]]
            
            # Pollution levels based on ward type
            if profile["type"] in ["commercial", "dense_mixed"]:
                pm25 = np.random.uniform(45, 85)
                pm10 = np.random.uniform(80, 150)
                no2 = np.random.uniform(35, 65)
                noise_level = np.random.uniform(65, 85)
            elif profile["type"] == "it_hub":
                pm25 = np.random.uniform(35, 60)
                pm10 = np.random.uniform(60, 100)
                no2 = np.random.uniform(25, 45)
                noise_level = np.random.uniform(55, 75)
            else:
                pm25 = np.random.uniform(25, 45)
                pm10 = np.random.uniform(40, 70)
                no2 = np.random.uniform(15, 35)
                noise_level = np.random.uniform(45, 65)
            
            # Calculate AQI (simplified)
            aqi = max(pm25 * 2, pm10 * 1.5, no2 * 3)
            
            pollution_data.append({
                "Ward_ID": ward["Ward_ID"],
                "Ward_Name": ward["Ward_Name"],
                "PM2_5": round(pm25, 1),
                "PM10": round(pm10, 1),
                "NO2": round(no2, 1),
                "SO2": round(np.random.uniform(5, 25), 1),
                "AQI": round(aqi, 1),
                "Noise_Level_dB": round(noise_level, 1),
                "Pollution_Load_Index": round(pm25 + pm10 + no2, 1)
            })
        
        return pd.DataFrame(pollution_data)
    
    def generate_green_cover_data(self, ward_df: pd.DataFrame) -> pd.DataFrame:
        """Generate green cover and environmental data."""
        green_data = []
        
        for _, ward in ward_df.iterrows():
            profile = self.ward_profiles[ward["Ward_Name"]]
            
            # Green cover based on ward type
            if profile["type"] == "residential_planned":
                green_cover_pct = np.random.uniform(25, 45)
                tree_count_per_sqkm = np.random.uniform(800, 1500)
            elif profile["type"] in ["commercial", "dense_mixed"]:
                green_cover_pct = np.random.uniform(5, 20)
                tree_count_per_sqkm = np.random.uniform(200, 600)
            elif profile["type"] == "it_hub":
                green_cover_pct = np.random.uniform(15, 30)
                tree_count_per_sqkm = np.random.uniform(400, 1000)
            else:
                green_cover_pct = np.random.uniform(10, 25)
                tree_count_per_sqkm = np.random.uniform(300, 800)
            
            green_data.append({
                "Ward_ID": ward["Ward_ID"],
                "Ward_Name": ward["Ward_Name"],
                "Green_Cover_Percentage": round(green_cover_pct, 1),
                "Tree_Count_per_sqkm": int(tree_count_per_sqkm),
                "Parks_Count": np.random.randint(2, 15),
                "Water_Bodies_Count": np.random.randint(0, 5),
                "Open_Spaces_sqkm": round(ward_df.loc[ward_df["Ward_ID"] == ward["Ward_ID"], "Area_sqkm"].iloc[0] * green_cover_pct / 100, 2)
            })
        
        return pd.DataFrame(green_data)
    
    def generate_infrastructure_data(self, ward_df: pd.DataFrame) -> pd.DataFrame:
        """Generate infrastructure and amenities data."""
        infra_data = []
        
        for _, ward in ward_df.iterrows():
            profile = self.ward_profiles[ward["Ward_Name"]]
            area = ward["Area_sqkm"]
            
            # Infrastructure density based on development level
            if profile["development_level"] == "high":
                schools = np.random.randint(8, 20)
                hospitals = np.random.randint(3, 10)
                banks = np.random.randint(5, 15)
                malls = np.random.randint(2, 8)
            elif profile["development_level"] == "medium":
                schools = np.random.randint(4, 12)
                hospitals = np.random.randint(1, 6)
                banks = np.random.randint(2, 8)
                malls = np.random.randint(0, 4)
            else:
                schools = np.random.randint(2, 8)
                hospitals = np.random.randint(1, 3)
                banks = np.random.randint(1, 4)
                malls = np.random.randint(0, 2)
            
            total_amenities = schools + hospitals + banks + malls
            
            infra_data.append({
                "Ward_ID": ward["Ward_ID"],
                "Ward_Name": ward["Ward_Name"],
                "Schools": schools,
                "Hospitals": hospitals,
                "Banks": banks,
                "Shopping_Malls": malls,
                "Total_Amenities": total_amenities,
                "Infrastructure_Density": round(total_amenities / area, 2),
                "Water_Supply_Hours": np.random.randint(12, 24),
                "Electricity_Reliability_Pct": round(np.random.uniform(85, 98), 1),
                "Internet_Connectivity_Pct": round(np.random.uniform(70, 95), 1)
            })
        
        return pd.DataFrame(infra_data)
    
    def generate_time_series_data(self, ward_df: pd.DataFrame, days: int = 365) -> pd.DataFrame:
        """Generate time series data for AQI and traffic patterns."""
        time_series_data = []
        start_date = datetime.now() - timedelta(days=days)
        
        # Select a subset of wards for time series to keep data manageable
        selected_wards = ["Shivajinagar", "Kothrud", "Hinjewadi", "Camp", "Aundh"]
        
        for ward_name in selected_wards:
            ward_info = ward_df[ward_df["Ward_Name"] == ward_name].iloc[0]
            profile = self.ward_profiles[ward_name]
            
            # Base values for the ward
            if profile["type"] in ["commercial", "dense_mixed"]:
                base_aqi = np.random.uniform(60, 90)
                base_congestion = np.random.uniform(70, 90)
            elif profile["type"] == "it_hub":
                base_aqi = np.random.uniform(45, 65)
                base_congestion = np.random.uniform(50, 70)
            else:
                base_aqi = np.random.uniform(30, 50)
                base_congestion = np.random.uniform(30, 50)
            
            for day in range(days):
                current_date = start_date + timedelta(days=day)
                
                # Add seasonal variations
                seasonal_factor = 1 + 0.3 * np.sin(2 * np.pi * day / 365)
                
                # Add weekly patterns (weekends lower)
                weekly_factor = 0.7 if current_date.weekday() >= 5 else 1.0
                
                # Add random noise
                noise = np.random.normal(0, 0.1)
                
                aqi_value = base_aqi * seasonal_factor * weekly_factor * (1 + noise)
                congestion_value = base_congestion * weekly_factor * (1 + noise)
                
                time_series_data.append({
                    "Date": current_date.strftime("%Y-%m-%d"),
                    "Ward_ID": ward_info["Ward_ID"],
                    "Ward_Name": ward_name,
                    "AQI": round(max(10, aqi_value), 1),
                    "Congestion_Index": round(max(10, min(100, congestion_value)), 1),
                    "Temperature": round(np.random.uniform(20, 35), 1),
                    "Humidity": round(np.random.uniform(40, 80), 1)
                })
        
        return pd.DataFrame(time_series_data)
    
    def generate_geojson_boundaries(self, ward_df: pd.DataFrame) -> dict:
        """Generate simplified GeoJSON boundaries for wards."""
        features = []
        
        for _, ward in ward_df.iterrows():
            # Create a simple rectangular polygon around the center point
            center_lat = ward["Center_Latitude"]
            center_lon = ward["Center_Longitude"]
            
            # Calculate approximate offsets for a rectangular boundary
            lat_offset = 0.01  # Roughly 1km
            lon_offset = 0.01
            
            # Create rectangle coordinates
            coordinates = [[
                [center_lon - lon_offset, center_lat - lat_offset],
                [center_lon + lon_offset, center_lat - lat_offset],
                [center_lon + lon_offset, center_lat + lat_offset],
                [center_lon - lon_offset, center_lat + lat_offset],
                [center_lon - lon_offset, center_lat - lat_offset]
            ]]
            
            feature = {
                "type": "Feature",
                "properties": {
                    "Ward_ID": ward["Ward_ID"],
                    "Ward_Name": ward["Ward_Name"],
                    "Area_sqkm": ward["Area_sqkm"],
                    "Ward_Type": ward["Ward_Type"]
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": coordinates
                }
            }
            features.append(feature)
        
        return {
            "type": "FeatureCollection",
            "features": features
        }
    
    def generate_all_datasets(self, output_dir: str = "data"):
        """Generate all datasets and save to files."""
        print("Generating Pune Urban Planning Datasets...")
        
        # Create output directories if they don't exist
        raw_dir = os.path.join(output_dir, "raw")
        spatial_dir = os.path.join(output_dir, "spatial")
        os.makedirs(raw_dir, exist_ok=True)
        os.makedirs(spatial_dir, exist_ok=True)
        
        # 1. Generate ward boundaries
        print("1. Generating ward boundaries...")
        ward_df = self.generate_ward_boundaries()
        ward_df.to_csv(os.path.join(raw_dir, "pune_wards.csv"), index=False)
        
        # 2. Generate demographic data
        print("2. Generating demographic data...")
        demo_df = self.generate_demographics_data(ward_df)
        demo_df.to_csv(os.path.join(raw_dir, "pune_demographics.csv"), index=False)
        
        # 3. Generate traffic data
        print("3. Generating traffic data...")
        traffic_df = self.generate_traffic_data(ward_df)
        traffic_df.to_csv(os.path.join(raw_dir, "pune_traffic.csv"), index=False)
        
        # 4. Generate pollution data
        print("4. Generating pollution data...")
        pollution_df = self.generate_pollution_data(ward_df)
        pollution_df.to_csv(os.path.join(raw_dir, "pune_pollution.csv"), index=False)
        
        # 5. Generate green cover data
        print("5. Generating green cover data...")
        green_df = self.generate_green_cover_data(ward_df)
        green_df.to_csv(os.path.join(raw_dir, "pune_green_cover.csv"), index=False)
        
        # 6. Generate infrastructure data
        print("6. Generating infrastructure data...")
        infra_df = self.generate_infrastructure_data(ward_df)
        infra_df.to_csv(os.path.join(raw_dir, "pune_infrastructure.csv"), index=False)
        
        # 7. Generate time series data
        print("7. Generating time series data...")
        timeseries_df = self.generate_time_series_data(ward_df)
        timeseries_df.to_csv(os.path.join(raw_dir, "pune_timeseries.csv"), index=False)
        
        # 8. Generate GeoJSON boundaries
        print("8. Generating spatial boundaries...")
        geojson_data = self.generate_geojson_boundaries(ward_df)
        with open(os.path.join(spatial_dir, "pune_ward_boundaries.geojson"), "w") as f:
            json.dump(geojson_data, f, indent=2)
        
        print("✅ All datasets generated successfully!")
        print(f"📁 Raw data saved to: {raw_dir}")
        print(f"🗺️  Spatial data saved to: {spatial_dir}")
        
        return {
            "wards": ward_df,
            "demographics": demo_df,
            "traffic": traffic_df,
            "pollution": pollution_df,
            "green_cover": green_df,
            "infrastructure": infra_df,
            "timeseries": timeseries_df,
            "geojson": geojson_data
        }

if __name__ == "__main__":
    generator = PuneDataGenerator()
    datasets = generator.generate_all_datasets()
    print(f"\n📊 Generated data for {len(datasets['wards'])} Pune wards")
    print(f"📈 Time series data for {len(datasets['timeseries'])} records")
