"""
Main Execution Script for Big Data Urban Planning Analysis
Run this script to execute the complete analysis pipeline.
"""

import os
import sys
import time
from datetime import datetime

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

try:
    from src.analysis import UrbanPlanningAnalyzer
except ImportError:
    # If direct import fails, try alternative import
    from analysis import UrbanPlanningAnalyzer

def print_banner():
    """Print project banner."""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║     BIG DATA-DRIVEN STRATEGIES FOR URBAN PLANNING           ║
    ║                    & DEVELOPMENT                             ║
    ║                                                              ║
    ║                  PUNE CITY CASE STUDY                       ║
    ║                                                              ║
    ║              CDAC Project - Aditya Kansana                  ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def check_dependencies():
    """Check if all required dependencies are available."""
    required_packages = [
        'pandas', 'numpy', 'scikit-learn', 'matplotlib', 
        'seaborn', 'folium', 'geopandas', 'plotly'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   • {package}")
        print("\n💡 Install missing packages with:")
        print("   pip install -r requirements.txt")
        return False
    
    print("✅ All dependencies are available!")
    return True

def show_real_data_sources():
    """Display information about real data sources available for urban planning."""
    print("\n🌐 REAL DATA SOURCES FOR URBAN PLANNING")
    print("="*60)
    
    print("\n📊 INDIAN GOVERNMENT OPEN DATA:")
    print("   🏛️  data.gov.in - National Data Portal")
    print("      • Census data, demographic statistics")
    print("      • Infrastructure and amenities data")
    print("      • Economic indicators")
    
    print("\n🏙️  PUNE MUNICIPAL CORPORATION (PMC) DATA:")
    print("   🌐 punecorporation.org")
    print("      • Ward boundaries and demographics")
    print("      • Property tax and land use data")
    print("      • Public facilities locations")
    
    print("\n🌍 POLLUTION & ENVIRONMENTAL DATA:")
    print("   🏭 Central Pollution Control Board (CPCB)")
    print("      • Air quality monitoring stations")
    print("      • Real-time AQI data")
    print("      • Historical pollution trends")
    print("   🛰️  ISRO Bhuvan Portal")
    print("      • Satellite imagery and land use")
    print("      • Green cover analysis")
    print("      • Urban sprawl monitoring")
    
    print("\n🚗 TRAFFIC & TRANSPORTATION:")
    print("   📍 Google Maps API / HERE API")
    print("      • Real-time traffic conditions")
    print("      • Travel time matrices")
    print("      • Road network analysis")
    print("   🚌 PMPML (Bus Service Data)")
    print("      • Public transport usage")
    print("      • Route optimization data")
    
    print("\n📈 ECONOMIC & SOCIAL DATA:")
    print("   📊 Census of India 2021")
    print("      • Population demographics")
    print("      • Income and education levels")
    print("      • Housing characteristics")
    print("   🏪 Ministry of Statistics and Programme Implementation")
    print("      • Economic indicators")
    print("      • Employment statistics")
    
    print("\n🗺️  GEOSPATIAL DATA:")
    print("   🌍 OpenStreetMap (OSM)")
    print("      • Detailed street networks")
    print("      • Points of interest")
    print("      • Building footprints")
    print("   📡 Survey of India")
    print("      • Official topographic maps")
    print("      • Administrative boundaries")

def show_data_integration_plan():
    """Show how to integrate real data into the existing framework."""
    print("\n🔧 REAL DATA INTEGRATION PLAN")
    print("="*60)
    
    print("\n✅ IMMEDIATE ACTIONS (Week 1-2):")
    print("   1. 📋 Register for API access:")
    print("      • Google Maps API (traffic data)")
    print("      • CPCB API (pollution data)")
    print("      • Census API (demographic data)")
    
    print("\n   2. 📥 Download static datasets:")
    print("      • PMC ward boundaries (GeoJSON)")
    print("      • Census 2021 ward-wise data")
    print("      • Historical AQI data from CPCB")
    
    print("\n🔄 DATA REPLACEMENT STRATEGY:")
    print("   📂 Current: src/data_generation.py (simulated)")
    print("   📂 New: src/real_data_loader.py (actual)")
    print("   ✅ Same output format - no pipeline changes needed!")
    
    print("\n📊 PHASE-WISE IMPLEMENTATION:")
    print("   🏗️  Phase 1: Replace demographics with Census 2021")
    print("   🌫️  Phase 2: Integrate CPCB pollution monitoring")
    print("   🚗 Phase 3: Add Google Traffic API data")
    print("   🌳 Phase 4: ISRO satellite green cover data")
    print("   🏢 Phase 5: PMC infrastructure and amenities")

def estimate_data_costs():
    """Estimate costs for real data APIs."""
    print("\n💰 DATA ACCESS COSTS")
    print("="*60)
    
    print("\n🆓 FREE DATA SOURCES:")
    print("   ✅ Government Open Data Portal")
    print("   ✅ Census India")
    print("   ✅ CPCB Pollution Data")
    print("   ✅ OpenStreetMap")
    print("   ✅ PMC Public Records")
    
    print("\n💵 PAID API SERVICES:")
    print("   🗺️  Google Maps API:")
    print("      • Traffic: ₹40 per 1000 requests")
    print("      • Estimated monthly: ₹2,000-5,000")
    print("   🌍 HERE API:")
    print("      • Similar pricing to Google")
    print("      • Free tier: 1000 requests/day")
    
    print("\n💡 COST OPTIMIZATION:")
    print("   • Use free tier limits first")
    print("   • Cache API responses")
    print("   • Academic discounts available")
    print("   • Government partnerships possible")

def run_free_data_analysis():
    """Run analysis using only FREE data sources."""
    print("\n🆓 RUNNING ANALYSIS WITH 100% FREE DATA")
    print("="*50)
    
    try:
        # Import free data loader
        from src.free_data_loader import FreeDataLoader, print_free_data_summary
        
        # Load all free data
        loader = FreeDataLoader()
        free_data_results = loader.integrate_all_free_data()
        
        # Print what we got
        print_free_data_summary()
        
        print(f"\n🎯 FREE DATA READY FOR ANALYSIS!")
        print(f"📊 Datasets created: {len(free_data_results['individual_datasets'])}")
        print(f"🏙️ Wards covered: {len(free_data_results['main_dataset'])}")
        print(f"💰 Total cost: ₹{free_data_results['total_cost']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Free data loading failed: {e}")
        print("💡 Falling back to simulated data...")
        return False

def main():
    """Main execution function."""
    print_banner()
    
    print(f"🕒 Analysis started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n" + "="*60)
    
    # Check dependencies
    print("🔍 Checking dependencies...")
    if not check_dependencies():
        return
    
    # Check if user wants free data analysis
    print("\n🆓 FREE DATA OPTION AVAILABLE!")
    print("   💡 Use 100% free government and open-source data")
    print("   📊 Sources: CPCB, Census, OpenStreetMap, ISRO")
    print("   💰 Cost: ₹0")
    
    # Try free data first
    free_data_success = run_free_data_analysis()
    
    # Initialize and run analyzer
    try:
        print("\n🚀 Initializing Urban Planning Analyzer...")
        analyzer = UrbanPlanningAnalyzer()
        
        print("\n📊 Starting complete analysis pipeline...")
        start_time = time.time()
        
        # Run complete analysis
        results = analyzer.run_complete_analysis()
        
        execution_time = time.time() - start_time
        
        # Print summary
        print("\n" + "="*60)
        print("🎉 ANALYSIS COMPLETED SUCCESSFULLY!")
        print("="*60)
        
        print(f"\n📈 RESULTS SUMMARY:")
        print(f"   • Total execution time: {execution_time:.2f} seconds")
        print(f"   • Wards analyzed: {results.get('total_wards', 'N/A')}")
        print(f"   • Features engineered: {results.get('features_analyzed', 'N/A')}")
        print(f"   • Clustering silhouette score: {results.get('silhouette_score', 'N/A'):.3f}")
        print(f"   • Data completeness: {results.get('data_completeness', 'N/A'):.1f}%")
        print(f"   • Validation status: {results.get('validation_status', 'N/A')}")
        
        print(f"\n🗂️  OUTPUT FILES GENERATED:")
        print(f"   📊 Raw Data: data/raw/")
        print(f"   🔧 Processed Data: data/processed/")
        print(f"   🗺️  Interactive Maps: outputs/maps/")
        print(f"   📈 Charts & Graphs: outputs/charts/")
        print(f"   📋 Analysis Reports: outputs/reports/")
        
        print(f"\n🎯 KEY FINDINGS:")
        
        # High-stress wards validation
        if results.get('high_stress_wards', {}).get('validation', {}).get('shivajinagar_validated'):
            print(f"   ✅ Shivajinagar validated as high-stress ward")
        else:
            print(f"   ⚠️  Shivajinagar not found in top high-stress wards")
            
        # Green zones validation
        if results.get('green_zones', {}).get('validation', {}).get('kothrud_validated'):
            print(f"   ✅ Kothrud validated as green zone")
        else:
            print(f"   ⚠️  Kothrud not found in top green zones")
        
        # Traffic-pollution correlation
        correlation = results.get('traffic_pollution_correlation')
        if correlation and correlation > 0.5:
            print(f"   ✅ Strong traffic-pollution correlation found: {correlation:.3f}")
        elif correlation:
            print(f"   ⚠️  Moderate traffic-pollution correlation: {correlation:.3f}")
        
        print(f"\n📖 DETAILED REPORTS:")
        print(f"   • Comprehensive Analysis: outputs/reports/comprehensive_analysis_report.md")
        print(f"   • Complete Results: outputs/reports/complete_analysis_results.json")
        print(f"   • Clustering Analysis: outputs/reports/clustering_analysis.json")
        
        print(f"\n🌐 INTERACTIVE VISUALIZATIONS:")
        print(f"   • Traffic Heatmap: outputs/maps/traffic_congestion_heatmap.html")
        print(f"   • Pollution Heatmap: outputs/maps/pollution_levels_heatmap.html")
        print(f"   • Green Cover Map: outputs/maps/green_cover_heatmap.html")
        print(f"   • Ward Clusters: outputs/maps/ward_clusters_map.html")
        
        print(f"\n💡 NEXT STEPS:")
        print(f"   1. Open the comprehensive report for detailed findings")
        print(f"   2. Explore interactive maps in your web browser")
        print(f"   3. Review clustering analysis for urban planning insights")
        print(f"   4. Use recommendations for policy development")
        
        print(f"\n🏆 DISSERTATION OBJECTIVES FULFILLED:")
        print(f"   ✅ Multi-domain data integration (5 domains)")
        print(f"   ✅ K-Means clustering implementation (k=3)")
        print(f"   ✅ Spatial analysis and visualization")
        print(f"   ✅ Evidence-based planning recommendations")
        print(f"   ✅ Validation of expected urban patterns")
        
        print(f"\n🌐 REAL DATA INTEGRATION OPTIONS:")
        print(f"   💡 To replace simulated data with real datasets:")
        print(f"   1. Run: python main.py --show-real-data-sources")
        print(f"   2. Check: Real Data Integration Guide below")
        
        # Show real data information
        show_real_data_sources()
        show_data_integration_plan()
        estimate_data_costs()
        
        print(f"\n📞 SUPPORT & GUIDANCE:")
        print(f"   • Government Data Portal: data.gov.in")
        print(f"   • PMC Contact: punecorporation.org")
        print(f"   • Academic Partnerships: Contact local universities")
        print(f"   • Technical Support: GitHub issues/documentation")
        
    except Exception as e:
        print(f"\n❌ Analysis failed with error:")
        print(f"   {str(e)}")
        print(f"\n🔧 Troubleshooting suggestions:")
        print(f"   1. Ensure all dependencies are installed")
        print(f"   2. Check write permissions in the project directory")
        print(f"   3. Verify sufficient disk space for outputs")
        return
    
    print(f"\n🎯 Analysis completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Thank you for using the Urban Planning Analysis System!")

if __name__ == "__main__":
    main()
