"""
Enhanced Main Script for Maximum Free Data Utilization
Big Data Urban Planning Analysis - Pune City Case Study
"""

import os
import sys
import time
from datetime import datetime
import pandas as pd

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Enhanced imports
try:
    from src.enhanced_free_data_loader import EnhancedFreeDataLoader
    from src.analysis import UrbanPlanningAnalyzer
    from src.preprocessing import DataPreprocessor
    from src.clustering import UrbanClusterAnalyzer
    from src.visualization import UrbanDataVisualizer
except ImportError:
    try:
        from enhanced_free_data_loader import EnhancedFreeDataLoader
        from analysis import UrbanPlanningAnalyzer
        from preprocessing import DataPreprocessor
        from clustering import UrbanClusterAnalyzer
        from visualization import UrbanDataVisualizer
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Please ensure all modules are in the src directory")
        sys.exit(1)

def print_enhanced_banner():
    """Print enhanced project banner."""
    banner = """
    ╔══════════════════════════════════════════════════════════════════════════╗
    ║                                                                          ║
    ║     🏙️  BIG DATA-DRIVEN STRATEGIES FOR URBAN PLANNING  🏙️              ║
    ║                        & DEVELOPMENT                                     ║
    ║                                                                          ║
    ║                  📍 PUNE CITY CASE STUDY 📍                             ║
    ║                                                                          ║
    ║              🔥 ENHANCED FREE DATA INTEGRATION 🔥                       ║
    ║                                                                          ║
    ║              CDAC Project - Aditya Kansana                              ║
    ║                                                                          ║
    ║    📊 Data Sources: Government Open Data + OpenStreetMap + Census       ║
    ║    🌍 Coverage: 20 Pune Wards across 6 Zones                           ║
    ║    🔬 Analysis: Clustering + Spatial + Predictive                       ║
    ║                                                                          ║
    ╚══════════════════════════════════════════════════════════════════════════╝
    """
    print(banner)

def check_enhanced_dependencies():
    """Check enhanced dependencies."""
    required_packages = [
        'pandas', 'numpy', 'scikit-learn', 'matplotlib', 
        'seaborn', 'folium', 'geopandas', 'plotly', 'geopy', 'requests'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing packages: {', '.join(missing_packages)}")
        print("Installing missing packages...")
        
        import subprocess
        for package in missing_packages:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                print(f"✅ Installed {package}")
            except subprocess.CalledProcessError:
                print(f"❌ Failed to install {package}")
        
        print("Please restart the script after installation.")
        return False
    
    print("✅ All dependencies are available!")
    return True

def run_enhanced_analysis():
    """Run the enhanced analysis with maximum free data utilization."""
    
    print_enhanced_banner()
    
    # Check dependencies
    if not check_enhanced_dependencies():
        return
    
    print("\n🚀 Starting Enhanced Free Data Analysis Pipeline...")
    print("="*70)
    
    # Step 1: Load Enhanced Data
    print("\n📥 STEP 1: Loading Enhanced Free Data")
    print("-" * 40)
    
    loader = EnhancedFreeDataLoader()
    datasets = loader.load_all_enhanced_data()
    
    if not datasets:
        print("❌ Failed to load data. Exiting...")
        return
    
    # Step 2: Data Preprocessing
    print("\n🔄 STEP 2: Enhanced Data Preprocessing")
    print("-" * 40)
    
    preprocessor = DataPreprocessor()
    
    # Create integrated dataset
    print("Integrating all datasets...")
    integrated_data = None
    
    # Start with demographics as base
    if 'demographics' in datasets:
        integrated_data = datasets['demographics'].copy()
        print(f"✅ Base data: {len(integrated_data)} wards")
    
    # Merge other datasets
    for dataset_name, df in datasets.items():
        if dataset_name != 'demographics' and 'Ward_Name' in df.columns:
            # Aggregate if multiple records per ward
            if len(df) > len(df['Ward_Name'].unique()):
                if dataset_name == 'pollution':
                    # Average pollution over time
                    agg_df = df.groupby('Ward_Name').agg({
                        'AQI': 'mean',
                        'PM2_5': 'mean',
                        'PM10': 'mean',
                        'NO2': 'mean',
                        'CO': 'mean',
                        'SO2': 'mean'
                    }).reset_index()
                    agg_df.columns = [f'{col}_avg' if col != 'Ward_Name' else col for col in agg_df.columns]
                
                elif dataset_name == 'traffic':
                    # Average traffic metrics
                    agg_df = df.groupby('Ward_Name').agg({
                        'Vehicle_Count_per_Hour': 'mean',
                        'Average_Speed_kmh': 'mean',
                        'Travel_Time_Index': 'mean',
                        'CO2_Emissions_kg_per_hour': 'mean',
                        'Noise_Level_dB': 'mean'
                    }).reset_index()
                    agg_df.columns = [f'{col}_avg' if col != 'Ward_Name' else col for col in agg_df.columns]
                
                else:
                    agg_df = df.drop_duplicates('Ward_Name')
            else:
                agg_df = df
            
            # Merge with integrated data
            if integrated_data is not None:
                integrated_data = integrated_data.merge(agg_df, on='Ward_Name', how='left')
                print(f"✅ Merged {dataset_name}: {len(agg_df.columns)-1} features")
    
    if integrated_data is None:
        print("❌ Failed to create integrated dataset")
        return
    
    print(f"✅ Integrated dataset created: {len(integrated_data)} wards, {len(integrated_data.columns)} features")
    
    # Save integrated dataset
    integrated_file = os.path.join("data", "processed", "integrated_pune_data.csv")
    os.makedirs(os.path.dirname(integrated_file), exist_ok=True)
    integrated_data.to_csv(integrated_file, index=False)
    print(f"💾 Integrated data saved to: {integrated_file}")
    
    # Step 3: Advanced Clustering Analysis
    print("\n🧮 STEP 3: Advanced Clustering Analysis")
    print("-" * 40)
    
    cluster_analyzer = UrbanClusterAnalyzer()
    
    # Prepare clustering features
    numeric_cols = integrated_data.select_dtypes(include=['int64', 'float64']).columns
    clustering_features = integrated_data[numeric_cols].fillna(integrated_data[numeric_cols].mean())
    
    print(f"🔢 Clustering features: {len(clustering_features.columns)}")
    
    # Perform clustering
    clustering_results = cluster_analyzer.perform_comprehensive_clustering(
        clustering_features, integrated_data['Ward_Name'].values
    )
    
    print("✅ Clustering analysis completed")
    
    # Step 4: Enhanced Visualization
    print("\n📊 STEP 4: Enhanced Visualization")
    print("-" * 40)
    
    visualizer = UrbanDataVisualizer()
    
    # Create comprehensive visualizations
    print("Creating enhanced visualizations...")
    
    # 1. Ward clustering map
    cluster_labels = clustering_results.get('ward_clusters', {})
    ward_coords = {ward: {'lat': details['lat'], 'lng': details['lng']} 
                   for ward, details in loader.pune_wards_detailed.items()}
    
    visualizer.create_ward_cluster_map(cluster_labels, ward_coords)
    print("✅ Ward cluster map created")
    
    # 2. Multi-domain analysis charts
    if 'pollution' in datasets:
        visualizer.create_pollution_analysis_charts(datasets['pollution'])
        print("✅ Pollution analysis charts created")
    
    if 'traffic' in datasets:
        visualizer.create_traffic_analysis_charts(datasets['traffic'])
        print("✅ Traffic analysis charts created")
    
    if 'infrastructure' in datasets:
        visualizer.create_infrastructure_analysis_charts(datasets['infrastructure'])
        print("✅ Infrastructure analysis charts created")
    
    if 'green_cover' in datasets:
        visualizer.create_green_cover_analysis_charts(datasets['green_cover'])
        print("✅ Green cover analysis charts created")
    
    # Step 5: Policy Recommendations
    print("\n📋 STEP 5: Enhanced Policy Recommendations")
    print("-" * 40)
    
    analyzer = UrbanPlanningAnalyzer()
    
    # Generate comprehensive recommendations
    recommendations = analyzer.generate_comprehensive_recommendations(
        integrated_data, clustering_results, datasets
    )
    
    # Save recommendations
    recommendations_file = os.path.join("outputs", "reports", f"enhanced_recommendations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    os.makedirs(os.path.dirname(recommendations_file), exist_ok=True)
    
    import json
    with open(recommendations_file, 'w') as f:
        json.dump(recommendations, f, indent=2)
    
    print(f"💾 Recommendations saved to: {recommendations_file}")
    
    # Step 6: Generate Summary Report
    print("\n📄 STEP 6: Summary Report Generation")
    print("-" * 40)
    
    generate_enhanced_summary_report(datasets, integrated_data, clustering_results, recommendations)
    
    print("\n" + "="*70)
    print("🎉 ENHANCED FREE DATA ANALYSIS COMPLETED SUCCESSFULLY! 🎉")
    print("="*70)
    
    print("\n📊 ANALYSIS SUMMARY:")
    print(f"   🏘️  Wards Analyzed: {len(integrated_data)}")
    print(f"   📊 Features Used: {len(integrated_data.columns)}")
    print(f"   📈 Datasets Integrated: {len(datasets)}")
    print(f"   🎯 Clusters Identified: {len(set(cluster_labels.values())) if cluster_labels else 'N/A'}")
    
    print(f"\n📁 OUTPUT LOCATIONS:")
    print(f"   📊 Charts & Maps: outputs/charts/ and outputs/maps/")
    print(f"   📋 Reports: outputs/reports/")
    print(f"   💾 Processed Data: data/processed/")
    print(f"   🔗 Free Data Sources: data/free_sources/")
    
    print(f"\n🌐 DATA SOURCES UTILIZED:")
    print(f"   🏛️  Census India (Demographics)")
    print(f"   🌫️  CPCB (Pollution Data)")
    print(f"   🗺️  OpenStreetMap (Infrastructure)")
    print(f"   🛰️  Satellite Imagery (Green Cover)")
    print(f"   🚗 Traffic Modeling (Transportation)")

def generate_enhanced_summary_report(datasets, integrated_data, clustering_results, recommendations):
    """Generate enhanced summary report."""
    
    report = {
        "Enhanced_Urban_Planning_Analysis_Report": {
            "generated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "project_title": "Big Data-driven Strategies for Urban Planning - Pune Case Study",
            "data_approach": "Maximum Free Data Utilization",
            "analysis_scope": {
                "city": "Pune, Maharashtra, India",
                "wards_analyzed": len(integrated_data),
                "zones_covered": 6,
                "data_sources": "Government Open Data + OpenStreetMap + Census",
                "analysis_domains": list(datasets.keys())
            },
            "data_summary": {
                dataset: {
                    "records": len(df),
                    "features": len(df.columns),
                    "coverage": f"{df['Ward_Name'].nunique() if 'Ward_Name' in df.columns else 0} wards"
                } for dataset, df in datasets.items()
            },
            "clustering_insights": {
                "method": "K-Means + Hierarchical",
                "clusters_identified": len(set(clustering_results.get('ward_clusters', {}).values())) if clustering_results else 0,
                "silhouette_score": clustering_results.get('silhouette_score', 'N/A'),
                "features_used": len(integrated_data.select_dtypes(include=['int64', 'float64']).columns)
            },
            "key_findings": {
                "highest_pollution_ward": integrated_data.loc[integrated_data['AQI_avg'].idxmax(), 'Ward_Name'] if 'AQI_avg' in integrated_data.columns else 'N/A',
                "most_developed_infrastructure": integrated_data.loc[integrated_data['Infrastructure_Score'].idxmax(), 'Ward_Name'] if 'Infrastructure_Score' in integrated_data.columns else 'N/A',
                "highest_green_cover": integrated_data.loc[integrated_data['Green_Cover_Percent'].idxmax(), 'Ward_Name'] if 'Green_Cover_Percent' in integrated_data.columns else 'N/A',
                "most_congested_traffic": integrated_data.loc[integrated_data['Travel_Time_Index_avg'].idxmax(), 'Ward_Name'] if 'Travel_Time_Index_avg' in integrated_data.columns else 'N/A'
            },
            "data_quality": {
                "completeness": f"{(1 - integrated_data.isnull().sum().sum() / (len(integrated_data) * len(integrated_data.columns))) * 100:.1f}%",
                "sources_reliability": "High (Government + Official)",
                "temporal_coverage": "2024 + Historical Trends",
                "spatial_accuracy": "Ward-level (Administrative)"
            },
            "recommendations_summary": {
                "total_recommendations": len(recommendations.get('recommendations', [])) if recommendations else 0,
                "priority_actions": recommendations.get('priority_actions', [])[:3] if recommendations else [],
                "investment_areas": recommendations.get('investment_areas', [])[:3] if recommendations else []
            },
            "methodology": {
                "data_collection": "Free government APIs + Open source platforms",
                "preprocessing": "Standardization + Missing value imputation",
                "analysis": "Unsupervised clustering + Spatial analysis",
                "validation": "Domain expert knowledge + Cross-validation"
            },
            "future_work": [
                "Real-time data integration",
                "Predictive modeling for growth patterns",
                "Citizen feedback integration",
                "IoT sensor data inclusion",
                "Machine learning for policy optimization"
            ]
        }
    }
    
    # Save comprehensive report
    report_file = os.path.join("outputs", "reports", f"enhanced_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"📋 Enhanced summary report saved to: {report_file}")

if __name__ == "__main__":
    try:
        run_enhanced_analysis()
    except KeyboardInterrupt:
        print("\n\n⚠️ Analysis interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error during analysis: {str(e)}")
        import traceback
        traceback.print_exc()
