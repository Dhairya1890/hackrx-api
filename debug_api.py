import requests
import json
import time
from urllib.parse import urljoin

def test_api_endpoints(base_url):
    """Comprehensive API testing"""
    print(f"Testing API at: {base_url}")
    print("=" * 60)
    
    # Test 1: Basic connectivity
    print("1. Testing basic connectivity...")
    try:
        response = requests.get(base_url, timeout=10)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text[:200]}...")
    except requests.exceptions.ConnectionError:
        print("   ❌ Connection failed - Check if the URL is correct")
        return False
    except requests.exceptions.Timeout:
        print("   ❌ Timeout - Server might be starting up")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    # Test 2: Health endpoint
    print("\n2. Testing health endpoint...")
    try:
        health_url = urljoin(base_url, "/health")
        response = requests.get(health_url, timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Health check: {data}")
        else:
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Query endpoint
    print("\n3. Testing query endpoint...")
    try:
        query_url = urljoin(base_url, "/query")
        payload = {
            "query": "What is covered under my health insurance policy?"
        }
        response = requests.post(
            query_url, 
            json=payload, 
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Query response: {json.dumps(data, indent=2)}")
        else:
            print(f"   Error response: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    return True

def test_with_different_urls():
    """Test with common URL patterns"""
    print("Testing different URL patterns...")
    print("=" * 60)
    
    # Common Render URL patterns
    test_urls = [
        "https://your-actual-app-name.onrender.com",  # Replace with your actual URL
        "https://your-actual-app-name.onrender.com/",
        "http://localhost:8000",  # For local testing
    ]
    
    for url in test_urls:
        print(f"\nTesting: {url}")
        if test_api_endpoints(url):
            print("✅ URL is accessible!")
            return url
        else:
            print("❌ URL failed")
    
    return None

def check_render_deployment():
    """Check common Render deployment issues"""
    print("\nRender Deployment Checklist:")
    print("=" * 60)
    
    checklist = [
        "1. Is your Render app deployed and running?",
        "2. Are environment variables set in Render dashboard?",
        "   - GEMINI_API_KEY",
        "   - PINECONE_API_KEY",
        "3. Is the Procfile correct?",
        "4. Are all dependencies in requirements.txt?",
        "5. Is the app starting without errors? (Check Render logs)",
        "6. Is the correct URL being used?",
    ]
    
    for item in checklist:
        print(f"   {item}")
    
    print("\nTo check Render logs:")
    print("1. Go to your Render dashboard")
    print("2. Click on your app")
    print("3. Go to 'Logs' tab")
    print("4. Look for any error messages")

if __name__ == "__main__":
    print("🔍 API Debugging Tool")
    print("=" * 60)
    
    # Test with different URLs
    working_url = test_with_different_urls()
    
    if working_url:
        print(f"\n✅ Found working URL: {working_url}")
        print(f"Use this URL in your application: {working_url}")
    else:
        print("\n❌ No working URLs found")
        check_render_deployment()
        
        print("\nNext steps:")
        print("1. Check your Render dashboard for the correct URL")
        print("2. Verify the app is deployed and running")
        print("3. Check Render logs for any startup errors")
        print("4. Ensure environment variables are set") 