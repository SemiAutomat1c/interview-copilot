"""
Audio handler for Interview Copilot.
Captures and transcribes audio using Vosk (real-time) with optional Google fallback.
Enhanced with buffer management and restart capabilities.
"""
import speech_recognition as sr
import logging
import queue
import threading
import pyaudio
import time
from typing import Optional, Callable

from src.vosk_handler import VoskStreamHandler

logger = logging.getLogger(__name__)

# Audio settings for Vosk (16kHz mono is optimal)
VOSK_SAMPLE_RATE = 16000
VOSK_CHANNELS = 1
VOSK_CHUNK_SIZE = 4000  # ~250ms of audio at 16kHz


class AudioHandler:
    """Handles audio capture and speech-to-text transcription with Vosk streaming."""
    
    def __init__(
        self,
        callback: Optional[Callable[[str], None]] = None,
        use_system_audio: bool = True,
        on_listening_start: Optional[Callable[[], None]] = None,
        on_audio_received: Optional[Callable[[], None]] = None,
        on_partial_transcription: Optional[Callable[[str], None]] = None,
        transcription_engine: str = "vosk",
        vosk_model_size: str = "small",
        use_google_refinement: bool = False
    ):
        """
        Initialize audio handler.
        
        Args:
            callback: Function to call when final transcription is ready
            use_system_audio: If True, try to use BlackHole for system audio capture
            on_listening_start: Callback when listening starts/resumes
            on_audio_received: Callback when audio is detected (for UI feedback)
            on_partial_transcription: Callback for real-time partial transcriptions
            transcription_engine: "vosk", "google", or "hybrid"
            vosk_model_size: "small" (~50MB) or "large" (~1.8GB)
            use_google_refinement: If True, refine Vosk results with Google
        """
        self.callback = callback
        self.on_listening_start = on_listening_start
        self.on_audio_received = on_audio_received
        self.on_partial_transcription = on_partial_transcription
        self.use_system_audio = use_system_audio
        
        # Transcription settings
        self.transcription_engine = transcription_engine
        self.vosk_model_size = vosk_model_size
        self.use_google_refinement = use_google_refinement
        
        # State
        self.is_listening = False
        self._stop_event = threading.Event()
        self._audio_thread: Optional[threading.Thread] = None
        
        # Vosk handler
        self.vosk_handler: Optional[VoskStreamHandler] = None
        
        # Google recognizer (for fallback)
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = False
        
        # Transcription buffer for accumulating results
        self.transcription_buffer = []
        self.buffer_lock = threading.Lock()
        self.last_transcription_time = 0
        
        # Device info
        self.device_index = None
        self.device_name = "Unknown"
        
        # PyAudio instance
        self._pyaudio: Optional[pyaudio.PyAudio] = None
        self._stream: Optional[pyaudio.Stream] = None
        
        logger.info(f"Audio handler initialized (engine: {transcription_engine})")
    
    def _find_blackhole_device(self) -> Optional[int]:
        """
        Find BlackHole audio device index.
        
        Returns:
            Device index if found, None otherwise
        """
        try:
            if not self._pyaudio:
                self._pyaudio = pyaudio.PyAudio()
            
            for i in range(self._pyaudio.get_device_count()):
                info = self._pyaudio.get_device_info_by_index(i)
                device_name = str(info.get('name', '')).lower()
                
                if 'blackhole' in device_name:
                    logger.info(f"Found BlackHole device: {info.get('name')} (index {i})")
                    self.device_name = str(info.get('name', 'BlackHole'))
                    return i
            
            logger.warning("BlackHole device not found, using default microphone")
            logger.warning("To capture browser audio, install BlackHole: brew install blackhole-2ch")
            return None
            
        except Exception as e:
            logger.error(f"Error finding BlackHole device: {e}")
            return None
    
    def start_listening(
        self,
        progress_callback: Optional[Callable[[int], None]] = None
    ) -> bool:
        """
        Start continuous listening with real-time transcription.
        
        Args:
            progress_callback: Called with model download progress (0-100)
            
        Returns:
            True if successfully started
        """
        try:
            # Initialize PyAudio
            if not self._pyaudio:
                self._pyaudio = pyaudio.PyAudio()
            
            # Find audio device
            self.device_index = None
            if self.use_system_audio:
                self.device_index = self._find_blackhole_device()
                if self.device_index is None:
                    self.device_name = "Default Microphone"
            else:
                self.device_name = "Default Microphone"
            
            # Initialize Vosk handler if using Vosk
            if self.transcription_engine in ("vosk", "hybrid"):
                self.vosk_handler = VoskStreamHandler(
                    sample_rate=VOSK_SAMPLE_RATE,
                    on_partial=self._handle_partial_transcription,
                    on_final=self._handle_final_transcription,
                    model_size=self.vosk_model_size
                )
                
                if not self.vosk_handler.start(progress_callback):
                    logger.error("Failed to start Vosk handler")
                    return False
            
            # Start audio capture thread
            self._stop_event.clear()
            self._audio_thread = threading.Thread(
                target=self._audio_capture_loop,
                daemon=True,
                name="AudioCapture"
            )
            self._audio_thread.start()
            
            self.is_listening = True
            
            if self.on_listening_start:
                self.on_listening_start()
            
            logger.info("Started continuous listening with Vosk")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start listening: {e}", exc_info=True)
            return False
    
    def _audio_capture_loop(self):
        """Background thread for capturing audio and feeding to Vosk."""
        try:
            # Open audio stream
            self._stream = self._pyaudio.open(
                format=pyaudio.paInt16,
                channels=VOSK_CHANNELS,
                rate=VOSK_SAMPLE_RATE,
                input=True,
                input_device_index=self.device_index,
                frames_per_buffer=VOSK_CHUNK_SIZE
            )
            
            logger.info(f"Audio stream opened (device: {self.device_name})")
            
            while not self._stop_event.is_set():
                try:
                    # Read audio chunk
                    audio_data = self._stream.read(
                        VOSK_CHUNK_SIZE,
                        exception_on_overflow=False
                    )
                    
                    # Notify audio received
                    if self.on_audio_received:
                        self.on_audio_received()
                    
                    # Feed to Vosk
                    if self.vosk_handler:
                        self.vosk_handler.feed_audio(audio_data)
                    
                except Exception as e:
                    if not self._stop_event.is_set():
                        logger.error(f"Error reading audio: {e}")
                    break
            
        except Exception as e:
            logger.error(f"Audio capture loop error: {e}")
        finally:
            self._cleanup_stream()
    
    def _cleanup_stream(self):
        """Clean up audio stream resources."""
        if self._stream:
            try:
                self._stream.stop_stream()
                self._stream.close()
            except Exception as e:
                logger.error(f"Error cleaning up audio stream: {e}")
            finally:
                self._stream = None
    
    def _handle_partial_transcription(self, text: str):
        """Handle partial (in-progress) transcription from Vosk."""
        if self.on_partial_transcription:
            # Combine with buffer for full context
            buffer_text = self.get_buffer_text()
            if buffer_text:
                full_text = f"{buffer_text} {text}"
            else:
                full_text = text
            self.on_partial_transcription(full_text)
    
    def _handle_final_transcription(self, text: str):
        """Handle final transcription from Vosk."""
        if text:
            logger.info(f"Transcribed: {text}")
            self.last_transcription_time = time.time()
            
            # Add to buffer
            with self.buffer_lock:
                self.transcription_buffer.append(text)
            
            # Call the user-provided callback
            if self.callback:
                self.callback(text)
            
            # Update partial display with full buffer
            if self.on_partial_transcription:
                self.on_partial_transcription(self.get_buffer_text())
    
    def stop_listening(self) -> None:
        """Stop continuous listening."""
        self._stop_event.set()
        
        if self._audio_thread:
            self._audio_thread.join(timeout=2.0)
        
        if self.vosk_handler:
            self.vosk_handler.stop()
        
        self._cleanup_stream()
        
        if self._pyaudio:
            try:
                self._pyaudio.terminate()
            except Exception as e:
                logger.error(f"Error terminating PyAudio: {e}")
            finally:
                self._pyaudio = None
        
        self.is_listening = False
        logger.info("Stopped listening")
    
    def restart_listening(self) -> bool:
        """
        Restart the listening process.
        
        Returns:
            True if successfully restarted
        """
        logger.info("Restarting listening...")
        self.stop_listening()
        self.clear_buffer()
        time.sleep(0.3)
        return self.start_listening()
    
    def get_buffer_text(self) -> str:
        """Get all accumulated text from the buffer."""
        with self.buffer_lock:
            return " ".join(self.transcription_buffer)
    
    def clear_buffer(self) -> None:
        """Clear the transcription buffer."""
        with self.buffer_lock:
            self.transcription_buffer.clear()
        if self.vosk_handler:
            self.vosk_handler.clear_buffer()
        logger.debug("Transcription buffer cleared")
    
    def pop_buffer(self) -> str:
        """Get and clear the buffer (atomic operation)."""
        with self.buffer_lock:
            text = " ".join(self.transcription_buffer)
            self.transcription_buffer.clear()
        return text
    
    def get_buffer_word_count(self) -> int:
        """Get the word count of buffered text."""
        text = self.get_buffer_text()
        return len(text.split()) if text.strip() else 0
    
    def get_device_info(self) -> dict:
        """Get information about the current audio device."""
        return {
            "name": self.device_name,
            "index": self.device_index,
            "is_listening": self.is_listening,
            "engine": self.transcription_engine,
            "vosk_model": self.vosk_model_size
        }
    
    def test_microphone(self) -> bool:
        """
        Test microphone access and functionality.
        
        Returns:
            True if microphone is accessible
        """
        try:
            if not self._pyaudio:
                self._pyaudio = pyaudio.PyAudio()
            
            device_idx = None
            if self.use_system_audio:
                device_idx = self._find_blackhole_device()
                if device_idx is not None:
                    logger.info("Testing BlackHole device")
            
            # Try to open stream briefly
            stream = self._pyaudio.open(
                format=pyaudio.paInt16,
                channels=VOSK_CHANNELS,
                rate=VOSK_SAMPLE_RATE,
                input=True,
                input_device_index=device_idx,
                frames_per_buffer=VOSK_CHUNK_SIZE
            )
            stream.read(VOSK_CHUNK_SIZE)
            stream.stop_stream()
            stream.close()
            
            logger.info("Audio device test successful")
            return True
            
        except Exception as e:
            logger.error(f"Audio device test failed: {e}")
            logger.warning("Attempting to continue anyway...")
            return True  # Don't block initialization
