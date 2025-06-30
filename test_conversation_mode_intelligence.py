#!/usr/bin/env python3
"""
Test Conversation Mode Intelligence implementation.
Tests the AI-driven mode detection, adaptation, and user engagement monitoring.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from unittest.mock import Mock, patch
from core.conversation_mode_intelligence import (
    ConversationModeIntelligence,
    AdaptiveModeManager,
    ConversationMode,
    UrgencyLevel,
    ComplexityPreference,
    UserSignals,
    EngagementMetrics
)


class TestConversationModeIntelligence:
    """Test suite for Conversation Mode Intelligence."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_gemini_client = Mock()
        self.mode_intelligence = ConversationModeIntelligence(
            gemini_client=self.mock_gemini_client,
            model_name="gemini-1.5-flash"
        )
        self.adaptive_manager = AdaptiveModeManager(self.mode_intelligence)
    
    def test_mode_intelligence_initialization(self):
        """Test proper initialization of mode intelligence system."""
        assert self.mode_intelligence.gemini_client == self.mock_gemini_client
        assert self.mode_intelligence.model_name == "gemini-1.5-flash"
        assert len(self.mode_intelligence.mode_configs) == 4
        
        # Test mode configurations
        quick_config = self.mode_intelligence.mode_configs[ConversationMode.QUICK]
        assert quick_config.max_questions == 3
        assert quick_config.question_depth == "surface"
        
        deep_config = self.mode_intelligence.mode_configs[ConversationMode.DEEP]
        assert deep_config.max_questions == 12
        assert deep_config.question_depth == "comprehensive"
    
    def test_urgency_detection(self):
        """Test urgency level detection from user language."""
        # Mock Gemini response for high urgency
        mock_response = Mock()
        mock_response.text = "high"
        self.mock_gemini_client.models.generate_content.return_value = mock_response
        
        urgent_query = "I need the best laptop ASAP for my presentation tomorrow"
        urgency = self.mode_intelligence.detect_urgency_indicators(urgent_query)
        
        assert urgency == UrgencyLevel.HIGH
        assert self.mock_gemini_client.models.generate_content.called
    
    def test_user_signals_analysis(self):
        """Test comprehensive user signals analysis."""
        # Mock Gemini response
        mock_response = Mock()
        mock_response.text = """
        URGENCY: high
        COMPLEXITY: detailed
        CONTEXT: business
        LANGUAGE_INDICATORS: urgent, comprehensive, thorough
        ENGAGEMENT: 0.8
        PATIENCE: moderate, deadline-focused
        """
        self.mock_gemini_client.models.generate_content.return_value = mock_response
        
        query = "I need comprehensive market analysis for urgent business decision"
        signals = self.mode_intelligence.analyze_user_signals(query)
        
        assert signals.urgency_level == UrgencyLevel.HIGH
        assert signals.complexity_preference == ComplexityPreference.DETAILED
        assert signals.context_type == "business"
        assert signals.engagement_score == 0.8
    
    def test_mode_recommendation_logic(self):
        """Test AI-powered mode recommendation."""
        # Create test user signals
        signals = UserSignals(
            urgency_level=UrgencyLevel.HIGH,
            complexity_preference=ComplexityPreference.SIMPLE,
            context_type="personal",
            language_indicators=["quick", "fast"],
            engagement_score=0.7,
            patience_indicators=["impatient"]
        )
        
        # Mock Gemini response
        mock_response = Mock()
        mock_response.text = """
        MODE: quick
        CONFIDENCE: 0.9
        REASONING: High urgency and simple preference indicate quick mode
        FALLBACK: standard
        TRIGGERS: user_feedback, engagement_drop
        """
        self.mock_gemini_client.models.generate_content.return_value = mock_response
        
        recommendation = self.mode_intelligence.recommend_conversation_mode(signals)
        
        assert recommendation.recommended_mode == ConversationMode.QUICK
        assert recommendation.confidence_score == 0.9
        assert recommendation.fallback_mode == ConversationMode.STANDARD
    
    def test_mode_switching_logic(self):
        """Test dynamic mode switching based on engagement."""
        engagement_metrics = EngagementMetrics(
            response_length_trend="decreasing",
            response_time_trend="fast",
            detail_request_frequency=0,
            impatience_indicators=["quick", "fast"],
            interest_indicators=[]
        )
        
        # Mock Gemini response for mode switch decision
        mock_response = Mock()
        mock_response.text = "YES"
        self.mock_gemini_client.models.generate_content.return_value = mock_response
        
        should_switch = self.mode_intelligence.should_switch_mode(
            ConversationMode.DEEP, engagement_metrics, 5
        )
        
        assert should_switch is True
    
    def test_adaptive_manager_transitions(self):
        """Test adaptive mode manager transitions."""
        # Test transition from deep to quick mode
        transition = self.adaptive_manager.transition_between_modes(
            ConversationMode.DEEP,
            ConversationMode.QUICK,
            "User showing impatience"
        )
        
        assert transition.pace_adjustment == "accelerate"
        assert "quicker approach" in transition.transition_message.lower()
        assert self.adaptive_manager.current_mode == ConversationMode.QUICK
        assert len(self.adaptive_manager.mode_history) == 1
    
    def test_engagement_monitoring(self):
        """Test user engagement pattern monitoring."""
        user_responses = [
            "I need comprehensive analysis of all available options with detailed comparisons",  # Long
            "Tell me more about the specific features and capabilities",  # Medium  
            "Ok, sounds good"  # Short - clear decreasing trend
        ]
        
        engagement = self.adaptive_manager.monitor_engagement(user_responses)
        
        assert engagement.response_length_trend == "decreasing"
        assert engagement.detail_request_frequency >= 1  # "Tell me more"
        assert any("tell me more" in indicator for indicator in engagement.interest_indicators)
    
    def test_mode_specific_prompting(self):
        """Test mode-specific AI prompt generation."""
        context = {
            'user_query': 'Best smartphone for photography',
            'context_type': 'personal'
        }
        
        quick_prompt = self.mode_intelligence.create_mode_specific_prompt(
            ConversationMode.QUICK, context
        )
        deep_prompt = self.mode_intelligence.create_mode_specific_prompt(
            ConversationMode.DEEP, context
        )
        
        # Quick mode should focus on essentials
        assert "1-2 most critical" in quick_prompt or "concise" in quick_prompt
        assert "Maximum questions: 3" in quick_prompt
        
        # Deep mode should be comprehensive
        assert "comprehensive" in deep_prompt or "detailed" in deep_prompt
        assert "Maximum questions: 12" in deep_prompt
    
    def test_complexity_preference_assessment(self):
        """Test complexity preference detection from responses."""
        detailed_responses = [
            "Can you explain the technical specifications in detail?",
            "I want to understand all the pros and cons",
            "What about the long-term implications?"
        ]
        
        simple_responses = [
            "Just tell me the best one",
            "Quick answer please",
            "Yes or no?"
        ]
        
        # Mock responses
        self.mock_gemini_client.models.generate_content.side_effect = [
            Mock(text="detailed"),  # For detailed responses
            Mock(text="simple")     # For simple responses
        ]
        
        detailed_pref = self.mode_intelligence.assess_complexity_preference(detailed_responses)
        simple_pref = self.mode_intelligence.assess_complexity_preference(simple_responses)
        
        assert detailed_pref == ComplexityPreference.DETAILED
        assert simple_pref == ComplexityPreference.SIMPLE
    
    def test_error_handling_fallbacks(self):
        """Test error handling and fallback behaviors."""
        # Test with Gemini API error
        self.mock_gemini_client.models.generate_content.side_effect = Exception("API Error")
        
        # Should return default values on error
        signals = self.mode_intelligence.analyze_user_signals("test query")
        assert signals.urgency_level == UrgencyLevel.MEDIUM
        assert signals.complexity_preference == ComplexityPreference.BALANCED
        
        urgency = self.mode_intelligence.detect_urgency_indicators("test query")
        assert urgency == UrgencyLevel.MEDIUM


def test_conversation_mode_intelligence_integration():
    """Integration test for complete conversation mode intelligence system."""
    # Create mock Gemini client
    mock_client = Mock()
    
    # Mock signal analysis response
    signal_response = Mock()
    signal_response.text = """
    URGENCY: medium
    COMPLEXITY: balanced
    CONTEXT: technology
    LANGUAGE_INDICATORS: smartphone, photography, best
    ENGAGEMENT: 0.75
    PATIENCE: moderate, research-oriented
    """
    
    # Mock mode recommendation response
    recommendation_response = Mock()
    recommendation_response.text = """
    MODE: standard
    CONFIDENCE: 0.8
    REASONING: Balanced complexity and medium urgency suggest standard mode
    FALLBACK: quick
    TRIGGERS: impatience_detected, detail_requests
    """
    
    mock_client.models.generate_content.side_effect = [
        signal_response,
        recommendation_response
    ]
    
    # Initialize system
    mode_intelligence = ConversationModeIntelligence(mock_client)
    adaptive_manager = AdaptiveModeManager(mode_intelligence)
    
    # Test full workflow
    query = "What's the best smartphone for photography under $800?"
    
    # 1. Analyze user signals
    signals = mode_intelligence.analyze_user_signals(query)
    assert signals.context_type == "technology"
    assert signals.engagement_score == 0.75
    
    # 2. Get mode recommendation
    recommendation = mode_intelligence.recommend_conversation_mode(signals)
    assert recommendation.recommended_mode == ConversationMode.STANDARD
    assert recommendation.confidence_score == 0.8
    
    # 3. Set initial mode
    adaptive_manager.current_mode = recommendation.recommended_mode
    
    # 4. Test mode-specific prompting
    context = {'user_query': query, 'context_type': signals.context_type}
    prompt = mode_intelligence.create_mode_specific_prompt(
        recommendation.recommended_mode, context
    )
    assert "Maximum questions: 6" in prompt  # Standard mode config
    
    # 5. Test engagement monitoring and adaptation
    user_responses = ["I want quick recommendations", "Just the top 3 options"]
    engagement = adaptive_manager.monitor_engagement(user_responses)
    
    # Should detect preference for quicker responses
    assert "quick" in engagement.impatience_indicators
    
    print("✅ Conversation Mode Intelligence integration test passed!")


if __name__ == "__main__":
    # Run integration test
    test_conversation_mode_intelligence_integration()
    
    # Run individual tests
    test_instance = TestConversationModeIntelligence()
    test_instance.setup_method()
    
    print("🧪 Running Conversation Mode Intelligence tests...")
    
    try:
        test_instance.test_mode_intelligence_initialization()
        print("✅ Initialization test passed")
        
        test_instance.test_urgency_detection()
        print("✅ Urgency detection test passed")
        
        test_instance.test_user_signals_analysis()
        print("✅ User signals analysis test passed")
        
        test_instance.test_mode_recommendation_logic()
        print("✅ Mode recommendation test passed")
        
        test_instance.test_adaptive_manager_transitions()
        print("✅ Adaptive transitions test passed")
        
        test_instance.test_engagement_monitoring()
        print("✅ Engagement monitoring test passed")
        
        test_instance.test_mode_specific_prompting()
        print("✅ Mode-specific prompting test passed")
        
        test_instance.test_complexity_preference_assessment()
        print("✅ Complexity assessment test passed")
        
        test_instance.test_error_handling_fallbacks()
        print("✅ Error handling test passed")
        
        print("\n🎉 All Conversation Mode Intelligence tests passed!")
        print("📊 Task 2.3: Conversation Mode Intelligence - IMPLEMENTATION COMPLETE")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
