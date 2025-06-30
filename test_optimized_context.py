#!/usr/bin/env python3
"""
Test the optimized context management for AI question generation.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.dynamic_personalization import DynamicPersonalizationEngine
from core.conversation_state import ConversationState, QuestionAnswer, QuestionType
from datetime import datetime

def test_optimized_context():
    """Test the optimized context management."""
    
    # Create engine instance
    engine = DynamicPersonalizationEngine()
    
    # Create a conversation state with progressive history
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
    
    print("=== OPTIMIZED CONTEXT MANAGEMENT TEST ===\n")
    
    # Test Question 1 (should use full prompt)
    print("QUESTION 1 (Full Prompt):")
    asked_questions = []
    prompt = engine._create_intelligent_ai_prompt(conversation_state, asked_questions)
    print(f"  Prompt Length: {len(prompt):,} characters")
    print(f"  Estimated Tokens: ~{len(prompt) // 4:,}")
    print()
    
    # Add some conversation history for Question 3
    conversation_state.question_history = [
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
    ]
    
    conversation_state.user_profile = {
        "budget": "$800-1200",
        "budget_flexibility": "some flexibility for right features",
        "photography_type": "portraits, family photos",
        "photography_style": "candid shots during gatherings"
    }
    
    asked_questions = [
        "What's your budget range for this smartphone?",
        "What type of photography do you enjoy most?"
    ]
    
    # Test Question 3 - Full prompt (should still be long)
    print("QUESTION 3 (Full Prompt - Old Method):")
    full_prompt = engine._create_intelligent_ai_prompt(conversation_state, asked_questions)
    print(f"  Prompt Length: {len(full_prompt):,} characters")
    print(f"  Estimated Tokens: ~{len(full_prompt) // 4:,}")
    
    # Show a sample of the full prompt
    print("  Sample:")
    print(f"    {full_prompt[:200]}...")
    print()
    
    # Test Question 3 - Concise prompt (should be much shorter)
    print("QUESTION 3 (Concise Prompt - New Method):")
    concise_prompt = engine._create_concise_intelligent_ai_prompt(conversation_state, asked_questions)
    print(f"  Prompt Length: {len(concise_prompt):,} characters")
    print(f"  Estimated Tokens: ~{len(concise_prompt) // 4:,}")
    
    # Show the full concise prompt
    print("  Full Concise Prompt:")
    print(f"    {concise_prompt}")
    print()
    
    # Test with even more history (Question 5)
    conversation_state.question_history.extend([
        create_qa(
            "How important is having the latest camera technology versus proven reliability?",
            "I prefer proven reliability. I don't need cutting edge, just something that consistently takes great photos",
            "technology_preference"
        ),
        create_qa(
            "What's your current phone, and what specific camera issues are you hoping to improve?",
            "I have an iPhone 12, but the low-light performance isn't great and sometimes the portraits are blurry",
            "current_device"
        )
    ])
    
    conversation_state.user_profile.update({
        "technology_preference": "proven reliability over cutting edge",
        "reliability_priority": "consistent great photos",
        "current_device": "iPhone 12",
        "improvement_needs": "better low-light performance, sharper portraits"
    })
    
    asked_questions.extend([
        "How important is having the latest camera technology versus proven reliability?",
        "What's your current phone, and what specific camera issues are you hoping to improve?"
    ])
    
    print("QUESTION 5 (Concise Prompt - Even More History):")
    concise_prompt_q5 = engine._create_concise_intelligent_ai_prompt(conversation_state, asked_questions)
    print(f"  Prompt Length: {len(concise_prompt_q5):,} characters")
    print(f"  Estimated Tokens: ~{len(concise_prompt_q5) // 4:,}")
    
    # Show the full concise prompt for Question 5
    print("  Full Concise Prompt:")
    print(f"    {concise_prompt_q5}")
    print()
    
    # Compare with full prompt at Question 5
    print("QUESTION 5 (Full Prompt - Comparison):")
    full_prompt_q5 = engine._create_intelligent_ai_prompt(conversation_state, asked_questions)
    print(f"  Prompt Length: {len(full_prompt_q5):,} characters")
    print(f"  Estimated Tokens: ~{len(full_prompt_q5) // 4:,}")
    
    print("\n=== OPTIMIZATION RESULTS ===")
    print(f"Context Reduction: {len(full_prompt_q5)} → {len(concise_prompt_q5)} characters")
    print(f"Token Savings: ~{(len(full_prompt_q5) - len(concise_prompt_q5)) // 4:,} tokens")
    print(f"Size Reduction: {((len(full_prompt_q5) - len(concise_prompt_q5)) / len(full_prompt_q5) * 100):.1f}%")

if __name__ == "__main__":
    test_optimized_context()
