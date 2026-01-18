try:
    import webrtcvad
    USE_REAL_VAD = True
except ImportError:
    print("⚠️ webrtcvad not installed, using dummy VAD for testing")
    USE_REAL_VAD = False

import collections
from typing import Optional

if USE_REAL_VAD:
    # Real VAD implementation
    class VoiceActivityDetector:
        def __init__(self, aggressiveness=3, sample_rate=16000):
            print(f"🎙️ Initializing VAD (aggressiveness={aggressiveness})")
            self.vad = webrtcvad.Vad(aggressiveness)
            self.sample_rate = sample_rate
            self.frame_duration_ms = 30
            self.bytes_per_frame = int(sample_rate * self.frame_duration_ms / 1000) * 2
            self.ring_buffer_size = 10
            self.ring_buffer = collections.deque(maxlen=self.ring_buffer_size)
            self.triggered = False
            self.voiced_frames = []
            self.num_padding_frames = 8
            print(f"✓ VAD initialized")
        
        def process_frame(self, audio_frame: bytes) -> Optional[bytes]:
            if len(audio_frame) != self.bytes_per_frame:
                return None
            
            is_speech = self.vad.is_speech(audio_frame, self.sample_rate)
            
            if not hasattr(self, '_frame_count'):
                self._frame_count = 0
            self._frame_count += 1
            
            if self._frame_count % 10 == 0:
                status = "🗣️ SPEECH" if is_speech else "🤫 SILENCE"
                print(f"Frame {self._frame_count}: {status}")
            
            if not self.triggered:
                self.ring_buffer.append((audio_frame, is_speech))
                num_voiced = len([f for f, speech in self.ring_buffer if speech])
                
                if num_voiced > 0.5 * self.ring_buffer.maxlen:
                    print("🎤 SPEECH STARTED")
                    self.triggered = True
                    self.voiced_frames.extend([f for f, s in self.ring_buffer])
                    self.ring_buffer.clear()
            else:
                self.voiced_frames.append(audio_frame)
                self.ring_buffer.append((audio_frame, is_speech))
                num_unvoiced = len([f for f, speech in self.ring_buffer if not speech])
                
                if num_unvoiced > 0.8 * self.ring_buffer.maxlen:
                    print("⏸️ PAUSE DETECTED")
                    self.triggered = False
                    audio_segment = b''.join(self.voiced_frames)
                    self.voiced_frames = []
                    self.ring_buffer.clear()
                    return audio_segment
            
            return None
        
        def reset(self):
            self.triggered = False
            self.voiced_frames = []
            self.ring_buffer.clear()
            self._frame_count = 0

else:
    # Dummy VAD for testing (triggers after collecting enough audio)
    class VoiceActivityDetector:
        def __init__(self, aggressiveness=3, sample_rate=16000):
            print(f"🎙️ Initializing DUMMY VAD (testing mode - no webrtcvad)")
            self.sample_rate = sample_rate
            self.frame_duration_ms = 30
            self.bytes_per_frame = int(sample_rate * self.frame_duration_ms / 1000) * 2
            self.voiced_frames = []
            self.frame_count = 0
            self.frames_threshold = 17  # ~500ms = 17 frames of 30ms
            print(f"✓ Dummy VAD initialized (will trigger after {self.frames_threshold} frames)")
            print(f"⚠️ Note: This is a TESTING mode. For production, install webrtcvad.")
        
        def process_frame(self, audio_frame: bytes) -> Optional[bytes]:
            if len(audio_frame) != self.bytes_per_frame:
                print(f"⚠️ Warning: Expected {self.bytes_per_frame} bytes, got {len(audio_frame)}")
                return None
            
            self.frame_count += 1
            self.voiced_frames.append(audio_frame)
            
            # Debug log
            if self.frame_count % 10 == 0:
                print(f"Frame {self.frame_count}: Collecting... ({len(self.voiced_frames)} frames buffered)")
            
            # Trigger after threshold
            if len(self.voiced_frames) >= self.frames_threshold:
                print(f"⏸️ TRIGGER - Word complete! (Collected {len(self.voiced_frames)} frames = ~{len(self.voiced_frames)*30}ms)")
                
                audio_segment = b''.join(self.voiced_frames)
                print(f"   Total audio: {len(audio_segment)} bytes")
                
                # Reset for next word
                self.voiced_frames = []
                
                return audio_segment
            
            return None
        
        def reset(self):
            print("🔄 Resetting Dummy VAD")
            self.voiced_frames = []
            self.frame_count = 0