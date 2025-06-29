"""
Tests for Conversation State Data Models
Comprehensive test suite for conversation tracking data structures.
"""

import json
import pytest
from datetime import datetime, timedelta
from typing import Dict, Any

from core.conversation_state import (
    ConversationState,
    QuestionAnswer,
    EmotionalIndicators,
    ContextUnderstanding,
    ConversationStateManager,
    ConversationMode,
    QuestionType
)


class TestQuestionAnswer:
    """Test suite for QuestionAnswer dataclass."""
    
    def test_question_answer_creation(self):
        """Test basic QuestionAnswer creation."""
        timestamp = datetime.now()
        qa = QuestionAnswer(
            question="What's your budget?",
            answer="Around $1500",
            question_type=QuestionType.OPEN_ENDED,
            timestamp=timestamp,
            category="budget",
            confidence=0.8,
            importance=0.9
        )
        
        assert qa.question == "What's your budget?"
        assert qa.answer == "Around $1500"
        assert qa.question_type == QuestionType.OPEN_ENDED
        assert qa.timestamp == timestamp
        assert qa.category == "budget"
        assert qa.confidence == 0.8
        assert qa.importance == 0.9
        assert qa.follow_up_needed is False
        assert qa.context == {}
    
    def test_question_answer_to_dict(self):
        """Test QuestionAnswer serialization to dict."""
        timestamp = datetime.now()
        qa = QuestionAnswer(
            question="Test question",
            answer="Test answer",
            question_type=QuestionType.MULTIPLE_CHOICE,
            timestamp=timestamp,
            category="test",
            context={"key": "value"}
        )
        
        qa_dict = qa.to_dict()
        
        assert qa_dict['question'] == "Test question"
        assert qa_dict['answer'] == "Test answer"
        assert qa_dict['question_type'] == "multiple_choice"
        assert qa_dict['timestamp'] == timestamp.isoformat()
        assert qa_dict['category'] == "test"
        assert qa_dict['context'] == {"key": "value"}
    
    def test_question_answer_from_dict(self):
        """Test QuestionAnswer deserialization from dict."""
        timestamp = datetime.now()
        data = {
            'question': "Test question",
            'answer': "Test answer",
            'question_type': "scale",
            'timestamp': timestamp.isoformat(),
            'category': "test",
            'confidence': 0.7,
            'importance': 0.6,
            'follow_up_needed': True,
            'context': {"key": "value"}
        }
        
        qa = QuestionAnswer.from_dict(data)
        
        assert qa.question == "Test question"
        assert qa.answer == "Test answer"
        assert qa.question_type == QuestionType.SCALE
        assert qa.timestamp == timestamp
        assert qa.category == "test"
        assert qa.confidence == 0.7
        assert qa.importance == 0.6
        assert qa.follow_up_needed is True
        assert qa.context == {"key": "value"}
    
    def test_question_answer_round_trip_serialization(self):
        """Test round-trip serialization preserves data."""
        original = QuestionAnswer(
            question="Original question",
            answer="Original answer",
            question_type=QuestionType.BOOLEAN,
            timestamp=datetime.now(),
            category="original",
            confidence=0.85,
            importance=0.75,
            follow_up_needed=True,
            context={"complex": {"nested": "data"}}
        )
        
        # Serialize and deserialize
        qa_dict = original.to_dict()
        restored = QuestionAnswer.from_dict(qa_dict)
        
        assert original.question == restored.question
        assert original.answer == restored.answer
        assert original.question_type == restored.question_type
        assert original.category == restored.category
        assert original.confidence == restored.confidence
        assert original.importance == restored.importance
        assert original.follow_up_needed == restored.follow_up_needed
        assert original.context == restored.context


class TestEmotionalIndicators:
    """Test suite for EmotionalIndicators dataclass."""
    
    def test_emotional_indicators_defaults(self):
        """Test EmotionalIndicators with default values."""
        indicators = EmotionalIndicators()
        
        assert indicators.urgency_level == 0.0
        assert indicators.anxiety_level == 0.0
        assert indicators.confidence_level == 0.5
        assert indicators.enthusiasm_level == 0.5
        assert indicators.frustration_level == 0.0
        assert indicators.decision_pressure == 0.0
        assert indicators.time_sensitivity == 0.0
        assert indicators.indicators_detected == []
        assert isinstance(indicators.last_updated, datetime)
    
    def test_emotional_indicators_custom_values(self):
        """Test EmotionalIndicators with custom values."""
        timestamp = datetime.now()
        indicators = EmotionalIndicators(
            urgency_level=0.8,
            anxiety_level=0.3,
            confidence_level=0.9,
            enthusiasm_level=0.7,
            indicators_detected=["urgency", "confidence"],
            last_updated=timestamp
        )
        
        assert indicators.urgency_level == 0.8
        assert indicators.anxiety_level == 0.3
        assert indicators.confidence_level == 0.9
        assert indicators.enthusiasm_level == 0.7
        assert indicators.indicators_detected == ["urgency", "confidence"]
        assert indicators.last_updated == timestamp
    
    def test_emotional_indicators_serialization(self):
        """Test EmotionalIndicators serialization round-trip."""
        original = EmotionalIndicators(
            urgency_level=0.6,
            anxiety_level=0.4,
            indicators_detected=["test1", "test2"]
        )
        
        # Serialize and deserialize
        data = original.to_dict()
        restored = EmotionalIndicators.from_dict(data)
        
        assert original.urgency_level == restored.urgency_level
        assert original.anxiety_level == restored.anxiety_level
        assert original.indicators_detected == restored.indicators_detected


class TestContextUnderstanding:
    """Test suite for ContextUnderstanding dataclass."""
    
    def test_context_understanding_defaults(self):
        """Test ContextUnderstanding with default values."""
        context = ContextUnderstanding()
        
        assert context.domain_expertise == {}
        assert context.communication_style == {}
        assert context.decision_making_style == "unknown"
        assert context.information_processing_preference == "unknown"
        assert context.risk_tolerance == 0.5
        assert context.detail_preference == 0.5
        assert context.stakeholders == []
        assert context.external_constraints == {}
    
    def test_context_understanding_custom_values(self):
        """Test ContextUnderstanding with custom values."""
        context = ContextUnderstanding(
            domain_expertise={"programming": 0.8, "design": 0.6},
            communication_style={"formal": 0.3, "casual": 0.7},
            decision_making_style="analytical",
            risk_tolerance=0.3,
            stakeholders=["manager", "team"]
        )
        
        assert context.domain_expertise == {"programming": 0.8, "design": 0.6}
        assert context.communication_style == {"formal": 0.3, "casual": 0.7}
        assert context.decision_making_style == "analytical"
        assert context.risk_tolerance == 0.3
        assert context.stakeholders == ["manager", "team"]
    
    def test_context_understanding_serialization(self):
        """Test ContextUnderstanding serialization round-trip."""
        original = ContextUnderstanding(
            domain_expertise={"test": 0.5},
            decision_making_style="collaborative",
            stakeholders=["person1", "person2"]
        )
        
        # Serialize and deserialize
        data = original.to_dict()
        restored = ContextUnderstanding.from_dict(data)
        
        assert original.domain_expertise == restored.domain_expertise
        assert original.decision_making_style == restored.decision_making_style
        assert original.stakeholders == restored.stakeholders


class TestConversationState:
    """Test suite for ConversationState dataclass."""
    
    @pytest.fixture
    def basic_conversation_state(self):
        """Create a basic conversation state for testing."""
        return ConversationState(
            session_id="test_session_123",
            user_query="What's the best laptop for programming?"
        )
    
    @pytest.fixture
    def comprehensive_conversation_state(self):
        """Create a comprehensive conversation state for testing."""
        timestamp = datetime.now()
        state = ConversationState(
            session_id="comprehensive_session",
            user_query="I need help choosing a laptop for machine learning work",
            conversation_mode=ConversationMode.DEEP
        )
        
        # Add some question history
        state.add_question_answer(
            question="What's your budget range?",
            answer="Between $2000-3000",
            category="budget",
            question_type=QuestionType.OPEN_ENDED,
            confidence=0.8
        )
        
        state.add_question_answer(
            question="What's your experience level with ML?",
            answer="Intermediate - I've worked on several projects",
            category="expertise_level",
            question_type=QuestionType.OPEN_ENDED,
            confidence=0.9
        )
        
        # Set some priority factors
        state.set_priority_factor("budget", 0.9)
        state.set_priority_factor("performance", 0.8)
        
        # Add information gaps
        state.add_information_gap("portability_requirements")
        state.add_information_gap("software_preferences")
        
        return state
    
    def test_conversation_state_creation(self, basic_conversation_state):
        """Test basic ConversationState creation."""
        state = basic_conversation_state
        
        assert state.session_id == "test_session_123"
        assert state.user_query == "What's the best laptop for programming?"
        assert isinstance(state.created_at, datetime)
        assert isinstance(state.last_updated, datetime)
        assert state.conversation_mode == ConversationMode.STANDARD
        assert state.completion_confidence == 0.0
        assert state.user_profile == {}
        assert state.information_gaps == []
        assert state.question_history == []
    
    def test_conversation_state_validation(self):
        """Test ConversationState validation."""
        # Test missing session_id
        with pytest.raises(ValueError, match="session_id is required"):
            ConversationState(session_id="", user_query="test")
        
        # Test missing user_query
        with pytest.raises(ValueError, match="user_query is required"):
            ConversationState(session_id="test", user_query="")
        
        # Test invalid confidence score
        state = ConversationState(session_id="test", user_query="test")
        with pytest.raises(ValueError, match="Confidence score"):
            state.confidence_scores["test"] = 1.5
            state.validate_state()
        
        # Test invalid priority factor (create new state to clear the confidence error)
        state2 = ConversationState(session_id="test2", user_query="test2")
        with pytest.raises(ValueError, match="Priority factor"):
            state2.priority_factors["test"] = -0.1
            state2.validate_state()
    
    def test_add_question_answer(self, basic_conversation_state):
        """Test adding question-answer pairs."""
        state = basic_conversation_state
        original_time = state.last_updated
        
        state.add_question_answer(
            question="What's your experience level?",
            answer="Intermediate",
            category="expertise_level",
            confidence=0.7
        )
        
        assert len(state.question_history) == 1
        qa = state.question_history[0]
        assert qa.question == "What's your experience level?"
        assert qa.answer == "Intermediate"
        assert qa.category == "expertise_level"
        assert qa.confidence == 0.7
        
        # Check user profile was updated
        assert "expertise_level" in state.user_profile
        assert state.confidence_scores["expertise_level"] == 0.7
        
        # Check timestamp was updated
        assert state.last_updated > original_time
    
    def test_update_user_profile(self, basic_conversation_state):
        """Test updating user profile."""
        state = basic_conversation_state
        
        state.update_user_profile("budget", "$2000", confidence=0.8)
        
        assert state.user_profile["budget"] == "$2000"
        assert state.confidence_scores["budget"] == 0.8
    
    def test_priority_factors(self, basic_conversation_state):
        """Test priority factor management."""
        state = basic_conversation_state
        
        state.set_priority_factor("budget", 0.9)
        state.set_priority_factor("performance", 0.7)
        
        assert state.priority_factors["budget"] == 0.9
        assert state.priority_factors["performance"] == 0.7
        
        # Test invalid priority
        with pytest.raises(ValueError):
            state.set_priority_factor("invalid", 1.5)
    
    def test_information_gaps(self, basic_conversation_state):
        """Test information gap management."""
        state = basic_conversation_state
        
        # Add gaps
        state.add_information_gap("timeline")
        state.add_information_gap("constraints")
        
        assert "timeline" in state.information_gaps
        assert "constraints" in state.information_gaps
        assert len(state.information_gaps) == 2
        
        # Remove gap
        state.remove_information_gap("timeline")
        assert "timeline" not in state.information_gaps
        assert len(state.information_gaps) == 1
        
        # Adding duplicate gap should not increase count
        state.add_information_gap("constraints")
        assert len(state.information_gaps) == 1
    
    def test_confidence_calculations(self, comprehensive_conversation_state):
        """Test confidence calculation methods."""
        state = comprehensive_conversation_state
        
        # Test category confidence
        budget_confidence = state.get_category_confidence("budget")
        assert budget_confidence == 0.8
        
        # Test non-existent category
        missing_confidence = state.get_category_confidence("nonexistent")
        assert missing_confidence == 0.0
        
        # Test overall confidence with priority weighting
        overall_confidence = state.get_overall_confidence()
        assert 0.0 <= overall_confidence <= 1.0
        assert overall_confidence > 0  # Should be positive with data
    
    def test_conversation_mode_update(self, basic_conversation_state):
        """Test conversation mode updates."""
        state = basic_conversation_state
        
        # Test enum update
        state.update_conversation_mode(ConversationMode.DEEP)
        assert state.conversation_mode == ConversationMode.DEEP
        
        # Test string update
        state.update_conversation_mode("iterative")
        assert state.conversation_mode == ConversationMode.ITERATIVE
        
        # Test invalid mode
        with pytest.raises(ValueError):
            state.update_conversation_mode("invalid_mode")
    
    def test_conversation_summary(self, comprehensive_conversation_state):
        """Test conversation summary generation."""
        state = comprehensive_conversation_state
        
        summary = state.get_conversation_summary()
        
        assert "machine learning work" in summary
        assert "budget" in summary.lower() or "Budget" in summary
        assert "expertise" in summary.lower() or "Expertise" in summary
    
    def test_serialization_to_dict(self, comprehensive_conversation_state):
        """Test serialization to dictionary."""
        state = comprehensive_conversation_state
        
        state_dict = state.to_dict()
        
        assert state_dict['session_id'] == state.session_id
        assert state_dict['user_query'] == state.user_query
        assert state_dict['conversation_mode'] == state.conversation_mode.value
        assert len(state_dict['question_history']) == len(state.question_history)
        assert 'emotional_indicators' in state_dict
        assert 'context_understanding' in state_dict
    
    def test_serialization_from_dict(self, comprehensive_conversation_state):
        """Test deserialization from dictionary."""
        original_state = comprehensive_conversation_state
        
        # Serialize to dict and back
        state_dict = original_state.to_dict()
        restored_state = ConversationState.from_dict(state_dict)
        
        assert restored_state.session_id == original_state.session_id
        assert restored_state.user_query == original_state.user_query
        assert restored_state.conversation_mode == original_state.conversation_mode
        assert len(restored_state.question_history) == len(original_state.question_history)
        assert restored_state.priority_factors == original_state.priority_factors
        assert restored_state.information_gaps == original_state.information_gaps
    
    def test_json_serialization(self, comprehensive_conversation_state):
        """Test JSON serialization round-trip."""
        original_state = comprehensive_conversation_state
        
        # Serialize to JSON and back
        json_str = original_state.to_json()
        restored_state = ConversationState.from_json(json_str)
        
        assert restored_state.session_id == original_state.session_id
        assert restored_state.user_query == original_state.user_query
        assert len(restored_state.question_history) == len(original_state.question_history)
        
        # Ensure JSON is valid
        json_data = json.loads(json_str)
        assert isinstance(json_data, dict)
        assert 'session_id' in json_data


class TestConversationStateManager:
    """Test suite for ConversationStateManager."""
    
    @pytest.fixture
    def manager(self):
        """Create a ConversationStateManager for testing."""
        return ConversationStateManager()
    
    def test_create_new_state(self, manager):
        """Test creating new conversation state."""
        state = manager.create_new_state(
            session_id="new_session",
            user_query="Test query",
            conversation_mode=ConversationMode.QUICK
        )
        
        assert state.session_id == "new_session"
        assert state.user_query == "Test query"
        assert state.conversation_mode == ConversationMode.QUICK
        assert isinstance(state.created_at, datetime)
    
    def test_create_new_state_validation(self, manager):
        """Test validation in new state creation."""
        # Test empty session_id
        with pytest.raises(ValueError, match="session_id cannot be empty"):
            manager.create_new_state("", "test query")
        
        # Test empty user_query
        with pytest.raises(ValueError, match="user_query cannot be empty"):
            manager.create_new_state("test_session", "")
        
        # Test whitespace-only user_query
        with pytest.raises(ValueError, match="user_query cannot be empty"):
            manager.create_new_state("test_session", "   ")
    
    def test_validate_serialization(self, manager):
        """Test serialization validation."""
        state = manager.create_new_state("test_session", "test query")
        
        # Add some data to make it more complex
        state.add_question_answer("test?", "test answer", "test_category")
        state.set_priority_factor("test", 0.5)
        
        # Test validation
        is_valid = manager.validate_serialization(state)
        assert is_valid is True
    
    def test_calculate_state_completeness(self, manager):
        """Test state completeness calculation."""
        # Create minimal state
        minimal_state = manager.create_new_state("minimal", "test query")
        minimal_completeness = manager.calculate_state_completeness(minimal_state)
        assert 0.0 <= minimal_completeness <= 1.0
        assert minimal_completeness < 0.5  # Should be low for minimal state
        
        # Create more complete state
        complete_state = manager.create_new_state("complete", "test query")
        complete_state.update_user_profile("context", "work", confidence=0.8)
        complete_state.update_user_profile("preferences", "high performance", confidence=0.9)
        complete_state.update_user_profile("constraints", "budget limit", confidence=0.7)
        complete_state.update_user_profile("timeline", "urgent", confidence=0.8)
        complete_state.update_user_profile("expertise_level", "expert", confidence=0.9)
        
        complete_state.add_question_answer("test1?", "answer1", "category1")
        complete_state.add_question_answer("test2?", "answer2", "category2")
        complete_state.add_question_answer("test3?", "answer3", "category3")
        
        complete_completeness = manager.calculate_state_completeness(complete_state)
        assert complete_completeness > minimal_completeness
        assert complete_completeness > 0.5  # Should be higher for complete state
    
    def test_merge_states(self, manager):
        """Test merging conversation states."""
        # Create two states for the same session
        primary = manager.create_new_state("same_session", "primary query")
        secondary = manager.create_new_state("same_session", "secondary query")
        
        # Add different data to each
        primary.add_question_answer("primary question?", "primary answer", "primary_cat")
        primary.update_user_profile("primary_info", "primary_value", confidence=0.6)
        
        secondary.add_question_answer("secondary question?", "secondary answer", "secondary_cat")
        secondary.update_user_profile("secondary_info", "secondary_value", confidence=0.8)
        secondary.update_user_profile("primary_info", "conflicting_value", confidence=0.4)  # Lower confidence
        
        # Merge states
        merged = manager.merge_states(primary, secondary)
        
        # Primary should take precedence for session info
        assert merged.user_query == "primary query"
        
        # Should have questions from both
        assert len(merged.question_history) == 2
        
        # Should have user profile from both
        assert "primary_info" in merged.user_profile
        assert "secondary_info" in merged.user_profile
        
        # Primary should keep higher confidence value
        assert merged.confidence_scores["primary_info"] == 0.6  # Primary's confidence
        assert merged.confidence_scores["secondary_info"] == 0.8  # Secondary's confidence
    
    def test_merge_different_sessions(self, manager):
        """Test that merging different sessions raises error."""
        state1 = manager.create_new_state("session1", "query1")
        state2 = manager.create_new_state("session2", "query2")
        
        with pytest.raises(ValueError, match="Cannot merge states from different sessions"):
            manager.merge_states(state1, state2)


class TestConversationModeEnum:
    """Test suite for ConversationMode enum."""
    
    def test_conversation_mode_values(self):
        """Test ConversationMode enum values."""
        assert ConversationMode.QUICK.value == "quick"
        assert ConversationMode.STANDARD.value == "standard"
        assert ConversationMode.DEEP.value == "deep"
        assert ConversationMode.ITERATIVE.value == "iterative"
    
    def test_conversation_mode_from_string(self):
        """Test creating ConversationMode from string."""
        assert ConversationMode("quick") == ConversationMode.QUICK
        assert ConversationMode("standard") == ConversationMode.STANDARD
        assert ConversationMode("deep") == ConversationMode.DEEP
        assert ConversationMode("iterative") == ConversationMode.ITERATIVE
        
        with pytest.raises(ValueError):
            ConversationMode("invalid")


class TestQuestionTypeEnum:
    """Test suite for QuestionType enum."""
    
    def test_question_type_values(self):
        """Test QuestionType enum values."""
        assert QuestionType.OPEN_ENDED.value == "open_ended"
        assert QuestionType.MULTIPLE_CHOICE.value == "multiple_choice"
        assert QuestionType.SCALE.value == "scale"
        assert QuestionType.BOOLEAN.value == "boolean"
        assert QuestionType.CLARIFICATION.value == "clarification"
        assert QuestionType.FOLLOW_UP.value == "follow_up"


# Integration Tests
class TestConversationStateIntegration:
    """Integration tests for complete conversation state workflow."""
    
    def test_complete_conversation_workflow(self):
        """Test a complete conversation workflow from start to finish."""
        manager = ConversationStateManager()
        
        # 1. Create initial state
        state = manager.create_new_state(
            session_id="workflow_test",
            user_query="I need to choose the best smartphone for photography",
            conversation_mode=ConversationMode.STANDARD
        )
        
        # 2. Add conversation history
        state.add_question_answer(
            question="What's your budget range?",
            answer="Between $800-1200",
            category="budget",
            question_type=QuestionType.OPEN_ENDED,
            confidence=0.9,
            importance=0.8
        )
        
        state.add_question_answer(
            question="What type of photography do you do most?",
            answer="Mainly portraits and street photography",
            category="use_case",
            question_type=QuestionType.OPEN_ENDED,
            confidence=0.8,
            importance=0.9
        )
        
        state.add_question_answer(
            question="How important is phone size/portability?",
            answer="Very important - I travel frequently",
            category="constraints",
            question_type=QuestionType.SCALE,
            confidence=0.9,
            importance=0.7
        )
        
        # 3. Set priority factors
        state.set_priority_factor("camera_quality", 0.9)
        state.set_priority_factor("portability", 0.8)
        state.set_priority_factor("budget", 0.7)
        
        # 4. Update emotional indicators
        state.emotional_indicators.confidence_level = 0.6
        state.emotional_indicators.urgency_level = 0.3
        state.emotional_indicators.indicators_detected = ["confident", "methodical"]
        
        # 5. Update context understanding
        state.context_understanding.domain_expertise["photography"] = 0.7
        state.context_understanding.decision_making_style = "analytical"
        state.context_understanding.detail_preference = 0.8
        
        # 6. Add some information gaps
        state.add_information_gap("brand_preferences")
        state.add_information_gap("upgrade_timeline")
        
        # 7. Test state completeness
        completeness = manager.calculate_state_completeness(state)
        assert completeness > 0.5  # Should be reasonably complete
        
        # 8. Test overall confidence
        overall_confidence = state.get_overall_confidence()
        assert overall_confidence > 0.7  # Should be high given good data
        
        # 9. Test serialization preserves everything
        assert manager.validate_serialization(state)
        
        # 10. Test JSON round-trip
        json_str = state.to_json()
        restored_state = ConversationState.from_json(json_str)
        
        assert restored_state.session_id == state.session_id
        assert len(restored_state.question_history) == 3
        assert restored_state.priority_factors == state.priority_factors
        assert restored_state.information_gaps == state.information_gaps
        assert restored_state.emotional_indicators.confidence_level == 0.6
        assert restored_state.context_understanding.domain_expertise["photography"] == 0.7
        
        # 11. Test conversation summary
        summary = state.get_conversation_summary()
        assert "smartphone" in summary.lower()
        assert "photography" in summary.lower()
        
        # 12. Test state updates still work after restoration
        restored_state.add_question_answer(
            question="Do you have any brand preferences?",
            answer="I prefer Android phones",
            category="brand_preferences"
        )
        
        # Remove the gap we just filled
        restored_state.remove_information_gap("brand_preferences")
        
        assert len(restored_state.question_history) == 4
        assert "brand_preferences" not in restored_state.information_gaps
        
        # Final validation
        final_completeness = manager.calculate_state_completeness(restored_state)
        # Note: completeness might fluctuate slightly due to weighting changes
        assert final_completeness >= completeness - 0.05  # Allow small tolerance
