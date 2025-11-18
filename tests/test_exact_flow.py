#!/usr/bin/env python3
"""
Test the exact flow used in dynamic personalization.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import Settings
from core.conversation_state import ConversationState
from core.dynamic_personalization import DynamicPersonalizationEngine
from google import genai

def test_exact_flow():
    """Test the exact flow used in dynamic personalization."""
    
    try:
        settings = Settings()
        gemini_client = genai.Client(api_key=settings.gemini_api_key)
        
        print("Creating conversation state...")
        conversation_state = ConversationState(
            session_id="test_exact",
            user_query="Best smartphone for photography"
        )
        
        print("Creating personalization engine...")
        engine = DynamicPersonalizationEngine(
            gemini_client=gemini_client,
            model_name=settings.ai_model
        )
        
        print("Creating prompt...")
        prompt = engine._create_intelligent_ai_prompt(conversation_state, [])
        print(f"Prompt length: {len(prompt)} characters")
        print(f"Prompt preview: {prompt[:200]}...")
        
        print("\nTesting direct API call with this exact prompt...")
        response = gemini_client.models.generate_content(
            model=settings.ai_model,
            contents=prompt
        )
        
        print(f"Direct call response.text: '{response.text}'")
        print(f"Direct call candidates: {len(response.candidates) if response.candidates else 0}")
        
        if response.text:
            print("✅ Direct call with same prompt works!")
        else:
            print("❌ Direct call with same prompt also fails!")
            # Try manual extraction
            if response.candidates and response.candidates[0].content.parts:
                manual_text = response.candidates[0].content.parts[0].text
                print(f"Manual extraction: '{manual_text}'")
        
        # Now test through the engine method
        print("\nTesting through engine method...")
        result = engine._generate_pure_ai_question(conversation_state, [])
        print(f"Engine result: {result}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_exact_flow()
