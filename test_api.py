import requests
import json

# Replace with your actual Render URL
BASE_URL = "https://your-app-name.onrender.com"  # Update this with your actual URL

def test_health():
    """Test the health endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"Root endpoint status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error testing root endpoint: {e}")

def test_health_detailed():
    """Test the detailed health endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Health endpoint status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error testing health endpoint: {e}")

def test_query():
    """Test the query endpoint"""
    test_query = "What is covered under my health insurance policy?"
    
    payload = {
        "query": test_query
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/query",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        print(f"Query endpoint status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error testing query endpoint: {e}")

if __name__ == "__main__":
    print("Testing API endpoints...")
    print("=" * 50)
    
    test_health()
    print("-" * 30)
    
    test_health_detailed()
    print("-" * 30)
    
    test_query() 