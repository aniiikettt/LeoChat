import sqlite3
from datetime import datetime
from loguru import logger
from config import DB_PATH

class SessionStore:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initializes the database and creates the messages table if it doesn't exist."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS chat_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT NOT NULL,
                        role TEXT NOT NULL, -- 'user', 'assistant', or 'system'
                        content TEXT NOT NULL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_session_id ON chat_history (session_id)
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS knowledge_base (
                        session_id TEXT PRIMARY KEY,
                        content TEXT NOT NULL
                    )
                """)
                conn.commit()
                logger.info(f"Database initialized at {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    def save_message(self, session_id: str, role: str, content: str):
        """Saves a single message to the conversation history."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO chat_history (session_id, role, content) VALUES (?, ?, ?)",
                    (session_id, role, content)
                )
                conn.commit()
                logger.debug(f"Saved message from '{role}' for session {session_id}")
        except Exception as e:
            logger.error(f"Failed to save message: {e}")

    def get_history(self, session_id: str, limit: int) -> list[dict]:
        """
        Retrieves the last `limit` messages for a session, 
        sorted chronologically (oldest to newest).
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # Subquery gets the latest `limit` messages, outer query sorts them ascending
                cursor.execute("""
                    SELECT role, content FROM (
                        SELECT role, content, timestamp 
                        FROM chat_history 
                        WHERE session_id = ? 
                        ORDER BY id DESC 
                        LIMIT ?
                    ) ORDER BY timestamp ASC
                """, (session_id, limit))
                
                rows = cursor.fetchall()
                history = [{"role": row[0], "content": row[1]} for row in rows]
                return history
        except Exception as e:
            logger.error(f"Failed to retrieve history for session {session_id}: {e}")
            return []

    def clear_history(self, session_id: str):
        """Clears all conversation history and document context for a given session."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM chat_history WHERE session_id = ?", (session_id,))
                cursor.execute("DELETE FROM knowledge_base WHERE session_id = ?", (session_id,))
                conn.commit()
                logger.info(f"Cleared history and knowledge base for session {session_id}")
        except Exception as e:
            logger.error(f"Failed to clear history for session {session_id}: {e}")

    def save_knowledge(self, session_id: str, content: str):
        """Saves or updates custom documentation context for the session."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO knowledge_base (session_id, content) 
                    VALUES (?, ?)
                    ON CONFLICT(session_id) DO UPDATE SET content=excluded.content
                """, (session_id, content))
                conn.commit()
                logger.info(f"Saved custom context docs for session {session_id}")
        except Exception as e:
            logger.error(f"Failed to save knowledge context: {e}")

    def get_knowledge(self, session_id: str) -> str:
        """Retrieves custom session-scoped documentation context."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT content FROM knowledge_base WHERE session_id = ?", (session_id,))
                row = cursor.fetchone()
                return row[0] if row else ""
        except Exception as e:
            logger.error(f"Failed to retrieve knowledge context: {e}")
            return ""

