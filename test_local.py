import subprocess
import time
import requests
import json
import os
import signal
import sys

def start_local_server():
    """Start the FastAPI server locally"""
    print("Starting local server...")
    try:
        # Start the server in background
        process = subprocess.Popen(
            [sys.executable, "app.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait a bit for server to start
        time.sleep(3)
        
        return process
    except Exception as e:
        print(f"Failed to start server: {e}")
        return None

def test_local_api():
    """Test the API locally"""
    print("Testing local API...")
    
    # Test health endpoint
    try:
        response = requests.get("http://localhost:8000/")
        print(f"Health check status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Health check failed: {e}")
        return False
    
    # Test query endpoint
    try:
        payload = {
            "query": "What is covered under my health insurance policy?"
        }
        response = requests.post(
            "http://localhost:8000/query",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        print(f"Query status: {response.status_code}")
        print(f"Response: {response.json()}")
        return True
    except Exception as e:
        print(f"Query test failed: {e}")
        return False

def main():
    print("🧪 Local API Testing")
    print("=" * 50)
    
    # Load environment variables from .env file
    from dotenv import load_dotenv
    load_dotenv()
    
    # Check if environment variables are set
    gemini_key = os.getenv("GEMINI_API_KEY")
    pinecone_key = os.getenv("PINECONE_API_KEY")
    
    print(f"GEMINI_API_KEY set: {'✅' if gemini_key else '❌'}")
    print(f"PINECONE_API_KEY set: {'✅' if pinecone_key else '❌'}")
    
    if not gemini_key or not pinecone_key:
        print("\n⚠️  Environment variables not set!")
        print("Please set GEMINI_API_KEY and PINECONE_API_KEY")
        print("You can create a .env file with:")
        print("GEMINI_API_KEY=your_gemini_key")
        print("PINECONE_API_KEY=your_pinecone_key")
        return
    
    # Start server
    process = start_local_server()
    if not process:
        print("Failed to start server")
        return
    
    try:
        # Test the API
        success = test_local_api()
        
        if success:
            print("\n✅ Local API is working!")
            print("If local works but Render doesn't, check:")
            print("1. Environment variables in Render dashboard")
            print("2. Render logs for startup errors")
            print("3. Correct URL in your requests")
        else:
            print("\n❌ Local API has issues")
            print("Fix local issues before deploying to Render")
            
    finally:
        # Clean up
        print("\nStopping local server...")
        process.terminate()
        process.wait()

if __name__ == "__main__":
    main() 