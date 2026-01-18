import os
from dotenv import load_dotenv

load_dotenv()

# Test API key
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    print("❌ OPENAI_API_KEY not found in .env file!")
    exit(1)

print(f"✓ API Key found: {api_key[:8]}...{api_key[-4:]}")

# Test API connection with simple request
try:
    import openai
    
    # Set API key
    openai.api_key = api_key
    
    print(f"✓ OpenAI library version: {openai.__version__}")
    
    # Simple test - list models
    print("Testing API connection...")
    
    # Use new client initialization
    from openai import OpenAI
    client = OpenAI(api_key=api_key)
    
    # Test with a simple API call
    models = client.models.list()
    print(f"✅ API connection successful!")
    print(f"✅ You have access to OpenAI API")
    
except ImportError:
    print("❌ OpenAI library not installed!")
    print("Run: pip install openai --upgrade")
    
except Exception as e:
    print(f"❌ API connection failed: {e}")
    print("\nTroubleshooting:")
    print("1. Check your API key is correct")
    print("2. Check you have credits in your OpenAI account")
    print("3. Check your internet connection")
    print("4. Try: pip install openai --upgrade")