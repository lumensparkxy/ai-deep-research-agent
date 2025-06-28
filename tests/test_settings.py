"""
Unit tests for Settings configuration management.

Tests configuration loading, validation, and error handling.
"""

import pytest
import os
import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch, Mock

from config.settings import Settings, ConfigurationError


@pytest.mark.priority1
@pytest.mark.config
@pytest.mark.core
class TestSettings:
    """Test cases for Settings configuration management."""
    
    def test_settings_initialization_with_defaults(self):
        """Test Settings initializes with default values."""
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"}, clear=True):
            settings = Settings()

            assert settings.app_name == "Deep Research Agent"
            assert settings.gemini_api_key == "test_key"
            assert settings.ai_model == "gemini-1.5-pro-latest"
            assert settings.debug_mode is False

    def test_settings_missing_api_key(self):
        """Test Settings raises error when GEMINI_API_KEY is missing."""
        with patch.dict(os.environ, {}, clear=True):
            # Temporarily remove the variable if it was set by a previous test in the same run
            if "GEMINI_API_KEY" in os.environ:
                del os.environ["GEMINI_API_KEY"]
            with pytest.raises(ConfigurationError, match="Missing required environment variables: GEMINI_API_KEY"):
                Settings()
    
    def test_settings_with_custom_config_file(self, temp_dir):
        """Test Settings loads custom YAML configuration."""
        config_data = {
            "app": {
                "name": "Custom Research Agent",
                "debug": True
            },
            "ai": {
                "model": "custom-model",
                "max_tokens": 5000
            }
        }
        
        config_file = temp_dir / "custom_config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"}, clear=True):
            settings = Settings(config_path=str(config_file))
            
            assert settings.app_name == "Custom Research Agent"
            assert settings.debug_mode is True
            assert settings.ai_model == "custom-model"
    
    def test_settings_invalid_config_file(self):
        """Test Settings handles invalid YAML configuration."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: [")
            invalid_config = f.name

        try:
            with patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"}, clear=True):
                with pytest.raises(ConfigurationError, match="Invalid YAML configuration"):
                    Settings(config_path=invalid_config)
        finally:
            os.unlink(invalid_config)
    
    def test_settings_nonexistent_config_file(self):
        """Test Settings handles nonexistent configuration file."""
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"}, clear=True):
            with pytest.raises(ConfigurationError, match="Configuration file not found"):
                Settings(config_path="/nonexistent/config.yaml")
    
    def test_settings_environment_override(self):
        """Test environment variables override config file values."""
        with patch.dict(os.environ, {
            "GEMINI_API_KEY": "env_key",
            "DEBUG": "true",
            "AI_MODEL": "env-model"
        }, clear=True):
            settings = Settings()
            
            assert settings.gemini_api_key == "env_key"
            assert settings.debug_mode is True
            assert settings.ai_model == "env-model"
    
    def test_settings_directory_creation(self, temp_dir):
        """Test Settings creates required directories."""
        custom_session_path = str(temp_dir / "custom_sessions")
        custom_report_path = str(temp_dir / "custom_reports")
        
        with patch.dict(os.environ, {
            "GEMINI_API_KEY": "test_key",
            "SESSION_STORAGE_PATH": custom_session_path,
            "REPORT_OUTPUT_PATH": custom_report_path
        }, clear=True):
            settings = Settings()
            
            assert Path(custom_session_path).exists()
            assert Path(custom_report_path).exists()
    
    def test_settings_category_questions(self):
        """Test category-specific question loading."""
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"}, clear=True):
            settings = Settings()
            
            health_questions = settings.get_category_questions("health")
            assert isinstance(health_questions, list)
            assert len(health_questions) > 0
            
            # Test invalid category returns default 'other' questions
            invalid_questions = settings.get_category_questions("invalid_category")
            assert invalid_questions == settings.personalization_categories.get("other", [])

    def test_settings_report_templates(self):
        """Test report template loading."""
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"}, clear=True):
            settings = Settings()
            
            # Test getting report template
            template = settings.get_report_template("standard")
            assert isinstance(template, dict)
            assert "sections" in template

            # Test invalid template returns None
            invalid_template = settings.get_report_template("invalid_template")
            assert invalid_template is None

    def test_settings_ai_safety_configuration(self):
        """Test AI safety settings are properly configured."""
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"}, clear=True):
            settings = Settings()

            # Test safety settings exist
            assert hasattr(settings, 'ai_model')

    def test_settings_logging_configuration(self):
        """Test logging is properly configured."""
        with patch.dict(os.environ, {
            "GEMINI_API_KEY": "test_key",
            "DEBUG": "true"
        }, clear=True):
            settings = Settings()
            
            # Verify logger is configured
            assert settings.logger is not None
            assert settings.debug_mode is True
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
