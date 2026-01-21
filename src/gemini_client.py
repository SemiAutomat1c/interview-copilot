"""
Gemini Client for Interview Copilot.
Provides enhanced answers using Google's Gemini API as a fallback/enhancement to local LLM.
"""
import logging
import threading
from typing import Dict, Any, Optional, Callable, TYPE_CHECKING

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

if TYPE_CHECKING:
    from src.session_manager import InterviewSession

logger = logging.getLogger(__name__)


class GeminiClient:
    """Client for Google's Gemini API - provides enhanced answers."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Gemini client with configuration.
        
        Args:
            config: Configuration dictionary containing gemini_settings
        """
        self.enabled = False
        self.model_name = "gemini-2.0-flash"
        self.model = None
        
        gemini_settings = config.get("gemini_settings", {})
        
        if not GEMINI_AVAILABLE:
            logger.warning("google-generativeai not installed. Run: pip install google-generativeai")
            return
        
        if not gemini_settings.get("enabled", False):
            logger.info("Gemini is disabled in config")
            return
        
        api_key = gemini_settings.get("api_key", "")
        if not api_key:
            logger.warning("Gemini API key not configured")
            return
        
        try:
            genai.configure(api_key=api_key)
            self.model_name = gemini_settings.get("model", "gemini-2.0-flash")
            self.model = genai.GenerativeModel(self.model_name)
            self.enabled = True
            logger.info(f"Gemini client initialized with model: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}")
    
    def is_available(self) -> bool:
        """Check if Gemini is available and configured."""
        return self.enabled and self.model is not None
    
    def generate_answer_async(
        self,
        session: 'InterviewSession',
        question: str,
        callback: Callable[[str], None],
        error_callback: Optional[Callable[[str], None]] = None
    ) -> None:
        """
        Generate answer asynchronously in background thread.
        
        Args:
            session: Interview session with context
            question: The interview question
            callback: Called with answer when ready
            error_callback: Called with error message if generation fails
        """
        if not self.is_available():
            if error_callback:
                error_callback("Gemini not available")
            return
        
        def _generate():
            try:
                answer = self._generate_answer(session, question)
                if answer:
                    callback(answer)
                elif error_callback:
                    error_callback("Empty response from Gemini")
            except Exception as e:
                logger.error(f"Gemini generation error: {e}")
                if error_callback:
                    error_callback(str(e))
        
        thread = threading.Thread(target=_generate, daemon=True)
        thread.start()
    
    def _generate_answer(self, session: 'InterviewSession', question: str) -> Optional[str]:
        """
        Generate answer using Gemini API.
        
        Args:
            session: Interview session with context
            question: The interview question
            
        Returns:
            Generated answer or None if error
        """
        if not self.model:
            return None
        
        # Build a focused prompt for Gemini
        prompt = f"""You are helping a candidate answer an interview question.

CANDIDATE BACKGROUND:
{session.profile}

TARGET ROLE:
{session.job_context}

INTERVIEW QUESTION:
{question}

INSTRUCTIONS:
1. Answer the question DIRECTLY in 2-3 sentences
2. Only reference the candidate's specific experience if it's directly relevant to the question
3. Be natural and conversational
4. If the question is about something not in the profile, give a thoughtful general answer
5. Do NOT start with "Based on my background..." or similar - just answer naturally

YOUR ANSWER:"""

        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.4,
                    max_output_tokens=150,
                )
            )
            
            answer = response.text.strip()
            logger.info(f"Gemini generated answer: {answer[:100]}...")
            return answer
            
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return None
