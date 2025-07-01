#!/usr/bin/env python3
"""
Test script to validate pure AI-driven question generation without hardcoded categories.
"""

import sys
import logging
from config.settings import Settings
from core.dynamic_personalization import DynamicPersonalizationEngine
from core.conversation_mode_intelligence import ConversationModeIntelligence

def test_pure_ai_questions():
    """Test pure AI question generation."""
    print("🧪 Testing Pure AI-Driven Question Generation")
    print("=" * 60)
    
    # Initialize settings and components
    settings = Settings()
    
    try:
        from google import genai
        client = genai.Client(api_key=settings.gemini_api_key)
        
        # Initialize engines
        personalization_engine = DynamicPersonalizationEngine(
            gemini_client=client,
            model_name=settings.ai_model
        )
        
        mode_intelligence = ConversationModeIntelligence(
            gemini_client=client,
            model_name=settings.ai_model  
        )
        
        print("✅ AI engines initialized successfully")
        
        # Test queries
        test_queries = [
            "Best smartphone under $500 for photography",
            "Best laptop for programming and video editing", 
            "Should I invest in solar panels for my home",
            "Best online course for learning Python programming",
            "What's the best diet plan for weight loss"
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n🔍 Test {i}: {query}")
            print("-" * 40)
            
            # Initialize conversation
            session_id = f"test_session_{i}"
            conversation_state = personalization_engine.initialize_conversation(query, session_id)
            
            # Generate first question using pure AI
            print("Generating first question with pure AI...")
            question = personalization_engine.generate_next_question(conversation_state)
            
            if question:
                print(f"✅ Generated: {question}")
                
                # Simulate a response and generate follow-up
                sample_responses = [
                    "I want something that takes great photos and isn't too expensive",
                    "I need it for work and gaming, budget around $1500",
                    "I'm interested in reducing electricity bills and being eco-friendly",
                    "I'm a complete beginner with no programming experience",
                    "I want to lose 20 pounds in 3 months safely"
                ]
                
                if i <= len(sample_responses):
                    response = sample_responses[i-1]
                    print(f"📝 Simulated response: {response}")
                    
                    # Process response
                    result = personalization_engine.process_user_response(
                        conversation_state, question, response
                    )
                    
                    # Generate follow-up question
                    follow_up = personalization_engine.generate_next_question(conversation_state)
                    if follow_up:
                        print(f"🔄 Follow-up: {follow_up}")
                        print(f"📊 Extracted info: {len(result.get('extracted_info', {}))}")
                    else:
                        print("❌ Failed to generate follow-up question")
            else:
                print("❌ Failed to generate first question")
                
            print()
            
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    test_pure_ai_questions()
