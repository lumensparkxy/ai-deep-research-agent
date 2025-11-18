#!/usr/bin/env python3
"""
Quick test to verify that AI question generation works and identify bottlenecks.
"""

import sys
import os
import logging
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import Settings
from core.conversation_state import ConversationState
from core.dynamic_personalization import DynamicPersonalizationEngine
from google import genai

# Set up logging to see what's happening
logging.basicConfig(level=logging.DEBUG)

def test_ai_generation():
    """Test AI question generation with real Gemini client."""
    
    print("🔍 Testing AI Question Generation...")
    print("=" * 50)
    
    try:
        # Load settings and initialize Gemini client
        settings = Settings()
        gemini_client = genai.Client(api_key=settings.gemini_api_key)
        
        print(f"✅ Gemini client initialized with model: {settings.ai_model}")
        
        # Create personalization engine
        engine = DynamicPersonalizationEngine(
            gemini_client=gemini_client,
            model_name=settings.ai_model
        )
        
        print("✅ DynamicPersonalizationEngine created")
        
        # Test different conversation states
        test_cases = [
            {
                'query': 'Best smartphone for photography',
                'asked_questions': [],
                'description': 'Initial tech question'
            },
            {
                'query': 'Best smartphone for photography', 
                'asked_questions': ['What type of photography interests you most?'],
                'description': 'Follow-up tech question'
            },
            {
                'query': 'How to learn Python programming',
                'asked_questions': [],
                'description': 'Learning question'
            }
        ]
        
        for i, test_case in enumerate(test_cases):
            print(f"\n📝 Test Case {i+1}: {test_case['description']}")
            print(f"Query: {test_case['query']}")
            print(f"Asked: {test_case['asked_questions']}")
            
            # Create conversation state
            conversation_state = ConversationState(
                session_id=f"test_{i}",
                user_query=test_case['query']
            )
            
            # Try AI generation
            print("🤖 Attempting AI question generation...")
            try:
                ai_question = engine._generate_intelligent_ai_question(
                    conversation_state, 
                    test_case['asked_questions']
                )
                
                if ai_question:
                    print(f"✅ AI Generated: {ai_question}")
                else:
                    print("⚠️  AI generation returned None")
                    
            except Exception as e:
                print(f"❌ AI generation failed: {e}")
                
            print("-" * 30)
    
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    test_ai_generation()
