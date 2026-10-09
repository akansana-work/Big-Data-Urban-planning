"""
Comprehensive Free Data Integration Test
Tests maximum free data utilization for urban planning analysis
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime
import json

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

try:
    from src.enhanced_free_data_loader import EnhancedFreeDataLoader
except ImportError:
    try:
        from enhanced_free_data_loader import EnhancedFreeDataLoader
    except ImportError as e:
        print(f"❌ Could not import enhanced loader: {e}")
        sys.exit(1)

def test_data_quality(df, dataset_name):
    """Test data quality metrics."""
    print(f"\n📊 Testing {dataset_name} data quality...")
    
    # Basic metrics
    total_records = len(df)
    total_features = len(df.columns)
    missing_data = df.isnull().sum().sum()
    completeness = (1 - missing_data / (total_records * total_features)) * 100
    
    print(f"   📈 Records: {total_records}")
    print(f"   📊 Features: {total_features}")
    print(f"   ✅ Completeness: {completeness:.1f}%")
    
    # Ward coverage
    if 'Ward_Name' in df.columns:
        unique_wards = df['Ward_Name'].nunique()
        print(f"   🏘️  Ward Coverage: {unique_wards}")
    
    # Data validation
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) > 0:
        negative_values = (df[numeric_cols] < 0).sum().sum()
        outliers = 0
        for col in numeric_cols:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            outliers += ((df[col] < (Q1 - 1.5 * IQR)) | (df[col] > (Q3 + 1.5 * IQR))).sum()
        
        print(f"   ⚠️  Negative Values: {negative_values}")
        print(f"   📊 Potential Outliers: {outliers}")
    
    return {
        'records': total_records,
        'features': total_features,
        'completeness': completeness,
        'wards': unique_wards if 'Ward_Name' in df.columns else 0,
        'quality_score': min(100, completeness - (negative_values * 0.1) - (outliers * 0.05))
    }

def test_data_integration(datasets):
    """Test data integration capabilities."""
    print(f"\n🔗 Testing Data Integration...")
    
    if not datasets:
        print("❌ No datasets to integrate")
        return False
    
    # Check common ward names
    ward_sets = []
    for name, df in datasets.items():
        if 'Ward_Name' in df.columns:
            ward_sets.append(set(df['Ward_Name'].unique()))
    
    if ward_sets:
        common_wards = set.intersection(*ward_sets)
        print(f"   🏘️  Common wards across all datasets: {len(common_wards)}")
        
        if len(common_wards) >= 15:  # At least 15 wards
            print("   ✅ Sufficient ward overlap for integration")
            return True
        else:
            print("   ⚠️  Limited ward overlap - may affect integration")
            return False
    else:
        print("   ❌ No ward data found for integration")
        return False

def test_spatial_consistency(datasets):
    """Test spatial data consistency."""
    print(f"\n🗺️  Testing Spatial Consistency...")
    
    # Check coordinate ranges for Pune
    pune_bounds = {
        'lat_min': 18.4, 'lat_max': 18.7,
        'lng_min': 73.7, 'lng_max': 74.0
    }
    
    spatial_valid = True
    
    for name, df in datasets.items():
        if 'lat' in df.columns and 'lng' in df.columns:
            invalid_coords = (
                (df['lat'] < pune_bounds['lat_min']) | (df['lat'] > pune_bounds['lat_max']) |
                (df['lng'] < pune_bounds['lng_min']) | (df['lng'] > pune_bounds['lng_max'])
            ).sum()
            
            print(f"   📍 {name}: {invalid_coords} invalid coordinates")
            if invalid_coords > 0:
                spatial_valid = False
    
    if spatial_valid:
        print("   ✅ All coordinates within Pune bounds")
    else:
        print("   ⚠️  Some coordinates outside expected Pune area")
    
    return spatial_valid

def test_temporal_consistency(datasets):
    """Test temporal data consistency."""
    print(f"\n⏰ Testing Temporal Consistency...")
    
    current_year = datetime.now().year
    temporal_valid = True
    
    for name, df in datasets.items():
        date_columns = [col for col in df.columns if 'date' in col.lower() or 'time' in col.lower()]
        
        for date_col in date_columns:
            try:
                dates = pd.to_datetime(df[date_col])
                future_dates = (dates > datetime.now()).sum()
                old_dates = (dates < datetime(2010, 1, 1)).sum()
                
                print(f"   📅 {name}.{date_col}: {future_dates} future, {old_dates} pre-2010")
                
                if future_dates > len(df) * 0.1 or old_dates > len(df) * 0.5:
                    temporal_valid = False
                    
            except:
                print(f"   ❌ {name}.{date_col}: Invalid date format")
                temporal_valid = False
    
    if temporal_valid:
        print("   ✅ Temporal data appears consistent")
    else:
        print("   ⚠️  Some temporal inconsistencies detected")
    
    return temporal_valid

def test_domain_specific_validation(datasets):
    """Test domain-specific data validation."""
    print(f"\n🔬 Testing Domain-Specific Validation...")
    
    validation_results = {}
    
    # Pollution data validation
    if 'pollution' in datasets:
        pollution_df = datasets['pollution']
        issues = []
        
        if 'AQI' in pollution_df.columns:
            invalid_aqi = ((pollution_df['AQI'] < 0) | (pollution_df['AQI'] > 500)).sum()
            if invalid_aqi > 0:
                issues.append(f"{invalid_aqi} invalid AQI values")
        
        if 'PM2_5' in pollution_df.columns:
            invalid_pm25 = ((pollution_df['PM2_5'] < 0) | (pollution_df['PM2_5'] > 500)).sum()
            if invalid_pm25 > 0:
                issues.append(f"{invalid_pm25} invalid PM2.5 values")
        
        validation_results['pollution'] = {
            'valid': len(issues) == 0,
            'issues': issues
        }
        
        print(f"   🌫️  Pollution: {'✅ Valid' if len(issues) == 0 else '⚠️ ' + ', '.join(issues)}")
    
    # Demographics validation
    if 'demographics' in datasets:
        demo_df = datasets['demographics']
        issues = []
        
        if 'Population_2024_Projected' in demo_df.columns:
            negative_pop = (demo_df['Population_2024_Projected'] < 0).sum()
            if negative_pop > 0:
                issues.append(f"{negative_pop} negative population values")
        
        if 'Population_Density_per_km2' in demo_df.columns:
            unrealistic_density = (demo_df['Population_Density_per_km2'] > 50000).sum()
            if unrealistic_density > 0:
                issues.append(f"{unrealistic_density} unrealistic density values")
        
        validation_results['demographics'] = {
            'valid': len(issues) == 0,
            'issues': issues
        }
        
        print(f"   👥 Demographics: {'✅ Valid' if len(issues) == 0 else '⚠️ ' + ', '.join(issues)}")
    
    # Infrastructure validation
    if 'infrastructure' in datasets:
        infra_df = datasets['infrastructure']
        issues = []
        
        count_columns = [col for col in infra_df.columns if 'count' in col.lower()]
        for col in count_columns:
            negative_counts = (infra_df[col] < 0).sum()
            if negative_counts > 0:
                issues.append(f"{negative_counts} negative {col}")
        
        validation_results['infrastructure'] = {
            'valid': len(issues) == 0,
            'issues': issues
        }
        
        print(f"   🏢 Infrastructure: {'✅ Valid' if len(issues) == 0 else '⚠️ ' + ', '.join(issues)}")
    
    # Traffic validation
    if 'traffic' in datasets:
        traffic_df = datasets['traffic']
        issues = []
        
        if 'Average_Speed_kmh' in traffic_df.columns:
            unrealistic_speed = ((traffic_df['Average_Speed_kmh'] < 0) | (traffic_df['Average_Speed_kmh'] > 100)).sum()
            if unrealistic_speed > 0:
                issues.append(f"{unrealistic_speed} unrealistic speed values")
        
        validation_results['traffic'] = {
            'valid': len(issues) == 0,
            'issues': issues
        }
        
        print(f"   🚗 Traffic: {'✅ Valid' if len(issues) == 0 else '⚠️ ' + ', '.join(issues)}")
    
    # Green cover validation
    if 'green_cover' in datasets:
        green_df = datasets['green_cover']
        issues = []
        
        if 'Green_Cover_Percent' in green_df.columns:
            invalid_percent = ((green_df['Green_Cover_Percent'] < 0) | (green_df['Green_Cover_Percent'] > 100)).sum()
            if invalid_percent > 0:
                issues.append(f"{invalid_percent} invalid percentage values")
        
        validation_results['green_cover'] = {
            'valid': len(issues) == 0,
            'issues': issues
        }
        
        print(f"   🌳 Green Cover: {'✅ Valid' if len(issues) == 0 else '⚠️ ' + ', '.join(issues)}")
    
    return validation_results

def run_comprehensive_test():
    """Run comprehensive free data integration test."""
    
    print("🔥 COMPREHENSIVE FREE DATA INTEGRATION TEST 🔥")
    print("="*60)
    
    # Initialize loader
    print("\n📥 Initializing Enhanced Free Data Loader...")
    loader = EnhancedFreeDataLoader()
    
    # Load all datasets
    print("\n📊 Loading all enhanced datasets...")
    datasets = loader.load_all_enhanced_data()
    
    if not datasets:
        print("❌ Failed to load datasets")
        return False
    
    print(f"\n✅ Loaded {len(datasets)} datasets successfully")
    
    # Test each dataset
    quality_results = {}
    for name, df in datasets.items():
        quality_results[name] = test_data_quality(df, name)
    
    # Integration tests
    integration_success = test_data_integration(datasets)
    spatial_consistency = test_spatial_consistency(datasets)
    temporal_consistency = test_temporal_consistency(datasets)
    domain_validation = test_domain_specific_validation(datasets)
    
    # Overall assessment
    print(f"\n📋 OVERALL ASSESSMENT")
    print("="*30)
    
    overall_score = 0
    total_tests = 0
    
    # Quality scores
    avg_quality = np.mean([result['quality_score'] for result in quality_results.values()])
    print(f"📊 Average Data Quality: {avg_quality:.1f}/100")
    overall_score += avg_quality
    total_tests += 1
    
    # Integration test
    integration_score = 100 if integration_success else 50
    print(f"🔗 Data Integration: {integration_score}/100")
    overall_score += integration_score
    total_tests += 1
    
    # Spatial consistency
    spatial_score = 100 if spatial_consistency else 70
    print(f"🗺️  Spatial Consistency: {spatial_score}/100")
    overall_score += spatial_score
    total_tests += 1
    
    # Temporal consistency
    temporal_score = 100 if temporal_consistency else 70
    print(f"⏰ Temporal Consistency: {temporal_score}/100")
    overall_score += temporal_score
    total_tests += 1
    
    # Domain validation
    domain_score = np.mean([100 if result['valid'] else 60 for result in domain_validation.values()])
    print(f"🔬 Domain Validation: {domain_score:.1f}/100")
    overall_score += domain_score
    total_tests += 1
    
    final_score = overall_score / total_tests
    
    print(f"\n🎯 FINAL SCORE: {final_score:.1f}/100")
    
    if final_score >= 85:
        status = "🟢 EXCELLENT"
    elif final_score >= 70:
        status = "🟡 GOOD"
    elif final_score >= 55:
        status = "🟠 ACCEPTABLE"
    else:
        status = "🔴 NEEDS IMPROVEMENT"
    
    print(f"📈 Status: {status}")
    
    # Save test results
    test_results = {
        'test_summary': {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'datasets_tested': len(datasets),
            'final_score': final_score,
            'status': status,
            'quality_results': quality_results,
            'integration_success': integration_success,
            'spatial_consistency': spatial_consistency,
            'temporal_consistency': temporal_consistency,
            'domain_validation': domain_validation
        }
    }
    
    test_file = os.path.join("outputs", "reports", f"free_data_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    os.makedirs(os.path.dirname(test_file), exist_ok=True)
    
    with open(test_file, 'w') as f:
        json.dump(test_results, f, indent=2)
    
    print(f"\n💾 Test results saved to: {test_file}")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    
    if final_score >= 85:
        print("   ✅ Data quality is excellent - ready for production analysis")
        print("   ✅ Consider expanding to real-time data integration")
    elif final_score >= 70:
        print("   ✅ Data quality is good - suitable for analysis")
        print("   💡 Consider minor improvements in data validation")
    else:
        print("   ⚠️  Data quality needs improvement before production use")
        print("   💡 Focus on data validation and cleaning processes")
    
    return final_score >= 70

if __name__ == "__main__":
    try:
        success = run_comprehensive_test()
        if success:
            print(f"\n🎉 FREE DATA INTEGRATION TEST PASSED! 🎉")
        else:
            print(f"\n⚠️  FREE DATA INTEGRATION TEST NEEDS ATTENTION ⚠️")
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
