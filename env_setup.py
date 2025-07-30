import os
from dotenv import load_dotenv

def setup_environment():
    """Set up and test environment variables"""
    print("🔧 Environment Setup")
    print("=" * 50)
    
    # Try to load .env file
    env_loaded = load_dotenv()
    print(f"📁 .env file loaded: {'✅' if env_loaded else '❌'}")
    
    # Check environment variables
    gemini_key = os.getenv("GEMINI_API_KEY")
    pinecone_key = os.getenv("PINECONE_API_KEY")
    
    print(f"🔑 GEMINI_API_KEY: {'✅ Set' if gemini_key else '❌ Not set'}")
    print(f"🔑 PINECONE_API_KEY: {'✅ Set' if pinecone_key else '❌ Not set'}")
    
    if not gemini_key or not pinecone_key:
        print("\n⚠️  Missing environment variables!")
        print("\nTo fix this:")
        print("1. Create a .env file in your project root with:")
        print("   GEMINI_API_KEY=your_actual_gemini_key")
        print("   PINECONE_API_KEY=your_actual_pinecone_key")
        print("\n2. Or set them manually:")
        print("   set GEMINI_API_KEY=your_key (Windows)")
        print("   export GEMINI_API_KEY=your_key (Mac/Linux)")
        
        return False
    
    print("\n✅ All environment variables are set!")
    return True

def test_api_keys():
    """Test if the API keys work"""
    print("\n🧪 Testing API Keys")
    print("=" * 50)
    
    try:
        import google.generativeai as genai
        from pinecone import Pinecone
        
        # Test Gemini
        gemini_key = os.getenv("GEMINI_API_KEY")
        genai.configure(api_key=gemini_key)
        print("✅ Gemini configured successfully")
        
        # Test Pinecone
        pinecone_key = os.getenv("PINECONE_API_KEY")
        pc = Pinecone(api_key=pinecone_key)
        print("✅ Pinecone configured successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ API key test failed: {e}")
        return False

if __name__ == "__main__":
    if setup_environment():
        test_api_keys()
    else:
        print("\nPlease set up your environment variables first!") 