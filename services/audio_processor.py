from pydub import AudioSegment
import io
import tempfile
import os

class AudioProcessor:
    """
    Process raw PCM audio chunks into clean WAV files using Pydub
    """
    
    def __init__(self):
        print("🎵 Audio Processor initialized")
    
    def process_pcm_to_wav(self, pcm_bytes: bytes) -> str:
        """
        Convert raw PCM bytes to clean WAV file
        
        Args:
            pcm_bytes: Raw PCM audio data
            
        Returns:
            Path to temporary WAV file
        """
        print(f"\n🔧 Processing {len(pcm_bytes)} bytes of PCM audio...")
        
        try:
            # Step 1: Load raw PCM bytes into AudioSegment
            print("  Step 1: Loading raw PCM bytes")
            audio = AudioSegment.from_raw(
                io.BytesIO(pcm_bytes),
                sample_width=2,      # 16-bit = 2 bytes
                frame_rate=16000,    # 16kHz
                channels=1           # Mono
            )
            print(f"    ✓ Loaded {len(audio)}ms of audio")
            
            # Step 2: Ensure 16kHz sample rate
            print("  Step 2: Ensuring 16kHz sample rate")
            if audio.frame_rate != 16000:
                audio = audio.set_frame_rate(16000)
                print(f"    ✓ Resampled to 16kHz")
            else:
                print(f"    ✓ Already 16kHz")
            
            # Step 3: Ensure mono (single channel)
            print("  Step 3: Ensuring mono channel")
            if audio.channels != 1:
                audio = audio.set_channels(1)
                print(f"    ✓ Converted to mono")
            else:
                print(f"    ✓ Already mono")
            
            # Step 4: Normalize volume levels
            print("  Step 4: Normalizing volume")
            audio = audio.normalize()
            print(f"    ✓ Volume normalized")
            
            # Step 5: Export as clean WAV file
            print("  Step 5: Exporting as WAV")
            temp_file = tempfile.NamedTemporaryFile(
                delete=False, 
                suffix='.wav'
            )
            temp_path = temp_file.name
            temp_file.close()
            
            audio.export(
                temp_path,
                format='wav',
                parameters=[
                    "-ar", "16000",           # Sample rate
                    "-ac", "1",               # Channels
                    "-sample_fmt", "s16"      # 16-bit
                ]
            )
            
            file_size = os.path.getsize(temp_path)
            print(f"    ✓ Exported to {temp_path}")
            print(f"    ✓ File size: {file_size} bytes")
            
            print(f"✓ Audio processing complete!")
            return temp_path
            
        except Exception as e:
            print(f"❌ Audio processing error: {e}")
            raise