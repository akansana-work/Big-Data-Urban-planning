"""
Test Free Data Integration
Quick test to verify free data sources work
"""

import os
import sys
sys.path.append('src')

def test_free_data():
    print("🆓 TESTING FREE DATA INTEGRATION")
    print("="*40)
    
    try:
        from free_data_loader import FreeDataLoader
        
        print("✅ Free data loader imported successfully")
        
        # Create loader instance
        loader = FreeDataLoader()
        print("✅ Loader instance created")
        
        # Test individual data loading functions
        print("\n📊 Testing data loading functions:")
        
        # Test pollution data
        pollution_df = loader.load_free_pollution_data()
        print(f"✅ Pollution data: {len(pollution_df)} records")
        
        # Test demographic data  
        demo_df = loader.load_free_demographic_data()
        print(f"✅ Demographics: {len(demo_df)} records")
        
        # Test infrastructure data
        infra_df = loader.load_osm_infrastructure_data()
        print(f"✅ Infrastructure: {len(infra_df)} records")
        
        print(f"\n🎉 FREE DATA TEST SUCCESSFUL!")
        print(f"📁 Sample files created in data/free_sources/")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_free_data()
    if success:
        print("\n🚀 Ready to run full free data analysis!")
    else:
        print("\n⚠️ Check dependencies and try again")
