"""
GUI for Interview Copilot using Flet.
Clean, modern UI inspired by shadcn/ui design system.
"""
import flet as ft
import logging
from typing import Dict, Any, Optional, Callable, List, Tuple
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class TranscriptionState(Enum):
    """State machine for transcription status."""
    IDLE = "Idle"
    LISTENING = "Listening..."
    TRANSCRIBING = "Transcribing..."
    GENERATING = "Generating Answer..."
    READY = "Ready"
    ERROR = "Error"


class CopilotGUI:
    """Flet-based GUI for displaying interview answers with clean shadcn-style UI."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize GUI with configuration."""
        self.config = config
        self.page: Optional[ft.Page] = None
        
        # UI components
        self.status_text: Optional[ft.Text] = None
        self.state_indicator: Optional[ft.Text] = None
        self.live_transcription: Optional[ft.TextField] = None
        self.word_count_text: Optional[ft.Text] = None
        self.question_field: Optional[ft.TextField] = None
        self.answer_field: Optional[ft.TextField] = None
        self.process_button: Optional[ft.ElevatedButton] = None
        self.start_button: Optional[ft.ElevatedButton] = None
        self.start_button_text: Optional[ft.Text] = None
        self.history_column: Optional[ft.Column] = None
        
        # Configuration
        self.width = config.get("window_width", 800)
        self.height = config.get("window_height", 700)
        
        # State
        self.current_state = TranscriptionState.IDLE
        self.is_listening = False
        self.qa_history: List[Tuple[str, str, str]] = []
        
        # Callbacks
        self.on_process_now: Optional[Callable[[], None]] = None
        self.on_restart_listening: Optional[Callable[[], None]] = None
        self.on_clear_buffer: Optional[Callable[[], None]] = None
        self.on_start_listening: Optional[Callable[[], None]] = None
        self.on_stop_listening: Optional[Callable[[], None]] = None
        self.on_app_ready: Optional[Callable[[], None]] = None
        
        # Colors (shadcn-inspired)
        self.colors = {
            "background": "#FFFFFF",
            "foreground": "#0A0A0A",
            "muted": "#F4F4F5",
            "muted_foreground": "#71717A",
            "border": "#E4E4E7",
            "primary": "#18181B",
            "primary_foreground": "#FAFAFA",
            "secondary": "#F4F4F5",
            "accent": "#F4F4F5",
            "destructive": "#EF4444",
            "success": "#22C55E",
            "warning": "#F59E0B",
        }
        
        logger.info("GUI initialized with Flet shadcn-style UI")
    
    def create_window(self) -> None:
        """Create the Flet app - called from main."""
        pass  # Flet app is created via ft.app()
    
    def _build_ui(self, page: ft.Page):
        """Build the complete UI."""
        self.page = page
        
        # Set up pubsub for thread-safe updates
        page.pubsub.subscribe(self._handle_pubsub_message)
        
        # Page configuration
        page.title = "Interview Copilot"
        page.window.width = self.width
        page.window.height = self.height
        page.window.always_on_top = True
        page.theme_mode = ft.ThemeMode.LIGHT
        page.padding = 24
        page.bgcolor = self.colors["background"]
        page.fonts = {"Inter": "https://fonts.gstatic.com/s/inter/v13/UcCO3FwrK3iLTeHuS_fvQtMwCp50KnMw2boKoduKmMEVuLyfAZ9hiJ-Ek-_EeA.woff2"}
        page.theme = ft.Theme(font_family="Inter")
        
        # Header
        header = self._build_header()
        
        # Live transcription card
        transcription_card = self._build_transcription_card()
        
        # Action buttons
        buttons = self._build_buttons()
        
        # Question card
        question_card = self._build_question_card()
        
        # Answer card
        answer_card = self._build_answer_card()
        
        # History section
        history_section = self._build_history_section()
        
        # Main layout
        page.add(
            ft.Column(
                controls=[
                    header,
                    ft.Container(height=12),
                    transcription_card,
                    ft.Container(height=12),
                    buttons,
                    ft.Container(height=12),
                    ft.Container(content=question_card, expand=True), # Make question card fill remaining space
                    ft.Container(height=12),
                    ft.Container(content=answer_card, expand=True), # Make answer card fill remaining space
                    ft.Container(height=12),
                    history_section,
                ],
                spacing=0,
                expand=True,
            )
        )
        
        # Keyboard shortcuts
        page.on_keyboard_event = self._handle_keyboard
        
        logger.info("Flet UI built successfully")
        
        # Signal that GUI is ready
        if self.on_app_ready:
            self.on_app_ready()
    
    def _build_header(self) -> ft.Container:
        """Build the header with status."""
        self.status_text = ft.Text(
            f"Status: {self.current_state.value}",
            size=12,
            color=self.colors["muted_foreground"],
        )
        
        self.state_indicator = ft.Text(
            f"● {self.current_state.value.upper()}",
            size=14,
            weight=ft.FontWeight.W_600,
            color=self.colors["muted_foreground"],
        )
        
        return ft.Container(
            content=ft.Row(
                controls=[
                    self.state_indicator,
                    ft.Container(expand=True),
                    self.status_text,
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
        )
    
    def _build_transcription_card(self) -> ft.Container:
        """Build the live transcription card."""
        self.word_count_text = ft.Text(
            "0 words",
            size=12,
            color=self.colors["muted_foreground"],
        )
        
        self.live_transcription = ft.TextField(
            multiline=True,
            read_only=True,
            border_radius=8,
            border_color=self.colors["border"],
            focused_border_color=self.colors["primary"],
            bgcolor=self.colors["background"],
            hint_text="Listening for speech...",
            text_style=ft.TextStyle(size=14),
            expand=True,
        )
        
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text(
                                "Live Transcription",
                                size=14,
                                weight=ft.FontWeight.W_500,
                            ),
                            ft.Container(expand=True),
                            self.word_count_text,
                        ],
                    ),
                    ft.Container(height=8),
                    self.live_transcription,
                ],
                spacing=0,
                expand=True,
            ),
            padding=16,
            border_radius=12,
            border=ft.border.all(1, self.colors["border"]),
            height=150, # Fixed height for transcription area, but expandable content
        )
    
    def _build_buttons(self) -> ft.Row:
        """Build action buttons with Start/Stop toggle."""
        # Text control for dynamic button text
        self.start_button_text = ft.Text(
            "▶ Start Listening",
            color="#FFFFFF",
            weight=ft.FontWeight.W_500,
        )
        
        # Primary action: Start/Stop Listening
        self.start_button = ft.ElevatedButton(
            content=self.start_button_text,
            on_click=lambda _: self._handle_toggle_listening(),
            style=ft.ButtonStyle(
                bgcolor="#3B82F6",  # Blue
                shape=ft.RoundedRectangleBorder(radius=8),
                padding=ft.padding.symmetric(horizontal=32, vertical=14),
            ),
            width=200,
        )
        
        # Secondary actions
        self.process_button = ft.ElevatedButton(
            "Process Question",
            icon=ft.Icons.SEND,
            on_click=lambda _: self._handle_process_now(),
            style=ft.ButtonStyle(
                color=self.colors["primary_foreground"],
                bgcolor=self.colors["primary"],
                shape=ft.RoundedRectangleBorder(radius=8),
                padding=ft.padding.symmetric(horizontal=20, vertical=12),
            ),
            disabled=True,  # Disabled until we have content
        )
        
        clear_button = ft.OutlinedButton(
            "Clear",
            icon=ft.Icons.CLEAR,
            on_click=lambda _: self._handle_clear_buffer(),
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                padding=ft.padding.symmetric(horizontal=16, vertical=12),
            ),
        )
        
        return ft.Row(
            controls=[
                self.start_button,
                self.process_button,
                clear_button,
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=12,
        )
    
    def _build_question_card(self) -> ft.Container:
        """Build the question display card."""
        self.question_field = ft.TextField(
            multiline=True,
            read_only=True,
            border_radius=8,
            border_color=self.colors["border"],
            bgcolor=self.colors["muted"],
            text_style=ft.TextStyle(size=14),
            expand=True,
        )
        
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "Question Detected",
                        size=14,
                        weight=ft.FontWeight.W_500,
                    ),
                    ft.Container(height=8),
                    self.question_field,
                ],
                spacing=0,
                expand=True,
            ),
            padding=16,
            border_radius=12,
            border=ft.border.all(1, self.colors["border"]),
            expand=True,
        )
    
    def _build_answer_card(self) -> ft.Container:
        """Build the answer display card."""
        self.answer_field = ft.TextField(
            multiline=True,
            read_only=True,
            border_radius=8,
            border_color=self.colors["border"],
            bgcolor=self.colors["background"],
            text_style=ft.TextStyle(size=14, weight=ft.FontWeight.W_400, color=self.colors["foreground"]),
            expand=True, # Utilize full height of container
            content_padding=12,
        )
        
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.LIGHTBULB, color=self.colors["success"], size=16),
                            ft.Text(
                                "Your Answer",
                                size=13,
                                weight=ft.FontWeight.W_600,
                                color=self.colors["success"],
                            ),
                        ],
                        spacing=6,
                    ),
                    ft.Container(height=8),
                    self.answer_field,
                ],
                spacing=0,
                expand=True,
            ),
            padding=12,
            border_radius=12,
            border=ft.border.all(1, self.colors["success"]),
            bgcolor="#F0FDF4",  # Very light green background
            expand=True,        # Expand to fill available height
        )
    
    def _build_history_section(self) -> ft.Container:
        """Build the Q&A history section."""
        self.history_column = ft.Column(
            controls=[
                ft.Text(
                    "No history yet",
                    size=12,
                    color=self.colors["muted_foreground"],
                    italic=True,
                ),
            ],
            spacing=8,
            scroll=ft.ScrollMode.AUTO,
        )
        
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "Recent Q&A",
                        size=12,
                        weight=ft.FontWeight.W_500,
                        color=self.colors["muted_foreground"],
                    ),
                    ft.Container(
                        content=self.history_column,
                        height=150,
                    ),
                ],
                spacing=0,
            ),
            padding=ft.padding.only(top=12),
        )
    
    def _handle_keyboard(self, e: ft.KeyboardEvent):
        """Handle keyboard shortcuts."""
        if e.key == " " or e.key == "Enter":
            if self.is_listening:
                self._handle_process_now()
        elif e.key == "S" or e.key == "s":
            self._handle_toggle_listening()
        elif e.key == "Escape":
            self._handle_clear_buffer()
    
    def _handle_toggle_listening(self):
        """Handle start/stop listening toggle."""
        if self.is_listening:
            self._handle_stop_listening()
        else:
            self._handle_start_listening()
    
    def _handle_start_listening(self):
        """Handle start listening."""
        if self.on_start_listening:
            logger.info("Start listening triggered")
            self.on_start_listening()
            self.is_listening = True
            self._update_start_button_state()
    
    def _handle_stop_listening(self):
        """Handle stop listening."""
        if self.on_stop_listening:
            logger.info("Stop listening triggered")
            self.on_stop_listening()
            self.is_listening = False
            self._update_start_button_state()
    
    def _update_start_button_state(self):
        """Update the start button appearance based on listening state."""
        if not self.start_button or not self.start_button_text:
            logger.warning("start_button or start_button_text is None, cannot update")
            return
        
        logger.info(f"Updating button state: is_listening={self.is_listening}")
        
        if self.is_listening:
            new_text = "⏹ Stop Listening"
            new_bgcolor = "#EF4444"  # Red
        else:
            new_text = "▶ Start Listening"
            new_bgcolor = "#3B82F6"  # Blue
        
        logger.info(f"Setting button text to: {new_text}")
        
        # Update the Text control inside the button
        self.start_button_text.value = new_text
        
        # Update button style
        self.start_button.style = ft.ButtonStyle(
            bgcolor=new_bgcolor,
            shape=ft.RoundedRectangleBorder(radius=8),
            padding=ft.padding.symmetric(horizontal=24, vertical=12),
        )
        
        if self.process_button:
            self.process_button.disabled = not self.is_listening
        
        # Force update
        if self.page:
            try:
                self.page.update()
                logger.info("Page updated successfully")
            except Exception as e:
                logger.error(f"Failed to update page: {e}")
    
    def _handle_process_now(self):
        """Handle process now button."""
        if self.on_process_now and self.is_listening:
            logger.info("Manual process triggered")
            self.on_process_now()
    
    def _handle_clear_buffer(self):
        """Handle clear buffer."""
        self.update_live_transcription("")
        if self.on_clear_buffer:
            self.on_clear_buffer()
    
    def set_state(self, state: TranscriptionState) -> None:
        """Update the transcription state."""
        self.current_state = state
        
        if not self.state_indicator:
            return
            
        state_colors = {
            TranscriptionState.IDLE: self.colors["muted_foreground"],
            TranscriptionState.LISTENING: "#3B82F6",  # Blue
            TranscriptionState.TRANSCRIBING: self.colors["warning"],
            TranscriptionState.GENERATING: "#8B5CF6",  # Purple
            TranscriptionState.READY: self.colors["success"],
            TranscriptionState.ERROR: self.colors["destructive"],
        }
        
        self.state_indicator.value = f"● {state.value.upper()}"
        self.state_indicator.color = state_colors.get(state, self.colors["muted_foreground"])
        
        if self.page:
            self.page.update()
    
    def update_status(self, status: str) -> None:
        """Update status text."""
        if self.status_text:
            self.status_text.value = f"Status: {status}"
            if self.page:
                self.page.update()
    
    def update_live_transcription(self, text: str) -> None:
        """Update live transcription display."""
        if self.live_transcription and self.page:
            self.live_transcription.value = text
            
            # Update word count
            word_count = len(text.split()) if text.strip() else 0
            if self.word_count_text:
                self.word_count_text.value = f"{word_count} word{'s' if word_count != 1 else ''}"
            
            self.page.update()
    
    def display_question_answer(self, question: str, answer: str) -> None:
        """Display question and answer."""
        if self.question_field:
            self.question_field.value = question
        if self.answer_field:
            self.answer_field.value = answer
        
        # Add to history
        timestamp = datetime.now().strftime("%H:%M")
        self.qa_history.append((timestamp, question, answer))
        if len(self.qa_history) > 5:
            self.qa_history = self.qa_history[-5:]
        
        self._update_history_display()
        self.update_live_transcription("")
        self.set_state(TranscriptionState.READY)
        
        if self.page:
            self.page.update()
        
        logger.info("Display updated with new Q&A")
    
    def _update_history_display(self):
        """Update history display."""
        if not self.history_column:
            return
        
        self.history_column.controls.clear()
        
        if not self.qa_history:
            self.history_column.controls.append(
                ft.Text("No history yet", size=12, color=self.colors["muted_foreground"], italic=True)
            )
        else:
            for timestamp, question, answer in self.qa_history[-3:]:
                q_short = question[:50] + "..." if len(question) > 50 else question
                a_short = answer[:70] + "..." if len(answer) > 70 else answer
                
                self.history_column.controls.append(
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Text(f"[{timestamp}] Q: {q_short}", size=11, color=self.colors["foreground"]),
                                ft.Text(f"A: {a_short}", size=11, color=self.colors["success"]),
                            ],
                            spacing=2,
                        ),
                        padding=8,
                        border_radius=6,
                        bgcolor=self.colors["muted"],
                    )
                )
    
    def clear_display(self) -> None:
        """Clear displays."""
        if self.question_field:
            self.question_field.value = ""
        if self.answer_field:
            self.answer_field.value = ""
        self.set_state(TranscriptionState.LISTENING)
        if self.page:
            self.page.update()
    
    def show_error(self, message: str) -> None:
        """Display error message."""
        self.set_state(TranscriptionState.ERROR)
        if self.answer_field:
            self.answer_field.value = f"Error: {message}"
        if self.page:
            self.page.update()
    
    def update_timestamp(self) -> None:
        """Update timestamp (compatibility method)."""
        pass
    
    def _handle_pubsub_message(self, message):
        """Handle pubsub messages for thread-safe UI updates."""
        if not isinstance(message, dict):
            return
        
        msg_type = message.get("type")
        
        if msg_type == "live_transcription":
            self._do_update_live_transcription(message.get("text", ""))
        elif msg_type == "state":
            self._do_set_state(message.get("state"))
        elif msg_type == "status":
            self._do_update_status(message.get("status", ""))
        elif msg_type == "question_answer":
            self._do_display_question_answer(
                message.get("question", ""),
                message.get("answer", "")
            )
        elif msg_type == "error":
            self._do_show_error(message.get("message", ""))
    
    def _do_update_live_transcription(self, text: str) -> None:
        """Internal method to update live transcription (called on main thread)."""
        if self.live_transcription:
            self.live_transcription.value = text
            word_count = len(text.split()) if text.strip() else 0
            if self.word_count_text:
                self.word_count_text.value = f"{word_count} word{'s' if word_count != 1 else ''}"
        if self.page:
            self.page.update()
    
    def _do_set_state(self, state: TranscriptionState) -> None:
        """Internal method to set state (called on main thread)."""
        self.current_state = state
        if not self.state_indicator:
            return
        state_colors = {
            TranscriptionState.IDLE: self.colors["muted_foreground"],
            TranscriptionState.LISTENING: "#3B82F6",
            TranscriptionState.TRANSCRIBING: self.colors["warning"],
            TranscriptionState.GENERATING: "#8B5CF6",
            TranscriptionState.READY: self.colors["success"],
            TranscriptionState.ERROR: self.colors["destructive"],
        }
        self.state_indicator.value = f"● {state.value.upper()}"
        self.state_indicator.color = state_colors.get(state, self.colors["muted_foreground"])
        if self.page:
            self.page.update()
    
    def _do_update_status(self, status: str) -> None:
        """Internal method to update status (called on main thread)."""
        if self.status_text:
            self.status_text.value = f"Status: {status}"
        if self.page:
            self.page.update()
    
    def _do_display_question_answer(self, question: str, answer: str) -> None:
        """Internal method to display Q&A (called on main thread)."""
        if self.question_field:
            self.question_field.value = question
        if self.answer_field:
            self.answer_field.value = answer
        timestamp = datetime.now().strftime("%H:%M")
        self.qa_history.append((timestamp, question, answer))
        if len(self.qa_history) > 5:
            self.qa_history = self.qa_history[-5:]
        self._update_history_display()
        self._do_update_live_transcription("")
        self._do_set_state(TranscriptionState.READY)
        if self.page:
            self.page.update()
        logger.info("Display updated with new Q&A")
    
    def _do_show_error(self, message: str) -> None:
        """Internal method to show error (called on main thread)."""
        self._do_set_state(TranscriptionState.ERROR)
        if self.answer_field:
            self.answer_field.value = f"Error: {message}"
        if self.page:
            self.page.update()
    
    # Thread-safe wrapper methods that use pubsub
    def update_live_transcription_safe(self, text: str) -> None:
        """Thread-safe live transcription update."""
        if self.page:
            self.page.pubsub.send_all({"type": "live_transcription", "text": text})
    
    def set_state_safe(self, state: TranscriptionState) -> None:
        """Thread-safe state update."""
        if self.page:
            self.page.pubsub.send_all({"type": "state", "state": state})
    
    def update_status_safe(self, status: str) -> None:
        """Thread-safe status update."""
        if self.page:
            self.page.pubsub.send_all({"type": "status", "status": status})
    
    def display_question_answer_safe(self, question: str, answer: str) -> None:
        """Thread-safe Q&A display."""
        if self.page:
            self.page.pubsub.send_all({"type": "question_answer", "question": question, "answer": answer})
    
    def show_error_safe(self, message: str) -> None:
        """Thread-safe error display."""
        if self.page:
            self.page.pubsub.send_all({"type": "error", "message": message})
    
    def run(self) -> None:
        """Start the Flet app."""
        logger.info("Starting Flet GUI")
        ft.app(target=self._build_ui)
