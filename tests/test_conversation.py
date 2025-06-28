"""
Unit tests for ConversationHandler class.

Tests user interaction, conversation flow, and error handling.
"""

import pytest
from unittest.mock import Mock, patch, call
from io import StringIO

from core.conversation import ConversationHandler
from utils.validators import ValidationError


class TestConversationHandler:
    """Test cases for ConversationHandler functionality."""
    
    @pytest.fixture
    def conversation_handler(self, mock_settings):
        """Create a ConversationHandler instance for testing."""
        return ConversationHandler(mock_settings)
    
    def test_conversation_handler_initialization(self, conversation_handler, mock_settings):
        """Test ConversationHandler initializes correctly."""
        assert conversation_handler.settings == mock_settings
        assert conversation_handler.session_manager is not None
        assert conversation_handler.validator is not None
        assert conversation_handler.current_session is None
        assert conversation_handler.user_context == {}
    
    def test_classify_query_health(self, conversation_handler):
        """Test query classification for health category."""
        health_queries = [
            "Best diet for weight loss",
            "How to improve my fitness routine",
            "What are healthy breakfast options",
            "Best medical insurance plans"
        ]
        
        for query in health_queries:
            category = conversation_handler._classify_query(query)
            assert category == "health"
    
    def test_classify_query_finance(self, conversation_handler):
        """Test query classification for finance category."""
        finance_queries = [
            "Best investment strategy for 2025",
            "Should I get a personal loan",
            "Compare credit card options",
            "Financial planning for retirement"
        ]
        
        for query in finance_queries:
            category = conversation_handler._classify_query(query)
            assert category == "finance"
    
    def test_classify_query_technology(self, conversation_handler):
        """Test query classification for technology category."""
        tech_queries = {
            "Best smartphone under $500": "technology",
            "Which laptop is good for programming": "technology",
            "Compare online project management software": "technology",
            "Best digital marketing tools": "technology"
        }
        
        for query, expected_category in tech_queries.items():
            category = conversation_handler._classify_query(query)
            assert category == expected_category
    
    def test_classify_query_lifestyle(self, conversation_handler):
        """Test query classification for lifestyle category."""
        lifestyle_queries = {
            "Best travel destinations in Europe": "lifestyle",
            "Where to find good restaurants in SF": "lifestyle",
            "Fun hobbies for adults": "lifestyle",
            "Best entertainment streaming services": "lifestyle"
        }
        
        for query, expected_category in lifestyle_queries.items():
            category = conversation_handler._classify_query(query)
            assert category == expected_category
    
    def test_classify_query_other(self, conversation_handler):
        """Test query classification for other category."""
        other_queries = [
            "How to learn a new language",
            "Best books to read this year",
            "Career change advice"
        ]
        
        for query in other_queries:
            category = conversation_handler._classify_query(query)
            assert category == "other"
    
    @patch('builtins.input', side_effect=['Best smartphone under $500', 'y'])
    def test_get_research_query_success(self, mock_input, conversation_handler):
        """Test successful research query input."""
        with patch.object(conversation_handler.validator, 'validate_query') as mock_validate:
            mock_validate.return_value = "Best smartphone under $500"
            
            result = conversation_handler._get_research_query()
            
            assert result == "Best smartphone under $500"
            mock_validate.assert_called_once_with("Best smartphone under $500")
    
    @patch('builtins.input', side_effect=['', 'Hi', 'Best smartphone under $500', 'y'])
    def test_get_research_query_with_retries(self, mock_input, conversation_handler):
        """Test research query input with empty input and retry."""
        with patch.object(conversation_handler.validator, 'validate_query') as mock_validate:
            # First call (empty) and second call (too short) fail, third succeeds
            mock_validate.side_effect = [
                ValidationError("Query too short"),
                "Best smartphone under $500"
            ]
            
            result = conversation_handler._get_research_query()
            
            assert result == "Best smartphone under $500"
            assert mock_validate.call_count == 2
    
    @patch('builtins.input', side_effect=['Best smartphone under $500', 'n', 'Better query', 'y'])
    def test_get_research_query_with_confirmation_retry(self, mock_input, conversation_handler):
        """Test research query input with confirmation retry."""
        with patch.object(conversation_handler.validator, 'validate_query') as mock_validate:
            mock_validate.side_effect = ["Best smartphone under $500", "Better query"]
            
            result = conversation_handler._get_research_query()
            
            assert result == "Better query"
            assert mock_validate.call_count == 2
    
    @patch('builtins.input', side_effect=['y'])
    def test_ask_personalization_yes(self, mock_input, conversation_handler):
        """Test asking for personalization - yes response."""
        result = conversation_handler._ask_personalization()
        assert result is True
    
    @patch('builtins.input', side_effect=['n'])
    def test_ask_personalization_no(self, mock_input, conversation_handler):
        """Test asking for personalization - no response."""
        result = conversation_handler._ask_personalization()
        assert result is False
    
    @patch('builtins.input', side_effect=['yes'])
    def test_ask_personalization_yes_full_word(self, mock_input, conversation_handler):
        """Test asking for personalization - 'yes' response."""
        result = conversation_handler._ask_personalization()
        assert result is True
    
    @patch('builtins.input', side_effect=[''])
    def test_ask_personalization_default_yes(self, mock_input, conversation_handler):
        """Test asking for personalization - default (empty) is yes."""
        result = conversation_handler._ask_personalization()
        assert result is True
    
    @patch('builtins.input', side_effect=['invalid', 'y'])
    def test_ask_personalization_invalid_then_valid(self, mock_input, conversation_handler):
        """Test asking for personalization with invalid input then valid."""
        result = conversation_handler._ask_personalization()
        assert result is True
    
    @patch('builtins.input', side_effect=['30', 'photography', '500', '6 months', 'USA'])
    def test_gather_personalization_health_category(self, mock_input, conversation_handler):
        """Test gathering personalization for health category."""
        query = "Best fitness routine for weight loss"
        
        with patch.object(conversation_handler, '_classify_query') as mock_classify, \
             patch.object(conversation_handler.settings, 'get_category_questions') as mock_questions:
            
            mock_classify.return_value = "health"
            mock_questions.return_value = ["age", "fitness_goal"]
            
            result = conversation_handler._gather_personalization(query)
            
            # Should contain user_info and constraints
            assert "user_info" in result
            assert "preferences" in result
            assert "constraints" in result
            assert result["user_info"]["age"] == "30"
            assert result["preferences"]["fitness_goal"] == "photography"
            assert result["constraints"]["budget"] == "500"
            assert result["constraints"]["timeline"] == "6 months"
            assert result["constraints"]["location"] == "USA"
    
    @patch('builtins.input', side_effect=[''])
    def test_ask_optional_empty_response(self, mock_input, conversation_handler):
        """Test asking optional question with empty response."""
        result = conversation_handler._ask_optional("Test question")
        assert result is None
    
    @patch('builtins.input', side_effect=['Some answer'])
    def test_ask_optional_with_answer(self, mock_input, conversation_handler):
        """Test asking optional question with answer."""
        result = conversation_handler._ask_optional("Test question")
        assert result == "Some answer"
    
    @patch('builtins.input', side_effect=['2'])
    def test_ask_report_depth_standard(self, mock_input, conversation_handler):
        """Test asking for report depth - standard."""
        result = conversation_handler._ask_report_depth()
        assert result == "standard"
    
    @patch('builtins.input', side_effect=['quick'])
    def test_ask_report_depth_quick_word(self, mock_input, conversation_handler):
        """Test asking for report depth - quick by word."""
        result = conversation_handler._ask_report_depth()
        assert result == "quick"
    
    @patch('builtins.input', side_effect=[''])
    def test_ask_report_depth_default(self, mock_input, conversation_handler):
        """Test asking for report depth - default is standard."""
        result = conversation_handler._ask_report_depth()
        assert result == "standard"
    
    @patch('builtins.input', side_effect=['invalid', '3'])
    def test_ask_report_depth_invalid_then_valid(self, mock_input, conversation_handler):
        """Test asking for report depth with invalid input then valid."""
        result = conversation_handler._ask_report_depth()
        assert result == "detailed"
    
    @patch('builtins.input', side_effect=['y'])
    def test_confirm_action_yes(self, mock_input, conversation_handler):
        """Test action confirmation - yes."""
        result = conversation_handler.confirm_action("Continue with action?")
        assert result is True
    
    @patch('builtins.input', side_effect=['n'])
    def test_confirm_action_no(self, mock_input, conversation_handler):
        """Test action confirmation - no."""
        result = conversation_handler.confirm_action("Continue with action?")
        assert result is False
    
    @patch('builtins.input', side_effect=[''])
    def test_confirm_action_default_yes(self, mock_input, conversation_handler):
        """Test action confirmation - default is yes."""
        result = conversation_handler.confirm_action("Continue with action?")
        assert result is True
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_display_progress(self, mock_stdout, conversation_handler):
        """Test progress display."""
        conversation_handler.display_progress(2, "Source Research", "Analyzing sources")
        
        output = mock_stdout.getvalue()
        assert "STAGE 2/" in output
        assert "Source Research" in output
        assert "Analyzing sources" in output
        assert "█" in output  # Progress bar
        assert "░" in output  # Progress bar
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_display_error_recoverable(self, mock_stdout, conversation_handler):
        """Test error display for recoverable errors."""
        conversation_handler.display_error("Test error message", is_recoverable=True)
        
        output = mock_stdout.getvalue()
        assert "❌ Test error message" in output
        assert "Attempting to continue" in output
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_display_error_non_recoverable(self, mock_stdout, conversation_handler):
        """Test error display for non-recoverable errors."""
        conversation_handler.display_error("Fatal error", is_recoverable=False)
        
        output = mock_stdout.getvalue()
        assert "❌ Fatal error" in output
        assert "cannot be recovered" in output
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_print_welcome(self, mock_stdout, conversation_handler):
        """Test welcome message printing."""
        conversation_handler._print_welcome()
        
        output = mock_stdout.getvalue()
        assert "Welcome to Deep Research Agent" in output
        assert "informed decisions" in output
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_show_completion_message(self, mock_stdout, conversation_handler):
        """Test completion message display."""
        research_results = {"confidence_score": 0.85}
        
        conversation_handler._show_completion_message(
            "DRA_20250628_120000",
            "/path/to/report.md",
            research_results
        )
        
        output = mock_stdout.getvalue()
        assert "Research Complete" in output
        assert "DRA_20250628_120000" in output
        assert "85.0%" in output  # Confidence as percentage
        assert "/path/to/report.md" in output
    
    def test_ask_personalization_question_with_response(self, conversation_handler):
        """Test asking personalization question with response."""
        with patch('builtins.input', return_value="Test answer"):
            result = conversation_handler._ask_personalization_question("test question")
            assert result == "Test answer"
    
    def test_ask_personalization_question_empty_response(self, conversation_handler):
        """Test asking personalization question with empty response."""
        with patch('builtins.input', return_value=""):
            result = conversation_handler._ask_personalization_question("test question")
            assert result is None
    
    @patch('builtins.input', side_effect=KeyboardInterrupt())
    def test_keyboard_interrupt_handling(self, mock_input, conversation_handler):
        """Test that KeyboardInterrupt is properly propagated."""
        with pytest.raises(KeyboardInterrupt):
            conversation_handler._get_research_query()
    
    @patch('builtins.input', side_effect=EOFError())
    def test_eof_error_handling(self, mock_input, conversation_handler):
        """Test that EOFError is properly propagated."""
        with pytest.raises(EOFError):
            conversation_handler._ask_personalization()
    
    def test_gather_personalization_with_constraints(self, conversation_handler):
        """Test gathering personalization with various constraint types."""
        query = "Best investment strategy"
        
        with patch.object(conversation_handler, '_classify_query') as mock_classify, \
             patch.object(conversation_handler.settings, 'get_category_questions') as mock_questions, \
             patch.object(conversation_handler, '_ask_personalization_question') as mock_ask, \
             patch.object(conversation_handler, '_ask_optional') as mock_optional:
            
            mock_classify.return_value = "finance"
            mock_questions.return_value = ["income", "risk_tolerance"]
            mock_ask.side_effect = ["50000", "moderate"]
            mock_optional.side_effect = ["10000", "6 months", "USA"]
            
            result = conversation_handler._gather_personalization(query)
            
            assert "user_info" in result
            assert "preferences" in result
            assert "constraints" in result
            assert result["user_info"]["income"] == "50000"
            assert result["preferences"]["risk_tolerance"] == "moderate"
            assert result["constraints"]["budget"] == "10000"
            assert result["constraints"]["timeline"] == "6 months"
            assert result["constraints"]["location"] == "USA"
    
    def test_gather_personalization_with_preferences(self, conversation_handler):
        """Test gathering personalization that results in preferences."""
        query = "Best smartphone"
        
        with patch.object(conversation_handler, '_classify_query') as mock_classify, \
             patch.object(conversation_handler.settings, 'get_category_questions') as mock_questions, \
             patch.object(conversation_handler, '_ask_personalization_question') as mock_ask, \
             patch.object(conversation_handler, '_ask_optional') as mock_optional:
            
            mock_classify.return_value = "technology"
            mock_questions.return_value = ["brand_preference", "features"]
            mock_ask.side_effect = ["Apple", "camera quality"]
            mock_optional.side_effect = [None, None, None]  # No constraints
            
            result = conversation_handler._gather_personalization(query)
            
            assert "preferences" in result
            assert result["preferences"]["brand_preference"] == "Apple"
            assert result["preferences"]["features"] == "camera quality"
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_start_interactive_session_foundation_mode(self, mock_stdout, conversation_handler):
        """Test interactive session in foundation mode (no research modules)."""
        with patch.object(conversation_handler, '_get_research_query') as mock_query, \
             patch.object(conversation_handler, '_ask_personalization') as mock_personalize, \
             patch.object(conversation_handler, '_gather_personalization') as mock_gather, \
             patch.object(conversation_handler.session_manager, 'create_session') as mock_create:
            
            mock_query.return_value = "Test query"
            mock_personalize.return_value = False
            mock_gather.return_value = {}
            mock_create.return_value = {"session_id": "DRA_20250628_120000"}
            
            # This should handle the ImportError gracefully
            with patch.dict('sys.modules', {'core.research_engine': None, 'core.report_generator': None}):
                conversation_handler.start_interactive_session()
            
            output = mock_stdout.getvalue()
            assert "Starting Research Session" in output
            assert "Core research modules are being implemented" in output
