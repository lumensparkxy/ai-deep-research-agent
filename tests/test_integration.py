"""
Integration tests for Deep Research Agent components.

Tests interaction between multiple components and end-to-end workflows.
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, Mock, MagicMock

from config.settings import Settings
from core.conversation import ConversationHandler
from core.research_engine import ResearchEngine
from utils.session_manager import SessionManager
from utils.validators import InputValidator, ValidationError


@pytest.mark.priority2
@pytest.mark.integration
@pytest.mark.slow
class TestIntegration:
    """Integration tests for component interactions."""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace for integration testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            (workspace / "sessions").mkdir()
            (workspace / "reports").mkdir()
            yield workspace
    
    @pytest.fixture
    def integration_settings(self, temp_workspace):
        """Settings configured for integration testing."""
        # Use a unique subdirectory for each test to ensure isolation
        test_session_path = temp_workspace / "sessions"
        test_report_path = temp_workspace / "reports"
        test_session_path.mkdir(exist_ok=True)
        test_report_path.mkdir(exist_ok=True)

        with patch.dict('os.environ', {
            'GEMINI_API_KEY': 'test_integration_key',
            'SESSION_STORAGE_PATH': str(test_session_path),
            'REPORT_OUTPUT_PATH': str(test_report_path),
            'DEBUG': 'true'
        }):
            yield Settings()
    
    def test_full_conversation_to_session_flow(self, integration_settings, temp_workspace):
        """Test complete flow from conversation to session creation."""
        # Mock the research engine to avoid real AI calls
        with patch('core.research_engine.ResearchEngine') as mock_engine_class, \
             patch('core.report_generator.ReportGenerator') as mock_generator_class:
            mock_engine = Mock()
            mock_engine_class.return_value = mock_engine
            mock_generator = Mock()
            mock_generator_class.return_value = mock_generator
            
            conversation_handler = ConversationHandler(integration_settings)
            
            # Test conversation flow with mocked inputs
            with patch('builtins.input', side_effect=['Best smartphone under $500', 'y', 'n', 'standard']):
                
                # Mock the research engine conduct_research method
                mock_engine.conduct_research.return_value = {
                    "session_id": "DRA_20250628_120000",
                    "status": "completed",
                    "research_results": {
                        "confidence_score": 0.85,
                        "final_conclusions": {"recommendation": "iPhone 15"}
                    }
                }
                
                # This should create a session and save it
                with patch.object(conversation_handler, 'display_progress'), \
                     patch.object(conversation_handler, '_show_completion_message'):
                    
                    conversation_handler.start_interactive_session()
                    
                    # Verify session was created
                    mock_engine.conduct_research.assert_called_once()
                    call_args = mock_engine.conduct_research.call_args[0]
                    assert "smartphone" in call_args[0].lower()  # Query was passed
    
    def test_session_manager_validator_integration(self, integration_settings, temp_workspace):
        """Test SessionManager and InputValidator work together correctly."""
        session_manager = SessionManager(integration_settings)
        
        # Test creating session with validation
        valid_query = "What are the best programming languages to learn?"
        valid_context = {
            "personalize": True,
            "user_info": {"experience": "beginner"},
            "constraints": {"budget": "free resources"}
        }
        
        session = session_manager.create_session(valid_query, valid_context)
        
        # Verify session structure
        assert session["session_id"].startswith("DRA_")
        assert session["query"] == valid_query
        assert "user_info" in session["context"]
        assert session["status"] == "created"
        
        # Test loading the session back
        loaded_session = session_manager.load_session(session["session_id"])
        assert loaded_session["query"] == valid_query
        assert loaded_session["session_id"] == session["session_id"]
    
    def test_settings_session_manager_integration(self, temp_workspace):
        """Test Settings and SessionManager directory management."""
        custom_session_path = str(temp_workspace / "custom_sessions")
        custom_report_path = str(temp_workspace / "custom_reports")
        
        with patch.dict('os.environ', {
            'GEMINI_API_KEY': 'test_key',
            'SESSION_STORAGE_PATH': custom_session_path,
            'REPORT_OUTPUT_PATH': custom_report_path
        }):
            settings = Settings()
            session_manager = SessionManager(settings)
            
            # Verify directories were created
            assert Path(custom_session_path).exists()
            assert Path(custom_report_path).exists()
            
            # Verify session manager uses correct paths
            assert str(session_manager.session_dir) == custom_session_path
    
    def test_validator_session_data_integration(self, integration_settings):
        """Test validator properly handles complex session data."""
        validator = InputValidator()
        session_manager = SessionManager(integration_settings)
        
        # Complex realistic data
        complex_context = {
            "personalize": True,
            "user_info": {
                "age": 28,
                "location": "San Francisco, CA",
                "budget": "$500-1000",
                "experience": "intermediate",
                "preferences": ["open source", "cross-platform", "good documentation"]
            },
            "constraints": {
                "timeline": "3 months",
                "learning_style": "hands-on projects",
                "availability": "2-3 hours per day"
            }
        }
        
        # Should validate and process correctly
        validated_context = validator.validate_context_data(complex_context)
        
        # Create session with validated data
        session = session_manager.create_session(
            "Best programming language for mobile app development",
            validated_context
        )
        
        assert session["context"]["personalize"] is True
        assert "user_info" in session["context"]
        assert len(session["context"]["user_info"]["preferences"]) == 3
    
    def test_error_propagation_integration(self, integration_settings):
        """Test error handling across component boundaries."""
        session_manager = SessionManager(integration_settings)
        
        # Test validation error propagation
        with pytest.raises(ValidationError, match="Query must be at least 5 characters"):
            session_manager.create_session("Hi", {})
        
        # Test session ID validation across components
        with pytest.raises(ValidationError, match="Session ID must follow format"):
            session_manager.load_session("invalid_session_id")
    
    def test_conversation_research_engine_integration(self, integration_settings):
        """Test ConversationHandler and ResearchEngine integration."""
        with patch('google.generativeai.configure'), \
             patch('google.generativeai.GenerativeModel') as mock_model_class, \
             patch('core.research_engine.ResearchEngine'), \
             patch('core.report_generator.ReportGenerator'):
            
            # Setup mocked AI model
            mock_model = Mock()
            mock_response = Mock()
            mock_response.text = "Mocked AI response for testing"
            mock_model.generate_content.return_value = mock_response
            mock_model_class.return_value = mock_model
            
            conversation_handler = ConversationHandler(integration_settings)
            
            # Test that conversation handler can create and use research engine
            assert hasattr(conversation_handler, 'settings')
            
            # Mock user input for complete flow
            with patch('builtins.input', side_effect=['Test research query', 'n', 'quick']):
                with patch.object(conversation_handler, 'display_progress'), \
                     patch.object(conversation_handler, '_show_completion_message'):
                    
                    # Should complete without errors
                    conversation_handler.start_interactive_session()
    
    def test_file_operations_integration(self, integration_settings, temp_workspace):
        """Test file operations work correctly across components."""
        session_manager = SessionManager(integration_settings)
        
        # Create multiple sessions
        session1 = session_manager.create_session("Query 1", {})
        session2 = session_manager.create_session("Query 2", {})
        
        # Update sessions with different data
        session_manager.update_session_stage(session1["session_id"], {
            "stage": 1,
            "findings": {"test": "data1"}
        })
        
        session_manager.update_session_stage(session2["session_id"], {
            "stage": 2,
            "findings": {"test": "data2"}
        })
        
        # List sessions and verify
        sessions = session_manager.list_sessions()
        assert len(sessions) == 2
        
        # Verify file system state
        session_files = list((temp_workspace / "sessions").glob("*.json"))
        assert len(session_files) == 2
        
        # Cleanup test
        deleted1 = session_manager.delete_session(session1["session_id"])
        deleted2 = session_manager.delete_session(session2["session_id"])
        
        assert deleted1 is True
        assert deleted2 is True
        
        # Verify cleanup
        remaining_sessions = session_manager.list_sessions()
        assert len(remaining_sessions) == 0
    
    def test_concurrent_session_operations(self, integration_settings):
        """Test handling of concurrent session operations."""
        session_manager = SessionManager(integration_settings)
        
        # Simulate concurrent session creation
        sessions = []
        for i in range(10):
            session = session_manager.create_session(f"Query {i}", {"test": i})
            sessions.append(session["session_id"])
        
        # Verify all sessions were created uniquely
        assert len(set(sessions)) == 10  # All unique
        
        # Verify all can be loaded
        for session_id in sessions:
            loaded = session_manager.load_session(session_id)
            assert loaded["session_id"] == session_id
    
    def test_data_consistency_across_operations(self, integration_settings):
        """Test data remains consistent across save/load operations."""
        session_manager = SessionManager(integration_settings)
        
        # Create session with complex data
        original_session = session_manager.create_session(
            "Complex query with special characters: $500 budget & <constraints>",
            {
                "personalize": True,
                "user_info": {"budget": 500, "special": "characters & symbols"},
                "preferences": ["item1", "item2", "item3"]
            }
        )
        
        session_id = original_session["session_id"]
        
        # Update with stage data
        session_manager.update_session_stage(session_id, {
            "stage": 3,
            "findings": {"complex": {"nested": {"data": [1, 2, 3]}}},
            "confidence": 0.85
        })
        
        # Update with conclusions
        session_manager.update_session_conclusions(
            session_id,
            {"final": "recommendation", "reasoning": "detailed analysis"},
            0.92
        )
        
        # Load and verify data integrity
        final_session = session_manager.load_session(session_id)
        
        assert final_session["query"] == original_session["query"]
        assert final_session["context"]["personalize"] is True
        assert len(final_session["research_results"]["stages"]) == 1
        assert final_session["research_results"]["confidence_score"] == 0.92
        assert final_session["research_results"]["final_conclusions"]["final"] == "recommendation"
