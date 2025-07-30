import requests
import json

def test_query_endpoint():
    """Test just the query endpoint"""
    print("🧪 Testing Query Endpoint")
    print("=" * 40)
    
    base_url = "https://hackrx-api-sycy.onrender.com"
    
    # Test with a specific insurance query
    test_queries = [
        "What is covered under my health insurance policy?",
        "Can I claim for dental treatment?",
        "What is the coverage for hospitalization?",
        "Is prescription medication covered?"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. Testing query: {query}")
        
        try:
            payload = {"query": query}
            response = requests.post(
                f"{base_url}/query",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if "error" in data:
                    print(f"   ❌ Error: {data['error']}")
                    if "raw" in data:
                        print(f"   Raw response: {data['raw'][:200]}...")
                else:
                    print(f"   ✅ Success: {json.dumps(data, indent=2)}")
            else:
                print(f"   ❌ HTTP Error: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Request failed: {e}")

if __name__ == "__main__":
    test_query_endpoint() 