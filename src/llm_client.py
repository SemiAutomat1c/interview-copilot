"""
LLM Client for Interview Copilot.
Handles communication with local Ollama API.
"""
import ollama
import logging
import re
from typing import Dict, Any, Optional, TYPE_CHECKING
import re

if TYPE_CHECKING:
    from src.session_manager import InterviewSession

logger = logging.getLogger(__name__)

# Constants for validation
MAX_QUESTION_LENGTH = 500  # Maximum characters for question
MIN_QUESTION_WORDS = 4  # Minimum words to consider as question


class LLMClient:
    """Client for interfacing with Ollama API."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize LLM client with configuration.
        
        Args:
            config: Configuration dictionary from config_loader
        """
        self.my_profile = config.get("my_profile", "")
        self.job_context = config.get("job_context", "")
        self.system_instruction = config.get("system_instruction", "")
        
        ollama_settings = config.get("ollama_settings", {})
        self.model = ollama_settings.get("model", "llama3.2:3b")
        self.temperature = ollama_settings.get("temperature", 0.3)
        self.max_tokens = ollama_settings.get("max_tokens", 120)
        self.num_ctx = ollama_settings.get("num_ctx", 2048)
        
        logger.info(f"Initialized LLM client with model: {self.model}")
    
    def _validate_and_sanitize_question(self, question: str) -> Optional[str]:
        """
        Validate and sanitize question input before sending to LLM.
        
        Args:
            question: Raw question text
            
        Returns:
            Sanitized question or None if invalid
        """
        # Type check
        if not question or not isinstance(question, str):
            logger.warning("Invalid question type")
            return None
        
        # Trim whitespace
        question = question.strip()
        
        # Check length
        if len(question) > MAX_QUESTION_LENGTH:
            logger.warning(f"Question too long: {len(question)} chars, truncating")
            question = question[:MAX_QUESTION_LENGTH]
        
        # Sanitize - remove control characters
        question = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', question)
        
        # Check minimum length after sanitization
        if len(question) < 5:
            logger.debug("Question too short after sanitization")
            return None
        
        return question
    
    def is_question(self, text: str) -> bool:
        """
        Detect if the input text is a question.
        
        Args:
            text: Input text to analyze
            
        Returns:
            True if text appears to be a question
        """
        if not text or len(text.strip()) < 5:
            return False
        
        text = text.strip().lower()
        
        # Minimum word count to avoid partial questions
        # With manual trigger, user controls when to process
        words = text.split()
        if len(words) < MIN_QUESTION_WORDS:
            logger.debug(f"Question too short ({len(words)} words): '{text}'")
            return False
        
        # Question markers
        question_words = [
            'what', 'when', 'where', 'who', 'why', 'how',
            'can you', 'could you', 'would you', 'will you',
            'do you', 'did you', 'have you', 'are you', 'is there',
            'tell me', 'explain', 'describe', 'walk me through',
            'experience with', 'worked on', 'your background'
        ]
        
        # Common interview preambles to ignore
        preambles = ['great', 'okay', 'alright', 'so', 'now', 'well', 'thanks', 'thank you']
        
        # Remove preambles
        if words and words[0] in preambles:
            text = ' '.join(words[1:])
        
        # Check if starts with question word (after removing preamble)
        if any(text.startswith(word) for word in question_words):
            return True
        
        # Check if question words appear anywhere in text
        if any(word in text for word in question_words):
            return True
        
        # Check if ends with question mark
        if text.endswith('?'):
            return True
        
        return False
    
    def generate_answer_with_session(self, session: 'InterviewSession', 
                                      question: str) -> Optional[str]:
        """
        Generate answer using pre-built session context (ZERO re-processing).
        
        This method uses the session's cached prompts and conversation history,
        eliminating the overhead of rebuilding context on every question.
        
        Args:
            session: Active interview session with pre-built prompts
            question: The interview question
            
        Returns:
            Generated answer or None if error/not a question
        """
        # Validate and sanitize input
        question = self._validate_and_sanitize_question(question)
        if not question:
            logger.debug("Question validation failed")
            return None
        
        # Check if it's a question
        if not self.is_question(question):
            logger.debug(f"Not identified as question: {question}")
            return None
        
        try:
            # Use session's pre-built messages (NO re-processing)
            messages = session.build_messages(question)
            
            logger.info(f"Generating answer for: {question[:50]}...")
            
            response = ollama.chat(
                model=self.model,
                messages=messages,
                stream=False,
                options={
                    "temperature": self.temperature,
                    "num_predict": self.max_tokens,
                    "num_ctx": self.num_ctx
                }
            )
            
            # Validate response structure
            try:
                answer = response.get('message', {}).get('content', '').strip()
                if not answer:
                    raise ValueError("Empty response from LLM")
            except (KeyError, AttributeError, TypeError) as e:
                logger.error(f"Unexpected response structure: {e}")
                logger.debug(f"Response: {response}")
                return "Error: Received invalid response from LLM"
            
            # Record in session history for conversation continuity
            session.add_exchange(question, answer)
            
            logger.info(f"Generated answer: {answer[:100]}...")
            return answer
            
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            return f"Error: Unable to generate answer ({str(e)})"
    
    def generate_answer(self, question: str) -> Optional[str]:
        """
        Generate answer to interview question using Ollama.
        
        Args:
            question: The interview question transcribed from audio
            
        Returns:
            Generated answer or None if error/not a question
        """
        # Skip if not a question
        if not self.is_question(question):
            logger.debug(f"Not identified as question: {question}")
            return None
        
        try:
            # Build the prompt
            prompt = self._build_prompt(question)
            
            # Call Ollama API with streaming
            logger.info(f"Generating answer for: {question[:50]}...")
            
            response = ollama.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_instruction},
                    {"role": "user", "content": prompt}
                ],
                stream=False,
                options={
                    "temperature": self.temperature,
                    "num_predict": self.max_tokens,
                    "num_ctx": self.num_ctx
                }
            )
            
            answer = response['message']['content'].strip()
            logger.info(f"Generated answer: {answer[:100]}...")
            
            return answer
            
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            return f"Error: Unable to generate answer ({str(e)})"
    
    def _build_prompt(self, question: str) -> str:
        """
        Build optimized prompt for Ollama.
        
        Args:
            question: The interview question
            
        Returns:
            Formatted prompt string
        """
        prompt = f"""Context about the candidate:
{self.my_profile}

Job context:
{self.job_context}

Question from interviewer: {question}

Provide a concise 2-3 sentence answer that:
- Directly addresses the question
- References specific experience from the profile
- Sounds natural and conversational
- Stays under 100 words

Answer:"""
        
        return prompt
    
    def test_connection(self) -> bool:
        """
        Test connection to Ollama and verify model availability.
        
        Returns:
            True if connection successful and model available
        """
        try:
            # List available models
            response = ollama.list()
            
            # Handle new API (objects) and old API (dicts)
            model_names = []
            if hasattr(response, 'models'):
                # New API: ListResponse object with models attribute
                model_names = [m.model for m in response.models]
            elif isinstance(response, dict):
                # Old API: dictionary
                model_names = [m.get('name') or m.get('model') for m in response.get('models', [])]
            
            if self.model not in model_names:
                logger.error(
                    f"Model {self.model} not found. Available: {model_names}"
                )
                return False
            
            logger.info(f"Successfully connected to Ollama. Model {self.model} available.")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Ollama: {e}")
            return False
