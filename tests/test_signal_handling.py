"""
Test signal handling for graceful session interruption.
"""

import pytest
import signal
import json
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from main import signal_handler, set_current_session, clear_current_session
from utils.session_manager import SessionManager


@pytest.mark.priority1
@pytest.mark.unit
class TestSignalHandling:
    """Test cases for signal handling functionality."""

    def test_signal_handler_with_active_session(self, mock_settings, temp_dir):
        """Test signal handler marks active session as interrupted."""
        # Setup
        mock_settings.session_storage_path = str(temp_dir / "sessions")
        session_manager = SessionManager(mock_settings)
        session_manager.session_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a session file
        session_data = {
            "session_id": "DRA_20250629_120000",
            "status": "stage_1",
            "query": "test query",
            "created_at": "2025-06-29T12:00:00"
        }
        
        session_file = session_manager.session_dir / "DRA_20250629_120000.json"
        with open(session_file, 'w') as f:
            json.dump(session_data, f)
        
        # Set current session
        set_current_session(session_manager, "DRA_20250629_120000")
        
        # Mock sys.exit to prevent actual exit
        with patch('main.sys.exit') as mock_exit, \
             patch('builtins.print') as mock_print:
            
            # Call signal handler
            signal_handler(signal.SIGINT, None)
            
            # Verify session was marked as interrupted
            with open(session_file, 'r') as f:
                updated_session = json.load(f)
            
            assert updated_session["status"] == "interrupted"
            mock_exit.assert_called_once_with(0)
            
            # Check that appropriate messages were printed
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            assert any("SIGINT" in call for call in print_calls)
            assert any("marked as interrupted" in call for call in print_calls)

    def test_signal_handler_without_active_session(self):
        """Test signal handler when no active session exists."""
        # Clear any existing session
        clear_current_session()
        
        with patch('main.sys.exit') as mock_exit, \
             patch('builtins.print') as mock_print:
            
            # Call signal handler
            signal_handler(signal.SIGINT, None)
            
            # Should exit gracefully without errors
            mock_exit.assert_called_once_with(0)
            
            # Check that appropriate messages were printed
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            assert any("SIGINT" in call for call in print_calls)
            assert any("interrupted. Goodbye!" in call for call in print_calls)

    def test_signal_handler_with_completed_session(self, mock_settings, temp_dir):
        """Test signal handler doesn't modify already completed sessions."""
        # Setup
        mock_settings.session_storage_path = str(temp_dir / "sessions")
        session_manager = SessionManager(mock_settings)
        session_manager.session_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a completed session file
        session_data = {
            "session_id": "DRA_20250629_120000",
            "status": "completed",
            "query": "test query",
            "created_at": "2025-06-29T12:00:00"
        }
        
        session_file = session_manager.session_dir / "DRA_20250629_120000.json"
        with open(session_file, 'w') as f:
            json.dump(session_data, f)
        
        # Set current session
        set_current_session(session_manager, "DRA_20250629_120000")
        
        with patch('main.sys.exit') as mock_exit:
            # Call signal handler
            signal_handler(signal.SIGINT, None)
            
            # Verify session status wasn't changed
            with open(session_file, 'r') as f:
                updated_session = json.load(f)
            
            assert updated_session["status"] == "completed"
            mock_exit.assert_called_once_with(0)

    def test_set_and_clear_current_session(self, mock_settings):
        """Test setting and clearing current session."""
        session_manager = SessionManager(mock_settings)
        session_id = "test_session_123"
        
        # Test setting current session
        set_current_session(session_manager, session_id)
        
        # Access globals to verify
        from main import _current_session_manager, _current_session_id
        assert _current_session_manager is session_manager
        assert _current_session_id == session_id
        
        # Test clearing current session
        clear_current_session()
        
        from main import _current_session_manager, _current_session_id
        assert _current_session_manager is None
        assert _current_session_id is None

    def test_signal_handler_sigterm(self, mock_settings, temp_dir):
        """Test signal handler works for SIGTERM as well."""
        # Setup similar to SIGINT test
        mock_settings.session_storage_path = str(temp_dir / "sessions")
        session_manager = SessionManager(mock_settings)
        session_manager.session_dir.mkdir(parents=True, exist_ok=True)
        
        session_data = {
            "session_id": "DRA_20250629_120000",
            "status": "created",
            "query": "test query",
            "created_at": "2025-06-29T12:00:00"
        }
        
        session_file = session_manager.session_dir / "DRA_20250629_120000.json"
        with open(session_file, 'w') as f:
            json.dump(session_data, f)
        
        set_current_session(session_manager, "DRA_20250629_120000")
        
        with patch('main.sys.exit') as mock_exit, \
             patch('builtins.print') as mock_print:
            
            # Call signal handler with SIGTERM
            signal_handler(signal.SIGTERM, None)
            
            # Verify session was marked as interrupted
            with open(session_file, 'r') as f:
                updated_session = json.load(f)
            
            assert updated_session["status"] == "interrupted"
            mock_exit.assert_called_once_with(0)
            
            # Check that SIGTERM was mentioned
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            assert any("SIGTERM" in call for call in print_calls)

    def test_signal_handler_error_handling(self, mock_settings):
        """Test signal handler handles errors gracefully."""
        # Create a mock session manager that raises an exception
        mock_session_manager = Mock()
        mock_session_manager.load_session.side_effect = Exception("Test error")
        
        set_current_session(mock_session_manager, "test_session")
        
        with patch('main.sys.exit') as mock_exit, \
             patch('builtins.print') as mock_print:
            
            # Call signal handler - should not crash
            signal_handler(signal.SIGINT, None)
            
            # Should still exit gracefully
            mock_exit.assert_called_once_with(0)
            
            # Check error was handled
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            assert any("Could not mark session as interrupted" in call for call in print_calls)