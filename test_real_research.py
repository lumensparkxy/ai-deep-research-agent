#!/usr/bin/env python3
"""
Quick test script for the real AI-powered research functionality
"""

import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.settings import Settings
from core.research_engine import ResearchEngine
from utils.session_manager import SessionManager


def test_real_research():
    """Test the real AI research functionality with a simple query."""
    print("🧪 Testing Real AI-Powered Research")
    print("=" * 50)
    
    try:
        # Initialize components
        settings = Settings()
        session_manager = SessionManager(settings)
        research_engine = ResearchEngine(settings)
        
        # Create a test session
        test_query = "What are the key benefits of regular exercise for mental health?"
        test_context = {
            "personalize": False,
            "constraints": {"timeline": "immediate"}
        }
        
        session = session_manager.create_session(test_query, test_context)
        session_id = session["session_id"]
        
        print(f"Created test session: {session_id}")
        print(f"Query: {test_query}")
        print()
        
        # Conduct actual AI research
        print("🤖 Starting AI Research Process...")
        research_results = research_engine.conduct_research(
            test_query, test_context, session_id
        )
        
        # Display results summary
        print("\n" + "=" * 50)
        print("✅ Research Complete!")
        print("=" * 50)
        
        confidence = research_results.get("confidence_score", 0.0)
        stages_completed = len(research_results.get("stages", []))
        
        print(f"Stages Completed: {stages_completed}/6")
        print(f"Confidence Score: {confidence:.1%}")
        
        # Show final conclusions summary
        conclusions = research_results.get("final_conclusions", {})
        if conclusions.get("summary"):
            print(f"\nSummary: {conclusions['summary'][:200]}...")
        
        if conclusions.get("primary_recommendation"):
            print(f"\nPrimary Recommendation: {conclusions['primary_recommendation'][:150]}...")
        
        print(f"\nSession saved: data/sessions/{session_id}.json")
        print("\n🎉 Real AI research functionality is working!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during research test: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Set up basic logging
    logging.basicConfig(level=logging.INFO)
    
    success = test_real_research()
    sys.exit(0 if success else 1)
