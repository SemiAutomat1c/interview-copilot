"""
Session Manager for Interview Copilot.
Manages interview context and pre-builds prompts for zero-latency Q&A.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
import json
import os
import uuid
import logging

logger = logging.getLogger(__name__)

SESSION_DIR = os.path.expanduser("~/.interview-copilot")
SESSION_FILE = os.path.join(SESSION_DIR, "session.json")


@dataclass
class InterviewSession:
    """Holds pre-built context for an interview session."""
    session_id: str
    profile: str
    job_context: str
    system_instruction: str
    created_at: str
    
    # Pre-computed messages (built once at session start)
    _system_message: Dict[str, str] = field(default_factory=dict)
    _context_template: str = ""
    
    # Conversation history (limited to last N)
    history: List[Tuple[str, str]] = field(default_factory=list)
    max_history: int = 3
    
    def build_messages(self, question: str) -> List[Dict[str, str]]:
        """
        Build complete Ollama message list with history.
        This uses cached prompts - no re-processing of context.
        
        Args:
            question: The interview question
            
        Returns:
            List of message dicts ready for ollama.chat()
        """
        messages = [self._system_message]
        
        # Add recent conversation history (last 3 exchanges)
        for q, a in self.history[-self.max_history:]:
            messages.append({"role": "user", "content": q})
            messages.append({"role": "assistant", "content": a})
        
        # Add current question with pre-built context template
        user_prompt = self._context_template.format(question=question)
        messages.append({"role": "user", "content": user_prompt})
        
        return messages
    
    def add_exchange(self, question: str, answer: str):
        """
        Record a Q&A exchange in conversation history.
        
        Args:
            question: The question that was asked
            answer: The generated answer
        """
        self.history.append((question, answer))
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
    
    def get_info(self) -> Dict[str, Any]:
        """
        Get session info for UI display.
        
        Returns:
            Dictionary with session metadata
        """
        return {
            "session_id": self.session_id[:8],
            "created_at": self.created_at,
            "profile_preview": self.profile[:50] + "..." if len(self.profile) > 50 else self.profile,
            "history_count": len(self.history),
            "is_active": True
        }
    
    def is_active(self) -> bool:
        """Check if session is active."""
        return bool(self.session_id)


class SessionManager:
    """Manages interview session lifecycle with persistence."""
    
    def __init__(self, default_system_instruction: str = ""):
        """
        Initialize session manager.
        
        Args:
            default_system_instruction: Default system instruction for sessions
        """
        self.default_system_instruction = default_system_instruction
        self.current_session: Optional[InterviewSession] = None
        self._ensure_session_dir()
    
    def _ensure_session_dir(self):
        """Create session directory if it doesn't exist."""
        os.makedirs(SESSION_DIR, exist_ok=True)
    
    def create_session(self, profile: str, job_context: str, 
                       system_instruction: str = None) -> InterviewSession:
        """
        Create a new session with pre-built prompts.
        This is where the ONE-TIME context processing happens.
        
        Args:
            profile: User's professional background
            job_context: Target job description
            system_instruction: Optional system instruction (uses default if None)
            
        Returns:
            Newly created InterviewSession
            
        Raises:
            ValueError: If both profile and job_context are empty
        """
        # Validate inputs
        if not profile.strip() and not job_context.strip():
            raise ValueError("At least one of profile or job_context must be provided")
        
        if not system_instruction:
            system_instruction = self.default_system_instruction
        
        session = InterviewSession(
            session_id=str(uuid.uuid4()),
            profile=profile,
            job_context=job_context,
            system_instruction=system_instruction,
            created_at=datetime.now().isoformat()
        )
        
        # Pre-build messages (ONE TIME COST - never rebuilt during Q&A)
        self._rebuild_session_prompts(session)
        
        self.current_session = session
        self.save_session()
        logger.info(f"Created new session: {session.session_id[:8]}")
        
        return session
    
    def _rebuild_session_prompts(self, session: InterviewSession):
        """
        Build/rebuild the pre-computed prompt templates for a session.
        Called once on session creation and when loading from disk.
        
        Args:
            session: Session to build prompts for
        """
        session._system_message = {"role": "system", "content": session.system_instruction}
        session._context_template = f"""Context about the candidate:
{session.profile}

Job context:
{session.job_context}

Question from interviewer: {{question}}

Provide a concise 2-3 sentence answer that:
- Directly addresses the question
- References specific experience from the profile
- Sounds natural and conversational
- Stays under 100 words

Answer:"""
    
    def has_active_session(self) -> bool:
        """
        Check if a session is currently active.
        
        Returns:
            True if session exists
        """
        return self.current_session is not None
    
    def get_current_session(self) -> Optional[InterviewSession]:
        """
        Get the current active session.
        
        Returns:
            Current session or None
        """
        return self.current_session
    
    def save_session(self):
        """
        Persist current session to disk using atomic write.
        Uses a temporary file and atomic rename to prevent corruption.
        """
        if not self.current_session:
            return
        
        session = self.current_session
        data = {
            "session_id": session.session_id,
            "profile": session.profile,
            "job_context": session.job_context,
            "system_instruction": session.system_instruction,
            "created_at": session.created_at,
            "history": session.history[-session.max_history:]  # Only save limited history
        }
        
        # Use atomic write with temporary file
        temp_file = SESSION_FILE + '.tmp'
        
        try:
            # Write to temporary file first
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            # Atomic rename (on POSIX systems, this is atomic)
            os.replace(temp_file, SESSION_FILE)
            logger.info("Session saved to disk")
            
        except Exception as e:
            logger.error(f"Failed to save session: {e}")
            # Clean up temp file if it exists
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception as cleanup_error:
                logger.error(f"Failed to remove temp file: {cleanup_error}")
    
    def load_session(self) -> Optional[InterviewSession]:
        """
        Load session from disk and rebuild pre-computed prompts.
        
        Returns:
            Restored session or None if no saved session
        """
        if not os.path.exists(SESSION_FILE):
            logger.info("No saved session found")
            return None
        
        try:
            with open(SESSION_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Create session object directly
            session = InterviewSession(
                session_id=data["session_id"],
                profile=data["profile"],
                job_context=data["job_context"],
                system_instruction=data["system_instruction"],
                created_at=data["created_at"]
            )
            
            # Rebuild prompts from saved data (necessary after deserialization)
            self._rebuild_session_prompts(session)
            
            # Restore conversation history
            session.history = [tuple(h) for h in data.get("history", [])]
            
            self.current_session = session
            logger.info(f"Session restored: {session.session_id[:8]} with {len(session.history)} Q&A in history")
            return session
            
        except Exception as e:
            logger.error(f"Failed to load session: {e}")
            return None
    
    def clear_session(self):
        """Clear current session and delete saved file."""
        self.current_session = None
        if os.path.exists(SESSION_FILE):
            try:
                os.remove(SESSION_FILE)
                logger.info("Session cleared")
            except Exception as e:
                logger.error(f"Failed to remove session file: {e}")
