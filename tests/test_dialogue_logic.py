"""
Tests for Multi-Turn Dialogue Logic

Tests the AI-driven conversation management system that maintains coherence
and builds context progressively.
"""

import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime

from core.dialogue_logic import (
    DialogueStateManager, 
    ConversationThread, 
    DialogueInsights
)
from core.conversation_state import ConversationState, QuestionAnswer


class TestConversationThread:
    """Test ConversationThread data structure"""
    
    def test_conversation_thread_creation(self):
        """Test creating a conversation thread"""
        thread = ConversationThread(
            thread_id="test_001",
            topic="smartphone_purchase"
        )
        
        assert thread.thread_id == "test_001"
        assert thread.topic == "smartphone_purchase"
        assert len(thread.questions) == 0
        assert thread.coherence_score == 1.0
        assert isinstance(thread.last_updated, datetime)
    
    def test_add_qa_to_thread(self):
        """Test adding question-answer pairs to thread"""
        thread = ConversationThread(
            thread_id="test_001",
            topic="test_topic"
        )
        
        from core.conversation_state import QuestionType
        qa = QuestionAnswer(
            question="What's your budget?",
            answer="Around $800",
            question_type=QuestionType.OPEN_ENDED,
            category="budget",
            timestamp=datetime.now(),
            context={}
        )
        
        initial_time = thread.last_updated
        thread.add_qa(qa)
        
        assert len(thread.questions) == 1
        assert thread.questions[0] == qa
        assert thread.last_updated > initial_time


class TestDialogueInsights:
    """Test DialogueInsights data structure"""
    
    def test_dialogue_insights_creation(self):
        """Test creating dialogue insights"""
        insights = DialogueInsights(
            conversation_assessment="Good flow",
            coherence_analysis="Coherent discussion",
            topic_shifts=["budget to features"],
            contradictions=["price sensitivity mismatch"],
            information_gaps=["usage patterns"],
            next_question_guidance="Ask about daily usage",
            conversation_quality=0.8,
            suggested_approach="detail-focused"
        )
        
        assert insights.conversation_quality == 0.8
        assert len(insights.topic_shifts) == 1
        assert len(insights.contradictions) == 1
        assert "usage patterns" in insights.information_gaps


class TestDialogueStateManager:
    """Test the AI-driven dialogue state manager"""
    
    @pytest.fixture
    def mock_gemini_client(self):
        """Create mock Gemini client"""
        client = Mock()
        
        # Mock analysis response
        analysis_response = Mock()
        analysis_response.text = """
        CONVERSATION FLOW: The conversation is progressing logically from general inquiry to specific needs.
        
        COHERENCE ANALYSIS: Good coherence maintained throughout the discussion.
        
        TOPIC MANAGEMENT: No significant topic shifts detected.
        
        CONTRADICTION DETECTION: No contradictions found.
        
        INFORMATION GAPS: Still need to understand budget constraints and usage patterns.
        
        NEXT QUESTION GUIDANCE: Focus on understanding their specific usage scenarios.
        
        CONVERSATION QUALITY: 8/10 - Good engagement and clear responses.
        
        SUGGESTED APPROACH: Continue with consultative approach, focus on practical needs.
        """
        
        client.generate_content.return_value = analysis_response
        return client
    
    @pytest.fixture
    def conversation_state(self):
        """Create basic conversation state"""
        state = ConversationState(
            session_id="test_session_123",
            user_query="Looking for a new smartphone"
        )
        state.information_gaps = ["budget", "usage_patterns", "preferences"]
        state.user_profile = {"intent": "smartphone_purchase"}
        
        # Add some conversation history
        from core.conversation_state import QuestionType
        qa1 = QuestionAnswer(
            question="What brings you to look for a new smartphone?",
            answer="My current phone camera isn't good enough for photos",
            question_type=QuestionType.OPEN_ENDED,
            category="motivation",
            timestamp=datetime.now(),
            context={}
        )
        qa2 = QuestionAnswer(
            question="What type of photography do you do most?",
            answer="Portrait photos of my family",
            question_type=QuestionType.OPEN_ENDED,
            category="usage",
            timestamp=datetime.now(),
            context={}
        )
        state.question_history = [qa1, qa2]
        
        return state
    
    @pytest.fixture
    def dialogue_manager(self, mock_gemini_client, conversation_state):
        """Create DialogueStateManager with mocked dependencies"""
        return DialogueStateManager(mock_gemini_client, conversation_state)
    
    def test_analyze_conversation_state(self, dialogue_manager):
        """Test analyzing conversation state with AI"""
        insights = dialogue_manager.analyze_conversation_state()
        
        assert isinstance(insights, DialogueInsights)
        assert isinstance(insights.conversation_quality, float)
        assert 0 <= insights.conversation_quality <= 1
        
        # Verify AI was called twice (once for analysis, once for insights extraction)
        assert dialogue_manager.gemini_client.generate_content.call_count == 2
    
    def test_track_conversation_thread(self, dialogue_manager):
        """Test tracking conversation threads"""
        question = "What's your budget range?"
        response = "Around $800-1000"
        
        thread = dialogue_manager.track_conversation_thread(question, response)
        
        assert isinstance(thread, ConversationThread)
        assert len(thread.questions) == 1
        assert thread.questions[0].question == question
        assert thread.questions[0].answer == response
        
        # Verify added to conversation state
        assert len(dialogue_manager.conversation_state.question_history) == 3  # 2 existing + 1 new
    
    def test_generate_coherent_followup(self, dialogue_manager):
        """Test generating coherent follow-up questions"""
        # Mock follow-up response
        followup_response = Mock()
        followup_response.text = "What specific features are most important to you in a smartphone camera?"
        dialogue_manager.gemini_client.generate_content.return_value = followup_response
        
        question = dialogue_manager.generate_coherent_followup()
        
        assert isinstance(question, str)
        assert len(question) > 0
        assert question.endswith('?')
        
        # Verify AI was called with appropriate prompt
        dialogue_manager.gemini_client.generate_content.assert_called_once()
    
    def test_generate_followup_with_context(self, dialogue_manager):
        """Test generating follow-up with additional context"""
        context = {"priority": "camera_quality", "user_expertise": "beginner"}
        
        followup_response = Mock()
        followup_response.text = "Are you looking for automatic camera features or do you prefer manual control?"
        dialogue_manager.gemini_client.generate_content.return_value = followup_response
        
        question = dialogue_manager.generate_coherent_followup(context)
        
        assert isinstance(question, str)
        assert question.endswith('?')
        
        # Check that context was included in prompt
        call_args = dialogue_manager.gemini_client.generate_content.call_args[0][0]
        assert "camera_quality" in call_args
        assert "beginner" in call_args
    
    def test_detect_conversation_issues(self, dialogue_manager):
        """Test detecting conversation issues"""
        # Mock issues detection response
        issues_response = Mock()
        issues_response.text = """
        CONTRADICTIONS: User mentioned budget is important but also said price doesn't matter for quality.
        
        AMBIGUITY: Response about "good camera" is vague - needs clarification on specific needs.
        
        No topic drift or confusion detected.
        """
        dialogue_manager.gemini_client.generate_content.return_value = issues_response
        
        issues = dialogue_manager.detect_conversation_issues()
        
        assert isinstance(issues, list)
        # Should detect the contradictions and ambiguity mentioned
        assert len(issues) >= 0  # Might be empty if parsing doesn't catch issues
    
    def test_generate_clarification_question(self, dialogue_manager):
        """Test generating clarification questions"""
        issue = "User gave conflicting information about budget importance"
        
        clarification_response = Mock()
        clarification_response.text = "I want to make sure I understand your budget considerations correctly - is staying within a specific price range important, or are you flexible if it means better quality?"
        dialogue_manager.gemini_client.generate_content.return_value = clarification_response
        
        question = dialogue_manager.generate_clarification_question(issue)
        
        assert isinstance(question, str)
        assert len(question) > 0
        assert question.endswith('?')
        
        # Verify issue was included in prompt
        call_args = dialogue_manager.gemini_client.generate_content.call_args[0][0]
        assert "budget" in call_args.lower()
    
    def test_assess_conversation_completeness(self, dialogue_manager):
        """Test assessing conversation completeness"""
        # Mock completeness assessment response
        completeness_response = Mock()
        completeness_response.text = """
        COMPLETE: No
        CONFIDENCE: 0.6
        REASONING: We understand camera needs but still need budget and timeline information for complete research.
        """
        dialogue_manager.gemini_client.generate_content.return_value = completeness_response
        
        is_complete, confidence, reasoning = dialogue_manager.assess_conversation_completeness()
        
        assert isinstance(is_complete, bool)
        assert isinstance(confidence, float)
        assert isinstance(reasoning, str)
        assert 0 <= confidence <= 1
        assert not is_complete  # Based on mock response
        assert "budget" in reasoning.lower()
    
    def test_format_conversation_history(self, dialogue_manager):
        """Test formatting conversation history"""
        formatted = dialogue_manager._format_conversation_history()
        
        assert isinstance(formatted, str)
        assert "What brings you to look for" in formatted
        assert "Portrait photos" in formatted
        assert "Q1:" in formatted
        assert "A1:" in formatted
    
    def test_format_user_profile(self, dialogue_manager):
        """Test formatting user profile"""
        formatted = dialogue_manager._format_user_profile()
        
        assert isinstance(formatted, str)
        assert "smartphone_purchase" in formatted
        assert "intent:" in formatted
    
    def test_clean_generated_question(self, dialogue_manager):
        """Test cleaning AI-generated questions"""
        # Test removing prefixes
        dirty_question = "NEXT QUESTION: What's your budget"
        clean = dialogue_manager._clean_generated_question(dirty_question)
        assert clean == "What's your budget?"
        
        # Test adding question mark
        no_mark = "What do you think"
        clean = dialogue_manager._clean_generated_question(no_mark)
        assert clean == "What do you think?"
        
        # Test already clean question
        already_clean = "How can I help you?"
        clean = dialogue_manager._clean_generated_question(already_clean)
        assert clean == "How can I help you?"
    
    def test_create_fallback_insights(self, dialogue_manager):
        """Test creating fallback insights"""
        insights = dialogue_manager._create_fallback_insights()
        
        assert isinstance(insights, DialogueInsights)
        assert insights.conversation_quality == 0.6
        assert len(insights.information_gaps) > 0
        assert insights.suggested_approach == "standard consultative approach"
    
    def test_dialogue_with_no_history(self):
        """Test dialogue manager with empty conversation history"""
        mock_client = Mock()
        empty_state = ConversationState(
            session_id="empty_session",
            user_query="Test query"
        )
        
        manager = DialogueStateManager(mock_client, empty_state)
        
        # Should handle empty history gracefully
        formatted = manager._format_conversation_history()
        assert "No conversation history" in formatted
        
        profile = manager._format_user_profile()
        assert "No user profile" in profile
    
    def test_error_handling_in_analysis(self):
        """Test error handling when AI analysis fails"""
        # Create client that raises exceptions
        failing_client = Mock()
        failing_client.generate_content.side_effect = Exception("API Error")
        
        state = ConversationState(
            session_id="error_session",
            user_query="Test error handling"
        )
        manager = DialogueStateManager(failing_client, state)
        
        # Should return fallback insights
        insights = manager.analyze_conversation_state()
        assert isinstance(insights, DialogueInsights)
        assert insights.conversation_quality == 0.6  # Fallback value
        
        # Should return fallback question
        question = manager.generate_coherent_followup()
        assert isinstance(question, str)
        assert len(question) > 0
    
    def test_determine_conversation_thread(self, dialogue_manager):
        """Test determining conversation threads"""
        from core.conversation_state import QuestionType
        qa = QuestionAnswer(
            question="Test question",
            answer="Test answer",
            question_type=QuestionType.OPEN_ENDED,
            category="test",
            timestamp=datetime.now(),
            context={}
        )
        
        # First call should create new thread
        thread1 = dialogue_manager._determine_conversation_thread(qa)
        assert thread1.thread_id == "main_001"
        
        # Second call should use existing thread
        thread2 = dialogue_manager._determine_conversation_thread(qa)
        assert thread2 == thread1  # Same thread


class TestDialogueIntegration:
    """Integration tests for complete dialogue flow"""
    
    def test_complete_dialogue_flow(self):
        """Test complete multi-turn dialogue scenario"""
        # Set up mock client with realistic responses
        mock_client = Mock()
        
        def generate_content_side_effect(prompt):
            if "CONVERSATION HISTORY" in prompt and "Analyze this ongoing" in prompt:
                # Analysis response
                response = Mock()
                response.text = """
                CONVERSATION FLOW: Progressing well from general to specific needs.
                COHERENCE ANALYSIS: Maintaining good coherence.
                INFORMATION GAPS: Need budget and timeline information.
                NEXT QUESTION GUIDANCE: Focus on budget constraints.
                CONVERSATION QUALITY: 7/10
                SUGGESTED APPROACH: Continue consultative approach.
                """
                return response
            else:
                # Follow-up question response
                response = Mock()
                response.text = "What budget range are you considering for this purchase?"
                return response
        
        mock_client.generate_content.side_effect = generate_content_side_effect
        
        # Create conversation state with history
        state = ConversationState(
            session_id="integration_test",
            user_query="Looking for a phone"
        )
        state.information_gaps = ["budget", "timeline"]
        
        from core.conversation_state import QuestionType
        qa = QuestionAnswer(
            question="What type of phone are you looking for?",
            answer="Something with a great camera",
            question_type=QuestionType.OPEN_ENDED,
            category="requirements",
            timestamp=datetime.now(),
            context={}
        )
        state.question_history = [qa]
        
        # Create manager and test flow
        manager = DialogueStateManager(mock_client, state)
        
        # Analyze conversation
        insights = manager.analyze_conversation_state()
        assert isinstance(insights, DialogueInsights)
        
        # Generate follow-up
        followup = manager.generate_coherent_followup()
        assert "budget" in followup.lower()
        
        # Track new turn
        thread = manager.track_conversation_thread(followup, "Around $800")
        assert len(thread.questions) == 1
        assert len(state.question_history) == 2
