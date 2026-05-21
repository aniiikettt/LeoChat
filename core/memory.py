from loguru import logger
from db.session_store import SessionStore
from config import MAX_HISTORY_TURNS

class MemoryManager:
    def __init__(self, store: SessionStore):
        self.store = store
        # 1 turn = 1 user message + 1 assistant response = 2 messages total.
        self.max_messages = MAX_HISTORY_TURNS * 2

    def get_context(self, session_id: str) -> list[dict]:
        """
        Retrieves the conversation history for a given session, applying the 
        sliding window strategy to cap the token cost and context window.
        """
        logger.debug(f"Fetching sliding window context (limit={self.max_messages}) for session {session_id}")
        history = self.store.get_history(session_id, limit=self.max_messages)
        return history

    def save_user_message(self, session_id: str, content: str):
        """Saves the user's input message to persistent store."""
        self.store.save_message(session_id, "user", content)

    def save_assistant_message(self, session_id: str, content: str):
        """Saves the assistant's response to persistent store."""
        self.store.save_message(session_id, "assistant", content)

    def clear_session(self, session_id: str):
        """Clears all history for a session."""
        self.store.clear_history(session_id)
