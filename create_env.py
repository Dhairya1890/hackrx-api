import os

def create_env_file():
    """Create .env file with template"""
    print("🔧 Creating .env file")
    print("=" * 50)
    
    env_content = """# Add your API keys here
GEMINI_API_KEY=your_gemini_api_key_here
PINECONE_API_KEY=your_pinecone_api_key_here
"""
    
    try:
        with open('.env', 'w') as f:
            f.write(env_content)
        print("✅ .env file created successfully!")
        print("\n📝 Please edit the .env file and add your actual API keys:")
        print("1. Open .env file in your editor")
        print("2. Replace 'your_gemini_api_key_here' with your actual Gemini API key")
        print("3. Replace 'your_pinecone_api_key_here' with your actual Pinecone API key")
        print("4. Save the file")
        print("\nThen run: python env_setup.py")
        
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")

if __name__ == "__main__":
    create_env_file() 