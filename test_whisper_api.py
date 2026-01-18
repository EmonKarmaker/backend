from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

# Test API key
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    print("❌ OPENAI_API_KEY not found in .env file!")
    exit(1)

print(f"✓ API Key found: {api_key[:8]}...{api_key[-4:]}")

# Test API connection
try:
    client = OpenAI(api_key=api_key)
    
    # List available models (test connection)
    models = client.models.list()
    print(f"✅ API connection successful!")
    print(f"✅ Available models: {len(models.data)} models")
    
    # Check if whisper-1 is available
    whisper_available = any(m.id == "whisper-1" for m in models.data)
    print(f"✅ Whisper model available: {whisper_available}")
    
except Exception as e:
    print(f"❌ API connection failed: {e}")