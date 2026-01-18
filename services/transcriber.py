import os
from openai import OpenAI

class WhisperTranscriber:
    """
    Transcribe Arabic audio to text using OpenAI Whisper API
    """
    
    def __init__(self, api_key=None):
        """
        Initialize OpenAI client with API key
        
        Args:
            api_key: OpenAI API key (or loaded from environment)
        """
        print(f"\n🤖 Initializing OpenAI Whisper API...")
        
        # Get API key from parameter or environment variable
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables!")
        
        # Initialize OpenAI client
        self.client = OpenAI(api_key=self.api_key)
        
        print(f"✓ OpenAI Whisper API initialized!")
        print(f"  API Key: {self.api_key[:8]}...{self.api_key[-4:]}")
    
    def transcribe(self, audio_path: str) -> dict:
        """
        Transcribe audio file to Arabic text using OpenAI API
        
        Args:
            audio_path: Path to WAV file
            
        Returns:
            {'text': 'بسم', 'language': 'ar'}
        """
        print(f"\n🎤 Transcribing audio via OpenAI API...")
        print(f"  File: {audio_path}")
        
        try:
            # Open audio file
            with open(audio_path, 'rb') as audio_file:
                
                # Call OpenAI Whisper API
                response = self.client.audio.transcriptions.create(
                    model="whisper-1",           # OpenAI's Whisper model
                    file=audio_file,             # Audio file
                    language="ar",               # Arabic
                    response_format="json",      # JSON response
                    temperature=0.0              # Deterministic output
                )
            
            # Extract text from response
            text = response.text.strip()
            
            print(f"✓ Transcription: '{text}'")
            print(f"  Language: {response.language}")
            
            # Calculate cost (approximate)
            file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)
            estimated_cost = file_size_mb * 0.006  # $0.006 per MB (rough estimate)
            print(f"  Estimated cost: ${estimated_cost:.6f}")
            
            return {
                'text': text,
                'language': response.language or 'ar'
            }
            
        except Exception as e:
            print(f"❌ Transcription error: {e}")
            raise
        
        finally:
            # Clean up temporary file
            if os.path.exists(audio_path):
                os.remove(audio_path)
                print(f"  🗑️ Cleaned up temp file")