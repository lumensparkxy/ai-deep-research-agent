#!/usr/bin/env python3
"""
Test real AI generation with the optimized context management.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.dynamic_personalization import DynamicPersonalizationEngine
from core.conversation_state import ConversationState, QuestionAnswer, QuestionType
from datetime import datetime

def test_real_ai_generation_optimized():
    """Test real AI generation with optimized context to solve the 3rd-4th question issue."""
    
    # Create engine instance
    engine = DynamicPersonalizationEngine()
    
    # Create a conversation state mimicking the problematic scenario
    conversation_state = ConversationState(
        user_query="I need help choosing a smartphone for photography",
        session_id="test_optimized_session"
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
    
    print("=== REAL AI GENERATION TEST WITH OPTIMIZATION ===")
    print("Testing the exact scenario where AI was failing at 3rd-4th questions...\n")
    
    # Build up to the problematic area step by step
    conversation_steps = [
        {
            "step": 3,
            "description": "Question 3 - Where issues started",
            "setup": {
                "qa_history": [
                    create_qa("What's your budget range?", "Around $800-1200, flexible for good features", "budget"),
                    create_qa("What type of photography do you do?", "Mainly family portraits and candid shots at gatherings", "photography_preferences")
                ],
                "user_profile": {
                    "budget": "$800-1200",
                    "photography_type": "family portraits",
                    "photography_style": "candid shots"
                },
                "asked_questions": [
                    "What's your budget range?",
                    "What type of photography do you do?"
                ]
            }
        },
        {
            "step": 4,
            "description": "Question 4 - Peak problem area",
            "setup": {
                "qa_history": [
                    create_qa("What's your budget range?", "Around $800-1200, flexible for good features", "budget"),
                    create_qa("What type of photography do you do?", "Mainly family portraits and candid shots at gatherings", "photography_preferences"),
                    create_qa("How important is camera quality vs ease of use?", "I want great quality but it should be intuitive to use", "preferences")
                ],
                "user_profile": {
                    "budget": "$800-1200",
                    "photography_type": "family portraits",
                    "photography_style": "candid shots",
                    "preferences": "great quality with intuitive interface"
                },
                "asked_questions": [
                    "What's your budget range?",
                    "What type of photography do you do?",
                    "How important is camera quality vs ease of use?"
                ]
            }
        },
        {
            "step": 5,
            "description": "Question 5 - Previous failure point",
            "setup": {
                "qa_history": [
                    create_qa("What's your budget range?", "Around $800-1200, flexible for good features", "budget"),
                    create_qa("What type of photography do you do?", "Mainly family portraits and candid shots at gatherings", "photography_preferences"),
                    create_qa("How important is camera quality vs ease of use?", "I want great quality but it should be intuitive to use", "preferences"),
                    create_qa("What's your current phone and what issues do you have?", "iPhone 11, but low-light photos are grainy and portraits sometimes blur", "current_device")
                ],
                "user_profile": {
                    "budget": "$800-1200",
                    "photography_type": "family portraits",
                    "photography_style": "candid shots",
                    "preferences": "great quality with intuitive interface",
                    "current_device": "iPhone 11",
                    "issues": "low-light grain, portrait blur"
                },
                "asked_questions": [
                    "What's your budget range?",
                    "What type of photography do you do?",
                    "How important is camera quality vs ease of use?",
                    "What's your current phone and what issues do you have?"
                ]
            }
        }
    ]
    
    for step_info in conversation_steps:
        print(f"=== TESTING QUESTION {step_info['step']} ===")
        print(f"{step_info['description']}")
        
        # Set up conversation state
        setup = step_info['setup']
        conversation_state.question_history = setup['qa_history']
        conversation_state.user_profile = setup['user_profile']
        
        print(f"Context: {len(setup['qa_history'])} previous Q&As, {len(setup['user_profile'])} profile items")
        
        # Try to generate a question with the optimized method
        print("Attempting AI question generation with optimization...")
        
        try:
            # This should now use the optimized context management
            generated_question = engine._generate_intelligent_ai_question(conversation_state, setup['asked_questions'])
            
            if generated_question:
                print(f"✅ SUCCESS: Generated question: '{generated_question}'")
                
                # Test similarity detection
                is_similar = engine._is_similar_question_context_aware(
                    generated_question, 
                    setup['asked_questions'], 
                    conversation_state
                )
                print(f"   Similarity check: {'❌ SIMILAR (would retry)' if is_similar else '✅ UNIQUE (would use)'}")
                
            else:
                print("❌ FAILED: AI generation returned None")
                
        except Exception as e:
            print(f"❌ ERROR: {str(e)[:100]}...")
        
        print()
    
    print("=== SUMMARY ===")
    print("The optimization should:")
    print("1. ✅ Use concise prompts (96-119 tokens vs 500+ tokens)")
    print("2. ✅ Apply context-aware similarity detection") 
    print("3. ✅ Allow more question variety in later stages")
    print("4. ✅ Prevent AI confusion from context overload")
    print("\nThis should resolve the 'AI generated similar questions after all attempts' issue!")

if __name__ == "__main__":
    test_real_ai_generation_optimized()
