import os
import requests

class WhisperTranscriber:
    """
    Transcribe Arabic audio to text using OpenAI Whisper API
    """
    
    def __init__(self, api_key=None):
        """
        Initialize OpenAI Whisper API
        """
        print(f"\n🤖 Initializing OpenAI Whisper API...")
        
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        
        if not self.api_key:
            raise ValueError("❌ OPENAI_API_KEY not found in .env file!")
        
        self.api_url = "https://api.openai.com/v1/audio/transcriptions"
        
        print(f"✓ OpenAI Whisper API initialized!")
        print(f"  API Key: {self.api_key[:10]}...{self.api_key[-4:]}")
    
    def transcribe(self, audio_path: str) -> dict:
        """
        Transcribe audio file to Arabic text using OpenAI API
        """
        print(f"\n🎤 Transcribing via OpenAI API: {audio_path}")
        
        try:
            # Prepare request
            headers = {
                "Authorization": f"Bearer {self.api_key}"
            }
            
            files = {
                "file": (os.path.basename(audio_path), open(audio_path, "rb"), "audio/wav")
            }
            
            data = {
                "model": "whisper-1",
                "language": "ar",
                "response_format": "json"
            }
            
            # Send to OpenAI
            response = requests.post(
                self.api_url,
                headers=headers,
                files=files,
                data=data,
                timeout=30
            )
            
            # Close file
            files["file"][1].close()
            
            # Check response
            if response.status_code == 200:
                result = response.json()
                text = result.get("text", "").strip()
                
                print(f"✓ Transcription: '{text}'")
                
                # Calculate cost
                if "usage" in result:
                    seconds = result["usage"].get("seconds", 0)
                    cost = (seconds / 60) * 0.006
                    print(f"  Duration: {seconds}s | Cost: ${cost:.6f}")
                
                return {
                    "text": text,
                    "language": "ar"
                }
            else:
                error_msg = response.text
                print(f"❌ OpenAI API Error {response.status_code}: {error_msg}")
                raise Exception(f"OpenAI API Error: {error_msg}")
                
        except Exception as e:
            print(f"❌ Transcription error: {e}")
            raise
        
        finally:
            # Clean up temp file
            try:
                if os.path.exists(audio_path):
                    os.remove(audio_path)
                    print(f"  🗑️ Cleaned up temp file")
            except:
                pass