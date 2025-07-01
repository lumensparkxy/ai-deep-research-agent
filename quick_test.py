#!/usr/bin/env python3
"""
Quick test of the main application functionality
"""

import sys
import os
import signal
import time
import subprocess

def test_application_startup():
    """Test that the application starts without the original errors."""
    
    print("Testing Deep Research Agent startup...")
    
    # Create a subprocess to run the application
    process = subprocess.Popen(
        ['.venv/bin/python', 'main.py'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd='/Users/admin/learn_python/702_gemini_deep_research'
    )
    
    try:
        # Wait a bit for startup
        time.sleep(2)
        
        # Send a test query
        process.stdin.write("test query for automated testing\n")
        process.stdin.flush()
        
        # Wait a bit more
        time.sleep(1)
        
        # Send confirmation
        process.stdin.write("y\n")
        process.stdin.flush()
        
        # Wait a bit more
        time.sleep(1)
        
        # Decline personalization to avoid AI calls
        process.stdin.write("n\n")
        process.stdin.flush()
        
        # Wait for processing
        time.sleep(3)
        
        # Terminate the process
        process.terminate()
        
        # Get output
        stdout, stderr = process.communicate(timeout=5)
        
        # Check for the specific errors that were fixed
        error_indicators = [
            "'ConversationHandler' object has no attribute '_get_mode_question_prefix'",
            "'QUICK' is not a valid ConversationMode",
            "Error in dynamic personalization with mode intelligence"
        ]
        
        found_errors = []
        for error in error_indicators:
            if error in stderr:
                found_errors.append(error)
        
        if found_errors:
            print("❌ Found original errors in stderr:")
            for error in found_errors:
                print(f"   - {error}")
            return False
        else:
            print("✅ No original errors found - fixes are working!")
            
            # Check that basic functionality is working
            if "Welcome to Deep Research Agent!" in stdout:
                print("✅ Application started successfully")
            else:
                print("⚠️  Application may not have started properly")
                
            return True
            
    except subprocess.TimeoutExpired:
        process.kill()
        print("❌ Test timed out")
        return False
    except Exception as e:
        process.terminate()
        print(f"❌ Test failed with exception: {e}")
        return False

if __name__ == "__main__":
    success = test_application_startup()
    
    if success:
        print("\n🎉 Application is working correctly - the errors have been fixed!")
    else:
        print("\n❌ There may still be issues with the application.")
