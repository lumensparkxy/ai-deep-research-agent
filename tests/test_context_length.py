#!/usr/bin/env python3
"""
Test script to analyze context length growth in conversation prompts.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.dynamic_personalization import DynamicPersonalizationEngine
from core.conversation_state import ConversationState, QuestionAnswer, QuestionType
from datetime import datetime

def test_context_length_growth():
    """Test how prompt length grows with conversation history."""
    
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
    
    # Simulate conversation progression
    conversation_scenarios = [
        # Question 1
        {
            "questions": [],
            "qa_history": [],
            "user_profile": {}
        },
        # Question 2
        {
            "questions": ["What's your budget range for this smartphone?"],
            "qa_history": [
                create_qa(
                    "What's your budget range for this smartphone?",
                    "I'm looking at around $800-1200, but could stretch a bit for the right features",
                    "budget"
                )
            ],
            "user_profile": {
                "budget": "$800-1200",
                "budget_flexibility": "some flexibility for right features"
            }
        },
        # Question 3
        {
            "questions": [
                "What's your budget range for this smartphone?",
                "What type of photography do you enjoy most - portraits, landscapes, or everyday moments?"
            ],
            "qa_history": [
                create_qa(
                    "What's your budget range for this smartphone?",
                    "I'm looking at around $800-1200, but could stretch a bit for the right features",
                    "budget"
                ),
                create_qa(
                    "What type of photography do you enjoy most - portraits, landscapes, or everyday moments?",
                    "I love taking portraits of my family and friends, especially candid shots during gatherings",
                    "photography_preferences"
                )
            ],
            "user_profile": {
                "budget": "$800-1200",
                "budget_flexibility": "some flexibility for right features",
                "photography_type": "portraits, family photos",
                "photography_style": "candid shots during gatherings"
            }
        },
        # Question 4
        {
            "questions": [
                "What's your budget range for this smartphone?",
                "What type of photography do you enjoy most - portraits, landscapes, or everyday moments?",
                "How important is having the latest camera technology versus proven reliability?"
            ],
            "qa_history": [
                create_qa(
                    "What's your budget range for this smartphone?",
                    "I'm looking at around $800-1200, but could stretch a bit for the right features",
                    "budget"
                ),
                create_qa(
                    "What type of photography do you enjoy most - portraits, landscapes, or everyday moments?",
                    "I love taking portraits of my family and friends, especially candid shots during gatherings",
                    "photography_preferences"
                ),
                create_qa(
                    "How important is having the latest camera technology versus proven reliability?",
                    "I prefer proven reliability. I don't need cutting edge, just something that consistently takes great photos",
                    "technology_preference"
                )
            ],
            "user_profile": {
                "budget": "$800-1200",
                "budget_flexibility": "some flexibility for right features",
                "photography_type": "portraits, family photos",
                "photography_style": "candid shots during gatherings",
                "technology_preference": "proven reliability over cutting edge",
                "reliability_priority": "consistent great photos"
            }
        },
        # Question 5 (problematic area)
        {
            "questions": [
                "What's your budget range for this smartphone?",
                "What type of photography do you enjoy most - portraits, landscapes, or everyday moments?",
                "How important is having the latest camera technology versus proven reliability?",
                "What's your current phone, and what specific camera issues are you hoping to improve?"
            ],
            "qa_history": [
                create_qa(
                    "What's your budget range for this smartphone?",
                    "I'm looking at around $800-1200, but could stretch a bit for the right features",
                    "budget"
                ),
                create_qa(
                    "What type of photography do you enjoy most - portraits, landscapes, or everyday moments?",
                    "I love taking portraits of my family and friends, especially candid shots during gatherings",
                    "photography_preferences"
                ),
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
            }
        }
    ]
    
    print("=== CONTEXT LENGTH ANALYSIS ===\n")
    
    for i, scenario in enumerate(conversation_scenarios, 1):
        # Set up conversation state
        conversation_state.question_history = scenario["qa_history"]
        conversation_state.user_profile = scenario["user_profile"]
        
        # Generate prompt
        prompt = engine._create_intelligent_ai_prompt(conversation_state, scenario["questions"])
        
        # Calculate metrics
        prompt_length = len(prompt)
        prompt_words = len(prompt.split())
        prompt_lines = len(prompt.split('\n'))
        
        print(f"QUESTION {i}:")
        print(f"  Asked Questions: {len(scenario['questions'])}")
        print(f"  QA History: {len(scenario['qa_history'])}")
        print(f"  User Profile Items: {len(scenario['user_profile'])}")
        print(f"  Prompt Length: {prompt_length:,} characters")
        print(f"  Prompt Words: {prompt_words:,} words")
        print(f"  Prompt Lines: {prompt_lines} lines")
        
        # Estimate token count (rough approximation: 1 token ≈ 4 characters)
        estimated_tokens = prompt_length // 4
        print(f"  Estimated Tokens: ~{estimated_tokens:,}")
        
        if i <= 2:
            print(f"  Status: ✅ Manageable size")
        elif i <= 3:
            print(f"  Status: ⚠️  Getting large")
        else:
            print(f"  Status: ❌ Too verbose - likely causing AI issues")
        
        print()
        
        # Show a sample of the prompt for context
        if i == 1:
            print("SAMPLE PROMPT (Question 1):")
            print("-" * 50)
            print(prompt[:400] + "..." if len(prompt) > 400 else prompt)
            print("-" * 50)
            print()
        elif i == 4:
            print("SAMPLE PROMPT (Question 4 - Problem Area):")
            print("-" * 50)
            print(prompt[:600] + "..." if len(prompt) > 600 else prompt)
            print("-" * 50)
            print()

if __name__ == "__main__":
    test_context_length_growth()
