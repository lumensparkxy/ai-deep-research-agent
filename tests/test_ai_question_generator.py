"""
Tests for AI Question Generator Foundation
Comprehensive test suite for Gemini-powered question generation system.
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from typing import Dict, Any, List

from core.ai_question_generator import (
    AIQuestionGenerator,
    IntentAnalysis,
    IntentType,
    GeneratedQuestion,
    QuestionGenerationResult
)
from core.conversation_state import (
    ConversationState,
    QuestionAnswer,
    QuestionType,
    ConversationMode
)


class TestAIQuestionGenerator:
    """Test suite for AIQuestionGenerator class."""
    
    @pytest.fixture
    def mock_gemini_client(self):
        """Create a mock Gemini client."""
        client = Mock()
        mock_response = Mock()
        mock_response.text = '''
        {
            "primary_intent": "purchase",
            "confidence": 0.85,
            "context_keywords": ["laptop", "programming", "budget"],
            "domain": "technology",
            "urgency_level": 0.3,
            "specificity_level": 0.7,
            "reasoning": "User wants to purchase a laptop for programming"
        }
        '''
        client.generate_content.return_value = mock_response
        return client
    
    @pytest.fixture
    def mock_gemini_client_async(self):
        """Create an async mock Gemini client."""
        client = Mock()
        mock_response = Mock()
        mock_response.text = '''
        {
            "primary_intent": "purchase",
            "confidence": 0.85,
            "context_keywords": ["laptop", "programming", "budget"],
            "domain": "technology",
            "urgency_level": 0.3,
            "specificity_level": 0.7,
            "reasoning": "User wants to purchase a laptop for programming"
        }
        '''
        client.generate_content = AsyncMock(return_value=mock_response)
        return client
    
    @pytest.fixture
    def question_generator(self, mock_gemini_client):
        """Create AIQuestionGenerator instance with mock client."""
        return AIQuestionGenerator(gemini_client=mock_gemini_client)
    
    @pytest.fixture
    def question_generator_no_ai(self):
        """Create AIQuestionGenerator instance without AI client."""
        return AIQuestionGenerator(gemini_client=None)
    
    @pytest.fixture
    def sample_conversation_state(self):
        """Create sample conversation state for testing."""
        return ConversationState(
            session_id="test_session_123",
            user_query="What's the best laptop for programming?",
            user_profile={
                "context": "programming",
                "expertise": "intermediate"
            },
            question_history=[
                QuestionAnswer(
                    question="What's the best laptop for programming?",
                    answer="I need a laptop for software development",
                    question_type=QuestionType.OPEN_ENDED,
                    timestamp=datetime.now(),
                    category="initial_query"
                )
            ],
            information_gaps=["budget", "timeline"],
            conversation_mode=ConversationMode.STANDARD
        )
    
    @pytest.fixture
    def sample_intent_analysis(self):
        """Create sample intent analysis for testing."""
        return IntentAnalysis(
            primary_intent=IntentType.PURCHASE,
            confidence=0.85,
            context_keywords=["laptop", "programming", "budget"],
            domain="technology",
            urgency_level=0.3,
            specificity_level=0.7,
            reasoning="User wants to purchase a laptop for programming"
        )
    
    def test_initialization_with_gemini_client(self, mock_gemini_client):
        """Test AIQuestionGenerator initialization with Gemini client."""
        generator = AIQuestionGenerator(gemini_client=mock_gemini_client)
        
        assert generator.gemini_client == mock_gemini_client
        assert generator.max_questions_per_request == 5
        assert generator.min_question_priority == 0.3
        assert generator.api_retry_attempts == 3
        assert isinstance(generator._response_cache, dict)
    
    def test_initialization_without_gemini_client(self):
        """Test AIQuestionGenerator initialization without Gemini client."""
        generator = AIQuestionGenerator(gemini_client=None)
        
        assert generator.gemini_client is None
        assert generator.max_questions_per_request == 5
        assert generator.min_question_priority == 0.3
    
    @pytest.mark.asyncio
    async def test_generate_questions_with_ai(self, question_generator, sample_conversation_state):
        """Test question generation with AI client."""
        # Mock the question generation response
        question_generator.gemini_client.generate_content.side_effect = [
            # Intent analysis response
            Mock(text='''
            {
                "primary_intent": "purchase",
                "confidence": 0.85,
                "context_keywords": ["laptop", "programming"],
                "domain": "technology",
                "urgency_level": 0.3,
                "specificity_level": 0.7,
                "reasoning": "Purchase intent detected"
            }
            '''),
            # Question generation response
            Mock(text='''
            [
                {
                    "question": "What's your budget range?",
                    "question_type": "open_ended",
                    "category": "budget",
                    "priority": 0.9,
                    "context_relevance": 0.95,
                    "expected_answer_type": "text",
                    "follow_up_potential": 0.7,
                    "reasoning": "Budget is critical for recommendations"
                }
            ]
            ''')
        ]
        
        result = await question_generator.generate_questions(sample_conversation_state)
        
        assert isinstance(result, QuestionGenerationResult)
        assert len(result.questions) >= 1
        assert result.intent_analysis.primary_intent == IntentType.PURCHASE
        assert result.generation_confidence > 0.0
        assert isinstance(result.recommended_next_questions, list)
    
    @pytest.mark.asyncio
    async def test_generate_questions_without_ai(self, question_generator_no_ai, sample_conversation_state):
        """Test question generation without AI client (rule-based fallback)."""
        result = await question_generator_no_ai.generate_questions(sample_conversation_state)
        
        assert isinstance(result, QuestionGenerationResult)
        assert len(result.questions) >= 1
        assert result.intent_analysis.primary_intent in IntentType
        assert result.generation_confidence > 0.0
        
        # Check that questions are relevant
        question_categories = {q.category for q in result.questions}
        expected_categories = {"budget", "timeline", "preferences", "constraints"}
        assert len(question_categories.intersection(expected_categories)) > 0
    
    @pytest.mark.asyncio
    async def test_analyze_intent_with_ai(self, question_generator):
        """Test intent analysis with AI client."""
        user_query = "I need a laptop for programming under $1500"
        context = {"expertise": "intermediate"}
        
        result = await question_generator.analyze_intent(user_query, context)
        
        assert isinstance(result, IntentAnalysis)
        assert result.primary_intent == IntentType.PURCHASE
        assert 0.0 <= result.confidence <= 1.0
        assert isinstance(result.context_keywords, list)
        assert result.domain == "technology"
    
    @pytest.mark.asyncio
    async def test_analyze_intent_without_ai(self, question_generator_no_ai):
        """Test intent analysis without AI client (rule-based)."""
        user_query = "I want to buy a laptop for programming"
        
        result = await question_generator_no_ai.analyze_intent(user_query)
        
        assert isinstance(result, IntentAnalysis)
        assert result.primary_intent == IntentType.PURCHASE
        assert 0.0 <= result.confidence <= 1.0
        assert "laptop" in result.context_keywords or "programming" in result.context_keywords
    
    def test_generate_single_question(self, question_generator_no_ai):
        """Test single question generation."""
        category = "budget"
        context = {"domain": "technology", "intent": "purchase"}
        
        question = question_generator_no_ai.generate_single_question(
            category, context, QuestionType.OPEN_ENDED
        )
        
        assert isinstance(question, GeneratedQuestion)
        assert question.category == category
        assert question.question_type == QuestionType.OPEN_ENDED
        assert len(question.question) > 0
        assert 0.0 <= question.priority <= 1.0
    
    def test_intent_classification_rules(self, question_generator_no_ai):
        """Test rule-based intent classification for different query types."""
        test_cases = [
            ("I want to buy a laptop", IntentType.PURCHASE),
            ("How do I learn Python programming?", IntentType.LEARNING),
            ("Compare iPhone vs Android", IntentType.COMPARISON),
            ("Recommend the best smartphone", IntentType.RECOMMENDATION),
            ("My computer won't start properly", IntentType.TROUBLESHOOTING),  # Updated for clarity
            ("Research machine learning algorithms", IntentType.RESEARCH),
            ("Tell me about electric cars", IntentType.EXPLORATION)
        ]
        
        for query, expected_intent in test_cases:
            result = asyncio.run(question_generator_no_ai.analyze_intent(query))
            assert result.primary_intent == expected_intent
    
    def test_domain_classification(self, question_generator_no_ai):
        """Test domain classification for different query types."""
        test_cases = [
            ("laptop programming software", "technology"),
            ("health fitness diet exercise", "health"),
            ("investment budget financial planning", "finance"),
            ("learn study course education", "education"),
            ("travel vacation flight hotel", "travel"),
            ("home furniture kitchen appliance", "home"),
            ("random unrelated query", "general")
        ]
        
        for query, expected_domain in test_cases:
            domain = question_generator_no_ai._classify_domain(query)
            assert domain == expected_domain
    
    def test_question_prioritization(self, question_generator_no_ai, sample_conversation_state, sample_intent_analysis):
        """Test question prioritization logic."""
        questions = [
            GeneratedQuestion(
                question="What's your budget?",
                question_type=QuestionType.OPEN_ENDED,
                category="budget",
                priority=0.8,
                context_relevance=0.9,
                expected_answer_type="text",
                follow_up_potential=0.7,
                reasoning="Budget question"
            ),
            GeneratedQuestion(
                question="Any color preferences?",
                question_type=QuestionType.OPEN_ENDED,
                category="aesthetics",
                priority=0.3,
                context_relevance=0.4,
                expected_answer_type="text",
                follow_up_potential=0.2,
                reasoning="Aesthetic question"
            )
        ]
        
        prioritized = question_generator_no_ai._prioritize_questions(
            questions, sample_conversation_state, sample_intent_analysis
        )
        
        assert len(prioritized) == 2
        assert prioritized[0].category == "budget"  # Higher priority should be first
        assert prioritized[0].priority >= prioritized[1].priority
    
    def test_context_summary_extraction(self, question_generator_no_ai, sample_conversation_state):
        """Test conversation context summary extraction."""
        summary = question_generator_no_ai._extract_context_summary(sample_conversation_state)
        
        assert isinstance(summary, dict)
        assert "user_profile" in summary
        assert "information_gaps" in summary
        assert "priority_factors" in summary
        assert "conversation_mode" in summary
        assert "question_count" in summary
        
        assert summary["user_profile"] == sample_conversation_state.user_profile
        assert summary["conversation_mode"] == sample_conversation_state.conversation_mode.value
    
    def test_follow_up_recommendations(self, question_generator_no_ai, sample_conversation_state):
        """Test follow-up question recommendations."""
        questions = [
            GeneratedQuestion(
                question="What's your budget?",
                question_type=QuestionType.OPEN_ENDED,
                category="budget",
                priority=0.8,
                context_relevance=0.9,
                expected_answer_type="text",
                follow_up_potential=0.7,
                reasoning="Budget question"
            )
        ]
        
        recommendations = question_generator_no_ai._generate_follow_up_recommendations(
            questions, sample_conversation_state
        )
        
        assert isinstance(recommendations, list)
        assert len(recommendations) <= 3
        assert "budget" not in recommendations  # Already covered in questions
        
        # Should recommend missing important categories
        important_missing = {"timeline", "preferences", "constraints"}
        recommended_set = set(recommendations)
        assert len(recommended_set.intersection(important_missing)) > 0
    
    @pytest.mark.asyncio
    async def test_api_retry_logic(self, mock_gemini_client_async):
        """Test API retry logic on failures."""
        generator = AIQuestionGenerator(gemini_client=mock_gemini_client_async)
        
        # Mock failures then success
        mock_gemini_client_async.generate_content.side_effect = [
            Exception("API Error 1"),
            Exception("API Error 2"),
            Mock(text='{"test": "response"}')
        ]
        
        prompt = "test prompt"
        response = await generator._query_gemini_with_retry(prompt)
        
        assert response.text == '{"test": "response"}'
        assert mock_gemini_client_async.generate_content.call_count == 3
    
    @pytest.mark.asyncio
    async def test_api_retry_exhaustion(self, mock_gemini_client_async):
        """Test API retry logic when all attempts fail."""
        generator = AIQuestionGenerator(gemini_client=mock_gemini_client_async)
        
        # Mock all failures
        mock_gemini_client_async.generate_content.side_effect = Exception("Persistent API Error")
        
        prompt = "test prompt"
        with pytest.raises(Exception, match="Persistent API Error"):
            await generator._query_gemini_with_retry(prompt)
        
        assert mock_gemini_client_async.generate_content.call_count == generator.api_retry_attempts
    
    def test_cache_functionality(self, question_generator_no_ai):
        """Test response caching functionality."""
        generator = question_generator_no_ai
        
        # Test cache miss
        assert not generator._is_cache_valid("nonexistent_key")
        
        # Test cache set and hit
        test_data = {"test": "data"}
        generator._cache_response("test_key", test_data)
        
        assert generator._is_cache_valid("test_key")
        assert generator._response_cache["test_key"] == test_data
        
        # Test cache clear
        generator.clear_cache()
        assert not generator._is_cache_valid("test_key")
        assert len(generator._response_cache) == 0
    
    def test_intent_analysis_parsing(self, question_generator_no_ai):
        """Test parsing of AI intent analysis responses."""
        response_text = '''
        Some preamble text
        {
            "primary_intent": "learning",
            "confidence": 0.75,
            "context_keywords": ["python", "programming"],
            "domain": "technology",
            "urgency_level": 0.2,
            "specificity_level": 0.8,
            "reasoning": "User wants to learn programming"
        }
        Some trailing text
        '''
        
        result = question_generator_no_ai._parse_intent_response(response_text)
        
        assert isinstance(result, IntentAnalysis)
        assert result.primary_intent == IntentType.LEARNING
        assert result.confidence == 0.75
        assert "python" in result.context_keywords
        assert result.domain == "technology"
    
    def test_questions_parsing(self, question_generator_no_ai):
        """Test parsing of AI question generation responses."""
        response_text = '''
        Here are the generated questions:
        [
            {
                "question": "What's your programming experience?",
                "question_type": "open_ended",
                "category": "expertise",
                "priority": 0.9,
                "context_relevance": 0.85,
                "expected_answer_type": "text",
                "follow_up_potential": 0.8,
                "reasoning": "Important to understand skill level"
            },
            {
                "question": "Do you prefer Windows or Mac?",
                "question_type": "multiple_choice",
                "category": "preferences",
                "priority": 0.6,
                "context_relevance": 0.7,
                "expected_answer_type": "choice",
                "follow_up_potential": 0.4,
                "reasoning": "Operating system preference"
            }
        ]
        '''
        
        result = question_generator_no_ai._parse_questions_response(response_text)
        
        assert isinstance(result, list)
        assert len(result) == 2
        
        assert result[0].question == "What's your programming experience?"
        assert result[0].question_type == QuestionType.OPEN_ENDED
        assert result[0].category == "expertise"
        assert result[0].priority == 0.9
        
        assert result[1].question_type == QuestionType.MULTIPLE_CHOICE
        assert result[1].expected_answer_type == "choice"
    
    @pytest.mark.asyncio
    async def test_error_handling_fallback(self, mock_gemini_client):
        """Test error handling and fallback to rule-based generation."""
        # Mock Gemini client to raise exception
        mock_gemini_client.generate_content.side_effect = Exception("API Error")
        
        generator = AIQuestionGenerator(gemini_client=mock_gemini_client)
        conversation_state = ConversationState(
            session_id="test",
            user_query="I need help choosing a laptop"
        )
        
        result = await generator.generate_questions(conversation_state)
        
        # Should fallback gracefully
        assert isinstance(result, QuestionGenerationResult)
        assert len(result.questions) > 0
        assert result.generation_confidence >= 0.0
    
    def test_prompt_creation_intent_analysis(self, question_generator_no_ai):
        """Test creation of intent analysis prompts."""
        user_query = "I need a laptop for programming"
        context = {"budget": "$1500"}
        
        prompt = question_generator_no_ai._create_intent_analysis_prompt(user_query, context)
        
        assert user_query in prompt
        assert "$1500" in prompt
        assert "primary_intent" in prompt
        assert "confidence" in prompt
        assert "JSON" in prompt
    
    def test_prompt_creation_question_generation(self, question_generator_no_ai, sample_conversation_state, sample_intent_analysis):
        """Test creation of question generation prompts."""
        prompt = question_generator_no_ai._create_question_generation_prompt(
            sample_conversation_state,
            sample_intent_analysis,
            3,
            ["budget", "timeline"]
        )
        
        assert sample_conversation_state.user_query in prompt
        assert sample_intent_analysis.primary_intent.value in prompt
        assert "budget" in prompt
        assert "timeline" in prompt
        assert "JSON" in prompt
    
    def test_confidence_calculation(self, question_generator_no_ai, sample_conversation_state, sample_intent_analysis):
        """Test generation confidence calculation."""
        questions = [
            GeneratedQuestion(
                question="Test question",
                question_type=QuestionType.OPEN_ENDED,
                category="test",
                priority=0.8,
                context_relevance=0.9,
                expected_answer_type="text",
                follow_up_potential=0.7,
                reasoning="Test"
            )
        ]
        
        confidence = question_generator_no_ai._calculate_generation_confidence(
            questions, sample_intent_analysis, sample_conversation_state
        )
        
        assert 0.0 <= confidence <= 1.0
        assert confidence > 0.5  # Should be reasonably confident with good inputs
    
    def test_alignment_scoring(self, question_generator_no_ai, sample_intent_analysis):
        """Test intent alignment scoring for questions."""
        # Test purchase intent alignment
        budget_question = GeneratedQuestion(
            question="What's your budget?",
            question_type=QuestionType.OPEN_ENDED,
            category="budget",
            priority=0.8,
            context_relevance=0.9,
            expected_answer_type="text",
            follow_up_potential=0.7,
            reasoning="Budget question"
        )
        
        alignment = question_generator_no_ai._calculate_intent_alignment(
            budget_question, sample_intent_analysis
        )
        
        assert alignment >= 0.8  # Budget should align well with purchase intent
        
        # Test irrelevant question
        aesthetic_question = GeneratedQuestion(
            question="What's your favorite color?",
            question_type=QuestionType.OPEN_ENDED,
            category="aesthetics",
            priority=0.3,
            context_relevance=0.4,
            expected_answer_type="text",
            follow_up_potential=0.2,
            reasoning="Aesthetic question"
        )
        
        alignment = question_generator_no_ai._calculate_intent_alignment(
            aesthetic_question, sample_intent_analysis
        )
        
        assert alignment <= 0.6  # Aesthetics should align poorly with purchase intent


class TestIntentAnalysis:
    """Test suite for IntentAnalysis dataclass."""
    
    def test_intent_analysis_creation(self):
        """Test IntentAnalysis creation and properties."""
        intent = IntentAnalysis(
            primary_intent=IntentType.PURCHASE,
            confidence=0.85,
            context_keywords=["laptop", "programming"],
            domain="technology",
            urgency_level=0.3,
            specificity_level=0.7,
            reasoning="Purchase intent detected"
        )
        
        assert intent.primary_intent == IntentType.PURCHASE
        assert intent.confidence == 0.85
        assert intent.context_keywords == ["laptop", "programming"]
        assert intent.domain == "technology"
        assert intent.urgency_level == 0.3
        assert intent.specificity_level == 0.7


class TestGeneratedQuestion:
    """Test suite for GeneratedQuestion dataclass."""
    
    def test_generated_question_creation(self):
        """Test GeneratedQuestion creation and properties."""
        question = GeneratedQuestion(
            question="What's your budget range?",
            question_type=QuestionType.OPEN_ENDED,
            category="budget",
            priority=0.9,
            context_relevance=0.95,
            expected_answer_type="text",
            follow_up_potential=0.7,
            reasoning="Budget is critical for recommendations"
        )
        
        assert question.question == "What's your budget range?"
        assert question.question_type == QuestionType.OPEN_ENDED
        assert question.category == "budget"
        assert question.priority == 0.9
        assert question.context_relevance == 0.95
        assert question.expected_answer_type == "text"
        assert question.follow_up_potential == 0.7


class TestQuestionGenerationResult:
    """Test suite for QuestionGenerationResult dataclass."""
    
    def test_question_generation_result_creation(self):
        """Test QuestionGenerationResult creation and properties."""
        questions = [
            GeneratedQuestion(
                question="Test question",
                question_type=QuestionType.OPEN_ENDED,
                category="test",
                priority=0.8,
                context_relevance=0.9,
                expected_answer_type="text",
                follow_up_potential=0.7,
                reasoning="Test question"
            )
        ]
        
        intent = IntentAnalysis(
            primary_intent=IntentType.PURCHASE,
            confidence=0.85,
            context_keywords=["test"],
            domain="technology",
            urgency_level=0.3,
            specificity_level=0.7,
            reasoning="Test intent"
        )
        
        result = QuestionGenerationResult(
            questions=questions,
            intent_analysis=intent,
            conversation_context={"test": "context"},
            generation_confidence=0.8,
            recommended_next_questions=["budget", "timeline"]
        )
        
        assert len(result.questions) == 1
        assert result.intent_analysis.primary_intent == IntentType.PURCHASE
        assert result.conversation_context == {"test": "context"}
        assert result.generation_confidence == 0.8
        assert result.recommended_next_questions == ["budget", "timeline"]


class TestIntegrationScenarios:
    """Integration tests for real-world scenarios."""
    
    @pytest.mark.asyncio
    async def test_laptop_purchase_scenario(self):
        """Test complete question generation for laptop purchase scenario."""
        generator = AIQuestionGenerator(gemini_client=None)  # Use rule-based
        
        conversation_state = ConversationState(
            session_id="laptop_purchase_test",
            user_query="I need to buy a laptop for programming and gaming",
            user_profile={},
            conversation_mode=ConversationMode.STANDARD
        )
        
        result = await generator.generate_questions(conversation_state, max_questions=3)
        
        assert isinstance(result, QuestionGenerationResult)
        assert result.intent_analysis.primary_intent == IntentType.PURCHASE
        assert len(result.questions) <= 3
        
        # Should ask about budget, timeline, or preferences
        categories = {q.category for q in result.questions}
        expected = {"budget", "timeline", "preferences", "constraints"}
        assert len(categories.intersection(expected)) > 0
    
    @pytest.mark.asyncio
    async def test_learning_scenario(self):
        """Test question generation for learning scenario."""
        generator = AIQuestionGenerator(gemini_client=None)
        
        conversation_state = ConversationState(
            session_id="learning_test",
            user_query="How can I learn machine learning?",
            user_profile={"context": "learning"},
            conversation_mode=ConversationMode.DEEP
        )
        
        result = await generator.generate_questions(conversation_state, max_questions=4)
        
        assert result.intent_analysis.primary_intent == IntentType.LEARNING
        assert len(result.questions) <= 4
        
        # Should ask about experience, timeline, preferences
        categories = {q.category for q in result.questions}
        learning_relevant = {"expertise", "timeline", "preferences", "learning_style"}
        assert len(categories.intersection(learning_relevant)) > 0
    
    @pytest.mark.asyncio
    async def test_progressive_question_refinement(self):
        """Test how questions adapt as conversation progresses."""
        generator = AIQuestionGenerator(gemini_client=None)
        
        # Initial state - no information
        initial_state = ConversationState(
            session_id="progression_test",
            user_query="I want to buy a smartphone",
            user_profile={}
        )
        
        initial_result = await generator.generate_questions(initial_state, max_questions=2)
        initial_categories = {q.category for q in initial_result.questions}
        
        # Updated state - with some information
        updated_state = ConversationState(
            session_id="progression_test",
            user_query="I want to buy a smartphone",
            user_profile={
                "budget": "$800",
                "context": "personal use"
            },
            question_history=[
                QuestionAnswer(
                    question="What's your budget?",
                    answer="Around $800",
                    question_type=QuestionType.OPEN_ENDED,
                    timestamp=datetime.now(),
                    category="budget"
                )
            ]
        )
        
        updated_result = await generator.generate_questions(updated_state, max_questions=2)
        updated_categories = {q.category for q in updated_result.questions}
        
        # Should ask different questions now that budget is known
        assert "budget" not in updated_categories  # Already have budget info
        assert len(initial_categories.symmetric_difference(updated_categories)) > 0
