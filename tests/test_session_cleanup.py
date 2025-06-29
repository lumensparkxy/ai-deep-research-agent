"""
Test cleanup functionality for incomplete sessions.
"""

import pytest
import json
import time
import os
from datetime import datetime, timedelta
from pathlib import Path

from utils.session_manager import SessionManager


@pytest.mark.priority1 
@pytest.mark.unit
class TestSessionCleanup:
    """Test cases for session cleanup functionality."""

    def test_cleanup_incomplete_sessions_corrupted_json(self, mock_settings, temp_dir):
        """Test cleanup removes corrupted JSON files."""
        mock_settings.session_storage_path = str(temp_dir / "sessions")
        session_manager = SessionManager(mock_settings)
        session_manager.session_dir.mkdir(parents=True, exist_ok=True)
        
        # Create corrupted session file
        corrupted_file = session_manager.session_dir / "DRA_20250629_120000.json"
        corrupted_file.write_text("{ invalid json content")
        
        # Create valid session file for comparison
        valid_session_data = {
            "session_id": "DRA_20250629_130000",
            "created_at": datetime.now().isoformat(),
            "query": "test query",
            "status": "completed"
        }
        valid_file = session_manager.session_dir / "DRA_20250629_130000.json"
        with open(valid_file, 'w') as f:
            json.dump(valid_session_data, f)
        
        # Run cleanup
        deleted_count = session_manager.cleanup_incomplete_sessions()
        
        # Should delete corrupted file but keep valid one
        assert deleted_count == 1
        assert not corrupted_file.exists()
        assert valid_file.exists()

    def test_cleanup_incomplete_sessions_missing_required_fields(self, mock_settings, temp_dir):
        """Test cleanup removes sessions missing required fields."""
        mock_settings.session_storage_path = str(temp_dir / "sessions")
        session_manager = SessionManager(mock_settings)
        session_manager.session_dir.mkdir(parents=True, exist_ok=True)
        
        # Create session missing required fields
        incomplete_session = {
            "session_id": "DRA_20250629_120000",
            # Missing created_at, query, status
        }
        incomplete_file = session_manager.session_dir / "DRA_20250629_120000.json"
        with open(incomplete_file, 'w') as f:
            json.dump(incomplete_session, f)
        
        # Create complete session
        complete_session = {
            "session_id": "DRA_20250629_130000",
            "created_at": datetime.now().isoformat(),
            "query": "test query",
            "status": "completed"
        }
        complete_file = session_manager.session_dir / "DRA_20250629_130000.json"
        with open(complete_file, 'w') as f:
            json.dump(complete_session, f)
        
        # Run cleanup
        deleted_count = session_manager.cleanup_incomplete_sessions()
        
        # Should delete incomplete session
        assert deleted_count == 1
        assert not incomplete_file.exists()
        assert complete_file.exists()

    def test_cleanup_incomplete_sessions_stale_created_status(self, mock_settings, temp_dir):
        """Test cleanup removes old sessions still in 'created' status."""
        mock_settings.session_storage_path = str(temp_dir / "sessions")
        session_manager = SessionManager(mock_settings)
        session_manager.session_dir.mkdir(parents=True, exist_ok=True)
        
        # Create stale session (created > 24 hours ago)
        stale_time = datetime.now() - timedelta(hours=25)
        stale_session = {
            "session_id": "DRA_20250628_120000",
            "created_at": stale_time.isoformat(),
            "query": "test query",
            "status": "created"
        }
        stale_file = session_manager.session_dir / "DRA_20250628_120000.json"
        with open(stale_file, 'w') as f:
            json.dump(stale_session, f)
        
        # Create recent session in 'created' status  
        recent_session = {
            "session_id": "DRA_20250629_120000",
            "created_at": datetime.now().isoformat(),
            "query": "test query", 
            "status": "created"
        }
        recent_file = session_manager.session_dir / "DRA_20250629_120000.json"
        with open(recent_file, 'w') as f:
            json.dump(recent_session, f)
        
        # Create old but completed session
        old_completed_session = {
            "session_id": "DRA_20250627_120000",
            "created_at": (datetime.now() - timedelta(hours=30)).isoformat(),
            "query": "test query",
            "status": "completed"
        }
        old_completed_file = session_manager.session_dir / "DRA_20250627_120000.json"
        with open(old_completed_file, 'w') as f:
            json.dump(old_completed_session, f)
        
        # Run cleanup
        deleted_count = session_manager.cleanup_incomplete_sessions()
        
        # Should only delete stale 'created' session
        assert deleted_count == 1
        assert not stale_file.exists()
        assert recent_file.exists()
        assert old_completed_file.exists()

    def test_cleanup_incomplete_sessions_invalid_timestamp(self, mock_settings, temp_dir):
        """Test cleanup removes sessions with invalid timestamps."""
        mock_settings.session_storage_path = str(temp_dir / "sessions")
        session_manager = SessionManager(mock_settings)
        session_manager.session_dir.mkdir(parents=True, exist_ok=True)
        
        # Create session with invalid timestamp
        invalid_timestamp_session = {
            "session_id": "DRA_20250629_120000",
            "created_at": "invalid-timestamp-format",
            "query": "test query",
            "status": "created"
        }
        invalid_file = session_manager.session_dir / "DRA_20250629_120000.json"
        with open(invalid_file, 'w') as f:
            json.dump(invalid_timestamp_session, f)
        
        # Run cleanup
        deleted_count = session_manager.cleanup_incomplete_sessions()
        
        # Should delete session with invalid timestamp
        assert deleted_count == 1
        assert not invalid_file.exists()

    def test_cleanup_incomplete_sessions_no_cleanup_needed(self, mock_settings, temp_dir):
        """Test cleanup when no cleanup is needed."""
        mock_settings.session_storage_path = str(temp_dir / "sessions")
        session_manager = SessionManager(mock_settings)
        session_manager.session_dir.mkdir(parents=True, exist_ok=True)
        
        # Create only valid, recent sessions
        sessions = [
            {
                "session_id": "DRA_20250629_120000",
                "created_at": datetime.now().isoformat(),
                "query": "test query 1",
                "status": "completed"
            },
            {
                "session_id": "DRA_20250629_130000", 
                "created_at": datetime.now().isoformat(),
                "query": "test query 2",
                "status": "interrupted"
            },
            {
                "session_id": "DRA_20250629_140000",
                "created_at": (datetime.now() - timedelta(hours=1)).isoformat(),
                "query": "test query 3",
                "status": "created"  # Recent, so should not be deleted
            }
        ]
        
        for session in sessions:
            session_file = session_manager.session_dir / f"{session['session_id']}.json"
            with open(session_file, 'w') as f:
                json.dump(session, f)
        
        # Run cleanup
        deleted_count = session_manager.cleanup_incomplete_sessions()
        
        # Should not delete any sessions
        assert deleted_count == 0
        
        # All sessions should still exist
        for session in sessions:
            session_file = session_manager.session_dir / f"{session['session_id']}.json"
            assert session_file.exists()

    def test_cleanup_incomplete_sessions_empty_directory(self, mock_settings, temp_dir):
        """Test cleanup with empty session directory."""
        mock_settings.session_storage_path = str(temp_dir / "sessions")
        session_manager = SessionManager(mock_settings)
        session_manager.session_dir.mkdir(parents=True, exist_ok=True)
        
        # Run cleanup on empty directory
        deleted_count = session_manager.cleanup_incomplete_sessions()
        
        # Should not delete anything
        assert deleted_count == 0

    def test_cleanup_incomplete_sessions_file_permission_error(self, mock_settings, temp_dir):
        """Test cleanup handles file permission errors gracefully."""
        mock_settings.session_storage_path = str(temp_dir / "sessions")
        session_manager = SessionManager(mock_settings)
        session_manager.session_dir.mkdir(parents=True, exist_ok=True)
        
        # Create corrupted session file
        corrupted_file = session_manager.session_dir / "DRA_20250629_120000.json"
        corrupted_file.write_text("{ invalid json")
        
        # Run cleanup with mocked permission error on deletion
        from unittest.mock import patch
        with patch.object(Path, 'unlink', side_effect=OSError("Permission denied")):
            deleted_count = session_manager.cleanup_incomplete_sessions()
            
            # Should handle error gracefully and not crash
            assert deleted_count >= 0  # May or may not count failed deletions