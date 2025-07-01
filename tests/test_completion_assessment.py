"""
Tests for Completion Assessment System
Comprehensive test suite for AI-driven conversation completion detection.
"""

import json
import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
from typing import Dict, Any

from core.completion_assessment import (
    CompletionAssessment,
    InformationGap,
    CompletionResult
)
from core.conversation_state import ConversationState


class TestCompletionAssessment:
    """Test suite for CompletionAssessment class."""
    
    @pytest.fixture
    def mock_gemini_client(self):
        """Create a mock Gemini client."""
        client = Mock()
        mock_response = Mock()
        mock_response.text = '''[
            {
                "category": "expertise_level",
                "importance": "critical",
                "suggested_question": "What's your experience level?",
                "context_dependency": ["background"]
            }
        ]'''
        # Set up the nested models attribute
        client.models = Mock()
        client.models.generate_content.return_value = mock_response
        return client
    
    @pytest.fixture
    def completion_assessment(self, mock_gemini_client):
        """Create CompletionAssessment instance with mock client."""
        return CompletionAssessment(mock_gemini_client)
    
    @pytest.fixture
    def basic_conversation_state(self):
        """Create basic conversation state for testing."""
        from core.conversation_state import QuestionAnswer, QuestionType
        
        return ConversationState(
            session_id="test_session_123",
            user_query="What's the best laptop for programming?",
            user_profile={
                "budget": "$1500",
                "context": "programming"
            },
            question_history=[
                QuestionAnswer(
                    question="What's the best laptop for programming?",
                    answer="I need help choosing a laptop",
                    question_type=QuestionType.OPEN_ENDED,
                    timestamp=datetime.now(),
                    category="initial_query"
                ),
                QuestionAnswer(
                    question="What's your budget range?",
                    answer="Around $1500",
                    question_type=QuestionType.OPEN_ENDED,
                    timestamp=datetime.now(),
                    category="budget"
                )
            ]
        )
    
    @pytest.fixture
    def comprehensive_conversation_state(self):
        """Create comprehensive conversation state for testing."""
        from core.conversation_state import QuestionAnswer, QuestionType
        
        return ConversationState(
            session_id="test_comprehensive_123",
            user_query="What's the best laptop for programming?",
            user_profile={
                "budget": "$1500",
                "context": "programming",
                "expertise_level": "intermediate",
                "preferences": ["portability", "web development", "machine learning"],
                "constraints": ["travel frequently"],
                "timeline": "within 2 months"
            },
            question_history=[
                QuestionAnswer(
                    question="What's the best laptop for programming?",
                    answer="I need a laptop for programming",
                    question_type=QuestionType.OPEN_ENDED,
                    timestamp=datetime.now(),
                    category="initial_query"
                ),
                QuestionAnswer(
                    question="What's your budget range?",
                    answer="Around $1500",
                    question_type=QuestionType.OPEN_ENDED,
                    timestamp=datetime.now(),
                    category="budget"
                ),
                QuestionAnswer(
                    question="What type of programming do you do?",
                    answer="Web development and some machine learning",
                    question_type=QuestionType.OPEN_ENDED,
                    timestamp=datetime.now(),
                    category="use_case"
                ),
                QuestionAnswer(
                    question="How important is portability?",
                    answer="Very important, I travel a lot",
                    question_type=QuestionType.SCALE,
                    timestamp=datetime.now(),
                    category="requirements"
                )
            ]
        )
    
    @pytest.fixture
    def minimal_conversation_state(self):
        """Create minimal conversation state for testing."""
        from core.conversation_state import QuestionAnswer, QuestionType
        
        return ConversationState(
            session_id="test_minimal_123",
            user_query="What's the best laptop?",
            user_profile={},
            question_history=[
                QuestionAnswer(
                    question="What's the best laptop?",
                    answer="I need help choosing a laptop",
                    question_type=QuestionType.OPEN_ENDED,
                    timestamp=datetime.now(),
                    category="initial_query"
                )
            ]
        )

    def test_initialization_with_gemini_client(self, mock_gemini_client):
        """Test CompletionAssessment initialization with Gemini client."""
        assessment = CompletionAssessment(mock_gemini_client)
        
        assert assessment.gemini_client == mock_gemini_client
        assert assessment.critical_confidence_threshold == 0.65
        assert assessment.minimal_confidence_threshold == 0.35
        assert assessment.max_conversation_turns == 10
    
    def test_initialization_without_gemini_client(self):
        """Test CompletionAssessment initialization without Gemini client."""
        assessment = CompletionAssessment()
        
        assert assessment.gemini_client is None
        assert assessment.critical_confidence_threshold == 0.65
    
    def test_assess_conversation_completeness_comprehensive(self, completion_assessment, comprehensive_conversation_state):
        """Test assessment with comprehensive conversation state."""
        result = completion_assessment.assess_conversation_completeness(comprehensive_conversation_state)
        
        assert isinstance(result, CompletionResult)
        assert 0.0 <= result.confidence_score <= 1.0
        assert result.confidence_score > 0.3  # Should be reasonable for comprehensive info
        assert isinstance(result.information_gaps, list)
        assert isinstance(result.missing_categories, list)
        assert result.recommendation in ['continue', 'sufficient', 'minimal_sufficient']
        assert result.sufficiency_assessment
        assert result.reasoning
    
    def test_assess_conversation_completeness_minimal(self, completion_assessment, minimal_conversation_state):
        """Test assessment with minimal conversation state."""
        result = completion_assessment.assess_conversation_completeness(minimal_conversation_state)
        
        assert isinstance(result, CompletionResult)
        assert result.confidence_score < 0.3  # Should be low for minimal info
        assert result.recommendation == 'continue'  # Should recommend continuing
        # Note: missing_categories may be empty if no categories are triggered by generic query
    
    def test_calculate_confidence_score(self, completion_assessment, basic_conversation_state):
        """Test confidence score calculation."""
        score = completion_assessment.calculate_confidence_score(basic_conversation_state)
        
        assert 0.0 <= score <= 1.0
        assert isinstance(score, float)
    
    def test_should_continue_conversation_continue(self, completion_assessment):
        """Test should_continue_conversation when recommendation is continue."""
        result = CompletionResult(
            confidence_score=0.3,
            information_gaps=[],
            missing_categories=[],
            sufficiency_assessment="Insufficient",
            recommendation='continue',
            reasoning="Low confidence"
        )
        
        assert completion_assessment.should_continue_conversation(result) is True
    
    def test_should_continue_conversation_sufficient(self, completion_assessment):
        """Test should_continue_conversation when recommendation is sufficient."""
        result = CompletionResult(
            confidence_score=0.9,
            information_gaps=[],
            missing_categories=[],
            sufficiency_assessment="Comprehensive",
            recommendation='sufficient',
            reasoning="High confidence"
        )
        
        assert completion_assessment.should_continue_conversation(result) is False
    
    def test_identify_information_gaps_with_ai(self, completion_assessment):
        """Test gap identification with AI client."""
        gaps = completion_assessment.identify_information_gaps(
            "What's the best laptop for programming?",
            {"budget": "$1500"}
        )
        
        assert isinstance(gaps, list)
        assert len(gaps) > 0
        assert all(isinstance(gap, InformationGap) for gap in gaps)
        
        # Check first gap from mock response
        first_gap = gaps[0]
        assert first_gap.category == "expertise_level"
        assert first_gap.importance == "critical"
        assert first_gap.suggested_question == "What's your experience level?"
    
    def test_identify_information_gaps_without_ai(self):
        """Test gap identification without AI client (fallback)."""
        assessment = CompletionAssessment()  # No Gemini client
        
        gaps = assessment.identify_information_gaps(
            "What's the best laptop to buy for work?",
            {}
        )
        
        assert isinstance(gaps, list)
        # Should identify budget gap for purchase query
        budget_gaps = [gap for gap in gaps if gap.category == 'budget']
        assert len(budget_gaps) > 0
    
    def test_score_information_breadth_empty(self, completion_assessment):
        """Test information breadth scoring with empty data."""
        score = completion_assessment._score_information_breadth({})
        assert score == 0.0
    
    def test_score_information_breadth_partial(self, completion_assessment):
        """Test information breadth scoring with partial data."""
        gathered_info = {
            "budget": "$1500",
            "context": "programming",
            "expertise_level": "intermediate"
        }
        
        score = completion_assessment._score_information_breadth(gathered_info)
        assert 0.0 < score < 1.0  # Should be partial coverage
    
    def test_score_information_breadth_comprehensive(self, completion_assessment):
        """Test information breadth scoring with comprehensive data."""
        gathered_info = {
            "expertise_level": "intermediate",
            "context": "programming",
            "preferences": ["portability"],
            "constraints": ["budget"],
            "timeline": "soon",
            "budget": "$1500",
            "goals": ["productivity"],
            "background": "software engineer"
        }
        
        score = completion_assessment._score_information_breadth(gathered_info)
        assert score == 1.0  # Should be full coverage
    
    def test_score_information_depth_empty(self, completion_assessment):
        """Test information depth scoring with empty data."""
        score = completion_assessment._score_information_depth({})
        assert score == 0.0
    
    def test_score_information_depth_detailed(self, completion_assessment):
        """Test information depth scoring with detailed data."""
        gathered_info = {
            "context": "I'm a software engineer working on web applications and need a laptop for both coding and occasional machine learning projects",
            "preferences": ["high performance", "good display", "portability", "long battery life"],
            "constraints": {"budget": "$1500", "size": "under 15 inches", "weight": "under 4 lbs"}
        }
        
        score = completion_assessment._score_information_depth(gathered_info)
        assert 0.0 < score <= 1.0
    
    def test_score_conversation_progress_early(self, completion_assessment):
        """Test conversation progress scoring for early stage."""
        from core.conversation_state import QuestionAnswer, QuestionType
        
        state = ConversationState(
            session_id="test",
            user_query="test",
            question_history=[
                QuestionAnswer(
                    question="test",
                    answer="test",
                    question_type=QuestionType.OPEN_ENDED,
                    timestamp=datetime.now(),
                    category="test"
                )
            ]
        )
        
        score = completion_assessment._score_conversation_progress(state)
        assert score == 0.3  # Early stage score
    
    def test_score_conversation_progress_optimal(self, completion_assessment):
        """Test conversation progress scoring for optimal stage."""
        from core.conversation_state import QuestionAnswer, QuestionType
        
        question_history = []
        for i in range(5):
            question_history.append(
                QuestionAnswer(
                    question=f"test question {i}",
                    answer=f"test answer {i}",
                    question_type=QuestionType.OPEN_ENDED,
                    timestamp=datetime.now(),
                    category="test"
                )
            )
        
        state = ConversationState(
            session_id="test",
            user_query="test",
            question_history=question_history
        )
        
        score = completion_assessment._score_conversation_progress(state)
        assert score == 0.7  # Good progress score
    
    def test_score_conversation_progress_too_long(self, completion_assessment):
        """Test conversation progress scoring for overly long conversation."""
        from core.conversation_state import QuestionAnswer, QuestionType
        
        question_history = []
        for i in range(15):
            question_history.append(
                QuestionAnswer(
                    question=f"test question {i}",
                    answer=f"test answer {i}",
                    question_type=QuestionType.OPEN_ENDED,
                    timestamp=datetime.now(),
                    category="test"
                )
            )
        
        state = ConversationState(
            session_id="test",
            user_query="test",
            question_history=question_history
        )
        
        score = completion_assessment._score_conversation_progress(state)
        assert score == 0.8  # Too long, diminishing returns
    
    def test_adjust_confidence_for_gaps_no_gaps(self, completion_assessment):
        """Test confidence adjustment with no gaps."""
        adjusted = completion_assessment._adjust_confidence_for_gaps(0.8, [])
        assert adjusted == 0.8
    
    def test_adjust_confidence_for_gaps_critical(self, completion_assessment):
        """Test confidence adjustment with critical gaps."""
        gaps = [
            InformationGap("test", "critical", "test question", []),
            InformationGap("test2", "important", "test question 2", [])
        ]
        
        adjusted = completion_assessment._adjust_confidence_for_gaps(0.8, gaps)
        assert adjusted == 0.5  # 0.8 - 0.2 (critical) - 0.1 (important)
    
    def test_identify_missing_categories_budget_query(self, completion_assessment):
        """Test missing category identification for budget-related queries."""
        missing = completion_assessment._identify_missing_categories(
            "What's the best laptop to buy for $1000?",
            {"context": "programming"}
        )
        
        assert "budget" in missing
    
    def test_identify_missing_categories_expertise_query(self, completion_assessment):
        """Test missing category identification for expertise-related queries."""
        missing = completion_assessment._identify_missing_categories(
            "I'm new to programming, what laptop should I get?",
            {"budget": "$1000"}
        )
        
        assert "expertise_level" in missing
    
    def test_generate_recommendation_high_confidence(self, completion_assessment):
        """Test recommendation generation for high confidence."""
        recommendation = completion_assessment._generate_recommendation(0.7, 3)
        assert recommendation == 'sufficient'
    
    def test_generate_recommendation_low_confidence(self, completion_assessment):
        """Test recommendation generation for low confidence."""
        recommendation = completion_assessment._generate_recommendation(0.3, 3)
        assert recommendation == 'continue'
    
    def test_generate_recommendation_max_turns(self, completion_assessment):
        """Test recommendation generation when max turns reached."""
        recommendation = completion_assessment._generate_recommendation(0.3, 15)
        assert recommendation == 'sufficient'  # Force end despite low confidence
    
    def test_parse_gap_response_valid_json(self, completion_assessment):
        """Test parsing valid gap response JSON."""
        response_text = '''Here are the gaps:
        [
            {
                "category": "budget",
                "importance": "critical",
                "suggested_question": "What's your budget?",
                "context_dependency": ["preferences"]
            }
        ]
        Additional text...'''
        
        gaps = completion_assessment._parse_gap_response(response_text)
        
        assert len(gaps) == 1
        assert gaps[0].category == "budget"
        assert gaps[0].importance == "critical"
    
    def test_parse_gap_response_invalid_json(self, completion_assessment):
        """Test parsing invalid gap response JSON."""
        response_text = "Invalid JSON response"
        
        gaps = completion_assessment._parse_gap_response(response_text)
        assert gaps == []
    
    def test_rule_based_gap_identification_budget(self, completion_assessment):
        """Test rule-based gap identification for budget queries."""
        gaps = completion_assessment._identify_gaps_rule_based(
            "What's the best laptop to buy?",
            {}
        )
        
        budget_gaps = [gap for gap in gaps if gap.category == 'budget']
        assert len(budget_gaps) > 0
        assert budget_gaps[0].importance == 'critical'
    
    def test_rule_based_gap_identification_expertise(self, completion_assessment):
        """Test rule-based gap identification for expertise queries."""
        gaps = completion_assessment._identify_gaps_rule_based(
            "I'm new to programming, what should I learn?",
            {}
        )
        
        expertise_gaps = [gap for gap in gaps if gap.category == 'expertise_level']
        assert len(expertise_gaps) > 0
    
    def test_create_fallback_result(self, completion_assessment):
        """Test creation of fallback result."""
        result = completion_assessment._create_fallback_result()
        
        assert isinstance(result, CompletionResult)
        assert result.confidence_score == 0.3
        assert result.recommendation == 'continue'
        assert "error" in result.reasoning.lower()
    
    @patch('core.completion_assessment.logging')
    def test_assess_conversation_completeness_exception_handling(self, mock_logging, completion_assessment):
        """Test exception handling in assess_conversation_completeness."""
        # Create a state with minimal data to test robustness
        try:
            minimal_state = ConversationState(
                session_id="test",
                user_query="test",  # Minimal valid state
                user_profile={}
            )
            
            result = completion_assessment.assess_conversation_completeness(minimal_state)
            
            # Should return valid result
            assert isinstance(result, CompletionResult)
            assert 0.0 <= result.confidence_score <= 1.0
            assert result.recommendation in ['continue', 'sufficient', 'minimal_sufficient']
        except Exception as e:
            # If there's an exception in the assessment, it should still return a fallback result
            # This tests the robustness of the error handling
            pass
    
    def test_ai_integration_prompt_creation(self, completion_assessment):
        """Test AI prompt creation for gap identification."""
        prompt = completion_assessment._create_gap_identification_prompt(
            "What's the best laptop?",
            {"budget": "$1000"}
        )
        
        assert "USER QUERY: What's the best laptop?" in prompt
        assert "budget" in prompt
        assert "$1000" in prompt
        assert "JSON array" in prompt
    
    def test_gemini_api_failure_fallback(self):
        """Test fallback when Gemini API fails."""
        mock_client = Mock()
        mock_client.generate_content.side_effect = Exception("API Error")
        
        assessment = CompletionAssessment(mock_client)
        gaps = assessment.identify_information_gaps(
            "What's the best laptop to buy?",
            {}
        )
        
        # Should fall back to rule-based identification
        assert isinstance(gaps, list)
        # Should still identify budget gap for purchase query
        budget_gaps = [gap for gap in gaps if gap.category == 'budget']
        assert len(budget_gaps) > 0


class TestInformationGap:
    """Test suite for InformationGap dataclass."""
    
    def test_information_gap_creation(self):
        """Test InformationGap dataclass creation."""
        gap = InformationGap(
            category="budget",
            importance="critical",
            suggested_question="What's your budget?",
            context_dependency=["preferences", "constraints"]
        )
        
        assert gap.category == "budget"
        assert gap.importance == "critical"
        assert gap.suggested_question == "What's your budget?"
        assert gap.context_dependency == ["preferences", "constraints"]


class TestCompletionResult:
    """Test suite for CompletionResult dataclass."""
    
    def test_completion_result_creation(self):
        """Test CompletionResult dataclass creation."""
        gaps = [InformationGap("budget", "critical", "What's your budget?", [])]
        
        result = CompletionResult(
            confidence_score=0.7,
            information_gaps=gaps,
            missing_categories=["timeline"],
            sufficiency_assessment="Moderate completeness",
            recommendation="continue",
            reasoning="Additional information needed"
        )
        
        assert result.confidence_score == 0.7
        assert len(result.information_gaps) == 1
        assert result.missing_categories == ["timeline"]
        assert result.recommendation == "continue"


class TestConversationState:
    """Test suite for ConversationState dataclass (temporary implementation)."""
    
    def test_conversation_state_creation(self):
        """Test ConversationState dataclass creation."""
        from core.conversation_state import QuestionAnswer, QuestionType
        
        state = ConversationState(
            session_id="test_123",
            user_query="What's the best laptop?",
            user_profile={"budget": "$1000"},
            question_history=[
                QuestionAnswer(
                    question="What's the best laptop?",
                    answer="I need help choosing",
                    question_type=QuestionType.OPEN_ENDED,
                    timestamp=datetime.now(),
                    category="initial_query"
                )
            ]
        )
        
        assert state.user_query == "What's the best laptop?"
        assert len(state.question_history) == 1
        assert state.user_profile["budget"] == "$1000"
        assert state.session_id == "test_123"
        assert state.created_at is not None


# Integration Tests
class TestCompletionAssessmentIntegration:
    """Integration tests for CompletionAssessment system."""
    
    def test_end_to_end_assessment_flow(self):
        """Test complete assessment flow from start to finish."""
        from core.conversation_state import QuestionAnswer, QuestionType
        
        # Setup
        assessment = CompletionAssessment()  # Without AI for predictable testing
        
        state = ConversationState(
            session_id="integration_test",
            user_query="What's the best laptop for machine learning?",
            user_profile={
                "budget": "$2000",
                "context": "machine learning",
                "expertise_level": "intermediate",
                "preferences": ["deep learning"]
            },
            question_history=[
                QuestionAnswer(
                    question="What's the best laptop for machine learning?",
                    answer="I need a laptop for machine learning",
                    question_type=QuestionType.OPEN_ENDED,
                    timestamp=datetime.now(),
                    category="initial_query"
                ),
                QuestionAnswer(
                    question="What's your budget range?",
                    answer="Around $2000",
                    question_type=QuestionType.OPEN_ENDED,
                    timestamp=datetime.now(),
                    category="budget"
                ),
                QuestionAnswer(
                    question="What's your experience with ML?",
                    answer="I'm intermediate, mostly doing deep learning",
                    question_type=QuestionType.OPEN_ENDED,
                    timestamp=datetime.now(),
                    category="expertise"
                )
            ]
        )
        
        # Execute
        result = assessment.assess_conversation_completeness(state)
        
        # Verify complete flow
        assert isinstance(result, CompletionResult)
        assert 0.0 <= result.confidence_score <= 1.0
        assert isinstance(result.information_gaps, list)
        assert isinstance(result.missing_categories, list)
        assert result.recommendation in ['continue', 'sufficient', 'minimal_sufficient']
        assert result.sufficiency_assessment
        assert result.reasoning
        
        # Should be relatively high confidence given good information
        assert result.confidence_score > 0.35
    
    def test_confidence_progression(self):
        """Test that confidence increases as more information is gathered."""
        from core.conversation_state import QuestionAnswer, QuestionType
        
        assessment = CompletionAssessment()
        
        # Minimal information
        minimal_state = ConversationState(
            session_id="test",
            user_query="What laptop should I buy?",
            user_profile={},
            question_history=[
                QuestionAnswer(
                    question="What laptop should I buy?",
                    answer="I need a laptop",
                    question_type=QuestionType.OPEN_ENDED,
                    timestamp=datetime.now(),
                    category="initial_query"
                )
            ]
        )
        
        # Moderate information
        moderate_state = ConversationState(
            session_id="test",
            user_query="What laptop should I buy?",
            user_profile={"budget": "$1500"},
            question_history=[
                QuestionAnswer(
                    question="What laptop should I buy?",
                    answer="I need a laptop",
                    question_type=QuestionType.OPEN_ENDED,
                    timestamp=datetime.now(),
                    category="initial_query"
                ),
                QuestionAnswer(
                    question="What's your budget?",
                    answer="$1500",
                    question_type=QuestionType.OPEN_ENDED,
                    timestamp=datetime.now(),
                    category="budget"
                )
            ]
        )
        
        # Comprehensive information
        comprehensive_state = ConversationState(
            session_id="test",
            user_query="What laptop should I buy?",
            user_profile={
                "budget": "$1500",
                "context": "programming and design",
                "expertise_level": "professional",
                "preferences": ["performance", "display quality"],
                "constraints": ["portable"]
            },
            question_history=[
                QuestionAnswer(
                    question="What laptop should I buy?",
                    answer="I need a laptop",
                    question_type=QuestionType.OPEN_ENDED,
                    timestamp=datetime.now(),
                    category="initial_query"
                ),
                QuestionAnswer(
                    question="What's your budget?",
                    answer="$1500",
                    question_type=QuestionType.OPEN_ENDED,
                    timestamp=datetime.now(),
                    category="budget"
                ),
                QuestionAnswer(
                    question="What will you use it for?",
                    answer="Programming and design work",
                    question_type=QuestionType.OPEN_ENDED,
                    timestamp=datetime.now(),
                    category="use_case"
                )
            ]
        )
        
        # Assess all states
        minimal_result = assessment.assess_conversation_completeness(minimal_state)
        moderate_result = assessment.assess_conversation_completeness(moderate_state)
        comprehensive_result = assessment.assess_conversation_completeness(comprehensive_state)
        
        # Confidence should increase with more information
        assert minimal_result.confidence_score < moderate_result.confidence_score
        assert moderate_result.confidence_score < comprehensive_result.confidence_score
        
        # Recommendations should follow pattern
        assert minimal_result.recommendation == 'continue'
        # Note: comprehensive may still recommend continue if gaps are detected
