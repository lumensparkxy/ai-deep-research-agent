#!/usr/bin/env python3
"""
Debug Gemini response to understand why it's empty.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import Settings
from google import genai

def debug_gemini_response():
    """Debug what Gemini is actually returning."""
    
    print("🔍 Debugging Gemini Response...")
    print("=" * 50)
    
    try:
        # Load settings and initialize Gemini client
        settings = Settings()
        client = genai.Client(api_key=settings.gemini_api_key)
        
        print(f"✅ Using model: {settings.ai_model}")
        
        # Test with a simple prompt first
        simple_prompt = "Ask one question about smartphones."
        print(f"\n📝 Testing simple prompt: {simple_prompt}")
        
        response = client.models.generate_content(
            model=settings.ai_model,
            contents=simple_prompt
        )
        
        print(f"Response type: {type(response)}")
        print(f"Response attributes: {[attr for attr in dir(response) if not attr.startswith('_')]}")
        
        if hasattr(response, 'text'):
            print(f"Response.text: '{response.text}'")
        if hasattr(response, 'candidates'):
            print(f"Response.candidates: {response.candidates}")
            if response.candidates:
                for i, candidate in enumerate(response.candidates):
                    print(f"  Candidate {i}: {candidate}")
                    if hasattr(candidate, 'content'):
                        print(f"    Content: {candidate.content}")
                    if hasattr(candidate, 'parts'):
                        print(f"    Parts: {candidate.parts}")
        
        # Test with our actual prompt
        complex_prompt = """You are having a friendly, helpful conversation with someone seeking personalized advice about: "Best smartphone for photography"

CONVERSATION SO FAR:
This is the beginning of your conversation.

WHAT YOU'VE LEARNED ABOUT THEM:
You're just getting to know them.

QUESTIONS ALREADY ASKED:
• None yet

YOUR TASK: Ask ONE thoughtful follow-up question that feels natural and helps you understand what matters most to them for making a great recommendation.

Generate ONE natural, engaging question that builds on the conversation:"""
        
        print(f"\n📝 Testing complex prompt...")
        
        response2 = client.models.generate_content(
            model=settings.ai_model,
            contents=complex_prompt
        )
        
        print(f"Complex response type: {type(response2)}")
        if hasattr(response2, 'text'):
            print(f"Complex response.text: '{response2.text}'")
        if hasattr(response2, 'candidates'):
            print(f"Complex response.candidates: {response2.candidates}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_gemini_response()
