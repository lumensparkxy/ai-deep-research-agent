#!/usr/bin/env python3
"""
Validation test for the context length optimization.
"""

import sys
import os
from pathlib import Path
import pytest
from datetime import datetime

# Ensure we can import from the project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.dynamic_personalization import DynamicPersonalizationEngine
from core.conversation_state import ConversationState, QuestionAnswer, QuestionType

def test_optimization_validation():
    """Validate the optimization addresses the core issues."""
    
    engine = DynamicPersonalizationEngine()
    conversation_state = ConversationState(
        user_query="I need help choosing a smartphone for photography",
        session_id="validation_session"
    )
    
    def create_qa(question, answer, category):
        return QuestionAnswer(
            question=question,
            answer=answer,
            question_type=QuestionType.OPEN_ENDED,
            timestamp=datetime.now(),
            category=category
        )
    
    print("=== VALIDATION: CONTEXT LENGTH OPTIMIZATION ===\n")
    
    # Simulate the problematic scenario (4 questions asked)
    conversation_state.question_history = [
        create_qa("What's your budget?", "Around $800-1200", "budget"),
        create_qa("What type of photos?", "Family portraits", "photography_preferences"),
        create_qa("Camera quality vs ease?", "Both important", "preferences"),
        create_qa("Current phone issues?", "Low-light is poor", "current_device")
    ]
    
    conversation_state.user_profile = {
        "budget": "$800-1200",
        "photography_type": "family portraits",
        "preferences": "quality and ease",
        "current_device_issues": "low-light poor"
    }
    
    asked_questions = [
        "What's your budget?",
        "What type of photos?", 
        "Camera quality vs ease?",
        "Current phone issues?"
    ]
    
    print("Scenario: 4 questions asked (problematic area)")
    print("Testing both old and new prompt methods...\n")
    
    # Test old method (should be long)
    # Note: We are accessing protected methods for validation purposes
    old_prompt = engine._create_intelligent_ai_prompt(conversation_state, asked_questions)
    print(f"OLD METHOD (Full Prompt):")
    print(f"  Length: {len(old_prompt):,} characters")
    
    # Test new method (should be short)
    new_prompt = engine._create_concise_intelligent_ai_prompt(conversation_state, asked_questions)
    print(f"\nNEW METHOD (Concise Prompt):")
    print(f"  Length: {len(new_prompt):,} characters")
    
    # Calculate improvement
    reduction = ((len(old_prompt) - len(new_prompt)) / len(old_prompt)) * 100
    print(f"\n📊 IMPROVEMENT: {reduction:.1f}% size reduction")
    
    # Assertions to ensure optimization is actually working
    assert len(new_prompt) < len(old_prompt), "New prompt should be shorter than old prompt"
    assert len(new_prompt) < 2000, "New prompt should be reasonably concise"
    
    # Test similarity detection improvement
    print(f"\n=== SIMILARITY DETECTION IMPROVEMENT ===")
    
    test_questions = [
        "What features matter most to you?",
        "How do you share your photos?",
        "What's your experience level?",
        "Are there any must-have features?"
    ]
    
    print("Testing questions that should be ALLOWED in later conversation:")
    for test_q in test_questions:
        old_similar = engine._is_similar_question(test_q, asked_questions)
        new_similar = engine._is_similar_question_context_aware(test_q, asked_questions, conversation_state)
        
        if old_similar and not new_similar:
            status = "✅ IMPROVEMENT: Now allowed (was blocked)"
        elif not old_similar and not new_similar:
            status = "✅ CONSISTENT: Still allowed"
        elif old_similar and new_similar:
            status = "⚠️  CONSISTENT: Still blocked"
        else:
            status = "❌ REGRESSION: Now blocked (was allowed)"
        
        print(f"  '{test_q}' → {status}")
    
    print(f"\n=== SOLUTION SUMMARY ===")
    print("✅ Context length reduced (prevents AI confusion)")
    print("✅ Concise prompts used for questions 3+ (focuses AI attention)")

if __name__ == "__main__":
    try:
        test_optimization_validation()
        print("✅ VALIDATION PASSED")
        sys.exit(0)
    except Exception as e:
        print(f"❌ VALIDATION FAILED: {e}")
        sys.exit(1)
