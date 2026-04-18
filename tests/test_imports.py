"""
Simple Import Test - Verify imports work correctly
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test if all imports work."""
    try:
        # Test src imports
        from src.cleaners.strategies.title_cleaning_strategy import TitleCleaningStrategy
        print("✅ TitleCleaningStrategy import successful")
        
        from src.scrapers.base_scraper import JobExtractor
        print("✅ JobExtractor import successful")
        
        from src.storage.base_storage_handler import StorageHandler
        print("✅ StorageHandler import successful")
        
        # Test pipeline imports
        from pipelines.cleaning_pipeline import DataCleaningPipeline
        print("✅ DataCleaningPipeline import successful")
        
        print("\n🎯 All imports working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
