#!/usr/bin/env python3
"""
Test script to validate the new dynamic gap identification system without predefined categories.
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from core.completion_assessment import CompletionAssessment, InformationGap
from core.conversation_state import ConversationState


def test_dynamic_gap_identification():
    """Test the new AI-driven gap identification."""
    print("🧪 Testing Dynamic Gap Identification System")
    print("=" * 60)
    
    # Initialize completion assessment
    completion_assessment = CompletionAssessment()
    
    # Test cases with different query types
    test_cases = [
        {
            'name': 'Software Purchase Decision',
            'query': 'I need to find the best project management software for my team',
            'gathered_info': {}
        },
        {
            'name': 'Learning Query',
            'query': 'I want to learn Python programming as a complete beginner',
            'gathered_info': {}
        },
        {
            'name': 'Budget-Conscious Purchase',
            'query': 'Looking for an affordable laptop for college work under $800',
            'gathered_info': {'rough_budget': 'under $800', 'use_case': 'college work'}
        },
        {
            'name': 'Urgent Decision',
            'query': 'Need to urgently choose a cloud hosting service for our app launch',
            'gathered_info': {'timeline': 'urgent - app launch soon'}
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        print(f"Query: {test_case['query']}")
        print(f"Existing Info: {test_case['gathered_info']}")
        
        # Test the new dynamic approach
        try:
            missing_categories = completion_assessment._analyze_natural_gaps(
                test_case['query'], 
                test_case['gathered_info']
            )
            
            print(f"🔍 Identified Gaps: {missing_categories}")
            
            # Test rule-based fallback
            rule_gaps = completion_assessment._identify_gaps_rule_based(
                test_case['query'],
                test_case['gathered_info']
            )
            
            print(f"📋 Rule-based Gaps: {[gap.category for gap in rule_gaps]}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("-" * 40)


def test_conversation_state_gaps():
    """Test gap identification with conversation state."""
    print("\n🔄 Testing Conversation State Gap Analysis")
    print("=" * 60)
    
    # Create a sample conversation state
    conversation_state = ConversationState(
        session_id="test_session",
        user_query="I want to buy a camera for travel photography",
        user_profile={
            'travel_focus': 'yes - mainly landscapes and street photography',
            'experience_level': 'intermediate photographer'
        }
    )
    
    conversation_state.question_history = [
        ("What type of photography interests you most?", "Travel photography, especially landscapes"),
        ("What's your experience level?", "I've been doing photography for about 2 years")
    ]
    
    print(f"Query: {conversation_state.user_query}")
    print(f"Profile: {conversation_state.user_profile}")
    print(f"Questions Asked: {len(conversation_state.question_history)}")
    
    # Test the completion assessment
    completion_assessment = CompletionAssessment()
    
    try:
        # Test missing categories identification
        missing = completion_assessment._analyze_natural_gaps(
            conversation_state.user_query,
            conversation_state.user_profile
        )
        
        print(f"\n🔍 Dynamic Gaps Identified: {missing}")
        
    except Exception as e:
        print(f"❌ Error in gap analysis: {e}")


def test_priority_based_gaps():
    """Test how gaps are identified based on detected priorities."""
    print("\n⭐ Testing Priority-Based Gap Detection")
    print("=" * 60)
    
    test_scenarios = [
        {
            'query': 'Looking for budget-friendly options under $500',
            'profile': {},
            'expected_themes': ['financial_aspects']
        },
        {
            'query': 'Need expert-level tools for professional work',
            'profile': {'budget': 'no strict limit'},
            'expected_themes': ['quality_expectations', 'expertise_context']
        },
        {
            'query': 'Quick decision needed for urgent project deadline',
            'profile': {'context': 'work project'},
            'expected_themes': ['temporal_constraints']
        }
    ]
    
    completion_assessment = CompletionAssessment()
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n{i}. Query: {scenario['query']}")
        print(f"   Profile: {scenario['profile']}")
        
        try:
            gaps = completion_assessment._analyze_natural_gaps(
                scenario['query'],
                scenario['profile']
            )
            
            print(f"   🎯 Identified Gaps: {gaps}")
            print(f"   📊 Expected Themes: {scenario['expected_themes']}")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")


if __name__ == "__main__":
    print("🚀 Dynamic Gap Identification Test Suite")
    print("Testing elimination of predefined categories\n")
    
    test_dynamic_gap_identification()
    test_conversation_state_gaps()
    test_priority_based_gaps()
    
    print("\n✅ Test suite completed!")
    print("\nKey improvements:")
    print("• Eliminated hardcoded category mappings")
    print("• AI discovers gaps contextually")
    print("• Categories emerge from actual conversation content")
    print("• More specific and relevant gap identification")
