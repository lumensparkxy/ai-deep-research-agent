#!/usr/bin/env python3
"""
Test script to verify conversation handler fixes
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import Settings
from core.conversation import ConversationHandler
from core.conversation_mode_intelligence import ConversationMode, UserSignals, EngagementMetrics, UrgencyLevel, ComplexityPreference

def test_missing_methods():
    """Test that previously missing methods now exist and work."""
    
    # Initialize settings and conversation handler
    settings = Settings()
    handler = ConversationHandler(settings)
    
    # Test _get_mode_question_prefix
    try:
        prefix = handler._get_mode_question_prefix(ConversationMode.QUICK, 1, 3)
        print(f"✅ _get_mode_question_prefix works: {prefix}")
    except AttributeError as e:
        print(f"❌ _get_mode_question_prefix missing: {e}")
        return False
    
    # Test _get_mode_acknowledgment
    try:
        ack = handler._get_mode_acknowledgment(ConversationMode.STANDARD, 2)
        print(f"✅ _get_mode_acknowledgment works: {ack}")
    except AttributeError as e:
        print(f"❌ _get_mode_acknowledgment missing: {e}")
        return False
    
    # Test _determine_new_mode
    try:
        user_signals = UserSignals(
            urgency_level=UrgencyLevel.MEDIUM,
            complexity_preference=ComplexityPreference.BALANCED,
            context_type="test",
            language_indicators=["test"],
            engagement_score=0.7,
            patience_indicators=["moderate"]
        )
        
        engagement_metrics = EngagementMetrics(
            response_length_trend="stable",
            response_time_trend="normal",
            detail_request_frequency=1,
            impatience_indicators=[],
            interest_indicators=[]
        )
        
        new_mode = handler._determine_new_mode(ConversationMode.STANDARD, engagement_metrics, user_signals)
        print(f"✅ _determine_new_mode works: {new_mode}")
    except AttributeError as e:
        print(f"❌ _determine_new_mode missing: {e}")
        return False
    
    # Test _show_personalization_completion
    try:
        context = {
            'user_info': {'budget': '1000'},
            'preferences': {'type': 'laptop'},
            'constraints': {'timeline': 'soon'}
        }
        handler._show_personalization_completion(ConversationMode.STANDARD, 3, context)
        print("✅ _show_personalization_completion works")
    except AttributeError as e:
        print(f"❌ _show_personalization_completion missing: {e}")
        return False
    
    return True

def test_enum_parsing():
    """Test that enum parsing handles case sensitivity correctly."""
    
    # Test mode recommendation parsing
    from core.conversation_mode_intelligence import ConversationModeIntelligence
    
    try:
        # Mock gemini client for testing
        class MockClient:
            class Models:
                def generate_content(self, **kwargs):
                    class MockResponse:
                        text = "Some response"
                    return MockResponse()
            
            def __init__(self):
                self.models = self.Models()
        
        mock_client = MockClient()
        intelligence = ConversationModeIntelligence(mock_client)
        
        # Test with uppercase response (which was causing the error)
        response_text = """
        MODE: QUICK
        CONFIDENCE: 0.8
        REASONING: Fast response needed
        FALLBACK: STANDARD
        TRIGGERS: timeout,impatience
        """
        
        recommendation = intelligence._parse_mode_recommendation(response_text)
        print(f"✅ Mode parsing works with uppercase: {recommendation.recommended_mode}")
        
        # Test user signals parsing
        signals_text = """
        URGENCY: HIGH
        COMPLEXITY: SIMPLE
        CONTEXT: business
        LANGUAGE_INDICATORS: quick,fast
        ENGAGEMENT: 0.6
        PATIENCE: low
        """
        
        signals = intelligence._parse_user_signals_response(signals_text)
        print(f"✅ Signals parsing works with uppercase: {signals.urgency_level}")
        
        return True
        
    except Exception as e:
        print(f"❌ Enum parsing failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing conversation handler fixes...")
    print("=" * 50)
    
    success = True
    
    print("\n1. Testing missing methods...")
    if not test_missing_methods():
        success = False
    
    print("\n2. Testing enum parsing...")
    if not test_enum_parsing():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 All tests passed! The conversation handler fixes are working.")
    else:
        print("❌ Some tests failed. There may still be issues.")
