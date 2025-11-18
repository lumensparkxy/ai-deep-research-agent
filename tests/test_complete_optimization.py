#!/usr/bin/env python3
"""
Test the complete optimization: concise prompts + context-aware similarity detection.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.dynamic_personalization import DynamicPersonalizationEngine
from core.conversation_state import ConversationState, QuestionAnswer, QuestionType
from datetime import datetime

def test_complete_optimization():
    """Test the complete optimization for the 3rd-4th question problem."""
    
    # Create engine instance
    engine = DynamicPersonalizationEngine()
    
    # Create a conversation state similar to the problematic scenario
    conversation_state = ConversationState(
        user_query="I need help choosing a smartphone for photography",
        session_id="test_session"
    )
    
    # Helper function to create QuestionAnswer
    def create_qa(question, answer, category):
        return QuestionAnswer(
            question=question,
            answer=answer,
            question_type=QuestionType.OPEN_ENDED,
            timestamp=datetime.now(),
            category=category
        )
    
    print("=== COMPLETE OPTIMIZATION TEST ===")
    print("Testing the problematic 3rd-4th question scenario...\n")
    
    # Simulate the progression to the problematic area
    scenarios = [
        # After Question 2 - Setup
        {
            "step": "After Question 2",
            "qa_history": [
                create_qa(
                    "What's your budget range for this smartphone?",
                    "I'm looking at around $800-1200, but could stretch a bit for the right features",
                    "budget"
                ),
                create_qa(
                    "What type of photography do you enjoy most?",
                    "I love taking portraits of my family and friends, especially candid shots during gatherings",
                    "photography_preferences"
                )
            ],
            "user_profile": {
                "budget": "$800-1200",
                "budget_flexibility": "some flexibility for right features",
                "photography_type": "portraits, family photos",
                "photography_style": "candid shots during gatherings"
            },
            "asked_questions": [
                "What's your budget range for this smartphone?",
                "What type of photography do you enjoy most?"
            ]
        },
        # After Question 3 - Problematic area begins
        {
            "step": "After Question 3",
            "qa_history": [
                create_qa("What's your budget range for this smartphone?", "I'm looking at around $800-1200, but could stretch a bit for the right features", "budget"),
                create_qa("What type of photography do you enjoy most?", "I love taking portraits of my family and friends, especially candid shots during gatherings", "photography_preferences"),
                create_qa("How important is having the latest camera technology versus proven reliability?", "I prefer proven reliability. I don't need cutting edge, just something that consistently takes great photos", "technology_preference")
            ],
            "user_profile": {
                "budget": "$800-1200",
                "budget_flexibility": "some flexibility for right features",
                "photography_type": "portraits, family photos", 
                "photography_style": "candid shots during gatherings",
                "technology_preference": "proven reliability over cutting edge",
                "reliability_priority": "consistent great photos"
            },
            "asked_questions": [
                "What's your budget range for this smartphone?",
                "What type of photography do you enjoy most?",
                "How important is having the latest camera technology versus proven reliability?"
            ]
        },
        # After Question 4 - Peak problematic area
        {
            "step": "After Question 4",
            "qa_history": [
                create_qa("What's your budget range for this smartphone?", "I'm looking at around $800-1200, but could stretch a bit for the right features", "budget"),
                create_qa("What type of photography do you enjoy most?", "I love taking portraits of my family and friends, especially candid shots during gatherings", "photography_preferences"),
                create_qa("How important is having the latest camera technology versus proven reliability?", "I prefer proven reliability. I don't need cutting edge, just something that consistently takes great photos", "technology_preference"),
                create_qa("What's your current phone, and what specific camera issues are you hoping to improve?", "I have an iPhone 12, but the low-light performance isn't great and sometimes the portraits are blurry", "current_device")
            ],
            "user_profile": {
                "budget": "$800-1200",
                "budget_flexibility": "some flexibility for right features",
                "photography_type": "portraits, family photos",
                "photography_style": "candid shots during gatherings", 
                "technology_preference": "proven reliability over cutting edge",
                "reliability_priority": "consistent great photos",
                "current_device": "iPhone 12",
                "improvement_needs": "better low-light performance, sharper portraits"
            },
            "asked_questions": [
                "What's your budget range for this smartphone?",
                "What type of photography do you enjoy most?",
                "How important is having the latest camera technology versus proven reliability?",
                "What's your current phone, and what specific camera issues are you hoping to improve?"
            ]
        }
    ]
    
    for scenario in scenarios:
        print(f"=== {scenario['step'].upper()} ===")
        
        # Set up conversation state
        conversation_state.question_history = scenario["qa_history"]
        conversation_state.user_profile = scenario["user_profile"]
        
        questions_count = len(scenario["qa_history"])
        print(f"Questions asked so far: {questions_count}")
        
        # Test prompt optimization
        if questions_count >= 2:
            prompt = engine._create_concise_intelligent_ai_prompt(conversation_state, scenario["asked_questions"])
            prompt_type = "OPTIMIZED CONCISE"
        else:
            prompt = engine._create_intelligent_ai_prompt(conversation_state, scenario["asked_questions"])
            prompt_type = "STANDARD FULL"
        
        print(f"Prompt type: {prompt_type}")
        print(f"Prompt length: {len(prompt):,} characters (~{len(prompt) // 4:,} tokens)")
        
        # Show the prompt for context
        print(f"Generated prompt:\n{prompt}\n")
        
        # Test similarity detection on various potential questions
        test_questions = [
            "What features are most important to you in a smartphone camera?",
            "How do you typically share your photos?", 
            "What matters most to you - image quality, convenience, or specific features?",
            "What's your experience level with smartphone photography?",
            "Are there any specific camera features you absolutely need?",
            "How important is video recording capability for you?",
            "What would make you feel confident about your smartphone choice?"
        ]
        
        print("Testing similarity detection:")
        for test_q in test_questions:
            # Use both old and new similarity detection
            old_similar = engine._is_similar_question(test_q, scenario["asked_questions"])
            new_similar = engine._is_similar_question_context_aware(test_q, scenario["asked_questions"], conversation_state)
            
            status = "BLOCKED" if new_similar else "ALLOWED"
            change = ""
            if old_similar != new_similar:
                change = f" (was {'BLOCKED' if old_similar else 'ALLOWED'} with old method)"
            
            print(f"  '{test_q[:60]}...' → {status}{change}")
        
        print("\n" + "-"*80 + "\n")

if __name__ == "__main__":
    test_complete_optimization()
