#!/usr/bin/env python3
"""
Interview Copilot - Main Application
Real-time interview assistant using local LLM and speech recognition.
Enhanced with manual controls and real-time transcription preview.
"""
import sys
import logging
from logging.handlers import RotatingFileHandler
import signal
import threading
from pathlib import Path
from typing import Optional, Tuple

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config_loader import ConfigLoader
from src.llm_client import LLMClient
from src.audio_handler import AudioHandler
from src.gui import CopilotGUI, TranscriptionState
from src.session_manager import SessionManager, InterviewSession


# Configure logging with rotation
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler(
            'interview_copilot.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class InterviewCopilot:
    """Main application orchestrator with enhanced UX features."""
    
    def __init__(self):
        """Initialize the application."""
        self.config_loader = None
        self.config = None
        self.llm_client: Optional[LLMClient] = None
        self.audio_handler: Optional[AudioHandler] = None
        self.gui: Optional[CopilotGUI] = None
        self.session_manager: Optional[SessionManager] = None
        
        # State tracking
        self.is_processing = False
        self.processing_lock = threading.Lock()
        self.current_buffer = ""
        
        # Auto-process timer
        self.auto_process_timer = None
        self.auto_process_delay = 1500  # ms - delay after last transcription
        
        logger.info("=" * 60)
        logger.info("Interview Copilot Starting (Enhanced Edition)")
        logger.info("=" * 60)
    
    def initialize(self) -> bool:
        """
        Initialize all components.
        
        Returns:
            True if initialization successful
        """
        try:
            # 1. Load configuration
            logger.info("[1/5] Loading configuration...")
            self.config_loader = ConfigLoader("config.json")
            self.config = self.config_loader.load()
            logger.info("Configuration loaded")
            
            # 2. Initialize LLM client
            logger.info("[2/5] Initializing LLM client...")
            self.llm_client = LLMClient(self.config)
            
            # Test Ollama connection
            if not self.llm_client.test_connection():
                logger.error("Failed to connect to Ollama")
                logger.error("  Make sure Ollama is running: brew services start ollama")
                logger.error(f"  And model is installed: ollama pull {self.llm_client.model}")
                return False
            logger.info("Ollama connected")
            
            # 3. Initialize GUI first (we need it for callbacks)
            logger.info("[3/5] Initializing GUI...")
            gui_settings = self.config_loader.get_gui_settings()
            self.gui = CopilotGUI(gui_settings)
            self.gui.create_window()
            
            # Wire up GUI callbacks
            self.gui.on_process_now = self._handle_process_now
            self.gui.on_start_listening = self._handle_start_listening
            self.gui.on_stop_listening = self._handle_stop_listening
            self.gui.on_clear_buffer = self._handle_clear_buffer
            
            # Wire up session callbacks
            self.gui.on_start_session = self._handle_start_session
            self.gui.on_load_config = self._handle_load_config
            
            self.gui.set_state(TranscriptionState.IDLE)
            logger.info("GUI created")
            
            # 4. Initialize audio handler with callbacks
            logger.info("[4/5] Initializing audio handler...")
            audio_settings = self.config.get("audio_settings", {})
            use_system_audio = audio_settings.get("use_system_audio", False)
            
            # Transcription settings (Vosk real-time)
            transcription_settings = self.config.get("transcription_settings", {})
            transcription_engine = transcription_settings.get("engine", "vosk")
            vosk_model_size = transcription_settings.get("vosk_model", "small")
            use_google_refinement = transcription_settings.get("use_google_refinement", False)
            
            self.audio_handler = AudioHandler(
                callback=self._on_transcription,
                use_system_audio=use_system_audio,
                on_listening_start=self._on_listening_start,
                on_audio_received=self._on_audio_received,
                on_partial_transcription=self._on_partial_transcription,
                transcription_engine=transcription_engine,
                vosk_model_size=vosk_model_size,
                use_google_refinement=use_google_refinement
            )
            
            # Test microphone
            if not self.audio_handler.test_microphone():
                logger.error("Microphone not accessible")
                logger.error("  Check System Preferences -> Security & Privacy -> Microphone")
                return False
            logger.info("Microphone accessible")
            
            # 5. Audio handler ready (but not started - user must click Start)
            logger.info("[5/5] Audio handler ready (waiting for user to start)")
            
            # 6. Initialize session manager with defaults from config
            logger.info("[6/7] Initializing session manager...")
            self.session_manager = SessionManager(
                default_system_instruction=self.config.get("system_instruction", "")
            )
            
            # Try to restore previous session
            restored_session = self.session_manager.load_session()
            
            # Pre-populate UI with config defaults or restored session
            if restored_session:
                logger.info(f"Restored session: {restored_session.session_id[:8]}")
                self.gui.set_context_fields(restored_session.profile, restored_session.job_context)
                self.gui.update_session_status(restored_session.get_info())
                self.gui.collapse_context_panel()
            else:
                logger.info("No saved session found, using config defaults")
                self.gui.set_context_fields(
                    self.config.get("my_profile", ""),
                    self.config.get("job_context", "")
                )
            
            logger.info("Session manager initialized")
            
            # 7. Update GUI with device info - start in IDLE state
            device_info = self.audio_handler.get_device_info()
            self.gui.update_status(f"Ready - {device_info['name']}")
            self.gui.set_state(TranscriptionState.IDLE)
            
            logger.info("=" * 60)
            logger.info("All systems ready! Press 'Start Listening' to begin.")
            logger.info("=" * 60)
            self._print_hotkeys()
            
            return True
            
        except FileNotFoundError as e:
            logger.error(f"Configuration error: {e}")
            return False
        except ValueError as e:
            logger.error(f"Configuration validation error: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during initialization: {e}", exc_info=True)
            return False
    
    def _print_hotkeys(self) -> None:
        """Print available hotkeys to console."""
        logger.info("=" * 60)
        logger.info("HOTKEYS:")
        logger.info("  S           : Start/Stop listening")
        logger.info("  Space/Enter : Process transcription NOW")
        logger.info("  Escape      : Clear transcription buffer")
        logger.info("=" * 60)
    
    def _on_listening_start(self) -> None:
        """Callback when listening starts/resumes."""
        if self.gui:
            self.gui.set_state_safe(TranscriptionState.LISTENING)
    
    def _on_audio_received(self) -> None:
        """Callback when audio is detected (before transcription)."""
        # This could be used for a visual "hearing audio" indicator
        pass
    
    def _on_partial_transcription(self, partial_text: str) -> None:
        """
        Callback for real-time partial transcription updates from Vosk.
        This enables live text preview with ~200-500ms latency.
        
        Args:
            partial_text: Current partial transcription (may be incomplete)
        """
        if self.gui:
            self.gui.update_live_transcription_safe(partial_text)
    
    def _on_transcription(self, transcribed_text: str) -> None:
        """
        Callback when audio is transcribed (called from background thread).
        Updates live preview and schedules potential auto-processing.
        
        Args:
            transcribed_text: The transcribed text chunk
        """
        logger.info(f"Transcription received: {transcribed_text}")
        
        if self.gui:
            self._update_live_preview()
            
            # Auto-process disabled - user prefers manual control
            # To re-enable: uncomment the next line
            # self._schedule_auto_process()
    
    def _update_live_preview(self) -> None:
        """Update the live transcription preview on main thread."""
        if not self.audio_handler or not self.gui:
            return
        
        # Get current buffer
        buffer_text = self.audio_handler.get_buffer_text()
        self.current_buffer = buffer_text
        
        # Update live preview
        self.gui.update_live_transcription_safe(buffer_text)
        self.gui.set_state_safe(TranscriptionState.LISTENING)
        self.gui.update_timestamp()
    
    def _schedule_auto_process(self) -> None:
        """Schedule auto-process check after delay."""
        import threading
        
        # Cancel existing timer
        if self.auto_process_timer:
            self.auto_process_timer.cancel()
        
        # Schedule new check
        self.auto_process_timer = threading.Timer(
            self.auto_process_delay / 1000.0,  # Convert ms to seconds
            self._check_auto_process
        )
        self.auto_process_timer.daemon = True
        self.auto_process_timer.start()
    
    def _check_auto_process(self) -> None:
        """Check if we should auto-process based on buffer content."""
        if not self.audio_handler:
            return
        
        word_count = self.audio_handler.get_buffer_word_count()
        
        # Auto-process if we have 4+ words (likely a complete question)
        if word_count >= 4:
            logger.info(f"Auto-processing: {word_count} words in buffer")
            self._handle_process_now()
    
    def _handle_process_now(self) -> None:
        """Handle manual 'Process Now' trigger."""
        # Check if session is active
        if not self.session_manager or not self.session_manager.has_active_session():
            logger.warning("No active session - cannot process question")
            if self.gui:
                self.gui.show_no_session_warning()
            return
        
        with self.processing_lock:
            if self.is_processing:
                logger.info("Already processing, ignoring trigger")
                return
            self.is_processing = True
        
        try:
            if not self.audio_handler or not self.gui or not self.llm_client:
                self.is_processing = False
                return
            
            # Get and clear buffer atomically
            text = self.audio_handler.pop_buffer()
            
            if not text.strip():
                logger.info("No text in buffer to process")
                self.gui.update_live_transcription("")
                self.is_processing = False
                return
            
            logger.info(f"Processing manually triggered text: {text}")
            
            # Update GUI state
            self.gui.set_state(TranscriptionState.TRANSCRIBING)
            self.gui.update_live_transcription("")
            
            # Process in a separate thread to avoid blocking UI
            thread = threading.Thread(
                target=self._process_question,
                args=(text,),
                daemon=True
            )
            thread.start()
            
        except Exception as e:
            logger.error(f"Error in process_now: {e}")
            self.is_processing = False
            if self.gui:
                self.gui.show_error(str(e))
            raise
    
    def _process_question(self, question_text: str) -> None:
        """
        Process question and generate answer (runs in thread).
        
        Args:
            question_text: The transcribed question
        """
        try:
            if not self.gui or not self.llm_client or not self.session_manager:
                return
            
            # Update state (thread-safe)
            self.gui.set_state_safe(TranscriptionState.GENERATING)
            
            # Get current session
            session = self.session_manager.get_current_session()
            if not session:
                logger.error("No active session during processing")
                self.gui.show_error_safe("No active session")
                return
            
            # Generate answer using session context (ZERO re-processing)
            answer = self.llm_client.generate_answer_with_session(session, question_text)
            
            if answer:
                self._display_result(question_text, answer)
                # Save session after each Q&A to persist conversation history
                self.session_manager.save_session()
            else:
                self._display_not_question(question_text)
                
        except Exception as e:
            logger.error(f"Error processing question: {e}")
            if self.gui:
                self.gui.show_error_safe(str(e))
        finally:
            self.is_processing = False
    
    def _display_result(self, question: str, answer: str) -> None:
        """Display question and answer result."""
        if self.gui:
            self.gui.display_question_answer_safe(question, answer)
            logger.info("Result displayed successfully")
    
    def _display_not_question(self, text: str) -> None:
        """Handle case where text wasn't identified as a question."""
        if self.gui:
            # Use thread-safe update
            self.gui.display_question_answer_safe(
                text, 
                "(Not identified as a question - need 4+ words with question indicators)"
            )
            logger.info("Text not identified as question")
    
    def _handle_start_session(self, profile: str, job_context: str) -> None:
        """
        Handle start new session request from GUI.
        
        Args:
            profile: User's professional background
            job_context: Target job description
        """
        if not self.session_manager:
            logger.error("Session manager not initialized")
            if self.gui:
                self.gui.show_error_safe("Session manager not available")
            return
        
        # Validate inputs
        if not profile.strip() and not job_context.strip():
            logger.warning("Cannot create session with empty profile and job context")
            if self.gui:
                self.gui.show_error_safe("Please provide profile or job context")
            return
        
        try:
            logger.info("Creating new session...")
            
            # Create new session (this is where context is processed ONCE)
            session = self.session_manager.create_session(
                profile=profile,
                job_context=job_context
            )
            
            # Update GUI with session info AFTER successful creation
            if self.gui:
                self.gui.update_session_status(session.get_info())
                self.gui.collapse_context_panel()
            
            logger.info(f"Session created: {session.session_id[:8]}")
            
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            if self.gui:
                self.gui.show_error_safe(f"Session creation failed: {str(e)}")
    
    def _handle_load_config(self) -> Tuple[str, str]:
        """
        Load profile and job context from config file.
        
        Returns:
            Tuple of (profile, job_context)
        """
        if not self.config:
            return ("", "")
        
        profile = self.config.get("my_profile", "")
        job_context = self.config.get("job_context", "")
        
        logger.info("Loaded context from config file")
        return (profile, job_context)
    
    def _handle_start_listening(self) -> None:
        """Handle start listening request."""
        if not self.audio_handler or not self.gui:
            return
        
        logger.info("Starting listening...")
        self.gui.set_state_safe(TranscriptionState.IDLE)
        self.gui.update_status_safe("Starting...")
        
        def do_start():
            success = self.audio_handler.start_listening()
            if success:
                self.gui.set_state_safe(TranscriptionState.LISTENING)
                device_info = self.audio_handler.get_device_info()
                self.gui.update_status_safe(f"Listening - {device_info['name']}")
                logger.info("Audio capture started")
            else:
                self.gui.show_error_safe("Failed to start listening")
                logger.error("Failed to start audio capture")
        
        # Start in background thread
        threading.Thread(target=do_start, daemon=True).start()
    
    def _handle_stop_listening(self) -> None:
        """Handle stop listening request."""
        if not self.audio_handler or not self.gui:
            return
        
        logger.info("Stopping listening...")
        
        def do_stop():
            self.audio_handler.stop_listening()
            self.gui.set_state_safe(TranscriptionState.IDLE)
            self.gui.update_status_safe("Stopped")
            logger.info("Audio capture stopped")
        
        # Stop in background thread
        threading.Thread(target=do_stop, daemon=True).start()
    
    def _handle_clear_buffer(self) -> None:
        """Handle clear buffer request."""
        if self.audio_handler:
            self.audio_handler.clear_buffer()
        if self.gui:
            self.gui.update_live_transcription_safe("")
        logger.info("Buffer cleared by user")
    
    def run(self) -> None:
        """Run the main application loop."""
        if not self.initialize():
            logger.error("Initialization failed. Exiting.")
            sys.exit(1)
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Run GUI main loop (blocks until window closed)
        try:
            self.gui.run()
        finally:
            self.shutdown()
    
    def shutdown(self) -> None:
        """Clean shutdown of all components."""
        logger.info("Shutting down...")
        
        if self.audio_handler:
            self.audio_handler.stop_listening()
        
        if self.gui and self.gui.page:
            try:
                self.gui.page.window_destroy()
            except Exception as e:
                logger.warning(f"Error closing GUI: {e}")
        
        logger.info("Interview Copilot stopped")
    
    def _signal_handler(self, signum, frame) -> None:
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}")
        self.shutdown()
        sys.exit(0)


def main():
    """Main entry point."""
    app = InterviewCopilot()
    app.run()


if __name__ == "__main__":
    main()
