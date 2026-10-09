"""
Data Preprocessing Module for Pune Urban Planning Analysis
Handles data cleaning, feature engineering, and spatial data integration.
"""

import pandas as pd
import numpy as np
import geopandas as gpd
from sklearn.preprocessing import MinMaxScaler
from sklearn.impute import SimpleImputer
import json
import os
import warnings
warnings.filterwarnings('ignore')

class UrbanDataPreprocessor:
    """Handle all data preprocessing tasks for urban planning analysis."""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.raw_dir = os.path.join(data_dir, "raw")
        self.processed_dir = os.path.join(data_dir, "processed")
        self.spatial_dir = os.path.join(data_dir, "spatial")
        
        # Ensure processed directory exists
        os.makedirs(self.processed_dir, exist_ok=True)
        
        # Initialize scalers
        self.scaler = MinMaxScaler()
        self.imputer = SimpleImputer(strategy='median')
        
    def load_raw_datasets(self) -> dict:
        """Load all raw datasets."""
        print("Loading raw datasets...")
        
        datasets = {}
        
        try:
            datasets['wards'] = pd.read_csv(os.path.join(self.raw_dir, "pune_wards.csv"))
            datasets['demographics'] = pd.read_csv(os.path.join(self.raw_dir, "pune_demographics.csv"))
            datasets['traffic'] = pd.read_csv(os.path.join(self.raw_dir, "pune_traffic.csv"))
            datasets['pollution'] = pd.read_csv(os.path.join(self.raw_dir, "pune_pollution.csv"))
            datasets['green_cover'] = pd.read_csv(os.path.join(self.raw_dir, "pune_green_cover.csv"))
            datasets['infrastructure'] = pd.read_csv(os.path.join(self.raw_dir, "pune_infrastructure.csv"))
            datasets['timeseries'] = pd.read_csv(os.path.join(self.raw_dir, "pune_timeseries.csv"))
            
            # Load GeoJSON
            with open(os.path.join(self.spatial_dir, "pune_ward_boundaries.geojson"), 'r') as f:
                datasets['geojson'] = json.load(f)
            
            print("✅ All raw datasets loaded successfully!")
            return datasets
            
        except Exception as e:
            print(f"❌ Error loading datasets: {e}")
            return {}
    
    def handle_missing_values(self, df: pd.DataFrame, strategy: str = 'median') -> pd.DataFrame:
        """Handle missing values in the dataset."""
        print(f"Handling missing values using {strategy} strategy...")
        
        # Separate numeric and non-numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        categorical_cols = df.select_dtypes(exclude=[np.number]).columns
        
        df_clean = df.copy()
        
        # Handle numeric columns
        if len(numeric_cols) > 0:
            if strategy == 'median':
                imputer = SimpleImputer(strategy='median')
            elif strategy == 'mean':
                imputer = SimpleImputer(strategy='mean')
            else:
                imputer = SimpleImputer(strategy='constant', fill_value=0)
            
            df_clean[numeric_cols] = imputer.fit_transform(df_clean[numeric_cols])
        
        # Handle categorical columns
        if len(categorical_cols) > 0:
            cat_imputer = SimpleImputer(strategy='most_frequent')
            df_clean[categorical_cols] = cat_imputer.fit_transform(df_clean[categorical_cols])
        
        # Report missing values
        missing_before = df.isnull().sum().sum()
        missing_after = df_clean.isnull().sum().sum()
        print(f"Missing values: {missing_before} → {missing_after}")
        
        return df_clean
    
    def engineer_features(self, datasets: dict) -> pd.DataFrame:
        """Create engineered features as specified in requirements."""
        print("Engineering features...")
        
        # Start with ward base data
        base_df = datasets['wards'].copy()
        
        # Add demographic features
        demo_df = datasets['demographics'].copy()
        base_df = base_df.merge(demo_df, on=['Ward_ID', 'Ward_Name'], how='left')
        
        # Add traffic features
        traffic_df = datasets['traffic'].copy()
        base_df = base_df.merge(traffic_df, on=['Ward_ID', 'Ward_Name'], how='left')
        
        # Add pollution features
        pollution_df = datasets['pollution'].copy()
        base_df = base_df.merge(pollution_df, on=['Ward_ID', 'Ward_Name'], how='left')
        
        # Add green cover features
        green_df = datasets['green_cover'].copy()
        base_df = base_df.merge(green_df, on=['Ward_ID', 'Ward_Name'], how='left')
        
        # Add infrastructure features
        infra_df = datasets['infrastructure'].copy()
        base_df = base_df.merge(infra_df, on=['Ward_ID', 'Ward_Name'], how='left')
        
        # Handle missing values
        base_df = self.handle_missing_values(base_df)
        
        # Feature Engineering as per requirements
        print("Creating engineered features...")
        
        # 1. Population_Density = Population / Area (already exists, but recalculate for consistency)
        base_df['Population_Density_Calc'] = base_df['Population'] / base_df['Area_sqkm']
        
        # 2. Pollution_Load_Index = PM2.5 + PM10 + NO2 (already exists, but recalculate)
        base_df['Pollution_Load_Index_Calc'] = base_df['PM2_5'] + base_df['PM10'] + base_df['NO2']
        
        # 3. Infrastructure_Density = Total amenities / Area (already exists, but recalculate)
        base_df['Infrastructure_Density_Calc'] = base_df['Total_Amenities'] / base_df['Area_sqkm']
        
        # Additional engineered features for better analysis
        # 4. Green Space Per Capita
        base_df['Green_Space_Per_Capita'] = (base_df['Open_Spaces_sqkm'] * 1000000) / base_df['Population']  # m² per person
        
        # 5. Traffic Stress Index (combination of congestion and volume)
        base_df['Traffic_Stress_Index'] = (base_df['Congestion_Index'] * 0.6) + (base_df['Peak_Hour_Volume'] / 1000 * 0.4)
        
        # 6. Environmental Quality Score (inverse of pollution, positive for green cover)
        base_df['Environmental_Quality_Score'] = (100 - base_df['AQI']) * 0.5 + base_df['Green_Cover_Percentage'] * 0.5
        
        # 7. Urban Development Index (composite score)
        base_df['Urban_Development_Index'] = (
            base_df['Infrastructure_Density_Calc'] * 0.3 +
            base_df['Population_Density_Calc'] / 1000 * 0.2 +
            base_df['Average_Income'] / 1000 * 0.3 +
            base_df['Literacy_Rate'] * 0.2
        )
        
        # 8. Quality of Life Index
        base_df['Quality_of_Life_Index'] = (
            base_df['Environmental_Quality_Score'] * 0.3 +
            (100 - base_df['Traffic_Stress_Index']) * 0.2 +
            base_df['Green_Space_Per_Capita'] / 10 * 0.2 +
            base_df['Water_Supply_Hours'] / 24 * 100 * 0.15 +
            base_df['Electricity_Reliability_Pct'] * 0.15
        )
        
        print(f"✅ Feature engineering completed. Total features: {len(base_df.columns)}")
        return base_df
    
    def normalize_features(self, df: pd.DataFrame, exclude_cols: list = None) -> pd.DataFrame:
        """Apply Min-Max normalization to numerical features."""
        print("Applying Min-Max normalization...")
        
        if exclude_cols is None:
            exclude_cols = ['Ward_ID', 'Ward_Name', 'Ward_Type', 'Development_Level', 
                          'Center_Latitude', 'Center_Longitude']
        
        df_normalized = df.copy()
        
        # Get numerical columns to normalize
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        cols_to_normalize = [col for col in numeric_cols if col not in exclude_cols]
        
        if cols_to_normalize:
            # Fit and transform
            scaler = MinMaxScaler()
            df_normalized[cols_to_normalize] = scaler.fit_transform(df[cols_to_normalize])
            
            # Save scaler for future use
            import joblib
            joblib.dump(scaler, os.path.join(self.processed_dir, 'feature_scaler.pkl'))
            
            print(f"✅ Normalized {len(cols_to_normalize)} numerical features")
        
        return df_normalized, cols_to_normalize
    
    def create_spatial_dataframe(self, df: pd.DataFrame, geojson_data: dict) -> gpd.GeoDataFrame:
        """Create a GeoPandas DataFrame by joining tabular data with spatial boundaries."""
        print("Creating spatial dataframe...")
        
        # Convert GeoJSON to GeoDataFrame
        gdf = gpd.GeoDataFrame.from_features(geojson_data['features'])
        
        # Merge with processed data
        spatial_df = gdf.merge(df, on=['Ward_ID', 'Ward_Name'], how='left')
        
        # Set CRS (assuming WGS84)
        spatial_df.crs = "EPSG:4326"
        
        print(f"✅ Created spatial dataframe with {len(spatial_df)} wards")
        return spatial_df
    
    def prepare_clustering_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare features specifically for clustering analysis."""
        print("Preparing features for clustering...")
        
        # Select key features for clustering based on the urban planning objectives
        clustering_features = [
            'Population_Density_Calc',
            'Pollution_Load_Index_Calc',
            'Infrastructure_Density_Calc',
            'Traffic_Stress_Index',
            'Environmental_Quality_Score',
            'Green_Cover_Percentage',
            'AQI',
            'Congestion_Index',
            'Average_Income',
            'Total_Amenities'
        ]
        
        # Ensure all features exist
        available_features = [f for f in clustering_features if f in df.columns]
        if len(available_features) != len(clustering_features):
            missing = set(clustering_features) - set(available_features)
            print(f"⚠️  Missing features for clustering: {missing}")
        
        # Create clustering dataset
        clustering_df = df[['Ward_ID', 'Ward_Name'] + available_features].copy()
        
        # Handle any remaining missing values
        clustering_df = self.handle_missing_values(clustering_df)
        
        # Normalize features for clustering
        feature_cols = available_features
        scaler = MinMaxScaler()
        clustering_df[feature_cols] = scaler.fit_transform(clustering_df[feature_cols])
        
        # Save clustering scaler
        import joblib
        joblib.dump(scaler, os.path.join(self.processed_dir, 'clustering_scaler.pkl'))
        
        print(f"✅ Prepared {len(available_features)} features for clustering")
        return clustering_df, available_features
    
    def process_time_series_data(self, timeseries_df: pd.DataFrame) -> pd.DataFrame:
        """Process time series data for temporal analysis."""
        print("Processing time series data...")
        
        ts_df = timeseries_df.copy()
        
        # Convert date column
        ts_df['Date'] = pd.to_datetime(ts_df['Date'])
        
        # Extract temporal features
        ts_df['Year'] = ts_df['Date'].dt.year
        ts_df['Month'] = ts_df['Date'].dt.month
        ts_df['DayOfWeek'] = ts_df['Date'].dt.dayofweek
        ts_df['DayOfYear'] = ts_df['Date'].dt.dayofyear
        ts_df['IsWeekend'] = ts_df['DayOfWeek'].isin([5, 6]).astype(int)
        
        # Create seasonal indicators
        ts_df['Season'] = ts_df['Month'].map({
            12: 'Winter', 1: 'Winter', 2: 'Winter',
            3: 'Spring', 4: 'Spring', 5: 'Spring',
            6: 'Summer', 7: 'Summer', 8: 'Summer',
            9: 'Monsoon', 10: 'Monsoon', 11: 'Post-Monsoon'
        })
        
        # Calculate moving averages
        ts_df = ts_df.sort_values(['Ward_Name', 'Date'])
        for ward in ts_df['Ward_Name'].unique():
            mask = ts_df['Ward_Name'] == ward
            ts_df.loc[mask, 'AQI_7day_MA'] = ts_df.loc[mask, 'AQI'].rolling(window=7, min_periods=1).mean()
            ts_df.loc[mask, 'AQI_30day_MA'] = ts_df.loc[mask, 'AQI'].rolling(window=30, min_periods=1).mean()
        
        print(f"✅ Processed time series data: {len(ts_df)} records")
        return ts_df
    
    def save_processed_data(self, datasets: dict):
        """Save all processed datasets."""
        print("Saving processed datasets...")
        
        for name, data in datasets.items():
            if name == 'spatial':
                # Save spatial data as both GeoJSON and Parquet
                data.to_file(os.path.join(self.processed_dir, f"processed_{name}.geojson"), driver='GeoJSON')
                # Remove geometry for CSV export
                df_no_geom = data.drop(columns=['geometry'])
                df_no_geom.to_csv(os.path.join(self.processed_dir, f"processed_{name}.csv"), index=False)
            elif isinstance(data, pd.DataFrame):
                data.to_csv(os.path.join(self.processed_dir, f"processed_{name}.csv"), index=False)
            else:
                # Handle other data types if needed
                with open(os.path.join(self.processed_dir, f"processed_{name}.json"), 'w') as f:
                    json.dump(data, f, indent=2)
        
        print(f"✅ All processed datasets saved to: {self.processed_dir}")
    
    def generate_data_summary(self, df: pd.DataFrame) -> dict:
        """Generate comprehensive data summary."""
        print("Generating data summary...")
        
        summary = {
            'basic_info': {
                'total_wards': len(df),
                'total_features': len(df.columns),
                'data_completeness': (1 - df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100
            },
            'ward_types': df['Ward_Type'].value_counts().to_dict(),
            'development_levels': df['Development_Level'].value_counts().to_dict(),
            'feature_statistics': {}
        }
        
        # Key feature statistics
        key_features = [
            'Population', 'Population_Density_Calc', 'AQI', 'Congestion_Index',
            'Green_Cover_Percentage', 'Infrastructure_Density_Calc',
            'Environmental_Quality_Score', 'Quality_of_Life_Index'
        ]
        
        for feature in key_features:
            if feature in df.columns:
                summary['feature_statistics'][feature] = {
                    'mean': round(df[feature].mean(), 2),
                    'std': round(df[feature].std(), 2),
                    'min': round(df[feature].min(), 2),
                    'max': round(df[feature].max(), 2),
                    'median': round(df[feature].median(), 2)
                }
        
        # Save summary
        with open(os.path.join(self.processed_dir, 'data_summary.json'), 'w') as f:
            json.dump(summary, f, indent=2)
        
        print("✅ Data summary generated")
        return summary
    
    def run_preprocessing_pipeline(self) -> dict:
        """Run the complete preprocessing pipeline."""
        print("🔄 Starting preprocessing pipeline...")
        print("=" * 50)
        
        # 1. Load raw datasets
        raw_datasets = self.load_raw_datasets()
        if not raw_datasets:
            return {}
        
        # 2. Engineer features
        processed_df = self.engineer_features(raw_datasets)
        
        # 3. Normalize features
        normalized_df, normalized_features = self.normalize_features(processed_df)
        
        # 4. Create spatial dataframe
        spatial_df = self.create_spatial_dataframe(processed_df, raw_datasets['geojson'])
        
        # 5. Prepare clustering features
        clustering_df, clustering_features = self.prepare_clustering_features(processed_df)
        
        # 6. Process time series data
        timeseries_df = self.process_time_series_data(raw_datasets['timeseries'])
        
        # 7. Generate data summary
        summary = self.generate_data_summary(processed_df)
        
        # 8. Prepare final datasets
        processed_datasets = {
            'main': processed_df,
            'normalized': normalized_df,
            'spatial': spatial_df,
            'clustering': clustering_df,
            'timeseries': timeseries_df,
            'summary': summary
        }
        
        # 9. Save processed data
        self.save_processed_data(processed_datasets)
        
        print("=" * 50)
        print("✅ Preprocessing pipeline completed successfully!")
        print(f"📊 Processed {len(processed_df)} wards with {len(processed_df.columns)} features")
        print(f"🎯 Prepared {len(clustering_features)} features for clustering")
        print(f"📈 Processed {len(timeseries_df)} time series records")
        
        return processed_datasets

if __name__ == "__main__":
    preprocessor = UrbanDataPreprocessor()
    processed_data = preprocessor.run_preprocessing_pipeline()
    
    if processed_data:
        print("\n📋 Processing Summary:")
        print(f"   • Main dataset: {len(processed_data['main'])} wards")
        print(f"   • Spatial features: {len(processed_data['spatial'])} geometries")
        print(f"   • Clustering ready: {len(processed_data['clustering'])} records")
        print(f"   • Time series: {len(processed_data['timeseries'])} data points")
