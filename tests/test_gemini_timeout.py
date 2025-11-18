#!/usr/bin/env python3
"""
Quick test to check Gemini client timeout behavior and response times.
"""

import sys
import os
import time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import Settings
from google import genai
import logging

def test_gemini_timeout_behavior():
    """Test Gemini client timeout behavior and response times."""
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    try:
        # Initialize settings and client
        settings = Settings()
        
        if not settings.gemini_api_key:
            print("❌ No GEMINI_API_KEY found in environment")
            return
            
        print("🔍 Testing Gemini client timeout behavior...")
        print("=" * 50)
        
        # Create client
        client = genai.Client(api_key=settings.gemini_api_key)
        
        # Test different prompt complexities and measure response times
        test_prompts = [
            ("Simple prompt", "What is 2+2?"),
            ("Medium complexity", """
                Analyze this conversation and suggest the next question:
                User Query: "Best smartphone for photography"
                Previous Q&A:
                Q: What type of photography interests you?
                A: Portrait photography of my family
                
                Generate the next question:
            """),
            ("Complex prompt", """
                You are an expert research consultant. Analyze this conversation and generate an intelligent follow-up question.
                
                USER'S RESEARCH QUERY: "Best laptop for programming and gaming"
                
                CONVERSATION PROGRESS:
                - Questions Asked So Far: 2
                - Information Gathered: 3 data points
                
                PREVIOUS QUESTIONS:
                - What type of programming do you primarily do?
                - What games do you typically play?
                
                RECENT USER RESPONSES:
                - Full-stack web development with React and Node.js
                - AAA games like Cyberpunk 2077 and competitive FPS games
                
                CURRENT PROFILE:
                - programming_type: full-stack web development
                - gaming_preference: AAA and competitive FPS
                - tech_stack: React, Node.js
                
                Generate ONE intelligent follow-up question (under 25 words):
            """)
        ]
        
        for test_name, prompt in test_prompts:
            print(f"\n📝 Testing: {test_name}")
            start_time = time.time()
            
            try:
                response = client.models.generate_content(
                    model=settings.ai_model,
                    contents=prompt
                )
                
                end_time = time.time()
                response_time = end_time - start_time
                
                print(f"✅ Success - Response time: {response_time:.2f}s")
                print(f"📄 Response: {response.text[:100]}{'...' if len(response.text) > 100 else ''}")
                
                # Check if response time is unusually long (potential timeout indicator)
                if response_time > 10:
                    print(f"⚠️  WARNING: Long response time ({response_time:.2f}s) - potential timeout risk")
                elif response_time > 5:
                    print(f"⚠️  NOTICE: Moderate response time ({response_time:.2f}s)")
                else:
                    print(f"✅ Good response time ({response_time:.2f}s)")
                    
            except Exception as e:
                end_time = time.time()
                response_time = end_time - start_time
                print(f"❌ Error after {response_time:.2f}s: {type(e).__name__}: {e}")
                
                # Check if this looks like a timeout
                if "timeout" in str(e).lower() or response_time > 30:
                    print("🕒 This appears to be a timeout-related error")
                elif response_time > 10:
                    print("🕒 Long response time before error - possible timeout")
                
        print("\n" + "=" * 50)
        print("🔍 Checking client configuration...")
        
        # Try to inspect client configuration
        print(f"Model: {settings.ai_model}")
        print(f"Research timeout setting: {settings.timeout_seconds}s")
        
        # Check if there are any client timeout settings
        print("\n📋 Client inspection:")
        try:
            # Try to access client configuration
            print(f"Client type: {type(client)}")
            if hasattr(client, '_client'):
                print(f"Internal client: {type(client._client)}")
            if hasattr(client, 'timeout'):
                print(f"Client timeout: {client.timeout}")
            else:
                print("No explicit timeout found on client")
        except Exception as e:
            print(f"Could not inspect client: {e}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_gemini_timeout_behavior()
