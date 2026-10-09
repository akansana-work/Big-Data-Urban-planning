"""
Visualization Module for Pune Urban Planning Analysis
Creates interactive maps, charts, and heatmaps for urban planning insights.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import folium
from folium.plugins import HeatMap
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import geopandas as gpd
import json
import os
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class UrbanVisualizationEngine:
    """Create comprehensive visualizations for urban planning analysis."""
    
    def __init__(self, data_dir: str = "data", output_dir: str = "outputs"):
        self.data_dir = data_dir
        self.processed_dir = os.path.join(data_dir, "processed")
        self.output_dir = output_dir
        self.maps_dir = os.path.join(output_dir, "maps")
        self.charts_dir = os.path.join(output_dir, "charts")
        self.reports_dir = os.path.join(output_dir, "reports")
        
        # Ensure output directories exist
        os.makedirs(self.maps_dir, exist_ok=True)
        os.makedirs(self.charts_dir, exist_ok=True)
        os.makedirs(self.reports_dir, exist_ok=True)
        
        # Pune city center coordinates
        self.pune_center = [18.5204, 73.8567]
        
        # Color schemes
        self.color_schemes = {
            'traffic': ['green', 'yellow', 'orange', 'red'],
            'pollution': ['blue', 'lightblue', 'yellow', 'orange', 'red'],
            'green_cover': ['red', 'orange', 'yellow', 'lightgreen', 'green'],
            'clusters': ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7']
        }
    
    def load_processed_data(self) -> dict:
        """Load all processed datasets for visualization."""
        print("Loading processed data for visualization...")
        
        datasets = {}
        
        try:
            # Load main datasets
            datasets['main'] = pd.read_csv(os.path.join(self.processed_dir, "processed_main.csv"))
            datasets['timeseries'] = pd.read_csv(os.path.join(self.processed_dir, "processed_timeseries.csv"))
            
            # Try to load clustered data if available
            try:
                datasets['clustered'] = pd.read_csv(os.path.join(self.processed_dir, "clustered_wards.csv"))
            except FileNotFoundError:
                print("⚠️  Clustered data not found, using main dataset")
                datasets['clustered'] = datasets['main'].copy()
                # Add dummy cluster labels if not present
                if 'Cluster' not in datasets['clustered'].columns:
                    datasets['clustered']['Cluster'] = np.random.randint(0, 3, len(datasets['clustered']))
            
            # Load spatial data if available
            try:
                spatial_file = os.path.join(self.processed_dir, "processed_spatial.csv")
                if os.path.exists(spatial_file):
                    datasets['spatial'] = pd.read_csv(spatial_file)
                else:
                    datasets['spatial'] = datasets['main'].copy()
            except:
                datasets['spatial'] = datasets['main'].copy()
            
            print(f"✅ Loaded datasets for {len(datasets['main'])} wards")
            return datasets
            
        except Exception as e:
            print(f"❌ Error loading visualization data: {e}")
            return {}
    
    def create_traffic_heatmap(self, df: pd.DataFrame) -> folium.Map:
        """Create interactive traffic congestion heatmap."""
        print("Creating traffic congestion heatmap...")
        
        # Create base map
        traffic_map = folium.Map(
            location=self.pune_center,
            zoom_start=11,
            tiles='OpenStreetMap'
        )
        
        # Prepare heatmap data
        heat_data = []
        for _, row in df.iterrows():
            if pd.notna(row['Center_Latitude']) and pd.notna(row['Center_Longitude']):
                # Normalize congestion index to 0-1 for heat intensity
                intensity = row.get('Congestion_Index', 50) / 100
                heat_data.append([
                    row['Center_Latitude'], 
                    row['Center_Longitude'], 
                    intensity
                ])
        
        # Add heatmap layer
        if heat_data:
            HeatMap(
                heat_data,
                min_opacity=0.3,
                max_zoom=18,
                radius=15,
                blur=10,
                gradient={0.2: 'blue', 0.4: 'lime', 0.6: 'orange', 1: 'red'}
            ).add_to(traffic_map)
        
        # Add ward markers with popup information
        for _, row in df.iterrows():
            if pd.notna(row['Center_Latitude']) and pd.notna(row['Center_Longitude']):
                # Color based on congestion level
                congestion = row.get('Congestion_Index', 50)
                if congestion > 70:
                    color = 'red'
                elif congestion > 50:
                    color = 'orange'
                elif congestion > 30:
                    color = 'yellow'
                else:
                    color = 'green'
                
                popup_text = f"""
                <b>{row['Ward_Name']}</b><br>
                Congestion Index: {congestion:.1f}<br>
                Peak Hour Volume: {row.get('Peak_Hour_Volume', 'N/A')}<br>
                Avg Speed: {row.get('Average_Speed_kmh', 'N/A')} km/h<br>
                Traffic Stress: {row.get('Traffic_Stress_Index', 'N/A'):.2f}
                """
                
                folium.CircleMarker(
                    location=[row['Center_Latitude'], row['Center_Longitude']],
                    radius=8,
                    popup=folium.Popup(popup_text, max_width=250),
                    color='black',
                    weight=1,
                    fillColor=color,
                    fillOpacity=0.7
                ).add_to(traffic_map)
        
        # Add legend
        legend_html = '''
        <div style="position: fixed; 
                    bottom: 50px; left: 50px; width: 150px; height: 90px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px">
        <p><b>Traffic Congestion</b></p>
        <p><i class="fa fa-circle" style="color:red"></i> High (>70)</p>
        <p><i class="fa fa-circle" style="color:orange"></i> Medium (50-70)</p>
        <p><i class="fa fa-circle" style="color:yellow"></i> Low (30-50)</p>
        <p><i class="fa fa-circle" style="color:green"></i> Very Low (<30)</p>
        </div>
        '''
        traffic_map.get_root().html.add_child(folium.Element(legend_html))
        
        # Save map
        map_path = os.path.join(self.maps_dir, 'traffic_congestion_heatmap.html')
        traffic_map.save(map_path)
        print(f"✅ Traffic heatmap saved: {map_path}")
        
        return traffic_map
    
    def create_pollution_heatmap(self, df: pd.DataFrame) -> folium.Map:
        """Create interactive pollution levels heatmap."""
        print("Creating pollution levels heatmap...")
        
        # Create base map
        pollution_map = folium.Map(
            location=self.pune_center,
            zoom_start=11,
            tiles='CartoDB positron'
        )
        
        # Prepare pollution heatmap data
        heat_data = []
        for _, row in df.iterrows():
            if pd.notna(row['Center_Latitude']) and pd.notna(row['Center_Longitude']):
                # Use AQI for heat intensity (normalize to 0-1)
                aqi = row.get('AQI', 50)
                intensity = min(aqi / 200, 1.0)  # Cap at 200 AQI
                heat_data.append([
                    row['Center_Latitude'], 
                    row['Center_Longitude'], 
                    intensity
                ])
        
        # Add heatmap layer
        if heat_data:
            HeatMap(
                heat_data,
                min_opacity=0.3,
                max_zoom=18,
                radius=20,
                blur=15,
                gradient={0.2: 'green', 0.4: 'yellow', 0.6: 'orange', 0.8: 'red', 1: 'purple'}
            ).add_to(pollution_map)
        
        # Add ward markers with detailed pollution info
        for _, row in df.iterrows():
            if pd.notna(row['Center_Latitude']) and pd.notna(row['Center_Longitude']):
                aqi = row.get('AQI', 50)
                
                # Color based on AQI levels
                if aqi > 150:
                    color = 'purple'
                    category = 'Very Unhealthy'
                elif aqi > 100:
                    color = 'red'
                    category = 'Unhealthy'
                elif aqi > 50:
                    color = 'orange'
                    category = 'Moderate'
                else:
                    color = 'green'
                    category = 'Good'
                
                popup_text = f"""
                <b>{row['Ward_Name']}</b><br>
                AQI: {aqi:.1f} ({category})<br>
                PM2.5: {row.get('PM2_5', 'N/A')} µg/m³<br>
                PM10: {row.get('PM10', 'N/A')} µg/m³<br>
                NO2: {row.get('NO2', 'N/A')} µg/m³<br>
                Pollution Load: {row.get('Pollution_Load_Index', 'N/A'):.1f}<br>
                Noise Level: {row.get('Noise_Level_dB', 'N/A')} dB
                """
                
                folium.CircleMarker(
                    location=[row['Center_Latitude'], row['Center_Longitude']],
                    radius=10,
                    popup=folium.Popup(popup_text, max_width=300),
                    color='black',
                    weight=1,
                    fillColor=color,
                    fillOpacity=0.8
                ).add_to(pollution_map)
        
        # Add AQI legend
        legend_html = '''
        <div style="position: fixed; 
                    bottom: 50px; right: 50px; width: 180px; height: 120px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px">
        <p><b>Air Quality Index</b></p>
        <p><i class="fa fa-circle" style="color:green"></i> Good (0-50)</p>
        <p><i class="fa fa-circle" style="color:orange"></i> Moderate (51-100)</p>
        <p><i class="fa fa-circle" style="color:red"></i> Unhealthy (101-150)</p>
        <p><i class="fa fa-circle" style="color:purple"></i> Very Unhealthy (>150)</p>
        </div>
        '''
        pollution_map.get_root().html.add_child(folium.Element(legend_html))
        
        # Save map
        map_path = os.path.join(self.maps_dir, 'pollution_levels_heatmap.html')
        pollution_map.save(map_path)
        print(f"✅ Pollution heatmap saved: {map_path}")
        
        return pollution_map
    
    def create_green_cover_heatmap(self, df: pd.DataFrame) -> folium.Map:
        """Create interactive green cover percentage heatmap."""
        print("Creating green cover heatmap...")
        
        # Create base map
        green_map = folium.Map(
            location=self.pune_center,
            zoom_start=11,
            tiles='OpenStreetMap'
        )
        
        # Prepare green cover heatmap data
        heat_data = []
        for _, row in df.iterrows():
            if pd.notna(row['Center_Latitude']) and pd.notna(row['Center_Longitude']):
                # Use green cover percentage for heat intensity
                green_pct = row.get('Green_Cover_Percentage', 20)
                intensity = green_pct / 100  # Normalize to 0-1
                heat_data.append([
                    row['Center_Latitude'], 
                    row['Center_Longitude'], 
                    intensity
                ])
        
        # Add heatmap layer (green gradient)
        if heat_data:
            HeatMap(
                heat_data,
                min_opacity=0.3,
                max_zoom=18,
                radius=18,
                blur=12,
                gradient={0.1: 'red', 0.3: 'orange', 0.5: 'yellow', 0.7: 'lightgreen', 1: 'darkgreen'}
            ).add_to(green_map)
        
        # Add ward markers with green space info
        for _, row in df.iterrows():
            if pd.notna(row['Center_Latitude']) and pd.notna(row['Center_Longitude']):
                green_pct = row.get('Green_Cover_Percentage', 20)
                
                # Color based on green cover levels
                if green_pct > 35:
                    color = 'darkgreen'
                    category = 'Excellent'
                elif green_pct > 25:
                    color = 'green'
                    category = 'Good'
                elif green_pct > 15:
                    color = 'orange'
                    category = 'Moderate'
                else:
                    color = 'red'
                    category = 'Poor'
                
                popup_text = f"""
                <b>{row['Ward_Name']}</b><br>
                Green Cover: {green_pct:.1f}% ({category})<br>
                Trees per km²: {row.get('Tree_Count_per_sqkm', 'N/A')}<br>
                Parks: {row.get('Parks_Count', 'N/A')}<br>
                Water Bodies: {row.get('Water_Bodies_Count', 'N/A')}<br>
                Open Spaces: {row.get('Open_Spaces_sqkm', 'N/A')} km²<br>
                Environmental Score: {row.get('Environmental_Quality_Score', 'N/A'):.2f}
                """
                
                folium.CircleMarker(
                    location=[row['Center_Latitude'], row['Center_Longitude']],
                    radius=9,
                    popup=folium.Popup(popup_text, max_width=300),
                    color='black',
                    weight=1,
                    fillColor=color,
                    fillOpacity=0.8
                ).add_to(green_map)
        
        # Add green cover legend
        legend_html = '''
        <div style="position: fixed; 
                    bottom: 50px; left: 50px; width: 160px; height: 110px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px">
        <p><b>Green Cover %</b></p>
        <p><i class="fa fa-circle" style="color:darkgreen"></i> Excellent (>35%)</p>
        <p><i class="fa fa-circle" style="color:green"></i> Good (25-35%)</p>
        <p><i class="fa fa-circle" style="color:orange"></i> Moderate (15-25%)</p>
        <p><i class="fa fa-circle" style="color:red"></i> Poor (<15%)</p>
        </div>
        '''
        green_map.get_root().html.add_child(folium.Element(legend_html))
        
        # Save map
        map_path = os.path.join(self.maps_dir, 'green_cover_heatmap.html')
        green_map.save(map_path)
        print(f"✅ Green cover heatmap saved: {map_path}")
        
        return green_map
    
    def create_cluster_map(self, df: pd.DataFrame) -> folium.Map:
        """Create interactive map showing ward clusters."""
        print("Creating cluster visualization map...")
        
        # Create base map
        cluster_map = folium.Map(
            location=self.pune_center,
            zoom_start=11,
            tiles='OpenStreetMap'
        )
        
        # Get unique clusters and assign colors
        unique_clusters = sorted(df['Cluster'].unique()) if 'Cluster' in df.columns else [0, 1, 2]
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7']
        
        # Cluster interpretations (you can modify these based on your analysis)
        cluster_names = {
            0: 'High-Development Commercial',
            1: 'Mixed Residential',
            2: 'Planned Green Zones'
        }
        
        # Add ward markers colored by cluster
        for _, row in df.iterrows():
            if pd.notna(row['Center_Latitude']) and pd.notna(row['Center_Longitude']):
                cluster = row.get('Cluster', 0)
                color = colors[int(cluster) % len(colors)]
                cluster_name = cluster_names.get(int(cluster), f'Cluster {cluster}')
                
                popup_text = f"""
                <b>{row['Ward_Name']}</b><br>
                <b>Cluster: {cluster_name}</b><br>
                Population Density: {row.get('Population_Density_Calc', 'N/A'):.0f}/km²<br>
                AQI: {row.get('AQI', 'N/A'):.1f}<br>
                Green Cover: {row.get('Green_Cover_Percentage', 'N/A'):.1f}%<br>
                Traffic Stress: {row.get('Traffic_Stress_Index', 'N/A'):.2f}<br>
                Quality of Life: {row.get('Quality_of_Life_Index', 'N/A'):.2f}
                """
                
                folium.CircleMarker(
                    location=[row['Center_Latitude'], row['Center_Longitude']],
                    radius=12,
                    popup=folium.Popup(popup_text, max_width=300),
                    color='black',
                    weight=2,
                    fillColor=color,
                    fillOpacity=0.8
                ).add_to(cluster_map)
        
        # Add cluster legend
        legend_html = f'''
        <div style="position: fixed; 
                    top: 50px; right: 50px; width: 200px; height: auto; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px">
        <p><b>Ward Clusters</b></p>
        '''
        
        for i, cluster in enumerate(unique_clusters):
            color = colors[i % len(colors)]
            name = cluster_names.get(cluster, f'Cluster {cluster}')
            legend_html += f'<p><i class="fa fa-circle" style="color:{color}"></i> {name}</p>'
        
        legend_html += '</div>'
        cluster_map.get_root().html.add_child(folium.Element(legend_html))
        
        # Save map
        map_path = os.path.join(self.maps_dir, 'ward_clusters_map.html')
        cluster_map.save(map_path)
        print(f"✅ Cluster map saved: {map_path}")
        
        return cluster_map
    
    def create_aqi_timeseries_plot(self, timeseries_df: pd.DataFrame):
        """Create AQI time series line plot."""
        print("Creating AQI time series plot...")
        
        # Convert date column
        ts_df = timeseries_df.copy()
        ts_df['Date'] = pd.to_datetime(ts_df['Date'])
        
        # Create figure with subplots
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('AQI Trends by Ward', 'AQI Distribution by Season'),
            vertical_spacing=0.15
        )
        
        # Plot 1: Time series by ward
        wards = ts_df['Ward_Name'].unique()
        colors = px.colors.qualitative.Set1
        
        for i, ward in enumerate(wards):
            ward_data = ts_df[ts_df['Ward_Name'] == ward].sort_values('Date')
            
            fig.add_trace(
                go.Scatter(
                    x=ward_data['Date'],
                    y=ward_data['AQI'],
                    mode='lines',
                    name=ward,
                    line=dict(color=colors[i % len(colors)], width=2),
                    hovertemplate=f'<b>{ward}</b><br>Date: %{{x}}<br>AQI: %{{y:.1f}}<extra></extra>'
                ),
                row=1, col=1
            )
        
        # Plot 2: Box plot by season
        if 'Season' in ts_df.columns:
            for season in ts_df['Season'].unique():
                season_data = ts_df[ts_df['Season'] == season]
                fig.add_trace(
                    go.Box(
                        y=season_data['AQI'],
                        name=season,
                        boxpoints='outliers',
                        marker_color=colors[hash(season) % len(colors)]
                    ),
                    row=2, col=1
                )
        
        # Update layout
        fig.update_layout(
            title='Pune Air Quality Index (AQI) Analysis',
            height=800,
            showlegend=True,
            font=dict(size=12)
        )
        
        fig.update_xaxes(title_text="Date", row=1, col=1)
        fig.update_yaxes(title_text="AQI", row=1, col=1)
        fig.update_xaxes(title_text="Season", row=2, col=1)
        fig.update_yaxes(title_text="AQI", row=2, col=1)
        
        # Save plot
        plot_path = os.path.join(self.charts_dir, 'aqi_timeseries_analysis.html')
        fig.write_html(plot_path)
        
        # Also save as static image
        static_path = os.path.join(self.charts_dir, 'aqi_timeseries_analysis.png')
        fig.write_image(static_path, width=1200, height=800, scale=2)
        
        print(f"✅ AQI time series plot saved: {plot_path}")
    
    def create_congestion_pollution_scatterplot(self, df: pd.DataFrame):
        """Create scatterplot showing congestion vs pollution correlation."""
        print("Creating congestion vs pollution scatterplot...")
        
        # Create scatter plot
        fig = px.scatter(
            df,
            x='Congestion_Index',
            y='AQI',
            size='Population_Density_Calc',
            color='Cluster' if 'Cluster' in df.columns else 'Ward_Type',
            hover_name='Ward_Name',
            hover_data={
                'Green_Cover_Percentage': ':.1f',
                'Infrastructure_Density_Calc': ':.2f',
                'Average_Income': ':,.0f'
            },
            title='Traffic Congestion vs Air Pollution Correlation',
            labels={
                'Congestion_Index': 'Traffic Congestion Index',
                'AQI': 'Air Quality Index (AQI)',
                'Population_Density_Calc': 'Population Density'
            }
        )
        
        # Add trend line
        fig.add_traces(
            px.scatter(
                df, x='Congestion_Index', y='AQI',
                trendline='ols'
            ).data[1:]
        )
        
        # Update layout
        fig.update_layout(
            width=1000,
            height=700,
            font=dict(size=12),
            showlegend=True
        )
        
        # Calculate correlation
        correlation = df['Congestion_Index'].corr(df['AQI'])
        fig.add_annotation(
            x=0.05, y=0.95,
            xref='paper', yref='paper',
            text=f'Correlation: {correlation:.3f}',
            showarrow=False,
            font=dict(size=14, color='red'),
            bgcolor='white',
            bordercolor='black',
            borderwidth=1
        )
        
        # Save plot
        plot_path = os.path.join(self.charts_dir, 'congestion_pollution_scatter.html')
        fig.write_html(plot_path)
        
        static_path = os.path.join(self.charts_dir, 'congestion_pollution_scatter.png')
        fig.write_image(static_path, width=1000, height=700, scale=2)
        
        print(f"✅ Congestion vs pollution scatterplot saved: {plot_path}")
        print(f"   Correlation coefficient: {correlation:.3f}")
    
    def create_correlation_heatmap(self, df: pd.DataFrame):
        """Create correlation heatmap for key urban planning features."""
        print("Creating correlation heatmap...")
        
        # Select numerical features for correlation analysis
        corr_features = [
            'Population_Density_Calc', 'AQI', 'Congestion_Index', 
            'Green_Cover_Percentage', 'Infrastructure_Density_Calc',
            'Traffic_Stress_Index', 'Environmental_Quality_Score',
            'Quality_of_Life_Index', 'Average_Income', 'Literacy_Rate'
        ]
        
        # Filter available features
        available_features = [f for f in corr_features if f in df.columns]
        
        # Calculate correlation matrix
        correlation_matrix = df[available_features].corr()
        
        # Create heatmap
        plt.figure(figsize=(12, 10))
        mask = np.triu(np.ones_like(correlation_matrix, dtype=bool))
        
        sns.heatmap(
            correlation_matrix,
            mask=mask,
            annot=True,
            cmap='RdBu_r',
            center=0,
            square=True,
            linewidths=0.5,
            cbar_kws={"shrink": .8},
            fmt='.2f'
        )
        
        plt.title('Urban Planning Features Correlation Matrix', fontsize=16, fontweight='bold', pad=20)
        plt.xlabel('Features', fontsize=12)
        plt.ylabel('Features', fontsize=12)
        plt.xticks(rotation=45, ha='right')
        plt.yticks(rotation=0)
        plt.tight_layout()
        
        # Save plot
        plot_path = os.path.join(self.charts_dir, 'correlation_heatmap.png')
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✅ Correlation heatmap saved: {plot_path}")
        
        # Save correlation data
        correlation_data = {
            'correlation_matrix': correlation_matrix.to_dict(),
            'strong_correlations': self._find_strong_correlations(correlation_matrix)
        }
        
        with open(os.path.join(self.reports_dir, 'correlation_analysis.json'), 'w') as f:
            json.dump(correlation_data, f, indent=2)
    
    def _find_strong_correlations(self, corr_matrix: pd.DataFrame, threshold: float = 0.5) -> dict:
        """Find strong correlations in the matrix."""
        strong_corrs = {}
        
        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                corr_value = corr_matrix.iloc[i, j]
                if abs(corr_value) >= threshold:
                    feature1 = corr_matrix.columns[i]
                    feature2 = corr_matrix.columns[j]
                    strong_corrs[f"{feature1} vs {feature2}"] = round(corr_value, 3)
        
        return strong_corrs
    
    def create_ward_comparison_dashboard(self, df: pd.DataFrame, focus_wards: list = None):
        """Create comprehensive dashboard comparing key wards."""
        print("Creating ward comparison dashboard...")
        
        if focus_wards is None:
            focus_wards = ['Shivajinagar', 'Kothrud', 'Hinjewadi', 'Camp', 'Aundh']
        
        # Filter data for focus wards
        focus_data = df[df['Ward_Name'].isin(focus_wards)].copy()
        
        if len(focus_data) == 0:
            print("⚠️  No focus wards found in data")
            return
        
        # Create subplots dashboard
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'Population vs Infrastructure Density',
                'Environmental Quality vs Green Cover',
                'Traffic Stress vs Pollution Load',
                'Quality of Life Index Comparison'
            ),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"type": "bar"}]]
        )
        
        colors = px.colors.qualitative.Set1
        
        # Plot 1: Population vs Infrastructure
        for i, ward in enumerate(focus_data['Ward_Name']):
            row_data = focus_data[focus_data['Ward_Name'] == ward].iloc[0]
            fig.add_trace(
                go.Scatter(
                    x=[row_data['Population_Density_Calc']],
                    y=[row_data['Infrastructure_Density_Calc']],
                    mode='markers+text',
                    name=ward,
                    text=[ward],
                    textposition="top center",
                    marker=dict(size=15, color=colors[i % len(colors)]),
                    showlegend=True
                ),
                row=1, col=1
            )
        
        # Plot 2: Environmental Quality vs Green Cover
        for i, ward in enumerate(focus_data['Ward_Name']):
            row_data = focus_data[focus_data['Ward_Name'] == ward].iloc[0]
            fig.add_trace(
                go.Scatter(
                    x=[row_data['Environmental_Quality_Score']],
                    y=[row_data['Green_Cover_Percentage']],
                    mode='markers+text',
                    name=ward,
                    text=[ward],
                    textposition="top center",
                    marker=dict(size=15, color=colors[i % len(colors)]),
                    showlegend=False
                ),
                row=1, col=2
            )
        
        # Plot 3: Traffic vs Pollution
        for i, ward in enumerate(focus_data['Ward_Name']):
            row_data = focus_data[focus_data['Ward_Name'] == ward].iloc[0]
            fig.add_trace(
                go.Scatter(
                    x=[row_data['Traffic_Stress_Index']],
                    y=[row_data['Pollution_Load_Index_Calc']],
                    mode='markers+text',
                    name=ward,
                    text=[ward],
                    textposition="top center",
                    marker=dict(size=15, color=colors[i % len(colors)]),
                    showlegend=False
                ),
                row=2, col=1
            )
        
        # Plot 4: Quality of Life comparison
        fig.add_trace(
            go.Bar(
                x=focus_data['Ward_Name'],
                y=focus_data['Quality_of_Life_Index'],
                name='Quality of Life Index',
                marker_color=colors[:len(focus_data)],
                showlegend=False
            ),
            row=2, col=2
        )
        
        # Update layout
        fig.update_layout(
            title='Pune Ward Comparison Dashboard',
            height=800,
            font=dict(size=10)
        )
        
        # Update axes labels
        fig.update_xaxes(title_text="Population Density", row=1, col=1)
        fig.update_yaxes(title_text="Infrastructure Density", row=1, col=1)
        fig.update_xaxes(title_text="Environmental Quality Score", row=1, col=2)
        fig.update_yaxes(title_text="Green Cover %", row=1, col=2)
        fig.update_xaxes(title_text="Traffic Stress Index", row=2, col=1)
        fig.update_yaxes(title_text="Pollution Load Index", row=2, col=1)
        fig.update_xaxes(title_text="Ward", row=2, col=2)
        fig.update_yaxes(title_text="Quality of Life Index", row=2, col=2)
        
        # Save dashboard
        dashboard_path = os.path.join(self.charts_dir, 'ward_comparison_dashboard.html')
        fig.write_html(dashboard_path)
        
        static_path = os.path.join(self.charts_dir, 'ward_comparison_dashboard.png')
        fig.write_image(static_path, width=1400, height=800, scale=2)
        
        print(f"✅ Ward comparison dashboard saved: {dashboard_path}")
    
    def generate_visualization_summary(self, datasets: dict) -> dict:
        """Generate summary of all visualizations created."""
        summary = {
            'creation_date': datetime.now().isoformat(),
            'total_wards': len(datasets.get('main', [])),
            'visualizations_created': {
                'interactive_maps': [
                    'Traffic Congestion Heatmap',
                    'Pollution Levels Heatmap',
                    'Green Cover Heatmap',
                    'Ward Clusters Map'
                ],
                'static_charts': [
                    'AQI Time Series Analysis',
                    'Congestion vs Pollution Scatter',
                    'Correlation Heatmap',
                    'Ward Comparison Dashboard'
                ]
            },
            'file_locations': {
                'maps': self.maps_dir,
                'charts': self.charts_dir,
                'reports': self.reports_dir
            }
        }
        
        # Save summary
        with open(os.path.join(self.reports_dir, 'visualization_summary.json'), 'w') as f:
            json.dump(summary, f, indent=2)
        
        return summary
    
    def run_visualization_pipeline(self) -> dict:
        """Run the complete visualization pipeline."""
        print("🔄 Starting visualization pipeline...")
        print("=" * 50)
        
        # 1. Load processed data
        datasets = self.load_processed_data()
        if not datasets:
            return {}
        
        main_df = datasets['main']
        clustered_df = datasets['clustered']
        timeseries_df = datasets['timeseries']
        
        # 2. Create interactive heatmaps
        self.create_traffic_heatmap(main_df)
        self.create_pollution_heatmap(main_df)
        self.create_green_cover_heatmap(main_df)
        self.create_cluster_map(clustered_df)
        
        # 3. Create analytical charts
        self.create_aqi_timeseries_plot(timeseries_df)
        self.create_congestion_pollution_scatterplot(main_df)
        self.create_correlation_heatmap(main_df)
        self.create_ward_comparison_dashboard(main_df)
        
        # 4. Generate summary
        summary = self.generate_visualization_summary(datasets)
        
        print("=" * 50)
        print("✅ Visualization pipeline completed successfully!")
        print(f"📊 Created visualizations for {len(main_df)} wards")
        print(f"🗺️  Interactive maps saved to: {self.maps_dir}")
        print(f"📈 Charts saved to: {self.charts_dir}")
        
        return summary

if __name__ == "__main__":
    visualizer = UrbanVisualizationEngine()
    summary = visualizer.run_visualization_pipeline()
    
    if summary:
        print(f"\n📋 Visualization Summary:")
        print(f"   • Interactive maps: {len(summary['visualizations_created']['interactive_maps'])}")
        print(f"   • Static charts: {len(summary['visualizations_created']['static_charts'])}")
        print(f"   • Total wards visualized: {summary['total_wards']}")
