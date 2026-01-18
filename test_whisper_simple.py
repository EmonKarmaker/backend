import os
from dotenv import load_dotenv
import requests

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    print("❌ OPENAI_API_KEY not found!")
    exit(1)

print(f"✓ API Key: {api_key[:10]}...{api_key[-4:]}")

# Create a simple test audio file
print("\nCreating test audio file...")

import wave
import struct
import math

# Generate 1 second of sine wave (test audio)
sample_rate = 16000
duration = 1.0
frequency = 440  # A note

with wave.open('test_audio.wav', 'w') as wav_file:
    wav_file.setnchannels(1)  # Mono
    wav_file.setsampwidth(2)  # 16-bit
    wav_file.setframerate(sample_rate)
    
    for i in range(int(sample_rate * duration)):
        value = int(32767 * 0.3 * math.sin(2 * math.pi * frequency * i / sample_rate))
        wav_file.writeframes(struct.pack('<h', value))

print("✓ Test audio file created")

# Test Whisper API with direct HTTP request
print("\nTesting Whisper API...")

try:
    url = "https://api.openai.com/v1/audio/transcriptions"
    
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    
    files = {
        "file": ("test.wav", open("test_audio.wav", "rb"), "audio/wav")
    }
    
    data = {
        "model": "whisper-1",
        "language": "ar"
    }
    
    response = requests.post(url, headers=headers, files=files, data=data)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ API Test Successful!")
        print(f"✅ Response: {result}")
    else:
        print(f"❌ API Error: {response.status_code}")
        print(f"Response: {response.text}")
        
except Exception as e:
    print(f"❌ Error: {e}")

# Clean up
if os.path.exists('test_audio.wav'):
    os.remove('test_audio.wav')
    print("\n✓ Cleaned up test file")