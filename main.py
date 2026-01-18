from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import services
from services.vad_processor import VoiceActivityDetector
from services.audio_processor import AudioProcessor
from services.transcriber import WhisperTranscriber
from services.database import QuranDatabase
from services.text_matcher import ArabicTextMatcher

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:123456@localhost:5432/quran_db")
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8000))

print(f"\n{'='*60}")
print(f"🚀 Starting Quran Recitation Server")
print(f"{'='*60}")
print(f"Database: {DATABASE_URL}")
print(f"Server: {HOST}:{PORT}")
print(f"{'='*60}\n")

app = FastAPI(title="Quran Recitation API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
audio_processor = AudioProcessor()
transcriber = WhisperTranscriber()  # Uses API key from .env
text_matcher = ArabicTextMatcher()
db = QuranDatabase(DATABASE_URL)


class RecitationSession:
    def __init__(self, surah: int, ayah: int):
        self.surah = surah
        self.ayah = ayah
        self.vad = VoiceActivityDetector(aggressiveness=3)
        self.current_word_index = 0
        self.expected_words = db.get_ayah_words(surah, ayah)
        self.results = []
        print(f"\n{'='*60}")
        print(f"📖 NEW SESSION: Surah {surah}, Ayah {ayah}")
        print(f"📝 Expected words: {self.expected_words}")
        print(f"{'='*60}\n")
    
    def process_audio_chunk(self, chunk: bytes):
        audio_segment = self.vad.process_frame(chunk)
        
        if not audio_segment:
            return None
        
        if self.current_word_index >= len(self.expected_words):
            return {'type': 'complete', 'message': 'All words completed'}
        
        expected_word = self.expected_words[self.current_word_index]
        
        print(f"\n{'='*60}")
        print(f"🎯 PROCESSING WORD #{self.current_word_index + 1}")
        print(f"{'='*60}")
        
        try:
            wav_path = audio_processor.process_pcm_to_wav(audio_segment)
            transcription = transcriber.transcribe(wav_path)
            user_said = transcription['text']
            comparison = text_matcher.compare_words(expected_word, user_said)
            
            result = {
                'type': 'word_result',
                'word_index': self.current_word_index,
                **comparison
            }
            
            self.results.append(result)
            self.current_word_index += 1
            
            print(f"\n{'='*60}")
            print(f"✅ WORD PROCESSED SUCCESSFULLY")
            print(f"{'='*60}\n")
            
            return result
            
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            return {'type': 'error', 'message': str(e)}
    
    def is_complete(self):
        return self.current_word_index >= len(self.expected_words)


@app.websocket("/ws/live-recite")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("\n🔌 WebSocket connection established")
    
    session = None
    
    try:
        while True:
            data = await websocket.receive()
            
            if 'text' in data:
                message = json.loads(data['text'])
                print(f"📥 Received: {message}")
                
                if message.get('type') == 'init':
                    session = RecitationSession(message['surah'], message['ayah'])
                    await websocket.send_json({
                        'type': 'session_started',
                        'expected_words': session.expected_words
                    })
            
            elif 'bytes' in data and session:
                result = session.process_audio_chunk(data['bytes'])
                if result:
                    await websocket.send_json(result)
                    
                    if session.is_complete():
                        await websocket.send_json({
                            'type': 'session_complete',
                            'results': session.results
                        })
                        break
    
    except WebSocketDisconnect:
        print("🔌 Client disconnected")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await websocket.close()


@app.get("/")
def root():
    return {
        "message": "Quran Recitation API",
        "status": "running",
        "version": "1.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)