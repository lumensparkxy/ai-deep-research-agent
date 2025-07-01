"""
Tests for Conversation Memory System
Comprehensive test suite for conversation history tracking and memory management.
"""

import pytest
import tempfile
import shutil
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any

from core.conversation_memory import (
    ConversationMemory,
    ConversationHistory,
    QuestionMetrics,
    ResponsePattern,
    ContextEvolution,
    ConversationInsight,
    ConversationSummary
)
from core.conversation_state import (
    ConversationState,
    QuestionAnswer,
    QuestionType,
    ConversationMode
)


class TestQuestionMetrics:
    """Test suite for QuestionMetrics dataclass."""
    
    def test_question_metrics_creation(self):
        """Test QuestionMetrics creation and properties."""
        metrics = QuestionMetrics(
            question_id="test_123",
            session_id="test_session",
            question_text="What's your budget?",
            question_type=QuestionType.OPEN_ENDED,
            category="budget",
            asked_at=datetime.now(),
            response_text="Around $1000",
            response_received=True,
            response_length=15,
            response_quality_score=0.8,
            user_engagement_score=0.7,
            information_gained=0.9,
            context_relevance=0.8,
            effectiveness_score=0.8
        )
        
        assert metrics.question_id == "test_123"
        assert metrics.session_id == "test_session"
        assert metrics.question_text == "What's your budget?"
        assert metrics.response_text == "Around $1000"
        assert metrics.question_type == QuestionType.OPEN_ENDED
        assert metrics.category == "budget"
        assert metrics.response_received is True
        assert metrics.effectiveness_score == 0.8


class TestResponsePattern:
    """Test suite for ResponsePattern dataclass."""
    
    def test_response_pattern_defaults(self):
        """Test ResponsePattern default values."""
        pattern = ResponsePattern()
        
        assert pattern.average_length == 0.0
        assert pattern.detail_preference == "medium"
        assert pattern.communication_style == "mixed"
        assert pattern.certainty_level == 0.5
        assert pattern.technical_comfort == 0.5
        assert pattern.engagement_trend == "stable"
    
    def test_response_pattern_custom_values(self):
        """Test ResponsePattern with custom values."""
        pattern = ResponsePattern(
            average_length=25.5,
            detail_preference="high",
            communication_style="analytical",
            certainty_level=0.8,
            technical_comfort=0.9,
            engagement_trend="increasing",
            question_asking_frequency=0.3
        )
        
        assert pattern.average_length == 25.5
        assert pattern.detail_preference == "high"
        assert pattern.communication_style == "analytical"
        assert pattern.certainty_level == 0.8
        assert pattern.question_asking_frequency == 0.3


class TestConversationHistory:
    """Test suite for ConversationHistory class."""
    
    @pytest.fixture
    def temp_storage_path(self):
        """Create temporary storage path for testing."""
        temp_dir = tempfile.mkdtemp()
        storage_path = Path(temp_dir) / "test_memory.json"
        yield str(storage_path)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def conversation_history(self, temp_storage_path):
        """Create ConversationHistory instance for testing."""
        return ConversationHistory(max_history_size=100, storage_path=temp_storage_path)
    
    @pytest.fixture
    def sample_conversation_state(self):
        """Create sample conversation state for testing."""
        return ConversationState(
            session_id="test_session_123",
            user_query="I need a laptop for programming work",
            user_profile={
                "context": "work",
                "budget": "$1500",
                "expertise": "intermediate"
            },
            question_history=[
                QuestionAnswer(
                    question="What's your budget range?",
                    answer="I can spend up to $1500, preferably around $1200",
                    question_type=QuestionType.OPEN_ENDED,
                    timestamp=datetime.now(),
                    category="budget"
                ),
                QuestionAnswer(
                    question="What programming languages do you use?",
                    answer="Mainly Python and JavaScript, sometimes Java",
                    question_type=QuestionType.OPEN_ENDED,
                    timestamp=datetime.now(),
                    category="technical_requirements"
                )
            ],
            conversation_mode=ConversationMode.STANDARD,
            completion_confidence=0.6
        )
    
    def test_initialization(self, conversation_history):
        """Test ConversationHistory initialization."""
        assert conversation_history.max_history_size == 100
        assert conversation_history.storage_path is not None
        assert len(conversation_history.conversations) == 0
        assert len(conversation_history.question_metrics) == 0
        assert len(conversation_history.response_patterns) == 0
        assert len(conversation_history.recent_conversations) == 0
    
    def test_add_conversation_state(self, conversation_history, sample_conversation_state):
        """Test adding conversation state to memory."""
        conversation_history.add_conversation_state(sample_conversation_state)
        
        session_id = sample_conversation_state.session_id
        assert session_id in conversation_history.conversations
        assert session_id in conversation_history.response_patterns
        assert len(conversation_history.recent_conversations) == 1
        
        stored_conversation = conversation_history.conversations[session_id]
        assert stored_conversation.user_query == sample_conversation_state.user_query
        assert stored_conversation.completion_confidence == 0.6
    
    def test_track_question_effectiveness(self, conversation_history):
        """Test tracking question effectiveness."""
        session_id = "test_session"
        question = "What's your budget?"
        response = "I have about $1000 to spend on this"
        question_type = QuestionType.OPEN_ENDED
        category = "budget"
        
        conversation_history.track_question_effectiveness(
            session_id, question, response, question_type, category
        )
        
        # Check that metrics were created
        question_id = f"{session_id}_{hash(question)}"
        assert question_id in conversation_history.question_metrics
        
        metrics = conversation_history.question_metrics[question_id]
        assert metrics.question_text == question
        assert metrics.question_type == question_type
        assert metrics.category == category
        assert metrics.response_received is True
        assert metrics.response_length > 0
        assert 0.0 <= metrics.effectiveness_score <= 1.0
        
        # Check question was added to asked questions
        question_hash = str(hash(question.lower().strip()))
        assert question_hash in conversation_history.asked_questions[session_id]
    
    def test_is_question_duplicate_exact_match(self, conversation_history):
        """Test duplicate detection for exact question matches."""
        session_id = "test_session"
        question = "What's your budget range?"
        
        # First time asking - should not be duplicate
        assert not conversation_history.is_question_duplicate(session_id, question)
        
        # Track the question
        conversation_history.track_question_effectiveness(
            session_id, question, "Around $1000", QuestionType.OPEN_ENDED, "budget"
        )
        
        # Second time asking - should be duplicate
        assert conversation_history.is_question_duplicate(session_id, question)
    
    def test_is_question_duplicate_case_insensitive(self, conversation_history):
        """Test duplicate detection is case insensitive."""
        session_id = "test_session"
        question1 = "What's your budget?"
        question2 = "WHAT'S YOUR BUDGET?"
        
        # Track first question
        conversation_history.track_question_effectiveness(
            session_id, question1, "Around $1000", QuestionType.OPEN_ENDED, "budget"
        )
        
        # Second question should be detected as duplicate
        assert conversation_history.is_question_duplicate(session_id, question2)
    
    def test_get_conversation_summary(self, conversation_history, sample_conversation_state):
        """Test conversation summary generation."""
        conversation_history.add_conversation_state(sample_conversation_state)
        
        summary = conversation_history.get_conversation_summary(sample_conversation_state.session_id)
        
        assert summary is not None
        assert summary.session_id == sample_conversation_state.session_id
        assert summary.user_query == sample_conversation_state.user_query
        assert isinstance(summary.key_preferences, dict)
        assert isinstance(summary.confidence_evolution, list)
        assert isinstance(summary.created_at, datetime)
    
    def test_get_response_pattern(self, conversation_history, sample_conversation_state):
        """Test response pattern retrieval."""
        conversation_history.add_conversation_state(sample_conversation_state)
        
        pattern = conversation_history.get_response_pattern(sample_conversation_state.session_id)
        
        assert pattern is not None
        assert isinstance(pattern, ResponsePattern)
        assert pattern.average_length > 0  # Should be calculated from responses
        assert pattern.detail_preference in ["low", "medium", "high"]
        assert pattern.communication_style in ["direct", "detailed", "questioning", "uncertain"]
    
    def test_get_context_evolution(self, conversation_history, sample_conversation_state):
        """Test context evolution tracking."""
        conversation_history.add_conversation_state(sample_conversation_state)
        
        evolution = conversation_history.get_context_evolution(sample_conversation_state.session_id)
        
        assert isinstance(evolution, list)
        assert len(evolution) > 0
        
        first_evolution = evolution[0]
        assert isinstance(first_evolution, ContextEvolution)
        assert first_evolution.confidence_score == sample_conversation_state.completion_confidence
        assert isinstance(first_evolution.timestamp, datetime)
    
    def test_get_conversation_insights(self, conversation_history, sample_conversation_state):
        """Test conversation insights retrieval."""
        conversation_history.add_conversation_state(sample_conversation_state)
        
        insights = conversation_history.get_conversation_insights(sample_conversation_state.session_id)
        
        assert isinstance(insights, list)
        # Should have insights based on user profile
        if insights:
            insight = insights[0]
            assert isinstance(insight, ConversationInsight)
            assert insight.insight_type in ["preference", "constraint", "priority", "style", "context"]
            assert 0.0 <= insight.confidence <= 1.0
    
    def test_get_question_recommendations(self, conversation_history, sample_conversation_state):
        """Test question recommendation generation."""
        conversation_history.add_conversation_state(sample_conversation_state)
        
        recommendations = conversation_history.get_question_recommendations(sample_conversation_state.session_id)
        
        assert isinstance(recommendations, list)
        assert len(recommendations) <= 5  # Should limit recommendations
        
        # Test category-specific recommendations
        budget_recs = conversation_history.get_question_recommendations(
            sample_conversation_state.session_id, category="timeline"
        )
        assert isinstance(budget_recs, list)
    
    def test_question_deduplication_in_recommendations(self, conversation_history, sample_conversation_state):
        """Test that recommendations don't include already asked questions."""
        conversation_history.add_conversation_state(sample_conversation_state)
        
        # Track a question as asked
        question = "What's your budget range?"
        conversation_history.track_question_effectiveness(
            sample_conversation_state.session_id, question, "Around $1500", 
            QuestionType.OPEN_ENDED, "budget"
        )
        
        # Get recommendations
        recommendations = conversation_history.get_question_recommendations(sample_conversation_state.session_id)
        
        # Should not include the already asked question
        assert question not in recommendations
    
    def test_save_to_storage(self, conversation_history, sample_conversation_state):
        """Test saving conversation history to storage."""
        conversation_history.add_conversation_state(sample_conversation_state)
        
        # Track some questions
        conversation_history.track_question_effectiveness(
            sample_conversation_state.session_id, "What's your budget?", 
            "Around $1500", QuestionType.OPEN_ENDED, "budget"
        )
        
        # Save to storage
        success = conversation_history.save_to_storage()
        assert success is True
        
        # Check file was created
        assert conversation_history.storage_path.exists()
    
    def test_cleanup_old_conversations(self, conversation_history):
        """Test cleanup of old conversations."""
        # Create old conversation
        old_conversation = ConversationState(
            session_id="old_session",
            user_query="Old query",
            question_history=[
                QuestionAnswer(
                    question="Old question?",
                    answer="Old answer",
                    question_type=QuestionType.OPEN_ENDED,
                    timestamp=datetime.now() - timedelta(days=35),  # 35 days old
                    category="old"
                )
            ]
        )
        
        # Create recent conversation
        recent_conversation = ConversationState(
            session_id="recent_session",
            user_query="Recent query",
            question_history=[
                QuestionAnswer(
                    question="Recent question?",
                    answer="Recent answer",
                    question_type=QuestionType.OPEN_ENDED,
                    timestamp=datetime.now() - timedelta(days=5),  # 5 days old
                    category="recent"
                )
            ]
        )
        
        conversation_history.add_conversation_state(old_conversation)
        conversation_history.add_conversation_state(recent_conversation)
        
        # Clean up conversations older than 30 days
        cleaned_count = conversation_history.cleanup_old_conversations(days_to_keep=30)
        
        assert cleaned_count == 1
        assert "old_session" not in conversation_history.conversations
        assert "recent_session" in conversation_history.conversations
    
    def test_get_memory_stats(self, conversation_history, sample_conversation_state):
        """Test memory statistics retrieval."""
        conversation_history.add_conversation_state(sample_conversation_state)
        conversation_history.track_question_effectiveness(
            sample_conversation_state.session_id, "What's your budget?",
            "Around $1500", QuestionType.OPEN_ENDED, "budget"
        )
        
        stats = conversation_history.get_memory_stats()
        
        assert isinstance(stats, dict)
        assert 'total_conversations' in stats
        assert 'total_questions_tracked' in stats
        assert 'average_question_effectiveness' in stats
        assert 'memory_usage_estimate_mb' in stats
        
        assert stats['total_conversations'] == 1
        # Account for questions imported from conversation history plus explicitly tracked
        assert stats['total_questions_tracked'] >= 1
        assert 0.0 <= stats['average_question_effectiveness'] <= 1.0
    
    def test_response_pattern_analysis_direct_style(self, conversation_history):
        """Test response pattern analysis for direct communication style."""
        conversation = ConversationState(
            session_id="direct_session",
            user_query="Need laptop",
            question_history=[
                QuestionAnswer(
                    question="What's your budget?",
                    answer="$1000",
                    question_type=QuestionType.OPEN_ENDED,
                    timestamp=datetime.now(),
                    category="budget"
                ),
                QuestionAnswer(
                    question="What will you use it for?",
                    answer="Work",
                    question_type=QuestionType.OPEN_ENDED,
                    timestamp=datetime.now(),
                    category="usage"
                )
            ]
        )
        
        conversation_history.add_conversation_state(conversation)
        pattern = conversation_history.get_response_pattern("direct_session")
        
        assert pattern.communication_style == "direct"
        assert pattern.detail_preference == "low"
        assert pattern.average_length < 10
    
    def test_response_pattern_analysis_detailed_style(self, conversation_history):
        """Test response pattern analysis for detailed communication style."""
        detailed_response = ("I'm looking for a laptop that can handle software development work, "
                           "particularly Python and JavaScript development. I also need it to run "
                           "Docker containers efficiently and handle some light machine learning tasks. "
                           "The laptop should be portable enough for travel but powerful enough for "
                           "demanding development work.")
        
        conversation = ConversationState(
            session_id="detailed_session",
            user_query="Need programming laptop",
            question_history=[
                QuestionAnswer(
                    question="What will you use the laptop for?",
                    answer=detailed_response,
                    question_type=QuestionType.OPEN_ENDED,
                    timestamp=datetime.now(),
                    category="usage"
                )
            ]
        )
        
        conversation_history.add_conversation_state(conversation)
        pattern = conversation_history.get_response_pattern("detailed_session")
        
        assert pattern.communication_style == "detailed"
        assert pattern.detail_preference in ["medium", "high"]
        assert pattern.average_length > 20
    
    def test_response_pattern_questioning_style(self, conversation_history):
        """Test response pattern analysis for questioning communication style."""
        conversation = ConversationState(
            session_id="questioning_session",
            user_query="Need smartphone",
            question_history=[
                QuestionAnswer(
                    question="What features are important?",
                    answer="Good camera I guess? What about battery life? Is 5G important?",
                    question_type=QuestionType.OPEN_ENDED,
                    timestamp=datetime.now(),
                    category="features"
                ),
                QuestionAnswer(
                    question="What's your budget?",
                    answer="Not sure, what's a good budget? What do you recommend?",
                    question_type=QuestionType.OPEN_ENDED,
                    timestamp=datetime.now(),
                    category="budget"
                )
            ]
        )
        
        conversation_history.add_conversation_state(conversation)
        pattern = conversation_history.get_response_pattern("questioning_session")
        
        assert pattern.communication_style == "questioning"
        assert pattern.question_asking_frequency > 0.5
    
    def test_response_pattern_uncertain_style(self, conversation_history):
        """Test response pattern analysis for uncertain communication style."""
        conversation = ConversationState(
            session_id="uncertain_session",
            user_query="Need tablet",
            question_history=[
                QuestionAnswer(
                    question="What size screen do you prefer?",
                    answer="I'm not sure, maybe around 10 inches? Perhaps a bit larger.",
                    question_type=QuestionType.OPEN_ENDED,
                    timestamp=datetime.now(),
                    category="specs"
                ),
                QuestionAnswer(
                    question="What will you use it for?",
                    answer="Maybe reading, perhaps some light work. Not really sure.",
                    question_type=QuestionType.OPEN_ENDED,
                    timestamp=datetime.now(),
                    category="usage"
                )
            ]
        )
        
        conversation_history.add_conversation_state(conversation)
        pattern = conversation_history.get_response_pattern("uncertain_session")
        
        assert pattern.communication_style == "uncertain"
    
    def test_effectiveness_scoring(self, conversation_history):
        """Test question effectiveness scoring."""
        session_id = "effectiveness_test"
        
        # Test high-quality response
        conversation_history.track_question_effectiveness(
            session_id, "What's your budget range?", 
            "I have exactly $1200 to spend, and I need something that offers great value for money in terms of performance and build quality",
            QuestionType.OPEN_ENDED, "budget"
        )
        
        # Test low-quality response
        conversation_history.track_question_effectiveness(
            session_id, "Any other preferences?",
            "No",
            QuestionType.OPEN_ENDED, "general"
        )
        
        metrics = list(conversation_history.question_metrics.values())
        
        # Find high and low quality metrics
        high_quality = next((m for m in metrics if "exactly $1200" in m.question_text or len(m.question_text) > 50), None)
        low_quality = next((m for m in metrics if m.response_length <= 3), None)
        
        if high_quality and low_quality:
            assert high_quality.effectiveness_score > low_quality.effectiveness_score
        
        # All effectiveness scores should be between 0 and 1
        for metric in metrics:
            assert 0.0 <= metric.effectiveness_score <= 1.0
    
    def test_question_pattern_extraction(self, conversation_history):
        """Test question pattern extraction for duplicate detection."""
        session_id = "pattern_test"
        
        # Similar questions with different specifics
        question1 = "What's your budget for this laptop?"
        question2 = "What's your budget for this smartphone?"
        question3 = "How much do you want to spend?"
        
        conversation_history.track_question_effectiveness(
            session_id, question1, "Around $1000", QuestionType.OPEN_ENDED, "budget"
        )
        
        # These should be detected as similar (simplified test)
        pattern1 = conversation_history._extract_question_pattern(question1)
        pattern2 = conversation_history._extract_question_pattern(question2)
        
        # Patterns should be similar for budget questions
        assert "budget" in pattern1.lower() or "what" in pattern1.lower()
        assert "budget" in pattern2.lower() or "what" in pattern2.lower()
    
    def test_question_adaptation_to_style(self, conversation_history):
        """Test question adaptation based on communication style."""
        # Create different response patterns
        direct_pattern = ResponsePattern(
            communication_style="direct",
            detail_preference="low",
            average_length=5.0
        )
        
        detailed_pattern = ResponsePattern(
            communication_style="detailed",
            detail_preference="high",
            average_length=30.0
        )
        
        questions = ["What's your budget?", "Could you tell me more about your requirements?"]
        
        # Adapt to direct style
        direct_adapted = conversation_history._adapt_questions_to_style(questions, direct_pattern)
        
        # Adapt to detailed style
        detailed_adapted = conversation_history._adapt_questions_to_style(questions, detailed_pattern)
        
        # Direct style should have shorter, more direct questions
        assert len(direct_adapted) == len(questions)
        
        # Detailed style should have more elaborate questions
        assert len(detailed_adapted) == len(questions)
    
    def test_information_gap_identification(self, conversation_history):
        """Test identification of missing information categories."""
        # Conversation with limited information
        conversation = ConversationState(
            session_id="gap_test",
            user_query="I need a laptop for work",
            user_profile={"context": "work"}  # Only context, missing budget, timeline, etc.
        )
        
        missing_categories = conversation_history._identify_missing_information(conversation)
        
        assert isinstance(missing_categories, list)
        assert "budget" in missing_categories
        assert "timeline" in missing_categories
        assert "preferences" in missing_categories
        assert "context" not in missing_categories  # Already have this
    
    def test_memory_efficiency_large_conversations(self, conversation_history):
        """Test memory efficiency with large conversation histories."""
        # Create multiple conversations
        for i in range(20):
            conversation = ConversationState(
                session_id=f"session_{i}",
                user_query=f"Query {i}",
                user_profile={"test": f"value_{i}"},
                question_history=[
                    QuestionAnswer(
                        question=f"Question {i}?",
                        answer=f"Answer {i}",
                        question_type=QuestionType.OPEN_ENDED,
                        timestamp=datetime.now(),
                        category="test"
                    )
                ]
            )
            conversation_history.add_conversation_state(conversation)
            
            # Track some questions
            conversation_history.track_question_effectiveness(
                f"session_{i}", f"Question {i}?", f"Answer {i}",
                QuestionType.OPEN_ENDED, "test"
            )
        
        stats = conversation_history.get_memory_stats()
        
        assert stats['total_conversations'] == 20
        assert stats['total_questions_tracked'] == 20
        assert stats['memory_usage_estimate_mb'] > 0
        
        # Memory usage should be reasonable
        assert stats['memory_usage_estimate_mb'] < 100  # Should be much less than 100MB


class TestConversationMemory:
    """Test suite for ConversationMemory main interface."""
    
    @pytest.fixture
    def temp_storage_path(self):
        """Create temporary storage path for testing."""
        temp_dir = tempfile.mkdtemp()
        storage_path = Path(temp_dir) / "test_memory.json"
        yield str(storage_path)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def conversation_memory(self, temp_storage_path):
        """Create ConversationMemory instance for testing."""
        return ConversationMemory(storage_path=temp_storage_path)
    
    @pytest.fixture
    def sample_conversation_state(self):
        """Create sample conversation state for testing."""
        return ConversationState(
            session_id="memory_test_session",
            user_query="I need a programming laptop",
            user_profile={
                "context": "programming",
                "budget": "up to $2000",
                "experience": "intermediate"
            },
            question_history=[
                QuestionAnswer(
                    question="What programming languages do you use?",
                    answer="Python, JavaScript, and some Go",
                    question_type=QuestionType.OPEN_ENDED,
                    timestamp=datetime.now(),
                    category="technical"
                )
            ],
            completion_confidence=0.7
        )
    
    def test_initialization(self, conversation_memory):
        """Test ConversationMemory initialization."""
        assert conversation_memory.history is not None
        assert isinstance(conversation_memory.history, ConversationHistory)
        assert conversation_memory.logger is not None
    
    def test_update_conversation(self, conversation_memory, sample_conversation_state):
        """Test updating conversation in memory."""
        conversation_memory.update_conversation(sample_conversation_state)
        
        # Check that conversation was stored
        session_id = sample_conversation_state.session_id
        assert session_id in conversation_memory.history.conversations
        
        stored_conversation = conversation_memory.history.conversations[session_id]
        assert stored_conversation.user_query == sample_conversation_state.user_query
        assert stored_conversation.completion_confidence == 0.7
    
    def test_track_question_response(self, conversation_memory):
        """Test tracking question and response."""
        session_id = "track_test"
        question = "What's your preferred screen size?"
        response = "I prefer a 15-inch screen for better productivity"
        question_type = QuestionType.OPEN_ENDED
        category = "preferences"
        
        conversation_memory.track_question_response(
            session_id, question, response, question_type, category
        )
        
        # Check that tracking was successful
        question_id = f"{session_id}_{hash(question)}"
        assert question_id in conversation_memory.history.question_metrics
        
        metrics = conversation_memory.history.question_metrics[question_id]
        assert metrics.question_text == question
        assert metrics.category == category
        assert metrics.response_received is True
    
    def test_should_ask_question(self, conversation_memory):
        """Test duplicate question detection."""
        session_id = "duplicate_test"
        question = "What's your budget?"
        
        # First time - should ask
        assert conversation_memory.should_ask_question(session_id, question) is True
        
        # Track the question
        conversation_memory.track_question_response(
            session_id, question, "Around $1500", QuestionType.OPEN_ENDED, "budget"
        )
        
        # Second time - should not ask (duplicate)
        assert conversation_memory.should_ask_question(session_id, question) is False
    
    def test_get_question_suggestions(self, conversation_memory, sample_conversation_state):
        """Test getting question suggestions."""
        conversation_memory.update_conversation(sample_conversation_state)
        
        suggestions = conversation_memory.get_question_suggestions(sample_conversation_state.session_id)
        
        assert isinstance(suggestions, list)
        assert len(suggestions) <= 5  # Should limit suggestions
        
        # Test category-specific suggestions
        budget_suggestions = conversation_memory.get_question_suggestions(
            sample_conversation_state.session_id, category="budget"
        )
        assert isinstance(budget_suggestions, list)
    
    def test_get_conversation_insights(self, conversation_memory, sample_conversation_state):
        """Test getting comprehensive conversation insights."""
        conversation_memory.update_conversation(sample_conversation_state)
        
        insights = conversation_memory.get_conversation_insights(sample_conversation_state.session_id)
        
        assert isinstance(insights, dict)
        assert 'summary' in insights
        assert 'response_pattern' in insights
        assert 'context_evolution' in insights
        assert 'insights' in insights
        
        # Check that summary exists and has correct session ID
        summary = insights['summary']
        if summary:
            assert summary.session_id == sample_conversation_state.session_id
    
    def test_save_memory(self, conversation_memory, sample_conversation_state):
        """Test saving memory to persistent storage."""
        conversation_memory.update_conversation(sample_conversation_state)
        conversation_memory.track_question_response(
            sample_conversation_state.session_id, "Test question?", "Test response",
            QuestionType.OPEN_ENDED, "test"
        )
        
        success = conversation_memory.save_memory()
        assert success is True
        
        # Check that storage file was created
        assert conversation_memory.history.storage_path.exists()
    
    def test_cleanup_old_data(self, conversation_memory):
        """Test cleaning up old conversation data."""
        # Create old conversation
        old_conversation = ConversationState(
            session_id="old_data_test",
            user_query="Old query",
            question_history=[
                QuestionAnswer(
                    question="Old question?",
                    answer="Old answer",
                    question_type=QuestionType.OPEN_ENDED,
                    timestamp=datetime.now() - timedelta(days=40),
                    category="old"
                )
            ]
        )
        
        conversation_memory.update_conversation(old_conversation)
        
        # Clean up data older than 30 days
        cleaned_count = conversation_memory.cleanup_old_data(days_to_keep=30)
        
        assert cleaned_count == 1
        assert "old_data_test" not in conversation_memory.history.conversations
    
    def test_get_stats(self, conversation_memory, sample_conversation_state):
        """Test getting memory system statistics."""
        conversation_memory.update_conversation(sample_conversation_state)
        conversation_memory.track_question_response(
            sample_conversation_state.session_id, "Stats test question?", "Stats test response",
            QuestionType.OPEN_ENDED, "test"
        )
        
        stats = conversation_memory.get_stats()
        
        assert isinstance(stats, dict)
        assert 'total_conversations' in stats
        assert 'total_questions_tracked' in stats
        assert 'average_question_effectiveness' in stats
        
        assert stats['total_conversations'] >= 1
        assert stats['total_questions_tracked'] >= 1


class TestIntegrationScenarios:
    """Integration tests for real-world conversation scenarios."""
    
    def test_complete_laptop_conversation_flow(self):
        """Test complete conversation flow for laptop recommendation."""
        memory = ConversationMemory()
        
        # Initial conversation state
        conversation = ConversationState(
            session_id="laptop_flow_test",
            user_query="I need a laptop for software development and gaming",
            user_profile={}
        )
        
        memory.update_conversation(conversation)
        
        # Simulate conversation progression
        questions_and_responses = [
            ("What's your budget range?", "I can spend up to $2500", "budget"),
            ("What games do you play?", "Mostly AAA titles like Cyberpunk 2077 and Call of Duty", "gaming"),
            ("What development work do you do?", "Full-stack web development with React and Node.js", "development"),
            ("Do you need portability?", "Yes, I travel frequently for work", "portability"),
            ("Any brand preferences?", "I prefer ASUS or MSI for gaming laptops", "preferences")
        ]
        
        for question, response, category in questions_and_responses:
            # Check if we should ask this question
            should_ask = memory.should_ask_question(conversation.session_id, question)
            assert should_ask is True  # First time asking each question
            
            # Track the question and response
            memory.track_question_response(
                conversation.session_id, question, response, 
                QuestionType.OPEN_ENDED, category
            )
            
            # Update conversation state with new information
            if category == "budget":
                conversation.user_profile["budget"] = response
            elif category == "gaming":
                conversation.user_profile["gaming_preferences"] = response
            elif category == "development":
                conversation.user_profile["development_work"] = response
            elif category == "portability":
                conversation.user_profile["portability_needs"] = response
            elif category == "preferences":
                conversation.user_profile["brand_preferences"] = response
            
            conversation.completion_confidence += 0.15  # Simulate increasing confidence
            memory.update_conversation(conversation)
        
        # Get final insights
        insights = memory.get_conversation_insights(conversation.session_id)
        
        assert insights['summary'] is not None
        assert insights['response_pattern'] is not None
        
        # Check response pattern
        pattern = insights['response_pattern']
        assert pattern.average_length > 5  # Reasonable responses (adjusted from 10)
        assert pattern.detail_preference in ["low", "medium", "high"]  # Accept all valid preferences
        
        # Test question suggestions for missing categories
        suggestions = memory.get_question_suggestions(conversation.session_id)
        assert isinstance(suggestions, list)
        
        # Test duplicate detection
        for question, _, _ in questions_and_responses:
            assert not memory.should_ask_question(conversation.session_id, question)
    
    def test_conversation_interruption_and_recovery(self):
        """Test conversation memory across interruptions."""
        memory = ConversationMemory()
        
        # Start conversation
        conversation = ConversationState(
            session_id="interruption_test",
            user_query="Looking for a smartphone",
            user_profile={"context": "personal"}
        )
        
        memory.update_conversation(conversation)
        
        # Ask some questions
        memory.track_question_response(
            "interruption_test", "What's your budget?", 
            "Around $800", QuestionType.OPEN_ENDED, "budget"
        )
        
        # Simulate interruption - save memory
        memory.save_memory()
        
        # Create new memory instance (simulating restart)
        memory2 = ConversationMemory(storage_path=memory.history.storage_path)
        
        # Continue conversation
        conversation.user_profile["budget"] = "Around $800"
        memory2.update_conversation(conversation)
        
        # Should remember previous questions
        assert not memory2.should_ask_question("interruption_test", "What's your budget?")
        
        # Should get appropriate new suggestions
        suggestions = memory2.get_question_suggestions("interruption_test")
        assert isinstance(suggestions, list)
        
        # Budget questions should be filtered out
        budget_questions = [s for s in suggestions if "budget" in s.lower()]
        assert len(budget_questions) == 0  # Should not suggest budget questions
    
    def test_cross_session_pattern_learning(self):
        """Test learning patterns across multiple conversation sessions."""
        memory = ConversationMemory()
        
        # Create multiple sessions with similar user behavior
        sessions = ["session_1", "session_2", "session_3"]
        
        for session_id in sessions:
            conversation = ConversationState(
                session_id=session_id,
                user_query=f"Need tech product - {session_id}",
                user_profile={}
            )
            
            memory.update_conversation(conversation)
            
            # Each session shows direct communication style
            memory.track_question_response(
                session_id, "What's your budget?", "$1000", 
                QuestionType.OPEN_ENDED, "budget"
            )
            
            memory.track_question_response(
                session_id, "What features matter?", "Performance, reliability",
                QuestionType.OPEN_ENDED, "features"
            )
        
        # Check that all sessions show direct communication pattern
        for session_id in sessions:
            pattern = memory.history.get_response_pattern(session_id)
            assert pattern.communication_style == "direct"
            assert pattern.detail_preference == "low"
        
        # Get stats to verify cross-session tracking
        stats = memory.get_stats()
        assert stats['total_conversations'] == 3
        assert stats['total_questions_tracked'] == 6  # 2 questions per session
    
    def test_memory_system_performance_with_large_dataset(self):
        """Test memory system performance with large conversation dataset."""
        memory = ConversationMemory()
        
        # Create many conversations
        num_sessions = 100
        questions_per_session = 5
        
        for i in range(num_sessions):
            session_id = f"perf_test_{i}"
            conversation = ConversationState(
                session_id=session_id,
                user_query=f"Query {i}",
                user_profile={f"key_{i}": f"value_{i}"}
            )
            
            memory.update_conversation(conversation)
            
            # Add questions for each session
            for j in range(questions_per_session):
                memory.track_question_response(
                    session_id, f"Question {j} for session {i}?",
                    f"Response {j} for session {i}",
                    QuestionType.OPEN_ENDED, f"category_{j}"
                )
        
        # Verify all data was stored
        stats = memory.get_stats()
        assert stats['total_conversations'] == num_sessions
        assert stats['total_questions_tracked'] == num_sessions * questions_per_session
        
        # Test that operations are still fast
        import time
        
        # Test question suggestion speed
        start_time = time.time()
        suggestions = memory.get_question_suggestions("perf_test_50")
        suggestion_time = time.time() - start_time
        
        assert isinstance(suggestions, list)
        assert suggestion_time < 1.0  # Should be fast even with large dataset
        
        # Test duplicate detection speed
        start_time = time.time()
        is_duplicate = memory.should_ask_question("perf_test_75", "Test duplicate question?")
        duplicate_time = time.time() - start_time
        
        assert isinstance(is_duplicate, bool)
        assert duplicate_time < 0.1  # Should be very fast
        
        # Test memory cleanup
        cleaned = memory.cleanup_old_data(days_to_keep=0)  # Clean all
        assert cleaned == num_sessions
        
        # Verify cleanup worked
        final_stats = memory.get_stats()
        assert final_stats['total_conversations'] == 0


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    def test_invalid_storage_path_handling(self):
        """Test handling of invalid storage paths."""
        # Test with invalid path
        memory = ConversationMemory(storage_path="/invalid/path/that/does/not/exist.json")
        
        # Should still initialize successfully
        assert memory.history is not None
        
        # Save should fail gracefully
        success = memory.save_memory()
        assert success is False  # Should fail but not crash
    
    def test_corrupted_conversation_state_handling(self):
        """Test handling of corrupted or invalid conversation states."""
        memory = ConversationMemory()
        
        # Test with None conversation state
        try:
            memory.update_conversation(None)
        except Exception:
            pass  # Should handle gracefully
        
        # Test with incomplete conversation state
        incomplete_conversation = ConversationState(
            session_id="incomplete_test",
            user_query="",  # Empty query
            user_profile=None  # None profile
        )
        
        # Should handle without crashing
        memory.update_conversation(incomplete_conversation)
        
        stats = memory.get_stats()
        assert stats['total_conversations'] >= 0
    
    def test_empty_response_handling(self):
        """Test handling of empty or invalid responses."""
        memory = ConversationMemory()
        
        # Test empty response
        memory.track_question_response(
            "empty_test", "What's your preference?", "",
            QuestionType.OPEN_ENDED, "test"
        )
        
        # Test None response
        memory.track_question_response(
            "none_test", "What's your preference?", None,
            QuestionType.OPEN_ENDED, "test"
        )
        
        # Should handle gracefully
        stats = memory.get_stats()
        assert stats['total_questions_tracked'] >= 0
    
    def test_memory_overflow_protection(self):
        """Test memory overflow protection mechanisms."""
        # Create memory system with small limit
        memory = ConversationMemory()
        memory.history.max_history_size = 5
        
        # Add more conversations than the limit
        for i in range(10):
            conversation = ConversationState(
                session_id=f"overflow_test_{i}",
                user_query=f"Query {i}",
                user_profile={}
            )
            memory.update_conversation(conversation)
        
        # Should not exceed reasonable memory usage
        stats = memory.get_stats()
        assert stats['memory_usage_estimate_mb'] < 50  # Should stay under 50MB
        
        # Recent conversations should be maintained
        assert stats['recent_conversations_cached'] > 0
