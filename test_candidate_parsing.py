#!/usr/bin/env python3
"""
Direct test of candidate parsing to debug the issue.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import Settings
from google import genai

def test_candidate_parsing():
    """Test candidate parsing directly."""
    
    try:
        settings = Settings()
        client = genai.Client(api_key=settings.gemini_api_key)
        
        prompt = """You are having a friendly conversation. Ask ONE short question about smartphones."""
        
        print("Testing candidate parsing...")
        
        response = client.models.generate_content(
            model=settings.ai_model,
            contents=prompt
        )
        
        print(f"Response.text: {response.text}")
        print(f"Candidates count: {len(response.candidates) if response.candidates else 0}")
        
        if response.candidates:
            for i, candidate in enumerate(response.candidates):
                print(f"\nCandidate {i}:")
                print(f"  Type: {type(candidate)}")
                print(f"  Content: {candidate.content}")
                print(f"  Finish reason: {getattr(candidate, 'finish_reason', 'None')}")
                
                if hasattr(candidate, 'content') and candidate.content:
                    print(f"  Content type: {type(candidate.content)}")
                    print(f"  Content parts: {getattr(candidate.content, 'parts', 'None')}")
                    
                    if hasattr(candidate.content, 'parts') and candidate.content.parts:
                        for j, part in enumerate(candidate.content.parts):
                            print(f"    Part {j}: {type(part)}")
                            print(f"    Part text: '{getattr(part, 'text', 'No text')}'")
        
        # Try to extract text manually
        try:
            if response.candidates and len(response.candidates) > 0:
                first_candidate = response.candidates[0]
                if hasattr(first_candidate, 'content') and first_candidate.content:
                    if hasattr(first_candidate.content, 'parts') and first_candidate.content.parts:
                        first_part = first_candidate.content.parts[0]
                        if hasattr(first_part, 'text'):
                            manual_text = first_part.text
                            print(f"\nManually extracted text: '{manual_text}'")
                            
                            # Test if this works for our extraction
                            if manual_text and manual_text.strip():
                                print("✅ Manual extraction successful!")
                                return manual_text
                            else:
                                print("❌ Manual extraction returned empty text")
        except Exception as e:
            print(f"❌ Manual extraction failed: {e}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_candidate_parsing()
