"""
Unit tests for SessionManager class.

Tests session creation, validation, persistence, and error handling.
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from datetime import datetime

from utils.session_manager import SessionManager
from utils.validators import ValidationError


@pytest.mark.priority1
@pytest.mark.core
@pytest.mark.unit  
class TestSessionManager:
    """Test cases for SessionManager functionality."""
    
    def test_session_manager_initialization(self, mock_settings, temp_dir):
        """Test SessionManager initializes correctly with settings."""
        session_manager = SessionManager(mock_settings)
        
        assert session_manager.settings == mock_settings
        assert session_manager.session_dir == Path(mock_settings.session_storage_path)
        assert session_manager.session_dir.exists()
    
    def test_session_manager_initialization_without_settings(self):
        """Test SessionManager can initialize without explicit settings."""
        with patch('utils.session_manager.get_settings') as mock_get_settings:
            mock_settings = Mock()
            mock_settings.session_storage_path = "/tmp/test_sessions"
            mock_get_settings.return_value = mock_settings
            
            session_manager = SessionManager()
            assert session_manager.settings == mock_settings
    
    def test_generate_session_id_format(self, mock_settings):
        """Test session ID generation follows correct format."""
        session_manager = SessionManager(mock_settings)
        
        with patch('utils.session_manager.datetime') as mock_dt:
            mock_dt.now().strftime.return_value = "20250628_120000"
            
            session_id = session_manager.generate_session_id()
            assert session_id == "DRA_20250628_120000"
            assert session_id.startswith("DRA_")
            assert len(session_id) == 19  # DRA_ + 8 digits + _ + 6 digits
    
    def test_create_session_success(self, mock_settings, sample_session_data, mock_datetime):
        """Test successful session creation."""
        session_manager = SessionManager(mock_settings)
        
        # Mock the validator methods
        with patch.object(session_manager.validator, 'validate_query') as mock_validate_query, \
             patch.object(session_manager.validator, 'validate_context_data') as mock_validate_context, \
             patch.object(session_manager, 'save_session') as mock_save:
            
            mock_validate_query.return_value = sample_session_data["query"]
            mock_validate_context.return_value = sample_session_data["context"]
            
            result = session_manager.create_session(
                sample_session_data["query"], 
                sample_session_data["context"]
            )
            
            # Verify the session structure
            assert result["session_id"].startswith("DRA_")
            assert result["query"] == sample_session_data["query"]
            assert result["context"] == sample_session_data["context"]
            assert result["status"] == "created"
            assert "created_at" in result
            assert "research_results" in result
            assert result["research_results"]["confidence_score"] == 0.0
            
            # Verify save was called
            mock_save.assert_called_once_with(result)
    
    def test_create_session_with_invalid_query(self, mock_settings):
        """Test session creation fails with invalid query."""
        session_manager = SessionManager(mock_settings)
        
        with patch.object(session_manager.validator, 'validate_query') as mock_validate:
            mock_validate.side_effect = ValidationError("Query too short")
            
            with pytest.raises(ValidationError, match="Query too short"):
                session_manager.create_session("Hi")
    
    def test_create_session_with_no_context(self, mock_settings, mock_datetime):
        """Test session creation works without context."""
        session_manager = SessionManager(mock_settings)
        
        with patch.object(session_manager.validator, 'validate_query') as mock_validate_query, \
             patch.object(session_manager.validator, 'validate_context_data') as mock_validate_context, \
             patch.object(session_manager, 'save_session') as mock_save:
            
            mock_validate_query.return_value = "Test query"
            mock_validate_context.return_value = {}
            
            result = session_manager.create_session("Test query")
            
            assert result["context"] == {}
            mock_validate_context.assert_called_once_with({})
    
    def test_save_session_success(self, mock_settings, sample_session_data, temp_dir):
        """Test successful session saving."""
        mock_settings.session_storage_path = str(temp_dir / "sessions")
        session_manager = SessionManager(mock_settings)
        
        # Create the sessions directory
        session_manager.session_dir.mkdir(parents=True, exist_ok=True)
        
        with patch.object(session_manager.validator, 'validate_session_id') as mock_validate:
            mock_validate.return_value = sample_session_data["session_id"]
            
            session_manager.save_session(sample_session_data)
            
            # Verify file was created
            session_file = session_manager.session_dir / f"{sample_session_data['session_id']}.json"
            assert session_file.exists()
            
            # Verify content
            with open(session_file, 'r') as f:
                saved_data = json.load(f)
            
            assert saved_data["session_id"] == sample_session_data["session_id"]
            assert saved_data["query"] == sample_session_data["query"]
            assert "modified_at" in saved_data
    
    def test_save_session_missing_session_id(self, mock_settings):
        """Test save_session fails when session_id is missing."""
        session_manager = SessionManager(mock_settings)
        
        invalid_session = {"query": "test", "context": {}}
        
        with pytest.raises(ValidationError, match="Session data missing session_id"):
            session_manager.save_session(invalid_session)
    
    def test_save_session_file_write_error(self, mock_settings, sample_session_data):
        """Test save_session handles file write errors."""
        session_manager = SessionManager(mock_settings)
        
        with patch.object(session_manager.validator, 'validate_session_id') as mock_validate, \
             patch("builtins.open", side_effect=OSError("Permission denied")):
            
            mock_validate.return_value = sample_session_data["session_id"]
            
            with pytest.raises(ValidationError, match="Could not save session"):
                session_manager.save_session(sample_session_data)
    
    def test_load_session_success(self, mock_settings, sample_session_data, temp_dir):
        """Test successful session loading."""
        mock_settings.session_storage_path = str(temp_dir / "sessions")
        session_manager = SessionManager(mock_settings)
        session_manager.session_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a session file
        session_file = session_manager.session_dir / f"{sample_session_data['session_id']}.json"
        with open(session_file, 'w') as f:
            json.dump(sample_session_data, f)
        
        with patch.object(session_manager.validator, 'validate_session_id') as mock_validate:
            mock_validate.return_value = sample_session_data["session_id"]
            
            loaded_data = session_manager.load_session(sample_session_data["session_id"])
            
            assert loaded_data == sample_session_data
    
    def test_load_session_not_found(self, mock_settings):
        """Test load_session fails when session doesn't exist."""
        session_manager = SessionManager(mock_settings)
        
        with patch.object(session_manager.validator, 'validate_session_id') as mock_validate:
            mock_validate.return_value = "DRA_20250628_120000"
            
            with pytest.raises(ValidationError, match="Session not found"):
                session_manager.load_session("DRA_20250628_120000")
    
    def test_load_session_invalid_json(self, mock_settings, temp_dir):
        """Test load_session handles corrupted JSON files."""
        mock_settings.session_storage_path = str(temp_dir / "sessions")
        session_manager = SessionManager(mock_settings)
        session_manager.session_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a corrupted session file
        session_file = session_manager.session_dir / "DRA_20250628_120000.json"
        with open(session_file, 'w') as f:
            f.write("invalid json content")
        
        with patch.object(session_manager.validator, 'validate_session_id') as mock_validate:
            mock_validate.return_value = "DRA_20250628_120000"
            
            with pytest.raises(ValidationError, match="Could not load session"):
                session_manager.load_session("DRA_20250628_120000")
    
    def test_update_session_stage_success(self, mock_settings, sample_session_data, sample_stage_data, temp_dir):
        """Test successful session stage update."""
        mock_settings.session_storage_path = str(temp_dir / "sessions")
        session_manager = SessionManager(mock_settings)
        session_manager.session_dir.mkdir(parents=True, exist_ok=True)
        
        # Create initial session
        session_file = session_manager.session_dir / f"{sample_session_data['session_id']}.json"
        with open(session_file, 'w') as f:
            json.dump(sample_session_data, f)
        
        with patch.object(session_manager, 'load_session') as mock_load, \
             patch.object(session_manager, 'save_session') as mock_save, \
             patch.object(session_manager.validator, 'validate_research_stage') as mock_validate_stage:
            
            mock_load.return_value = sample_session_data.copy()
            mock_validate_stage.return_value = sample_stage_data["stage"]
            
            session_manager.update_session_stage(
                sample_session_data["session_id"], 
                sample_stage_data
            )
            
            # Verify save was called with updated data
            mock_save.assert_called_once()
            saved_data = mock_save.call_args[0][0]
            
            assert len(saved_data["research_results"]["stages"]) == 1
            assert saved_data["research_results"]["stages"][0]["stage"] == sample_stage_data["stage"]
            assert saved_data["status"] == f"stage_{sample_stage_data['stage']}"
            assert "timestamp" in saved_data["research_results"]["stages"][0]
    
    def test_update_session_stage_invalid_data(self, mock_settings):
        """Test update_session_stage fails with invalid stage data."""
        session_manager = SessionManager(mock_settings)
        
        with patch.object(session_manager, 'load_session'):
            # Missing 'stage' field
            invalid_stage = {"findings": "test"}
            
            with pytest.raises(ValidationError, match="Stage data must contain 'stage' field"):
                session_manager.update_session_stage("DRA_20250628_120000", invalid_stage)
    
    def test_update_session_conclusions_success(self, mock_settings, sample_session_data):
        """Test successful session conclusions update."""
        session_manager = SessionManager(mock_settings)
        
        conclusions = {"recommendation": "iPhone 15", "reasoning": "Best camera quality"}
        confidence_score = 0.85
        
        with patch.object(session_manager, 'load_session') as mock_load, \
             patch.object(session_manager, 'save_session') as mock_save, \
             patch.object(session_manager.validator, 'validate_confidence_score') as mock_validate:
            
            mock_load.return_value = sample_session_data.copy()
            mock_validate.return_value = confidence_score
            
            session_manager.update_session_conclusions(
                sample_session_data["session_id"], 
                conclusions, 
                confidence_score
            )
            
            # Verify save was called with updated data
            mock_save.assert_called_once()
            saved_data = mock_save.call_args[0][0]
            
            assert saved_data["research_results"]["final_conclusions"] == conclusions
            assert saved_data["research_results"]["confidence_score"] == confidence_score
            assert saved_data["status"] == "completed"
    
    def test_list_sessions_success(self, mock_settings, temp_dir):
        """Test successful session listing."""
        mock_settings.session_storage_path = str(temp_dir / "sessions")
        session_manager = SessionManager(mock_settings)
        session_manager.session_dir.mkdir(parents=True, exist_ok=True)
        
        # Create multiple session files
        sessions_data = [
            {"session_id": "DRA_20250628_120000", "query": "Test 1", "status": "completed", "created_at": "2025-06-28T12:00:00"},
            {"session_id": "DRA_20250628_130000", "query": "Test 2", "status": "created", "created_at": "2025-06-28T13:00:00"}
        ]
        
        for session_data in sessions_data:
            session_file = session_manager.session_dir / f"{session_data['session_id']}.json"
            full_session = {
                **session_data,
                "research_results": {"confidence_score": 0.8}
            }
            with open(session_file, 'w') as f:
                json.dump(full_session, f)
        
        sessions = session_manager.list_sessions()
        
        assert len(sessions) == 2
        # Sessions should be sorted by creation time (newest first)
        assert sessions[0]["session_id"] == "DRA_20250628_130000"
        assert sessions[1]["session_id"] == "DRA_20250628_120000"
        
        # Check metadata structure
        for session in sessions:
            assert "session_id" in session
            assert "created_at" in session
            assert "query" in session
            assert "status" in session
            assert "confidence_score" in session
    
    def test_list_sessions_empty_directory(self, mock_settings):
        """Test list_sessions returns empty list when no sessions exist."""
        session_manager = SessionManager(mock_settings)
        
        sessions = session_manager.list_sessions()
        assert sessions == []
    
    def test_list_sessions_handles_corrupted_files(self, mock_settings, temp_dir):
        """Test list_sessions skips corrupted session files."""
        mock_settings.session_storage_path = str(temp_dir / "sessions")
        session_manager = SessionManager(mock_settings)
        session_manager.session_dir.mkdir(parents=True, exist_ok=True)
        
        # Create one valid and one corrupted session file
        valid_session = {
            "session_id": "DRA_20250628_120000", 
            "query": "Test", 
            "status": "completed",
            "created_at": "2025-06-28T12:00:00",
            "research_results": {"confidence_score": 0.8}
        }
        
        valid_file = session_manager.session_dir / "DRA_20250628_120000.json"
        with open(valid_file, 'w') as f:
            json.dump(valid_session, f)
        
        corrupted_file = session_manager.session_dir / "DRA_20250628_130000.json"
        with open(corrupted_file, 'w') as f:
            f.write("invalid json")
        
        sessions = session_manager.list_sessions()
        
        # Should only return the valid session
        assert len(sessions) == 1
        assert sessions[0]["session_id"] == "DRA_20250628_120000"
    
    def test_delete_session_success(self, mock_settings, sample_session_data, temp_dir):
        """Test successful session deletion."""
        mock_settings.session_storage_path = str(temp_dir / "sessions")
        mock_settings.report_storage_path = str(temp_dir / "reports")
        session_manager = SessionManager(mock_settings)
        session_manager.session_dir.mkdir(parents=True, exist_ok=True)
        
        # Create session file
        session_file = session_manager.session_dir / f"{sample_session_data['session_id']}.json"
        with open(session_file, 'w') as f:
            json.dump(sample_session_data, f)
        
        # Create report file
        report_dir = Path(temp_dir / "reports")
        report_dir.mkdir(parents=True, exist_ok=True)
        report_file = report_dir / "test_report.md"
        report_file.write_text("Test report content")
        
        # Update session with report path
        sample_session_data["report_path"] = str(report_file)
        with open(session_file, 'w') as f:
            json.dump(sample_session_data, f)
        
        with patch.object(session_manager.validator, 'validate_session_id') as mock_validate:
            mock_validate.return_value = sample_session_data["session_id"]
            
            result = session_manager.delete_session(sample_session_data["session_id"])
            
            assert result is True
            assert not session_file.exists()
            assert not report_file.exists()
    
    def test_delete_session_not_found(self, mock_settings):
        """Test delete_session returns False when session doesn't exist."""
        session_manager = SessionManager(mock_settings)
        
        with patch.object(session_manager.validator, 'validate_session_id') as mock_validate:
            mock_validate.return_value = "DRA_20250628_120000"
            
            result = session_manager.delete_session("DRA_20250628_120000")
            assert result is False
    
    def test_delete_session_without_report(self, mock_settings, sample_session_data, temp_dir):
        """Test delete_session works when session has no report file."""
        mock_settings.session_storage_path = str(temp_dir / "sessions")
        session_manager = SessionManager(mock_settings)
        session_manager.session_dir.mkdir(parents=True, exist_ok=True)
        
        # Create session file without report_path
        session_data = sample_session_data.copy()
        session_data["report_path"] = None
        
        session_file = session_manager.session_dir / f"{session_data['session_id']}.json"
        with open(session_file, 'w') as f:
            json.dump(session_data, f)
        
        with patch.object(session_manager.validator, 'validate_session_id') as mock_validate:
            mock_validate.return_value = session_data["session_id"]
            
            result = session_manager.delete_session(session_data["session_id"])
            
            assert result is True
            assert not session_file.exists()
    
    def test_cleanup_old_sessions_success(self, mock_settings, temp_dir):
        """Test cleanup of old sessions based on age."""
        mock_settings.session_storage_path = str(temp_dir / "sessions")
        session_manager = SessionManager(mock_settings)
        session_manager.session_dir.mkdir(parents=True, exist_ok=True)
        
        # Create session files with different ages
        old_session = session_manager.session_dir / "DRA_20250501_120000.json"
        recent_session = session_manager.session_dir / "DRA_20250627_120000.json"
        
        old_session.write_text('{"session_id": "DRA_20250501_120000"}')
        recent_session.write_text('{"session_id": "DRA_20250627_120000"}')
        
        # Mock file modification times
        import os
        import time
        from datetime import timedelta
        
        # Set old file to 40 days ago
        old_time = time.time() - (40 * 24 * 60 * 60)
        os.utime(old_session, (old_time, old_time))
        
        # Set recent file to 1 day ago
        recent_time = time.time() - (1 * 24 * 60 * 60)
        os.utime(recent_session, (recent_time, recent_time))
        
        with patch.object(session_manager, 'delete_session') as mock_delete:
            mock_delete.return_value = True
            
            deleted_count = session_manager.cleanup_old_sessions(days_old=30)
            
            assert deleted_count == 1
            mock_delete.assert_called_once_with("DRA_20250501_120000")
    
    def test_update_session_report_path_success(self, mock_settings, sample_session_data):
        """Test successful update of session report path."""
        session_manager = SessionManager(mock_settings)
        report_path = "/path/to/report.md"
        
        with patch.object(session_manager, 'load_session') as mock_load, \
             patch.object(session_manager, 'save_session') as mock_save, \
             patch.object(session_manager.validator, 'validate_file_path') as mock_validate:
            
            mock_load.return_value = sample_session_data.copy()
            mock_validate.return_value = report_path
            
            session_manager.update_session_report_path(
                sample_session_data["session_id"], 
                report_path
            )
            
            # Verify save was called with updated data
            mock_save.assert_called_once()
            saved_data = mock_save.call_args[0][0]
            
            assert saved_data["report_path"] == report_path
    
    def test_session_manager_directory_creation(self, mock_settings, temp_dir):
        """Test that SessionManager creates session directory if it doesn't exist."""
        non_existent_path = str(temp_dir / "new_sessions_dir")
        mock_settings.session_storage_path = non_existent_path
        
        # Directory doesn't exist initially
        assert not Path(non_existent_path).exists()
        
        session_manager = SessionManager(mock_settings)
        
        # Directory should be created
        assert session_manager.session_dir.exists()
        assert session_manager.session_dir == Path(non_existent_path)
    
    def test_generate_session_id_uniqueness(self, mock_settings):
        """Test that generated session IDs are unique across multiple calls."""
        session_manager = SessionManager(mock_settings)
        
        # Generate multiple session IDs
        ids = set()
        for i in range(10):
            with patch('utils.session_manager.datetime') as mock_dt:
                # Simulate different timestamps
                mock_dt.now().strftime.return_value = f"20250628_12000{i}"
                session_id = session_manager.generate_session_id()
                ids.add(session_id)
        
        # All IDs should be unique
        assert len(ids) == 10
        # All should follow correct format
        for session_id in ids:
            assert session_id.startswith("DRA_")
            assert len(session_id) == 19
    
    def test_save_session_updates_modified_timestamp(self, mock_settings, sample_session_data, temp_dir):
        """Test that save_session adds/updates modified_at timestamp."""
        mock_settings.session_storage_path = str(temp_dir / "sessions")
        session_manager = SessionManager(mock_settings)
        session_manager.session_dir.mkdir(parents=True, exist_ok=True)
        
        with patch.object(session_manager.validator, 'validate_session_id') as mock_validate:
            mock_validate.return_value = sample_session_data["session_id"]
            
            # Remove modified_at if it exists
            test_data = sample_session_data.copy()
            test_data.pop("modified_at", None)
            
            session_manager.save_session(test_data)
            
            # Load and verify modified_at was added
            session_file = session_manager.session_dir / f"{sample_session_data['session_id']}.json"
            with open(session_file, 'r') as f:
                saved_data = json.load(f)
            
            assert "modified_at" in saved_data
            assert saved_data["modified_at"] != test_data.get("created_at")
    
    def test_list_sessions_with_limit(self, mock_settings, temp_dir):
        """Test list_sessions respects the limit parameter."""
        mock_settings.session_storage_path = str(temp_dir / "sessions")
        session_manager = SessionManager(mock_settings)
        session_manager.session_dir.mkdir(parents=True, exist_ok=True)
        
        # Create 5 session files
        for i in range(5):
            session_data = {
                "session_id": f"DRA_20250628_12000{i}",
                "query": f"Test query {i}",
                "status": "completed",
                "created_at": f"2025-06-28T12:00:0{i}",
                "research_results": {"confidence_score": 0.8}
            }
            
            session_file = session_manager.session_dir / f"{session_data['session_id']}.json"
            with open(session_file, 'w') as f:
                json.dump(session_data, f)
        
        # Test with limit
        sessions = session_manager.list_sessions(limit=3)
        assert len(sessions) == 3
        
        # Test without limit (should return all 5)
        all_sessions = session_manager.list_sessions()
        assert len(all_sessions) == 5
    
    def test_list_sessions_query_truncation(self, mock_settings, temp_dir):
        """Test that list_sessions truncates long queries."""
        mock_settings.session_storage_path = str(temp_dir / "sessions")
        session_manager = SessionManager(mock_settings)
        session_manager.session_dir.mkdir(parents=True, exist_ok=True)
        
        # Create session with very long query
        long_query = "a" * 150  # 150 characters
        session_data = {
            "session_id": "DRA_20250628_120000",
            "query": long_query,
            "status": "completed",
            "created_at": "2025-06-28T12:00:00",
            "research_results": {"confidence_score": 0.8}
        }
        
        session_file = session_manager.session_dir / f"{session_data['session_id']}.json"
        with open(session_file, 'w') as f:
            json.dump(session_data, f)
        
        sessions = session_manager.list_sessions()
        
        # Query should be truncated to 100 characters
        assert len(sessions[0]["query"]) == 100
        assert sessions[0]["query"] == long_query[:100]
    
    def test_update_session_stage_with_existing_stages(self, mock_settings, sample_session_data, temp_dir):
        """Test updating session stage when stages already exist."""
        mock_settings.session_storage_path = str(temp_dir / "sessions")
        session_manager = SessionManager(mock_settings)
        
        # Create session with existing stages
        session_with_stages = sample_session_data.copy()
        session_with_stages["research_results"]["stages"] = [
            {"stage": 1, "findings": "Initial findings", "timestamp": "2025-06-28T12:00:00"}
        ]
        
        new_stage_data = {
            "stage": 2,
            "stage_name": "Source Research",
            "findings": {"sources": ["url1", "url2"]},
            "confidence": 0.8
        }
        
        with patch.object(session_manager, 'load_session') as mock_load, \
             patch.object(session_manager, 'save_session') as mock_save, \
             patch.object(session_manager.validator, 'validate_research_stage') as mock_validate_stage:
            
            mock_load.return_value = session_with_stages
            mock_validate_stage.return_value = new_stage_data["stage"]
            
            session_manager.update_session_stage(
                session_with_stages["session_id"], 
                new_stage_data
            )
            
            # Verify save was called with updated data
            mock_save.assert_called_once()
            saved_data = mock_save.call_args[0][0]
            
            # Should now have 2 stages
            assert len(saved_data["research_results"]["stages"]) == 2
            assert saved_data["research_results"]["stages"][1]["stage"] == 2
            assert saved_data["status"] == "stage_2"
    
    def test_update_session_stage_creates_research_results(self, mock_settings, sample_session_data):
        """Test that update_session_stage creates research_results if missing."""
        session_manager = SessionManager(mock_settings)
        
        # Create session without research_results
        session_without_results = sample_session_data.copy()
        del session_without_results["research_results"]
        
        stage_data = {"stage": 1, "findings": "test"}
        
        with patch.object(session_manager, 'load_session') as mock_load, \
             patch.object(session_manager, 'save_session') as mock_save, \
             patch.object(session_manager.validator, 'validate_research_stage') as mock_validate_stage:
            
            mock_load.return_value = session_without_results
            mock_validate_stage.return_value = 1
            
            session_manager.update_session_stage(
                session_without_results["session_id"], 
                stage_data
            )
            
            # Verify save was called with research_results created
            mock_save.assert_called_once()
            saved_data = mock_save.call_args[0][0]
            
            assert "research_results" in saved_data
            assert "stages" in saved_data["research_results"]
            assert len(saved_data["research_results"]["stages"]) == 1
    
    def test_session_manager_with_complex_context(self, mock_settings, mock_datetime):
        """Test session creation with complex nested context data."""
        session_manager = SessionManager(mock_settings)
        
        complex_context = {
            "personalize": True,
            "user_info": {
                "age": 30,
                "location": "San Francisco",
                "preferences": ["quality", "value", "sustainability"]
            },
            "constraints": {
                "budget": {"min": 100, "max": 500},
                "timeline": "urgent",
                "requirements": ["waterproof", "good camera"]
            },
            "preferences": {
                "brands": ["Apple", "Samsung", "Google"],
                "features": {
                    "camera": "high_priority",
                    "battery": "medium_priority",
                    "storage": "low_priority"
                }
            }
        }
        
        with patch.object(session_manager.validator, 'validate_query') as mock_validate_query, \
             patch.object(session_manager.validator, 'validate_context_data') as mock_validate_context, \
             patch.object(session_manager, 'save_session') as mock_save:
            
            mock_validate_query.return_value = "Complex test query"
            mock_validate_context.return_value = complex_context
            
            result = session_manager.create_session("Complex test query", complex_context)
            
            assert result["context"] == complex_context
            assert result["query"] == "Complex test query"
            mock_save.assert_called_once_with(result)
    
    def test_error_handling_in_cleanup_old_sessions(self, mock_settings, temp_dir):
        """Test error handling in cleanup_old_sessions method."""
        mock_settings.session_storage_path = str(temp_dir / "sessions")
        session_manager = SessionManager(mock_settings)
        session_manager.session_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a session file
        session_file = session_manager.session_dir / "DRA_20250501_120000.json"
        session_file.write_text('{"session_id": "DRA_20250501_120000"}')
        
        # Make file very old
        import os, time
        old_time = time.time() - (40 * 24 * 60 * 60)
        os.utime(session_file, (old_time, old_time))
        
        # Mock delete_session to fail
        with patch.object(session_manager, 'delete_session') as mock_delete:
            mock_delete.return_value = False  # Simulate failure
            
            deleted_count = session_manager.cleanup_old_sessions(days_old=30)
            
            # Should return 0 since deletion failed
            assert deleted_count == 0
