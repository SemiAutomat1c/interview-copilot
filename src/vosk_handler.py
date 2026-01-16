"""
Vosk Handler for real-time speech recognition.
Provides streaming transcription with ~200-500ms latency.
"""
import os
import json
import logging
import threading
import queue
import urllib.request
import zipfile
from pathlib import Path
from typing import Optional, Callable
from vosk import Model, KaldiRecognizer

logger = logging.getLogger(__name__)

# Model URLs and sizes
VOSK_MODELS = {
    "small": {
        "url": "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip",
        "name": "vosk-model-small-en-us-0.15",
        "size_mb": 40
    },
    "large": {
        "url": "https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip",
        "name": "vosk-model-en-us-0.22",
        "size_mb": 1800
    }
}


class VoskModelManager:
    """Manages Vosk model downloading and caching."""
    
    def __init__(self, model_size: str = "small"):
        """
        Initialize model manager.
        
        Args:
            model_size: "small" (~40MB) or "large" (~1.8GB)
        """
        self.model_size = model_size
        self.model_info = VOSK_MODELS.get(model_size, VOSK_MODELS["small"])
        
        # Store models in user's cache directory
        self.cache_dir = Path.home() / ".cache" / "interview-copilot" / "vosk-models"
        self.model_path = self.cache_dir / self.model_info["name"]
        
        self._model: Optional[Model] = None
    
    def ensure_model(self, progress_callback: Optional[Callable[[int], None]] = None) -> Path:
        """
        Download model if not present.
        
        Args:
            progress_callback: Called with download percentage (0-100)
            
        Returns:
            Path to the model directory
        """
        if self.model_path.exists():
            logger.info(f"Vosk model found at {self.model_path}")
            return self.model_path
        
        logger.info(f"Downloading Vosk {self.model_size} model (~{self.model_info['size_mb']}MB)...")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        zip_path = self.cache_dir / f"{self.model_info['name']}.zip"
        
        try:
            import requests
            
            # Download with progress using requests (handles SSL properly on macOS)
            response = requests.get(self.model_info["url"], stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback and total_size > 0:
                            percent = int((downloaded / total_size) * 100)
                            progress_callback(min(percent, 100))
            
            # Extract
            logger.info("Extracting model...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(self.cache_dir)
            
            # Clean up zip
            zip_path.unlink()
            
            logger.info(f"Model ready at {self.model_path}")
            return self.model_path
            
        except Exception as e:
            logger.error(f"Failed to download Vosk model: {e}")
            raise
    
    def get_model(self) -> Model:
        """Get or load the Vosk model."""
        if self._model is None:
            model_path = self.ensure_model()
            self._model = Model(str(model_path))
        return self._model


class VoskStreamHandler:
    """
    Handles real-time streaming transcription using Vosk.
    
    Processes audio chunks and emits partial/final transcriptions.
    """
    
    def __init__(
        self,
        sample_rate: int = 16000,
        on_partial: Optional[Callable[[str], None]] = None,
        on_final: Optional[Callable[[str], None]] = None,
        model_size: str = "small"
    ):
        """
        Initialize the Vosk stream handler.
        
        Args:
            sample_rate: Audio sample rate (default 16000 Hz)
            on_partial: Callback for partial (in-progress) transcriptions
            on_final: Callback for final (complete phrase) transcriptions
            model_size: "small" or "large"
        """
        self.sample_rate = sample_rate
        self.on_partial = on_partial
        self.on_final = on_final
        
        self.model_manager = VoskModelManager(model_size)
        self.recognizer: Optional[KaldiRecognizer] = None
        
        self._is_running = False
        self._audio_queue: queue.Queue = queue.Queue()
        self._process_thread: Optional[threading.Thread] = None
        
        # Track accumulated text
        self._current_text = ""
        self._final_buffer = []
        
        logger.info(f"VoskStreamHandler initialized (model: {model_size})")
    
    def start(self, progress_callback: Optional[Callable[[int], None]] = None) -> bool:
        """
        Start the stream handler.
        
        Args:
            progress_callback: Called with model download progress (0-100)
            
        Returns:
            True if successfully started
        """
        try:
            # Ensure model is downloaded
            model = self.model_manager.get_model()
            
            # Create recognizer
            self.recognizer = KaldiRecognizer(model, self.sample_rate)
            self.recognizer.SetWords(True)
            
            # Start processing thread
            self._is_running = True
            self._process_thread = threading.Thread(
                target=self._process_loop,
                daemon=True,
                name="VoskProcessor"
            )
            self._process_thread.start()
            
            logger.info("VoskStreamHandler started")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start VoskStreamHandler: {e}")
            return False
    
    def stop(self):
        """Stop the stream handler."""
        self._is_running = False
        if self._process_thread:
            self._audio_queue.put(None)  # Signal to stop
            self._process_thread.join(timeout=2.0)
        logger.info("VoskStreamHandler stopped")
    
    def feed_audio(self, audio_data: bytes):
        """
        Feed audio data for processing.
        
        Args:
            audio_data: Raw PCM audio bytes (16-bit, mono)
        """
        if self._is_running:
            self._audio_queue.put(audio_data)
    
    def _process_loop(self):
        """Background thread for processing audio."""
        while self._is_running:
            try:
                audio_data = self._audio_queue.get(timeout=0.1)
                if audio_data is None:
                    break
                
                self._process_chunk(audio_data)
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error in Vosk processing loop: {e}")
    
    def _process_chunk(self, audio_data: bytes):
        """Process a single audio chunk."""
        if not self.recognizer:
            return
        
        if self.recognizer.AcceptWaveform(audio_data):
            # Final result for this phrase
            result = json.loads(self.recognizer.Result())
            text = result.get("text", "").strip()
            
            if text:
                self._final_buffer.append(text)
                self._current_text = ""
                
                if self.on_final:
                    self.on_final(text)
                    
                logger.debug(f"Vosk final: {text}")
        else:
            # Partial result (still speaking)
            partial = json.loads(self.recognizer.PartialResult())
            text = partial.get("partial", "").strip()
            
            if text and text != self._current_text:
                self._current_text = text
                
                if self.on_partial:
                    self.on_partial(text)
                    
                logger.debug(f"Vosk partial: {text}")
    
    def get_buffer_text(self) -> str:
        """Get all accumulated final text."""
        return " ".join(self._final_buffer)
    
    def clear_buffer(self):
        """Clear the accumulated text buffer."""
        self._final_buffer.clear()
        self._current_text = ""
    
    def pop_buffer(self) -> str:
        """Get and clear the buffer (atomic operation)."""
        text = self.get_buffer_text()
        self.clear_buffer()
        return text
    
    def get_current_partial(self) -> str:
        """Get the current partial (in-progress) transcription."""
        return self._current_text
