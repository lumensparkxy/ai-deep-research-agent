"""
Session Management for Deep Research Agent
Handles persistence and retrieval of research sessions.
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from config.settings import get_settings
from utils.validators import InputValidator, ValidationError


class SessionManager:
    """Manages research session persistence and retrieval."""
    
    def __init__(self, settings=None):
        """
        Initialize session manager.
        
        Args:
            settings: Configuration settings instance
        """
        self.settings = settings or get_settings()
        self.validator = InputValidator(self.settings)
        self.logger = logging.getLogger(__name__)
        
        # Ensure session directory exists
        self.session_dir = Path(self.settings.session_storage_path)
        self.session_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_session_id(self) -> str:
        """
        Generate a unique session ID with timestamp.
        
        Returns:
            Session ID in format: DRA_YYYYMMDD_HHMMSS
        """
        # Generate unique session ID with microsecond precision
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        return f"DRA_{timestamp}"
    
    def create_session(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Create a new research session.
        
        Args:
            query: Research question
            context: Additional context data
            
        Returns:
            Session data dictionary
            
        Raises:
            ValidationError: If inputs are invalid
        """
        # Validate inputs
        query = self.validator.validate_query(query)
        context = self.validator.validate_context_data(context or {})
        
        # Generate session
        session_id = self.generate_session_id()
        
        session_data = {
            "session_id": session_id,
            "created_at": datetime.now().isoformat(),
            "version": self.settings.app_version,
            "query": query,
            "context": context,
            "research_results": {
                "stages": [],
                "final_conclusions": {},
                "confidence_score": 0.0
            },
            "report_path": None,
            "status": "created"
        }
        
        # Save session
        self.save_session(session_data)
        
        self.logger.info(f"Created new session: {session_id}")
        return session_data
    
    def save_session(self, session_data: Dict[str, Any]) -> None:
        """
        Save session data to file.
        
        Args:
            session_data: Complete session data
            
        Raises:
            ValidationError: If session data is invalid
        """
        session_id = session_data.get("session_id")
        if not session_id:
            raise ValidationError("Session data missing session_id")
        # Validate session ID but allow non-standard formats for new sessions
        try:
            session_id = self.validator.validate_session_id(session_id)
        except ValidationError as e:
            self.logger.warning(f"Skipping strict session_id validation on save: {e}")
        
        # Update modified timestamp
        session_data["modified_at"] = datetime.now().isoformat()
        
        # Save to file
        session_file = self.session_dir / f"{session_id}.json"
        
        try:
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)
            
            # Set secure file permissions
            permission_octal = int(self.settings.session_file_permissions, 8)
            os.chmod(session_file, permission_octal)

            self.logger.debug(f"Saved session: {session_id}")
            
        except (OSError, ValueError) as e:
            self.logger.error(f"Failed to save session {session_id}: {e}")
            raise ValidationError(f"Could not save session: {e}")
    
    def load_session(self, session_id: str) -> Dict[str, Any]:
        """
        Load session data from file.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session data dictionary
            
        Raises:
            ValidationError: If session not found or invalid
        """
        # Validate session ID
        session_id = self.validator.validate_session_id(session_id)
        
        session_file = self.session_dir / f"{session_id}.json"
        
        if not session_file.exists():
            raise ValidationError(f"Session not found: {session_id}")
        
        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            self.logger.debug(f"Loaded session: {session_id}")
            return session_data
            
        except (OSError, json.JSONDecodeError) as e:
            self.logger.error(f"Failed to load session {session_id}: {e}")
            raise ValidationError(f"Could not load session: {e}")
    
    def update_session_stage(self, session_id: str, stage_data: Dict[str, Any]) -> None:
        """
        Update session with new stage results.
        
        Args:
            session_id: Session identifier
            stage_data: Stage results to add
        """
        # Load existing session
        session_data = self.load_session(session_id)
        
        # Validate stage data
        if not isinstance(stage_data, dict) or "stage" not in stage_data:
            raise ValidationError("Stage data must contain 'stage' field")
        
        stage_num = self.validator.validate_research_stage(stage_data["stage"])
        
        # Add timestamp
        stage_data["timestamp"] = datetime.now().isoformat()
        
        # Update session
        if "research_results" not in session_data:
            session_data["research_results"] = {"stages": [], "final_conclusions": {}}
        
        session_data["research_results"]["stages"].append(stage_data)
        session_data["status"] = f"stage_{stage_num}"
        
        # Save updated session
        self.save_session(session_data)
        
        self.logger.debug(f"Updated session {session_id} with stage {stage_num}")
    
    def update_session_conclusions(self, session_id: str, conclusions: Dict[str, Any], 
                                 confidence_score: float) -> None:
        """
        Update session with final conclusions.
        
        Args:
            session_id: Session identifier
            conclusions: Final research conclusions
            confidence_score: Overall confidence score
        """
        # Validate inputs
        confidence_score = self.validator.validate_confidence_score(confidence_score)
        
        # Load existing session
        session_data = self.load_session(session_id)
        
        # Update conclusions
        session_data["research_results"]["final_conclusions"] = conclusions
        session_data["research_results"]["confidence_score"] = confidence_score
        session_data["status"] = "completed"
        
        # Save updated session
        self.save_session(session_data)
        
        self.logger.info(f"Completed session {session_id} with confidence {confidence_score:.2f}")
    
    def update_session_report_path(self, session_id: str, report_path: str) -> None:
        """
        Update session with generated report path.
        
        Args:
            session_id: Session identifier
            report_path: Path to generated report
        """
        # Validate report path
        report_path = self.validator.validate_file_path(report_path, project_root=self.settings.base_path)
        
        # Load existing session
        session_data = self.load_session(session_id)
        
        # Update report path
        session_data["report_path"] = report_path
        
        # Save updated session
        self.save_session(session_data)
        
        self.logger.debug(f"Updated session {session_id} with report path: {report_path}")
    
    def list_sessions(self, limit: int = None) -> List[Dict[str, Any]]:
        """
        List all sessions with basic metadata.
        
        Args:
            limit: Maximum number of sessions to return (uses setting default if None)
            
        Returns:
            List of session metadata dictionaries
        """
        if limit is None:
            limit = self.settings.default_session_limit
        
        sessions = []
        session_files = sorted(self.session_dir.glob("DRA_*.json"), reverse=True)
        
        for session_file in session_files[:limit]:
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
                
                # Extract metadata
                metadata = {
                    "session_id": session_data.get("session_id"),
                    "created_at": session_data.get("created_at"),
                    "query": session_data.get("query", "")[:self.settings.query_display_length],  # Truncate query
                    "status": session_data.get("status", "unknown"),
                    "confidence_score": session_data.get("research_results", {}).get("confidence_score", 0.0)
                }
                
                sessions.append(metadata)
                
            except (OSError, json.JSONDecodeError) as e:
                self.logger.warning(f"Could not read session file {session_file}: {e}")
                continue
        
        return sessions
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session and its associated files.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if deleted successfully
        """
        # Validate session ID
        session_id = self.validator.validate_session_id(session_id)
        
        session_file = self.session_dir / f"{session_id}.json"
        
        if not session_file.exists():
            self.logger.warning(f"Session file not found for deletion: {session_id}")
            return False
        
        try:
            # Load session to get report path
            session_data = self.load_session(session_id)
            
            # Delete report file if exists
            if session_data.get("report_path"):
                report_file = Path(session_data["report_path"])
                if report_file.exists():
                    report_file.unlink()
                    self.logger.debug(f"Deleted report file: {report_file}")
            
            # Delete session file
            session_file.unlink()
            
            self.logger.info(f"Deleted session: {session_id}")
            return True
            
        except (OSError, ValidationError) as e:
            self.logger.error(f"Failed to delete session {session_id}: {e}")
            return False
    
    def cleanup_old_sessions(self, days_old: int = 30) -> int:
        """
        Clean up sessions older than specified days.
        
        Args:
            days_old: Number of days after which to delete sessions
            
        Returns:
            Number of sessions deleted
        """
        from datetime import timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days_old)
        deleted_count = 0
        
        session_files = self.session_dir.glob("DRA_*.json")
        
        for session_file in session_files:
            try:
                # Check file modification time
                file_time = datetime.fromtimestamp(session_file.stat().st_mtime)
                
                if file_time < cutoff_date:
                    session_id = session_file.stem
                    if self.delete_session(session_id):
                        deleted_count += 1
                        
            except (OSError, ValidationError) as e:
                self.logger.warning(f"Could not process session file {session_file}: {e}")
                continue
        
        self.logger.info(f"Cleaned up {deleted_count} old sessions")
        return deleted_count

    def cleanup_incomplete_sessions(self) -> int:
        """
        Clean up sessions that are truly incomplete (corrupted or invalid).
        
        Returns:
            Number of sessions deleted
        """
        deleted_count = 0
        session_files = self.session_dir.glob("DRA_*.json")
        
        for session_file in session_files:
            try:
                # Try to load the session
                with open(session_file, 'r') as f:
                    session_data = json.load(f)
                
                # Check if session has minimum required fields
                required_fields = ["session_id", "created_at", "query", "status"]
                if not all(field in session_data for field in required_fields):
                    self.logger.warning(f"Session file missing required fields: {session_file}")
                    session_file.unlink()
                    deleted_count += 1
                    continue
                
                # Check if session is in an impossible state (created but no further progress for >24h)
                from datetime import datetime, timedelta
                try:
                    created_at = datetime.fromisoformat(session_data["created_at"].replace('Z', '+00:00'))
                    if (session_data.get("status") == "created" and 
                        datetime.now() - created_at > timedelta(hours=24)):
                        self.logger.info(f"Cleaning up stale 'created' session: {session_data['session_id']}")
                        session_file.unlink()
                        deleted_count += 1
                        continue
                except (ValueError, TypeError):
                    # Invalid timestamp format
                    self.logger.warning(f"Session with invalid timestamp: {session_file}")
                    session_file.unlink()
                    deleted_count += 1
                    continue
                        
            except (OSError, json.JSONDecodeError) as e:
                self.logger.warning(f"Corrupted session file deleted: {session_file}: {e}")
                try:
                    session_file.unlink()
                    deleted_count += 1
                except OSError:
                    pass  # File might already be deleted
                continue
        
        if deleted_count > 0:
            self.logger.info(f"Cleaned up {deleted_count} incomplete/corrupted sessions")
        return deleted_count
