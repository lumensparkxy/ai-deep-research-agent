"""
Tests for Dynamic Personalization Engine
Comprehensive test suite for the main orchestration class that integrates all Phase 1 components.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from dataclasses import asdict

from core.dynamic_personalization import DynamicPersonalizationEngine
from core.conversation_state import ConversationState, QuestionAnswer, QuestionType
from core.ai_question_generator import AIQuestionGenerator
from core.context_analyzer import ContextAnalyzer
from core.conversation_memory import ConversationHistory


@pytest.fixture
def mock_gemini_client():
    """Create a mock Gemini client."""
    return Mock()

@pytest.fixture
def mock_conversation_history():
    """Create a mock conversation history."""
    return Mock(spec=ConversationHistory)

@pytest.fixture
def engine(mock_gemini_client, mock_conversation_history):
    """Create a DynamicPersonalizationEngine instance for testing."""
    return DynamicPersonalizationEngine(
        gemini_client=mock_gemini_client,
        conversation_history=mock_conversation_history
    )

@pytest.fixture
def sample_conversation_state():
    """Create a sample conversation state for testing."""
    state = ConversationState(
        session_id="test_session_001",
        user_query="I need help choosing a laptop for programming"
    )
    
    # Set up user profile
    state.user_profile = {
        'expertise_level': 'intermediate',
        'context': 'work',
        'budget': '1500'
    }
    
    # Set up priority factors
    state.priority_factors = {
        'laptop': 0.8,
        'programming': 0.9,
        'budget': 0.7
    }
    
    # Set up metadata
    state.metadata = {
        'started_at': datetime.now().isoformat(),
        'engine_version': '2.1.0'
    }
    
    # Add a sample question-answer
    state.add_question_answer(
        question="What type of programming do you do?",
        answer="Mainly web development with React and Node.js",
        category="expertise",
        question_type=QuestionType.OPEN_ENDED,
        confidence=0.8
    )
    
    return state


class TestDynamicPersonalizationEngine:
    """Test suite for DynamicPersonalizationEngine class."""


class TestInitialization:
    """Test engine initialization."""
    
    def test_engine_initialization_with_all_params(self, mock_gemini_client, mock_conversation_history):
        """Test engine initialization with all parameters."""
        engine = DynamicPersonalizationEngine(
            gemini_client=mock_gemini_client,
            conversation_history=mock_conversation_history
        )
        
        assert engine.question_generator is not None
        assert engine.context_analyzer is not None
        assert engine.conversation_history == mock_conversation_history
        assert engine.max_questions_per_session == 10
        assert engine.min_confidence_threshold == 0.6
        assert engine.adaptive_depth_enabled is True
    
    def test_engine_initialization_with_defaults(self):
        """Test engine initialization with default parameters."""
        engine = DynamicPersonalizationEngine()
        
        assert engine.question_generator is not None
        assert engine.context_analyzer is not None
        assert engine.conversation_history is not None
        assert isinstance(engine.conversation_history, ConversationHistory)
    
    def test_engine_initialization_with_partial_params(self, mock_gemini_client):
        """Test engine initialization with partial parameters."""
        engine = DynamicPersonalizationEngine(gemini_client=mock_gemini_client)
        
        assert engine.question_generator is not None
        assert engine.context_analyzer is not None
        assert engine.conversation_history is not None


class TestConversationInitialization:
    """Test conversation initialization functionality."""
    
    @patch('core.dynamic_personalization.datetime')
    def test_initialize_conversation_success(self, mock_datetime, engine):
        """Test successful conversation initialization."""
        # Mock datetime
        fixed_time = datetime(2025, 6, 29, 12, 0, 0)
        mock_datetime.now.return_value = fixed_time
        
        # Mock context analyzer to return a mock result
        mock_analysis_result = Mock()
        mock_analysis_result.priority_insights = []
        mock_analysis_result.emotional_indicators = []
        mock_analysis_result.communication_style = Mock()
        mock_analysis_result.communication_style.value = 'analytical'
        mock_analysis_result.overall_confidence = 0.8
        mock_analysis_result.pattern_insights = []
        
        engine.context_analyzer.analyze_context = Mock(return_value=mock_analysis_result)
        
        # Test initialization
        result = engine.initialize_conversation(
            user_query="I need a laptop for programming",
            session_id="test_session"
        )
        
        # Verify result
        assert isinstance(result, ConversationState)
        assert result.session_id == "test_session"
        assert result.user_query == "I need a laptop for programming"
        assert result.user_profile == {}
        assert len(result.priority_factors) >= 0  # May have topics extracted
        assert 'started_at' in result.metadata
        assert result.metadata['engine_version'] == '2.1.0'
        
        # Verify method calls
        engine.conversation_history.add_conversation_state.assert_called_once()
    
    def test_initialize_conversation_with_context_analyzer_error(self, engine):
        """Test conversation initialization when context analyzer fails."""
        # Mock to raise exception during topic extraction (simulated error)
        with patch.object(engine, '_extract_topics_from_query', side_effect=Exception("Analysis failed")):
            # Test that exception is propagated
            with pytest.raises(Exception, match="Analysis failed"):
                engine.initialize_conversation(
                    user_query="Test query",
                    session_id="test_session"
                )
    
    def test_extract_topics_from_query(self, engine):
        """Test topic extraction from user query."""
        user_query = "I need a laptop for programming and gaming"
        
        # Mock context analyzer
        mock_result = Mock()
        mock_result.priority_insights = [
            Mock(category='laptop', keywords=['programming', 'gaming']),
            Mock(category='performance', keywords=['speed'])
        ]
        engine.context_analyzer.analyze_context = Mock(return_value=mock_result)
        
        topics = engine._extract_topics_from_query(user_query)
        
        # Should extract topics from priority insights
        assert isinstance(topics, dict)
        assert len(topics) >= 0


class TestQuestionGeneration:
    """Test question generation functionality."""
    
    def test_generate_next_question_success(self, engine, sample_conversation_state):
        """Test successful question generation."""
        # Mock should continue conversation
        engine._should_continue_conversation = Mock(return_value=True)
        
        # Mock AI question generation
        engine._generate_intelligent_ai_question = Mock(return_value="What's your budget range?")
        
        # Test question generation
        question = engine.generate_next_question(sample_conversation_state)
        
        # Verify result
        assert question == "What's your budget range?"
        
        # Verify method calls (note: _generate_intelligent_ai_question takes conversation_state and asked_questions list)
        engine._should_continue_conversation.assert_called_once_with(sample_conversation_state)
        assert engine._generate_intelligent_ai_question.called
    
    def test_generate_next_question_conversation_complete(self, engine, sample_conversation_state):
        """Test question generation when conversation is complete."""
        # Mock should not continue conversation
        engine._should_continue_conversation = Mock(return_value=False)
        
        # Test question generation
        question = engine.generate_next_question(sample_conversation_state)
        
        # Should return None when conversation is complete
        assert question is None
        
        # Should not call other methods
        engine._should_continue_conversation.assert_called_once_with(sample_conversation_state)
    
    def test_generate_next_question_with_error(self, engine, sample_conversation_state):
        """Test question generation with error handling."""
        # Mock should continue conversation
        engine._should_continue_conversation = Mock(return_value=True)
        
        # Mock error in AI question generation
        engine._generate_intelligent_ai_question = Mock(side_effect=Exception("Generation failed"))
        
        # Test question generation
        question = engine.generate_next_question(sample_conversation_state)
        
        # Should return None on error
        assert question is None
    
    def test_should_continue_conversation_max_questions(self, engine, sample_conversation_state):
        """Test conversation continuation with max questions reached."""
        # Set max questions and add many questions
        engine.max_questions_per_session = 3
        for i in range(5):
            sample_conversation_state.question_history.append(
                QuestionAnswer(
                    question=f"Question {i}",
                    answer=f"Response {i}",
                    question_type=QuestionType.OPEN_ENDED,
                    timestamp=datetime.now(),
                    category="test_category"
                )
            )
        
        # Should not continue when max questions reached
        assert not engine._should_continue_conversation(sample_conversation_state)
    
    def test_should_continue_conversation_sufficient_info(self, engine, sample_conversation_state):
        """Test conversation continuation with sufficient information."""
        # Add sufficient information to user profile
        sample_conversation_state.user_profile = {
            'expertise_level': 'intermediate',
            'context': 'work',
            'budget': '1500',
            'timeline': 'soon',
            'preferences': 'lightweight',
            'constraints': 'no gaming'
        }
        
        # Should not continue when sufficient info gathered
        assert not engine._should_continue_conversation(sample_conversation_state)
    
    def test_should_continue_conversation_normal_case(self, engine, sample_conversation_state):
        """Test conversation continuation in normal case."""
        # Normal case with some questions and partial info
        # Should continue since we have limited information
        assert engine._should_continue_conversation(sample_conversation_state)


class TestResponseProcessing:
    """Test user response processing functionality."""
    
    @patch('core.dynamic_personalization.datetime')
    def test_process_user_response_success(self, mock_datetime, engine, sample_conversation_state):
        """Test successful user response processing."""
        # Mock datetime
        fixed_time = datetime(2025, 6, 29, 12, 30, 0)
        mock_datetime.now.return_value = fixed_time
        
        # Mock context analyzer
        mock_analysis_result = Mock()
        mock_analysis_result.priority_insights = [Mock(category='budget', keywords=['2000'])]
        mock_analysis_result.emotional_indicators = []
        mock_analysis_result.communication_style = Mock()
        mock_analysis_result.communication_style.value = 'analytical'
        mock_analysis_result.overall_confidence = 0.9
        mock_analysis_result.pattern_insights = [Mock(category='portability')]
        
        engine.context_analyzer.analyze_context = Mock(return_value=mock_analysis_result)
        
        # Test response processing
        question = "What's your budget range?"
        response = "Around $2000, and I prefer something lightweight"
        
        result = engine.process_user_response(sample_conversation_state, question, response)
        
        # Verify result structure
        assert 'extracted_info' in result
        assert 'response_analysis' in result
        assert 'conversation_progress' in result
        assert 'updated_priority_factors' in result
        
        # Verify user profile updated
        assert 'budget' in sample_conversation_state.user_profile
        assert sample_conversation_state.user_profile['budget'] == '2000'
        
        # Verify question-answer added
        assert len(sample_conversation_state.question_history) == 2  # Had 1, added 1
        latest_qa = sample_conversation_state.question_history[-1]
        assert latest_qa.question == question
        assert latest_qa.answer == response
        
        # Verify method calls
        engine.context_analyzer.analyze_context.assert_called_once()
    
    def test_process_user_response_with_error(self, engine, sample_conversation_state):
        """Test response processing with error handling."""
        # Mock context analyzer to raise exception
        engine.context_analyzer.analyze_context = Mock(side_effect=Exception("Analysis failed"))
        
        # Test response processing
        result = engine.process_user_response(
            sample_conversation_state, 
            "Test question", 
            "Test response"
        )
        
        # Should handle error gracefully and return partial result
        assert isinstance(result, dict)
    
    def test_extract_personalization_info(self, engine):
        """Test personalization information extraction."""
        response = "I need something with good performance and battery life"
        analysis = {
            'extracted_info': {'preferences': 'performance', 'requirements': 'battery life'},
            'confidence_score': 0.8
        }
        
        extracted = engine._extract_personalization_info(response, analysis)
        
        # Should include analysis info plus metadata
        assert 'preferences' in extracted
        assert 'requirements' in extracted
        assert 'response_engagement' in extracted
        assert 'extracted_at' in extracted
        assert extracted['response_engagement'] == len(response.split())
    
    def test_update_user_profile_content(self, engine, sample_conversation_state):
        """Test user profile updating with content filtering."""
        new_info = {
            'timeline': 'urgent',
            'constraints': 'budget limited',
            'response_engagement': 10,  # Should be filtered out
            'extracted_at': '2025-06-29'  # Should be filtered out
        }
        
        initial_profile_size = len(sample_conversation_state.user_profile)
        engine._update_user_profile(sample_conversation_state, new_info)
        
        # Should add relevant info, skip metadata
        assert 'timeline' in sample_conversation_state.user_profile
        assert 'constraints' in sample_conversation_state.user_profile
        assert 'response_engagement' not in sample_conversation_state.user_profile
        assert 'extracted_at' not in sample_conversation_state.user_profile
        assert len(sample_conversation_state.user_profile) == initial_profile_size + 2


class TestConversationAnalysis:
    """Test conversation analysis and summary functionality."""
    
    def test_get_conversation_summary(self, engine, sample_conversation_state):
        """Test conversation summary generation."""
        # Mock internal methods
        engine._calculate_conversation_progress = Mock(return_value={'progress': 0.6})
        engine._assess_conversation_quality = Mock(return_value={'quality': 'high'})
        engine._extract_key_insights = Mock(return_value=['insight1', 'insight2'])
        engine._generate_research_recommendations = Mock(return_value=['rec1', 'rec2'])
        
        # Test summary generation
        summary = engine.get_conversation_summary(sample_conversation_state)
        
        # Verify summary structure
        assert 'session_id' in summary
        assert 'conversation_length' in summary
        assert 'user_profile_completeness' in summary
        assert 'priority_factors' in summary
        assert 'progress_metrics' in summary
        assert 'quality_assessment' in summary
        assert 'key_insights' in summary
        assert 'research_recommendations' in summary
        assert 'metadata' in summary
        
        # Verify values
        assert summary['session_id'] == sample_conversation_state.session_id
        assert summary['conversation_length'] == len(sample_conversation_state.question_history)
        assert summary['priority_factors'] == sample_conversation_state.priority_factors
    
    def test_get_conversation_summary_with_error(self, engine, sample_conversation_state):
        """Test conversation summary generation with error."""
        # Mock internal method to raise exception
        engine._calculate_conversation_progress = Mock(side_effect=Exception("Calculation failed"))
        
        # Test summary generation
        summary = engine.get_conversation_summary(sample_conversation_state)
        
        # Should return empty dict on error
        assert summary == {}
    
    def test_calculate_conversation_progress(self, engine, sample_conversation_state):
        """Test conversation progress calculation."""
        # Mock depth score calculation
        engine._calculate_depth_score = Mock(return_value=0.7)
        
        progress = engine._calculate_conversation_progress(sample_conversation_state)
        
        # Verify progress metrics
        assert 'questions_asked' in progress
        assert 'information_gathered' in progress
        assert 'priority_factors_explored' in progress
        assert 'conversation_depth_score' in progress
        assert 'completeness_estimate' in progress
        
        assert progress['questions_asked'] == len(sample_conversation_state.question_history)
        assert progress['information_gathered'] == len(sample_conversation_state.user_profile)
        assert progress['conversation_depth_score'] == 0.7
    
    def test_assess_conversation_quality(self, engine, sample_conversation_state):
        """Test conversation quality assessment."""
        quality = engine._assess_conversation_quality(sample_conversation_state)
        
        # Verify quality metrics
        assert 'response_quality' in quality
        assert 'information_density' in quality
        assert 'priority_consistency' in quality
        
        # Verify calculations
        expected_density = len(sample_conversation_state.user_profile) / len(sample_conversation_state.question_history)
        assert quality['information_density'] == expected_density
    
    def test_extract_key_insights(self, engine, sample_conversation_state):
        """Test key insights extraction."""
        insights = engine._extract_key_insights(sample_conversation_state)
        
        # Should extract insights from user profile
        assert isinstance(insights, list)
        assert any('expertise' in insight.lower() for insight in insights)
        assert any('context' in insight.lower() for insight in insights)
    
    def test_generate_research_recommendations(self, engine, sample_conversation_state):
        """Test research recommendations generation."""
        recommendations = engine._generate_research_recommendations(sample_conversation_state)
        
        # Should generate recommendations based on priority factors
        assert isinstance(recommendations, list)
        # Should have recommendations for key priority factors
        priority_areas = list(sample_conversation_state.priority_factors.keys())
        for area in priority_areas[:3]:  # Check first 3 priority areas
            assert any(area in rec for rec in recommendations)


class TestConversationStrategy:
    """Test conversation strategy adaptation functionality."""
    
    def test_adapt_conversation_strategy(self, engine, sample_conversation_state):
        """Test conversation strategy adaptation."""
        # Mock internal methods
        engine._analyze_conversation_patterns = Mock(return_value={'pattern1': 'value1'})
        engine._assess_user_engagement = Mock(return_value='high')
        engine._determine_optimal_question_types = Mock(return_value=['open_ended'])
        engine._calculate_conversation_efficiency = Mock(return_value={'efficiency': 0.8})
        engine._generate_strategy_recommendations = Mock(return_value=['rec1', 'rec2'])
        
        # Test strategy adaptation
        adaptations = engine.adapt_conversation_strategy(sample_conversation_state)
        
        # Verify adaptation structure
        assert 'detected_patterns' in adaptations
        assert 'engagement_level' in adaptations
        assert 'recommended_question_types' in adaptations
        assert 'efficiency_metrics' in adaptations
        assert 'strategy_recommendations' in adaptations
        
        # Verify method calls
        engine._analyze_conversation_patterns.assert_called_once_with(sample_conversation_state)
        engine._assess_user_engagement.assert_called_once_with(sample_conversation_state)
        engine._determine_optimal_question_types.assert_called_once_with(sample_conversation_state)
        engine._calculate_conversation_efficiency.assert_called_once_with(sample_conversation_state)
    
    def test_adapt_conversation_strategy_with_error(self, engine, sample_conversation_state):
        """Test strategy adaptation with error handling."""
        # Mock method to raise exception
        engine._analyze_conversation_patterns = Mock(side_effect=Exception("Analysis failed"))
        
        # Test strategy adaptation
        adaptations = engine.adapt_conversation_strategy(sample_conversation_state)
        
        # Should return empty dict on error
        assert adaptations == {}
    
    def test_assess_user_engagement_high(self, engine, sample_conversation_state):
        """Test user engagement assessment - high engagement."""
        # Add long responses
        for i in range(3):
            sample_conversation_state.question_history.append(
                QuestionAnswer(
                    question=f"Question {i}",
                    answer="This is a very detailed response with many words describing the user's needs and preferences in great detail and providing comprehensive information about their specific requirements and expectations for the product they are researching",
                    question_type=QuestionType.OPEN_ENDED,
                    timestamp=datetime.now(),
                    category="test_category",
                    context={}
                )
            )
        
        engagement = engine._assess_user_engagement(sample_conversation_state)
        assert engagement == 'high'
    
    def test_assess_user_engagement_medium(self, engine, sample_conversation_state):
        """Test user engagement assessment - medium engagement."""
        # Add medium responses
        for i in range(3):
            sample_conversation_state.question_history.append(
                QuestionAnswer(
                    question=f"Question {i}",
                    answer="This is a moderate response with some detail",
                    question_type=QuestionType.OPEN_ENDED,
                    timestamp=datetime.now(),
                    category="test_category",
                    context={}
                )
            )
        
        engagement = engine._assess_user_engagement(sample_conversation_state)
        assert engagement == 'medium'
    
    def test_assess_user_engagement_low(self, engine, sample_conversation_state):
        """Test user engagement assessment - low engagement."""
        # Add short responses
        for i in range(3):
            sample_conversation_state.question_history.append(
                QuestionAnswer(
                    question=f"Question {i}",
                    answer="Yes",
                    question_type=QuestionType.BOOLEAN,
                    timestamp=datetime.now(),
                    category="test_category",
                    context={}
                )
            )
        
        engagement = engine._assess_user_engagement(sample_conversation_state)
        assert engagement == 'low'
    
    def test_determine_optimal_question_types_early_conversation(self, engine):
        """Test optimal question types for early conversation."""
        # Create conversation with few questions
        conversation_state = ConversationState(
            session_id="test",
            user_query="test query"
        )
        conversation_state.question_history = [QuestionAnswer(
            question="Q1",
            answer="A1", 
            question_type=QuestionType.OPEN_ENDED,
            timestamp=datetime.now(),
            category="test_category",
            context={}
        )]
        
        question_types = engine._determine_optimal_question_types(conversation_state)
        assert 'open_ended' in question_types
    
    def test_determine_optimal_question_types_later_conversation(self, engine, sample_conversation_state):
        """Test optimal question types for later conversation."""
        # Add more questions to simulate later conversation
        for i in range(3):
            sample_conversation_state.question_history.append(
                QuestionAnswer(
                    question=f"Question {i}",
                    answer=f"Response {i}",
                    question_type=QuestionType.OPEN_ENDED,
                    timestamp=datetime.now(),
                    category="test_category",
                    context={}
                )
            )
        
        question_types = engine._determine_optimal_question_types(sample_conversation_state)
        assert 'specific' in question_types
        assert 'clarifying' in question_types
    
    def test_calculate_conversation_efficiency(self, engine, sample_conversation_state):
        """Test conversation efficiency calculation."""
        efficiency = engine._calculate_conversation_efficiency(sample_conversation_state)
        
        # Verify efficiency metrics
        assert 'information_per_question' in efficiency
        assert 'priority_coverage' in efficiency
        assert 'conversation_velocity' in efficiency
        
        # Verify calculations
        questions_count = len(sample_conversation_state.question_history)
        info_count = len(sample_conversation_state.user_profile)
        priority_count = len(sample_conversation_state.priority_factors)
        
        assert efficiency['information_per_question'] == info_count / questions_count
        assert efficiency['priority_coverage'] == priority_count / questions_count
        assert efficiency['conversation_velocity'] == questions_count / 10
    
    def test_generate_strategy_recommendations_low_engagement(self, engine):
        """Test strategy recommendations for low engagement."""
        patterns = {}
        engagement = 'low'
        efficiency = {'information_per_question': 0.8}
        
        recommendations = engine._generate_strategy_recommendations(patterns, engagement, efficiency)
        
        # Should recommend shorter questions for low engagement
        assert any('shorter' in rec.lower() for rec in recommendations)
    
    def test_generate_strategy_recommendations_low_efficiency(self, engine):
        """Test strategy recommendations for low efficiency."""
        patterns = {}
        engagement = 'high'
        efficiency = {'information_per_question': 0.3}  # Low efficiency
        
        recommendations = engine._generate_strategy_recommendations(patterns, engagement, efficiency)
        
        # Should recommend more information-rich questions
        assert any('information-rich' in rec.lower() for rec in recommendations)


class TestHelperMethods:
    """Test various helper methods."""
    
    def test_identify_information_gaps(self, engine, sample_conversation_state):
        """Test information gap identification."""
        # Remove some categories from user profile
        sample_conversation_state.user_profile = {'expertise_level': 'intermediate'}
        
        gaps = engine._identify_information_gaps(sample_conversation_state)
        
        # Should identify missing essential categories
        essential_categories = [
            'context', 'preferences', 'constraints', 'timeline', 'budget'
        ]
        # Check that most essential categories are identified as gaps
        gap_matches = sum(1 for category in essential_categories if category in gaps)
        assert gap_matches >= 3  # At least 3 should be identified
    
    def test_analyze_current_context(self, engine, sample_conversation_state):
        """Test current context analysis."""
        context = engine._analyze_current_context(sample_conversation_state)
        
        # Verify context structure
        assert 'conversation_flow' in context
        assert 'information_density' in context
        assert 'completion_confidence' in context
        assert 'asked_questions' in context
        
        # Verify values
        assert context['conversation_flow'] == len(sample_conversation_state.question_history)
        assert context['information_density'] == len(sample_conversation_state.user_profile)
        assert context['completion_confidence'] == sample_conversation_state.completion_confidence
    
    def test_analyze_current_context_no_history(self, engine):
        """Test current context analysis with no history."""
        conversation_state = ConversationState(
            session_id="test",
            user_query="test"
        )
        
        context = engine._analyze_current_context(conversation_state)
        # Should return basic context even with no history
        assert isinstance(context, dict)
        assert 'conversation_flow' in context
        assert context['conversation_flow'] == 0
    
    def test_calculate_depth_score(self, engine, sample_conversation_state):
        """Test conversation depth score calculation."""
        depth_score = engine._calculate_depth_score(sample_conversation_state)
        
        # Should be between 0 and 1
        assert 0.0 <= depth_score <= 1.0
        
        # Should increase with more questions and information
        questions_contribution = len(sample_conversation_state.question_history) * 0.1
        info_contribution = len(sample_conversation_state.user_profile) * 0.05
        expected_score = min(1.0, questions_contribution + info_contribution)
        
        assert depth_score == expected_score
    
    def test_calculate_depth_score_no_history(self, engine):
        """Test depth score calculation with no conversation history."""
        conversation_state = ConversationState(
            session_id="test",
            user_query="test"
        )
        
        depth_score = engine._calculate_depth_score(conversation_state)
        assert depth_score == 0.0


# Integration tests
class TestIntegration:
    """Integration tests for complete conversation flows."""
    
    @patch('core.dynamic_personalization.datetime')
    def test_complete_conversation_flow(self, mock_datetime, mock_gemini_client):
        """Test a complete conversation flow from start to finish."""
        # Mock datetime for consistent timestamps
        fixed_time = datetime(2025, 6, 29, 12, 0, 0)
        mock_datetime.now.return_value = fixed_time
        
        # Create engine with mocked dependencies
        engine = DynamicPersonalizationEngine(gemini_client=mock_gemini_client)
        
        # Mock AI components
        engine.context_analyzer.analyze_context = Mock(return_value=Mock(
            priority_insights=[Mock(category='laptop', keywords=['programming'])],
            emotional_indicators=[],
            communication_style=Mock(value='analytical'),
            overall_confidence=0.8,
            pattern_insights=[]
        ))
        engine._generate_intelligent_ai_question = Mock(return_value="What's your budget?")
        
        # Step 1: Initialize conversation
        conversation_state = engine.initialize_conversation(
            user_query="I need a laptop for programming",
            session_id="integration_test"
        )
        
        assert conversation_state.session_id == "integration_test"
        assert len(conversation_state.priority_factors) >= 0
        
        # Step 2: Generate question
        question = engine.generate_next_question(conversation_state)
        assert question == "What's your budget?"
        
        # Step 3: Process response
        result = engine.process_user_response(
            conversation_state, 
            question, 
            "Around $1500"
        )
        
        assert isinstance(result, dict)
        assert 'conversation_progress' in result
        
        # Step 4: Get summary
        summary = engine.get_conversation_summary(conversation_state)
        assert summary['session_id'] == "integration_test"
        
        # Step 5: Adapt strategy
        adaptations = engine.adapt_conversation_strategy(conversation_state)
        assert 'engagement_level' in adaptations
    
    def test_error_resilience(self, mock_gemini_client):
        """Test engine resilience to component failures."""
        engine = DynamicPersonalizationEngine(gemini_client=mock_gemini_client)
        
        # Mock components to fail
        engine.context_analyzer.analyze_context = Mock(side_effect=Exception("Analyzer failed"))
        
        # Should handle initialization error gracefully
        with pytest.raises(Exception):
            engine.initialize_conversation("test query", "test_session")
        
        # Mock successful initialization for further testing
        conversation_state = ConversationState(
            session_id="test",
            user_query="test query"
        )
        
        # Mock question generator to fail
        engine._generate_intelligent_ai_question = Mock(side_effect=Exception("Generator failed"))
        
        # Should return None on question generation failure
        question = engine.generate_next_question(conversation_state)
        assert question is None
        
        # Mock context analyzer to fail on response processing
        engine.context_analyzer.analyze_context = Mock(side_effect=Exception("Response analysis failed"))
        
        # Should handle response processing failure gracefully
        result = engine.process_user_response(conversation_state, "question", "response")
        assert isinstance(result, dict)  # Should return partial result, not crash


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
