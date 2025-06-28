#!/usr/bin/env python3
"""
Test script for Deep Research Agent Foundation
Demonstrates core functionality without interactive input.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.settings import Settings
from utils.session_manager import SessionManager
from utils.validators import InputValidator
from core.conversation import ConversationHandler
from core.research_engine import ResearchEngine
from core.report_generator import ReportGenerator


def test_foundation():
    """Test all foundation components."""
    print("🧪 Testing Deep Research Agent Foundation")
    print("=" * 50)
    
    try:
        # Test 1: Configuration
        print("1. Testing Configuration Management...")
        settings = Settings()
        print(f"   ✅ App: {settings.app_name} v{settings.app_version}")
        print(f"   ✅ Storage: {settings.session_storage_path}")
        
        # Test 2: Input Validation
        print("\n2. Testing Input Validation...")
        validator = InputValidator()
        test_query = "Best smartphone under $500 for photography"
        validated_query = validator.validate_query(test_query)
        print(f"   ✅ Query validation: '{validated_query}'")
        
        # Test 3: Session Management
        print("\n3. Testing Session Management...")
        session_manager = SessionManager(settings)
        
        # Create test session
        test_context = {
            "personalize": True,
            "user_info": {"experience_level": "intermediate"},
            "constraints": {"budget": "$400", "timeline": "2 weeks"},
            "preferences": {"use_case": "photography", "platform_preference": "Android"}
        }
        
        session = session_manager.create_session(validated_query, test_context)
        session_id = session["session_id"]
        print(f"   ✅ Session created: {session_id}")
        
        # Test session retrieval
        loaded_session = session_manager.load_session(session_id)
        print(f"   ✅ Session loaded: {loaded_session['query'][:50]}...")
        
        # Test 4: Research Engine (Placeholder)
        print("\n4. Testing Research Engine...")
        research_engine = ResearchEngine(settings)
        research_results = research_engine.conduct_research(validated_query, test_context, session_id)
        print(f"   ✅ Research completed with confidence: {research_results['confidence_score']:.2f}")
        
        # Test 5: Report Generation (Placeholder)
        print("\n5. Testing Report Generation...")
        report_generator = ReportGenerator(settings)
        report_path = report_generator.generate_report(session, research_results, "standard")
        print(f"   ✅ Report generated: {report_path}")
        
        # Test 6: Session Listing
        print("\n6. Testing Session Listing...")
        sessions = session_manager.list_sessions()
        print(f"   ✅ Found {len(sessions)} session(s)")
        
        if sessions:
            latest = sessions[0]
            print(f"   ✅ Latest session: {latest['session_id']} - {latest['query'][:30]}...")
        
        print("\n" + "=" * 50)
        print("🎉 All Foundation Tests Passed!")
        print("✅ Configuration management working")
        print("✅ Session persistence working") 
        print("✅ Input validation working")
        print("✅ Research engine framework ready")
        print("✅ Report generation framework ready")
        print("\n📋 Next Steps:")
        print("   1. Implement full Research Engine with Gemini AI")
        print("   2. Implement comprehensive Report Generation")
        print("   3. Add advanced personalization features")
        print("   4. Enhance user interface")
        print("   5. Add production deployment features")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_foundation()
    sys.exit(0 if success else 1)
