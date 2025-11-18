#!/usr/bin/env python3
"""
Quick test to verify that the fallback question improvements work correctly.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.conversation_state import ConversationState
from core.dynamic_personalization import DynamicPersonalizationEngine
from unittest.mock import Mock

def test_fallback_questions():
    """Test that fallback questions are now more diverse and context-aware."""
    
    # Create a mock question generator (simulating AI failure scenario)
    mock_question_generator = Mock()
    mock_question_generator.gemini_client = None  # Simulate no AI available
    
    # Create personalization engine
    engine = DynamicPersonalizationEngine(mock_question_generator)
    
    # Test different query types
    test_cases = [
        {
            'query': 'Best smartphone for photography',
            'asked_questions': []
        },
        {
            'query': 'Best smartphone for photography', 
            'asked_questions': ['What features matter most for your specific needs?']
        },
        {
            'query': 'How to learn Python programming',
            'asked_questions': []
        },
        {
            'query': 'Investment advice for retirement',
            'asked_questions': []
        },
        {
            'query': 'Travel recommendations for Europe',
            'asked_questions': []
        }
    ]
    
    print("Testing fallback question diversity...")
    print("=" * 50)
    
    for i, test_case in enumerate(test_cases):
        print(f"\nTest Case {i+1}:")
        print(f"Query: {test_case['query']}")
        print(f"Asked: {test_case['asked_questions']}")
        
        # Create conversation state
        conversation_state = ConversationState(
            session_id=f"test_{i}",
            user_query=test_case['query']
        )
        
        # Generate fallback question
        fallback_question = engine._generate_simple_fallback_question(
            conversation_state, 
            test_case['asked_questions']
        )
        
        print(f"Fallback: {fallback_question}")
        
        # Check if it's the old generic question
        if "most important" in fallback_question.lower():
            print("⚠️  WARNING: Still using generic 'most important' question!")
        else:
            print("✅ Good: Using context-aware fallback")
    
    print("\n" + "=" * 50)
    
    # Test similarity detection
    print("\nTesting question similarity detection...")
    
    similar_questions = [
        "What's most important to you in making this decision?",
        "What matters most in your choice?",
        "What are your key priorities for this decision?",
        "What features are most important to you?"
    ]
    
    for question in similar_questions:
        is_similar = engine._is_similar_question(
            question, 
            ["What's most important to you in making this decision?"]
        )
        print(f"'{question}' -> Similar: {is_similar}")
        
if __name__ == "__main__":
    test_fallback_questions()
