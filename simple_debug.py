import requests

def test_api():
    print("Testing API connectivity...")
    
    url = "https://hackrx-api-sycy.onrender.com"
    
    try:
        print(f"Testing: {url}")
        response = requests.get(url, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:200]}")
        return True
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - App is down")
        return False
    except requests.exceptions.Timeout:
        print("❌ Timeout - App might be starting")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_api() 