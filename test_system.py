#!/usr/bin/env python3
"""
System validation tests that don't require API keys
"""

import os
import sys
from pathlib import Path

def test_directory_structure():
    """Test that all required directories exist"""
    print("🏗️  Testing directory structure...")
    
    required_dirs = [
        "core",
        "platforms/hackernews", 
        "platforms/reddit",
        "platforms/twitter",
        "platforms/medium", 
        "platforms/devto",
        "platforms/peerlist"
    ]
    
    missing = []
    for dir_path in required_dirs:
        if not Path(dir_path).exists():
            missing.append(dir_path)
    
    if missing:
        print(f"❌ Missing directories: {missing}")
        return False
    
    print("✅ All required directories exist")
    return True

def test_required_files():
    """Test that all required files exist"""
    print("📁 Testing required files...")
    
    required_files = [
        "main.py",
        "requirements.txt",
        "sample_content.md",
        "core/models.py",
        "core/content_analyzer.py", 
        "core/platform_engine.py",
        "core/scheduler.py",
        "core/cache_manager.py",
        "platforms/hackernews/profile.yaml",
        "platforms/hackernews/adapter.py",
        "platforms/reddit/subreddit_data.yaml",
        "platforms/reddit/adapter.py"
    ]
    
    missing = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing.append(file_path)
    
    if missing:
        print(f"❌ Missing files: {missing}")
        return False
    
    print("✅ All required files exist")
    return True

def test_imports():
    """Test that imports work without API keys"""
    print("🐍 Testing Python imports...")
    
    try:
        # Test core imports
        sys.path.insert(0, str(Path.cwd()))
        
        from core.models import ContentDNA, PlatformContent, ValidationResult, PublishResult
        from core.scheduler import SmartScheduler
        from core.cache_manager import CacheManager
        
        print("✅ Core modules import successfully")
        
        # Test that we can instantiate non-API classes
        scheduler = SmartScheduler()
        cache_manager = CacheManager()
        
        print("✅ Core classes instantiate successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_platform_configs():
    """Test that platform configs are valid"""
    print("⚙️  Testing platform configurations...")
    
    try:
        import yaml
        
        # Test HN profile
        with open("platforms/hackernews/profile.yaml") as f:
            hn_config = yaml.safe_load(f)
        
        required_keys = ['culture', 'timing', 'validation_rules']
        for key in required_keys:
            if key not in hn_config:
                print(f"❌ Missing key '{key}' in HN profile")
                return False
        
        # Test Reddit subreddit data
        with open("platforms/reddit/subreddit_data.yaml") as f:
            reddit_config = yaml.safe_load(f)
        
        if 'subreddits' not in reddit_config:
            print("❌ Missing 'subreddits' key in Reddit config")
            return False
        
        print("✅ Platform configurations are valid")
        return True
        
    except Exception as e:
        print(f"❌ Config validation error: {e}")
        return False

def test_sample_content():
    """Test that sample content exists and is readable"""
    print("📄 Testing sample content...")
    
    try:
        with open("sample_content.md", 'r') as f:
            content = f.read()
        
        if len(content) < 100:
            print("❌ Sample content too short")
            return False
        
        if not content.startswith("#"):
            print("❌ Sample content doesn't start with markdown header")
            return False
        
        print("✅ Sample content is valid")
        return True
        
    except Exception as e:
        print(f"❌ Sample content error: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Running Global Publisher system tests...\n")
    
    tests = [
        test_directory_structure,
        test_required_files,
        test_imports,
        test_platform_configs,
        test_sample_content
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            failed += 1
        print()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! System is ready.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())