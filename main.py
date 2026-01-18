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
print("🎵 Initializing Audio Processor...")
audio_processor = AudioProcessor()

print("🤖 Initializing Whisper Transcriber...")
transcriber = WhisperTranscriber()  # Uses OpenAI API

print("🔤 Initializing Text Matcher...")
text_matcher = ArabicTextMatcher()

print("📚 Initializing Database...")
db = QuranDatabase(DATABASE_URL)

print("\n✅ All services initialized!\n")


class RecitationSession:
    """Manages a single recitation session"""
    
    def __init__(self, surah: int, ayah: int):
        self.surah = surah
        self.ayah = ayah
        self.vad = VoiceActivityDetector(aggressiveness=3)
        self.current_word_index = 0
        self.expected_words = db.get_ayah_words(surah, ayah)  # List of dicts with harakat
        self.results = []
        
        print(f"\n{'='*60}")
        print(f"📖 NEW SESSION: Surah {surah}, Ayah {ayah}")
        print(f"📝 Total words: {len(self.expected_words)}")
        print(f"📝 With harakat: {' '.join([w['with_harakat'] for w in self.expected_words])}")
        print(f"📝 Simple text: {' '.join([w['simple'] for w in self.expected_words])}")
        print(f"{'='*60}\n")
    
    def process_audio_chunk(self, chunk: bytes):
        """
        Process one audio chunk through the pipeline
        
        Returns:
            dict: Result if word completed, None otherwise
        """
        # Step 1: VAD processes chunk
        audio_segment = self.vad.process_frame(chunk)
        
        if not audio_segment:
            return None
        
        # Check if all words completed
        if self.current_word_index >= len(self.expected_words):
            return {'type': 'complete', 'message': 'All words completed'}
        
        # Get expected word (simple version for comparison)
        expected_word_simple = self.expected_words[self.current_word_index]['simple']
        expected_word_harakat = self.expected_words[self.current_word_index]['with_harakat']
        
        print(f"\n{'='*60}")
        print(f"🎯 PROCESSING WORD #{self.current_word_index + 1}/{len(self.expected_words)}")
        print(f"📝 Expected (simple): {expected_word_simple}")
        print(f"📝 Expected (harakat): {expected_word_harakat}")
        print(f"{'='*60}")
        
        try:
            # Step 2: Audio processing (Pydub)
            print("\n🔧 Step 1: Audio Processing...")
            wav_path = audio_processor.process_pcm_to_wav(audio_segment)
            print(f"✓ WAV file created: {wav_path}")
            
            # Step 3: Transcription (OpenAI Whisper API)
            print("\n🎤 Step 2: Transcription...")
            transcription = transcriber.transcribe(wav_path)
            user_said = transcription['text']
            print(f"✓ User said: '{user_said}'")
            
            # Step 4: Text comparison
            print("\n🔍 Step 3: Text Comparison...")
            comparison = text_matcher.compare_words(expected_word_simple, user_said)
            print(f"✓ Similarity: {comparison['similarity']}%")
            print(f"✓ Status: {comparison['status']}")
            print(f"✓ Color: {comparison['color']}")
            
            # Step 5: Prepare result
            result = {
                'type': 'word_result',
                'word_index': self.current_word_index,
                'expected': expected_word_simple,
                'expected_with_harakat': expected_word_harakat,
                **comparison
            }
            
            self.results.append(result)
            self.current_word_index += 1
            
            print(f"\n{'='*60}")
            print(f"✅ WORD PROCESSED SUCCESSFULLY")
            print(f"Progress: {self.current_word_index}/{len(self.expected_words)}")
            print(f"{'='*60}\n")
            
            return result
            
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            return {
                'type': 'error',
                'message': str(e),
                'word_index': self.current_word_index
            }
    
    def is_complete(self):
        """Check if all words have been evaluated"""
        return self.current_word_index >= len(self.expected_words)
    
    def get_final_stats(self):
        """Calculate final session statistics"""
        if not self.results:
            return {
                'total_words': 0,
                'correct_words': 0,
                'overall_accuracy': 0.0
            }
        
        total = len(self.results)
        correct = sum(1 for r in self.results if r.get('status') == 'correct')
        avg_similarity = sum(r.get('similarity', 0) for r in self.results) / total
        
        return {
            'total_words': total,
            'correct_words': correct,
            'overall_accuracy': round(avg_similarity, 2),
            'results': self.results
        }


@app.websocket("/ws/live-recite")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for live recitation evaluation
    
    Protocol:
    1. Client sends: {"type": "init", "surah": 1, "ayah": 1}
    2. Server responds: {"type": "session_started", "expected_words": [...]}
    3. Client streams audio chunks (binary data)
    4. Server sends results: {"type": "word_result", ...}
    5. Server sends: {"type": "session_complete", ...}
    """
    await websocket.accept()
    print("\n🔌 WebSocket connection established")
    
    session = None
    
    try:
        while True:
            data = await websocket.receive()
            
            # Handle text messages (JSON)
            if 'text' in data:
                message = json.loads(data['text'])
                print(f"📥 Received message: {message.get('type', 'unknown')}")
                
                if message.get('type') == 'init':
                    surah = message.get('surah', 1)
                    ayah = message.get('ayah', 1)
                    
                    # Create new session
                    session = RecitationSession(surah, ayah)
                    
                    # Send session start confirmation with harakat
                    response = {
                        'type': 'session_started',
                        'surah': surah,
                        'ayah': ayah,
                        'expected_words': [w['simple'] for w in session.expected_words],
                        'expected_words_with_harakat': [w['with_harakat'] for w in session.expected_words],
                        'total_words': len(session.expected_words)
                    }
                    
                    print(f"📤 Sending session_started")
                    await websocket.send_json(response)
            
            # Handle binary data (audio chunks)
            elif 'bytes' in data and session:
                chunk = data['bytes']
                
                # Process audio chunk
                result = session.process_audio_chunk(chunk)
                
                if result:
                    print(f"📤 Sending result: {result.get('type')}")
                    await websocket.send_json(result)
                    
                    # Check if session complete
                    if session.is_complete():
                        final_stats = session.get_final_stats()
                        
                        completion_message = {
                            'type': 'session_complete',
                            **final_stats
                        }
                        
                        print(f"📤 Sending session_complete")
                        print(f"📊 Stats: {final_stats['correct_words']}/{final_stats['total_words']} correct ({final_stats['overall_accuracy']}%)")
                        
                        await websocket.send_json(completion_message)
                        break
    
    except WebSocketDisconnect:
        print("🔌 Client disconnected")
    
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
        import traceback
        traceback.print_exc()
        
        try:
            await websocket.send_json({
                'type': 'error',
                'message': str(e)
            })
        except:
            pass
    
    finally:
        try:
            await websocket.close()
            print("🔌 WebSocket closed")
        except:
            pass


@app.get("/")
def root():
    """Health check endpoint"""
    return {
        "message": "Quran Recitation API",
        "status": "running",
        "version": "2.0",
        "features": {
            "harakat_support": True,
            "openai_whisper": True,
            "real_time_evaluation": True
        }
    }


@app.get("/api/surahs")
def get_surahs():
    """Get list of all Surahs"""
    try:
        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT surah_number, name_arabic, name_english, name_transliteration, total_ayahs
            FROM surahs
            ORDER BY surah_number
        """)
        
        surahs = []
        for row in cursor.fetchall():
            surahs.append({
                'number': row[0],
                'name_arabic': row[1],
                'name_english': row[2],
                'name_transliteration': row[3],
                'total_ayahs': row[4]
            })
        
        cursor.close()
        return {'surahs': surahs, 'total': len(surahs)}
    
    except Exception as e:
        return {'error': str(e)}


@app.get("/api/surah/{surah_number}/ayah/{ayah_number}")
def get_ayah(surah_number: int, ayah_number: int):
    """Get specific ayah with harakat"""
    try:
        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT a.text_uthmani, a.text_simple, a.translation_en
            FROM ayahs a
            JOIN surahs s ON a.surah_id = s.id
            WHERE s.surah_number = %s AND a.ayah_number = %s
        """, (surah_number, ayah_number))
        
        result = cursor.fetchone()
        
        if not result:
            return {'error': 'Ayah not found'}
        
        # Get words
        words = db.get_ayah_words(surah_number, ayah_number)
        
        cursor.close()
        
        return {
            'surah': surah_number,
            'ayah': ayah_number,
            'text_with_harakat': result[0],
            'text_simple': result[1],
            'translation': result[2],
            'words': words,
            'total_words': len(words)
        }
    
    except Exception as e:
        return {'error': str(e)}


if __name__ == "__main__":
    import uvicorn
    
    print(f"\n{'='*60}")
    print(f"🚀 STARTING SERVER")
    print(f"{'='*60}")
    print(f"URL: http://{HOST}:{PORT}")
    print(f"WebSocket: ws://{HOST}:{PORT}/ws/live-recite")
    print(f"{'='*60}\n")
    
    uvicorn.run(app, host=HOST, port=PORT)