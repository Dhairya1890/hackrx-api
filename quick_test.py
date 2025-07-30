#!/usr/bin/env python3
"""
Quick test script to verify environment variables and API functionality
Run this with: python quick_test.py
"""

import os
import sys
from dotenv import load_dotenv

def test_env_vars():
    """Test if environment variables are loaded"""
    print("🔧 Testing Environment Variables")
    print("=" * 40)
    
    # Load .env file
    load_dotenv()
    
    # Check variables
    gemini_key = os.getenv("GEMINI_API_KEY")
    pinecone_key = os.getenv("PINECONE_API_KEY")
    
    print(f"GEMINI_API_KEY: {'✅ Set' if gemini_key else '❌ Not set'}")
    print(f"PINECONE_API_KEY: {'✅ Set' if pinecone_key else '❌ Not set'}")
    
    if not gemini_key or not pinecone_key:
        print("\n❌ Environment variables not set!")
        print("Please check your .env file")
        return False
    
    print("\n✅ Environment variables are set!")
    return True

def test_imports():
    """Test if required packages can be imported"""
    print("\n📦 Testing Package Imports")
    print("=" * 40)
    
    try:
        import google.generativeai as genai
        print("✅ google.generativeai imported")
    except ImportError as e:
        print(f"❌ google.generativeai import failed: {e}")
        return False
    
    try:
        from pinecone import Pinecone
        print("✅ pinecone imported")
    except ImportError as e:
        print(f"❌ pinecone import failed: {e}")
        return False
    
    try:
        from langchain.embeddings.base import Embeddings
        print("✅ langchain imported")
    except ImportError as e:
        print(f"❌ langchain import failed: {e}")
        return False
    
    print("\n✅ All packages imported successfully!")
    return True

def test_api_config():
    """Test API configuration"""
    print("\n🔑 Testing API Configuration")
    print("=" * 40)
    
    try:
        import google.generativeai as genai
        from pinecone import Pinecone
        
        # Test Gemini
        gemini_key = os.getenv("GEMINI_API_KEY")
        genai.configure(api_key=gemini_key)
        print("✅ Gemini configured")
        
        # Test Pinecone
        pinecone_key = os.getenv("PINECONE_API_KEY")
        pc = Pinecone(api_key=pinecone_key)
        print("✅ Pinecone configured")
        
        return True
        
    except Exception as e:
        print(f"❌ API configuration failed: {e}")
        return False

def test_local_server():
    """Test if local server can start"""
    print("\n🚀 Testing Local Server")
    print("=" * 40)
    
    try:
        import subprocess
        import time
        
        # Start server
        print("Starting local server...")
        process = subprocess.Popen(
            [sys.executable, "app.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for server to start
        time.sleep(5)
        
        # Test health endpoint
        import requests
        response = requests.get("http://localhost:8000/", timeout=10)
        print(f"✅ Server responding: {response.status_code}")
        
        # Clean up
        process.terminate()
        process.wait()
        
        return True
        
    except Exception as e:
        print(f"❌ Local server test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Quick Test Suite")
    print("=" * 50)
    
    tests = [
        ("Environment Variables", test_env_vars),
        ("Package Imports", test_imports),
        ("API Configuration", test_api_config),
        ("Local Server", test_local_server),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n📊 Test Results")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! Your setup is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the errors above.")

if __name__ == "__main__":
    main() 