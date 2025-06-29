"""
Unit tests for ResearchEngine critical error handling.

Tests AI initialization, API failures, and safety mechanisms.
"""

import pytest
from unittest.mock import patch, Mock, MagicMock

from core.research_engine import ResearchEngine
from utils.validators import ValidationError


class TestResearchEngineErrorHandling:
    """Test cases for ResearchEngine error handling and safety."""
    
    def test_research_engine_initialization_failure(self, mock_settings):
        """Test ResearchEngine handles AI initialization failures."""
        with patch('google.generativeai.configure') as mock_configure, \
             patch('google.generativeai.GenerativeModel') as mock_model:
            
            # Simulate API key configuration failure
            mock_configure.side_effect = Exception("Invalid API key")
            
            with pytest.raises(ValidationError, match="Could not initialize AI model"):
                ResearchEngine(mock_settings)
    
    def test_research_engine_gemini_api_failure(self, mock_settings):
        """Test ResearchEngine handles Gemini API failures gracefully."""
        with patch('google.generativeai.configure'), \
             patch('google.generativeai.GenerativeModel') as mock_model_class:
            
            # Mock model setup
            mock_model = Mock()
            mock_model_class.return_value = mock_model
            
            engine = ResearchEngine(mock_settings)
            
            # Mock API failure during research
            mock_model.generate_content.side_effect = Exception("API Rate Limit")
            
            with pytest.raises(ValidationError, match="Gemini API failed"):
                engine._call_gemini_with_retry("test query", max_retries=1)
    
    def test_research_engine_empty_response_handling(self, mock_settings):
        """Test ResearchEngine handles empty AI responses."""
        with patch('google.generativeai.configure'), \
             patch('google.generativeai.GenerativeModel') as mock_model_class:
            
            mock_model = Mock()
            mock_model_class.return_value = mock_model
            
            engine = ResearchEngine(mock_settings)
            
            # Mock empty response
            mock_response = Mock()
            mock_response.text = ""
            mock_model.generate_content.return_value = mock_response
            
            with pytest.raises(ValidationError, match="Empty response from Gemini"):
                engine._call_gemini_with_retry("test query")
    
    def test_research_engine_session_management_failure(self, mock_settings):
        """Test ResearchEngine handles session management failures."""
        with patch('google.generativeai.configure'), \
             patch('google.generativeai.GenerativeModel'), \
             patch('core.research_engine.SessionManager') as mock_session_manager_class:
            
            # Mock session manager failure
            mock_session_manager = Mock()
            mock_session_manager.create_session.side_effect = ValidationError("Session creation failed")
            mock_session_manager_class.return_value = mock_session_manager
            
            engine = ResearchEngine(mock_settings)
            
            with pytest.raises(ValidationError, match="Session creation failed"):
                engine.conduct_research("test query", {}, "test_session_id")
    
    def test_research_engine_validation_error_propagation(self, mock_settings):
        """Test ResearchEngine properly propagates validation errors."""
        with patch('google.generativeai.configure'), \
             patch('google.generativeai.GenerativeModel'):
            
            engine = ResearchEngine(mock_settings)
            
            # Test invalid query validation
            with patch.object(engine.validator, 'validate_query') as mock_validate:
                mock_validate.side_effect = ValidationError("Invalid query format")
                
                with pytest.raises(ValidationError, match="Invalid query format"):
                    engine.conduct_research("", {}, "test_session_id")
    
    def test_research_engine_stage_failure_recovery(self, mock_settings):
        """Test ResearchEngine handles individual stage failures."""
        with patch('google.generativeai.configure'), \
             patch('google.generativeai.GenerativeModel') as mock_model_class:
            
            mock_model = Mock()
            mock_model_class.return_value = mock_model
            
            engine = ResearchEngine(mock_settings)
            
            # Mock successful query validation but stage failure
            with patch.object(engine.validator, 'validate_query', return_value="valid query"), \
                 patch.object(engine.session_manager, 'create_session') as mock_create, \
                 patch.object(engine.session_manager, 'update_session_conclusions') as mock_update, \
                 patch.object(engine, '_stage_1_information_gathering') as mock_stage:
                
                mock_create.return_value = {"session_id": "DRA_20250629_120000"}
                mock_update.return_value = None  # Mock the update method to prevent session ID validation
                mock_stage.side_effect = Exception("Stage 1 failed")
                
                # Should handle stage failure gracefully
                result = engine.conduct_research("test query", {}, "DRA_20250629_120000")
                # When stages fail, the engine continues and reports errors in gaps_identified
                assert "final_conclusions" in result
                # Check that stage errors are reported somewhere in the result
                gaps = result["final_conclusions"].get("gaps_identified", [])
                stage_error_found = any("Error in" in gap for gap in gaps)
                assert stage_error_found, f"Expected stage error in gaps, got: {gaps}"
    
    def test_research_engine_safety_settings_validation(self, mock_settings):
        """Test ResearchEngine applies proper safety settings."""
        with patch('google.generativeai.configure'), \
             patch('google.generativeai.GenerativeModel') as mock_model_class:
            
            engine = ResearchEngine(mock_settings)
            
            # Verify model was created with safety settings
            mock_model_class.assert_called_once()
            call_args = mock_model_class.call_args
            assert "safety_settings" in call_args[1]
    
    def test_research_engine_network_timeout_handling(self, mock_settings):
        """Test ResearchEngine handles network timeouts."""
        with patch('google.generativeai.configure'), \
             patch('google.generativeai.GenerativeModel') as mock_model_class:
            
            mock_model = Mock()
            mock_model_class.return_value = mock_model
            
            engine = ResearchEngine(mock_settings)
            
            # Mock network timeout
            import socket
            mock_model.generate_content.side_effect = socket.timeout("Network timeout")
            
            with pytest.raises(ValidationError, match="Gemini API failed"):
                engine._call_gemini_with_retry("test query", max_retries=1)
    
    def test_research_engine_memory_management(self, mock_settings):
        """Test ResearchEngine handles large response data safely."""
        with patch('google.generativeai.configure'), \
             patch('google.generativeai.GenerativeModel') as mock_model_class:
            
            mock_model = Mock()
            mock_model_class.return_value = mock_model
            
            engine = ResearchEngine(mock_settings)
            
            # Mock very large response
            large_response = Mock()
            large_response.text = "x" * (10 * 1024 * 1024)  # 10MB response
            mock_model.generate_content.return_value = large_response
            
            # Should handle large responses without memory issues
            result = engine._call_gemini_with_retry("test query")
            assert len(result) > 0  # Check that some response is returned
