import json
import os
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path
import threading

from medical_models import UserSession, Patient
from utils.logger import logger

logger.info("SessionManager initialized")


class SessionManager:
    """Manages user sessions for the medical voice agent system"""
    
    def __init__(self, session_file: str = "user_sessions.json"):
        self.session_file = Path("data") / session_file
        self.sessions: Dict[str, UserSession] = {}
        self.lock = threading.Lock()
        self._ensure_data_directory()
        self._load_sessions()
    
    def _ensure_data_directory(self):
        """Ensure the data directory exists"""
        self.session_file.parent.mkdir(exist_ok=True)
    
    def _load_sessions(self):
        """Load sessions from file"""
        try:
            if self.session_file.exists():
                with open(self.session_file, 'r') as f:
                    data = json.load(f)
                    for session_id, session_data in data.items():
                        # Convert datetime strings back to datetime objects
                        session_data['created_at'] = datetime.fromisoformat(session_data['created_at'])
                        session_data['last_activity'] = datetime.fromisoformat(session_data['last_activity'])
                        self.sessions[session_id] = UserSession(**session_data)
                logger.info(f"Loaded {len(self.sessions)} sessions from {self.session_file}")
        except Exception as e:
            logger.error(f"Error loading sessions: {e}")
            self.sessions = {}
    
    def _save_sessions(self):
        """Save sessions to file"""
        try:
            # Convert sessions to dict format for JSON serialization
            sessions_data = {}
            for session_id, session in self.sessions.items():
                session_dict = session.model_dump()
                # Convert datetime objects to ISO format strings
                session_dict['created_at'] = session.created_at.isoformat()
                session_dict['last_activity'] = session.last_activity.isoformat()
                sessions_data[session_id] = session_dict
            
            with open(self.session_file, 'w') as f:
                json.dump(sessions_data, f, indent=2)
            logger.debug(f"Saved {len(self.sessions)} sessions to {self.session_file}")
        except Exception as e:
            logger.error(f"Error saving sessions: {e}")
    
    def create_session(self, user_id: str, room_name: str, initial_context: Dict[str, Any] = None) -> UserSession:
        """Create a new user session"""
        with self.lock:
            session = UserSession(
                user_id=user_id,
                room_name=room_name,
                context=initial_context or {}
            )
            self.sessions[session.session_id] = session
            self._save_sessions()
            logger.info(f"Created new session {session.session_id} for user {user_id}")
            return session
    
    def get_session(self, session_id: str) -> Optional[UserSession]:
        """Get a session by ID"""
        return self.sessions.get(session_id)
    
    def get_user_session(self, user_id: str) -> Optional[UserSession]:
        """Get the most recent session for a user"""
        user_sessions = [s for s in self.sessions.values() if s.user_id == user_id]
        if user_sessions:
            return max(user_sessions, key=lambda s: s.last_activity)
        return None
    
    def update_session(self, session_id: str, **updates) -> bool:
        """Update session data"""
        with self.lock:
            if session_id in self.sessions:
                session = self.sessions[session_id]
                for key, value in updates.items():
                    if hasattr(session, key):
                        setattr(session, key, value)
                session.last_activity = datetime.now()
                self._save_sessions()
                logger.debug(f"Updated session {session_id}")
                return True
            return False
    
    def add_conversation_entry(self, session_id: str, role: str, message: str, metadata: Dict[str, Any] = None):
        """Add a conversation entry to the session"""
        with self.lock:
            if session_id in self.sessions:
                entry = {
                    "timestamp": datetime.now().isoformat(),
                    "role": role,
                    "message": message,
                    "metadata": metadata or {}
                }
                self.sessions[session_id].conversation_history.append(entry)
                self.sessions[session_id].last_activity = datetime.now()
                self._save_sessions()
                logger.debug(f"Added conversation entry to session {session_id}")
    
    def update_context(self, session_id: str, context_updates: Dict[str, Any]):
        """Update session context"""
        with self.lock:
            if session_id in self.sessions:
                self.sessions[session_id].context.update(context_updates)
                self.sessions[session_id].last_activity = datetime.now()
                self._save_sessions()
                logger.debug(f"Updated context for session {session_id}")
    
    def set_current_agent(self, session_id: str, agent_name: str):
        """Set the current agent for the session"""
        self.update_session(session_id, current_agent=agent_name)
    
    def cleanup_old_sessions(self, max_age_hours: int = 24):
        """Remove sessions older than specified hours"""
        with self.lock:
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            old_sessions = [
                sid for sid, session in self.sessions.items()
                if session.last_activity < cutoff_time
            ]
            
            for session_id in old_sessions:
                del self.sessions[session_id]
            
            if old_sessions:
                self._save_sessions()
                logger.info(f"Cleaned up {len(old_sessions)} old sessions")
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get statistics about current sessions"""
        total_sessions = len(self.sessions)
        active_sessions = sum(
            1 for s in self.sessions.values()
            if s.last_activity > datetime.now() - timedelta(hours=1)
        )
        
        return {
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "agents_in_use": list(set(s.current_agent for s in self.sessions.values() if s.current_agent))
        }

# Global session manager instance
session_manager = SessionManager()