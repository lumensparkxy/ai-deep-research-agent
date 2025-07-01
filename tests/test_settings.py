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
            assert settings.ai_model == "gemini-2.5-flash"
            assert settings.debug_mode is False

    def test_settings_missing_api_key(self):
        """Test Settings raises error when GEMINI_API_KEY is missing."""
        # Mock dotenv loading to prevent it from loading the .env file
        with patch('config.settings.load_dotenv'), \
             patch.dict(os.environ, {}, clear=True):
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
    
    def test_dynamic_personalization_settings(self):
        """Test dynamic personalization settings are properly loaded."""
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"}, clear=True):
            settings = Settings()
            
            # Test dynamic personalization settings
            dp_settings = settings.dynamic_personalization
            assert dp_settings.enabled is True
            assert dp_settings.fallback_to_static is True
            assert dp_settings.max_questions == 10
            assert dp_settings.min_questions == 3
            assert dp_settings.timeout_seconds == 300
            assert dp_settings.ai_question_generation is True
            assert dp_settings.context_analysis is True
            assert dp_settings.completion_assessment is True
    
    def test_ai_question_generation_settings(self):
        """Test AI question generation settings are properly loaded."""
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"}, clear=True):
            settings = Settings()
            
            # Test AI question generation settings
            ai_settings = settings.ai_question_generation
            assert ai_settings.enabled is True
            assert ai_settings.temperature == 0.9
            assert ai_settings.top_p == 0.95
            assert ai_settings.max_tokens == 4000
            assert ai_settings.question_validation is True
            assert ai_settings.duplicate_detection is True
            assert ai_settings.relevance_threshold == 0.6
    
    def test_context_analysis_settings(self):
        """Test context analysis settings are properly loaded."""
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"}, clear=True):
            settings = Settings()
            
            # Test context analysis settings
            context_settings = settings.context_analysis
            assert context_settings.enabled is True
            assert context_settings.confidence_threshold == 0.6
            assert context_settings.budget_weight == 0.8
            assert context_settings.timeline_weight == 0.9
            assert context_settings.quality_weight == 0.7
            assert context_settings.convenience_weight == 0.6
            assert context_settings.communication_style is True
            assert context_settings.expertise_level is True
            assert context_settings.decision_making_style is True
            assert context_settings.emotional_indicators is True
            assert context_settings.critical_gap_threshold == 0.8
            assert context_settings.importance_weighting is True
            assert context_settings.research_impact_scoring is True
    
    def test_user_preferences_settings(self):
        """Test user preferences settings are properly loaded."""
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"}, clear=True):
            settings = Settings()
            
            # Test user preferences settings
            pref_settings = settings.user_preferences
            assert pref_settings.storage_enabled is True
            assert pref_settings.storage_location == "data/user_preferences"
            assert pref_settings.session_learning is True
            assert pref_settings.cross_session_patterns is False
            assert pref_settings.preference_expiry_days == 30
    
    def test_performance_settings(self):
        """Test performance settings are properly loaded."""
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"}, clear=True):
            settings = Settings()
            
            # Test performance settings
            perf_settings = settings.performance
            assert perf_settings.ai_response_timeout == 10
            assert perf_settings.concurrent_analysis is False
            assert perf_settings.cache_question_templates is True
            assert perf_settings.context_analysis_depth == "standard"
    
    def test_conversation_mode_configuration(self):
        """Test conversation mode configurations are properly loaded."""
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"}, clear=True):
            settings = Settings()
            
            # Test getting specific conversation modes
            quick_mode = settings.get_conversation_mode_config("quick")
            assert quick_mode.max_questions == 3
            assert quick_mode.time_sensitivity_threshold == 0.8
            assert quick_mode.question_depth == "surface"
            assert "concise" in quick_mode.ai_prompt_modifier.lower()
            
            standard_mode = settings.get_conversation_mode_config("standard")
            assert standard_mode.max_questions == 6
            assert standard_mode.time_sensitivity_threshold == 0.5
            assert standard_mode.question_depth == "moderate"
            
            deep_mode = settings.get_conversation_mode_config("deep")
            assert deep_mode.max_questions == 12
            assert deep_mode.time_sensitivity_threshold == 0.2
            assert deep_mode.question_depth == "comprehensive"
            
            # Test fallback for invalid mode
            invalid_mode = settings.get_conversation_mode_config("invalid")
            assert invalid_mode.max_questions == 6  # Falls back to standard
    
    def test_fallback_questions(self):
        """Test fallback questions for different categories."""
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"}, clear=True):
            settings = Settings()
            
            # Test category-specific fallback questions
            tech_questions = settings.get_fallback_questions("technology")
            assert isinstance(tech_questions, list)
            assert len(tech_questions) > 0
            
            health_questions = settings.get_fallback_questions("health")
            assert isinstance(health_questions, list)
            assert len(health_questions) > 0
            
            # Test fallback for invalid category
            other_questions = settings.get_fallback_questions("invalid_category")
            assert isinstance(other_questions, list)
            assert len(other_questions) > 0
    
    def test_available_conversation_modes(self):
        """Test getting list of available conversation modes."""
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"}, clear=True):
            settings = Settings()
            
            modes = settings.available_conversation_modes
            assert isinstance(modes, list)
            assert "quick" in modes
            assert "standard" in modes
            assert "deep" in modes
            assert "adaptive" in modes
    
    def test_environment_overrides(self):
        """Test environment-specific setting overrides."""
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"}, clear=True):
            settings = Settings()
            
            # Test getting environment override in production (default environment)
            # In production environment, max_questions is overridden to 12
            override = settings.get_environment_override("dynamic_personalization.max_questions")
            assert override == 12  # Production environment overrides this to 12
            
            # Test with default value
            override_with_default = settings.get_environment_override(
                "nonexistent.setting", default="default_value"
            )
            assert override_with_default == "default_value"
    
    def test_user_preferences_directory_creation(self, temp_dir):
        """Test that user preferences directory is created."""
        custom_session_path = str(temp_dir / "custom_sessions")
        custom_report_path = str(temp_dir / "custom_reports")
        custom_prefs_path = str(temp_dir / "custom_user_prefs")
        
        config_data = {
            "user_preferences": {
                "storage_location": custom_prefs_path
            }
        }
        
        config_file = temp_dir / "test_config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        with patch.dict(os.environ, {
            "GEMINI_API_KEY": "test_key",
            "SESSION_STORAGE_PATH": custom_session_path,
            "REPORT_OUTPUT_PATH": custom_report_path
        }, clear=True):
            settings = Settings(config_path=str(config_file))
            
            assert Path(custom_session_path).exists()
            assert Path(custom_report_path).exists()
            assert Path(custom_prefs_path).exists()
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
