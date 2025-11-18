#!/usr/bin/env python3
"""
Verification script to test the fix for ConversationHandler.
Simulates a full user session by mocking input.
"""

import sys
import os
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.conversation import ConversationHandler
from config.settings import Settings

def verify_fix():
    print("🧪 Verifying fix for ConversationHandler...")
    
    # Mock settings
    settings = Settings()
    
    # Mock inputs: 
    # 1. Query: "Test query"
    # 2. Confirm query: "y"
    # 3. Personalize?: "n" (skip personalization to be faster)
    # 4. Report depth: "1" (quick)
    inputs = ["Test query", "y", "n", "1"]
    
    # Mock ResearchEngine and ReportGenerator to avoid actual API calls and long waits
    # Note: We patch the classes where they are defined, not where they are imported
    # because they are imported locally inside the method
    with patch('core.research_engine.ResearchEngine') as MockResearchEngine, \
         patch('core.report_generator.ReportGenerator') as MockReportGenerator, \
         patch('builtins.input', side_effect=inputs):
        
        # Setup mock return values
        mock_research_engine = MockResearchEngine.return_value
        mock_research_engine.conduct_research.return_value = {
            "confidence_score": 0.95,
            "findings": []
        }
        
        mock_report_generator = MockReportGenerator.return_value
        # Use a relative path to avoid validation errors
        mock_report_generator.generate_report.return_value = "data/reports/test_report.md"
        
        # Initialize handler
        handler = ConversationHandler(settings)
        
        # Run session
        try:
            print("\n🚀 Starting simulated session...")
            handler.start_interactive_session()
            print("\n✅ Session completed without crashing!")
            print("The fix for '_show_completion_message' is working.")
            return True
        except AttributeError as e:
            if "_show_completion_message" in str(e):
                print(f"\n❌ FAILED: Still getting AttributeError: {e}")
            else:
                print(f"\n❌ FAILED: Unexpected AttributeError: {e}")
            return False
        except Exception as e:
            print(f"\n❌ FAILED: Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = verify_fix()
    sys.exit(0 if success else 1)
