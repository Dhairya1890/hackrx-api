import requests
import json
import time

def test_deployed_api():
    """Test the deployed API on Render"""
    print("🌐 Testing Deployed API")
    print("=" * 50)
    
    base_url = "https://hackrx-api-sycy.onrender.com"
    
    # Test 1: Health check
    print("1. Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/", timeout=15)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {response.json()}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Health check failed: {e}")
    
    # Test 2: Detailed health check
    print("\n2. Testing detailed health endpoint...")
    try:
        response = requests.get(f"{base_url}/health", timeout=15)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Health data: {data}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Detailed health check failed: {e}")
    
    # Test 3: Query endpoint
    print("\n3. Testing query endpoint...")
    try:
        payload = {
            "query": "What is covered under my health insurance policy?"
        }
        response = requests.post(
            f"{base_url}/query",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Query response: {json.dumps(data, indent=2)}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Query test failed: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Deployed API test completed!")

if __name__ == "__main__":
    test_deployed_api() 