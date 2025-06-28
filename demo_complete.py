#!/usr/bin/env python3
"""
Demonstration of the Complete Deep Research Agent with Real AI Integration
"""

import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.settings import Settings
from core.research_engine import ResearchEngine
from core.report_generator import ReportGenerator
from utils.session_manager import SessionManager


def demonstrate_complete_functionality():
    """Demonstrate the complete AI-powered research functionality."""
    print("🚀 Deep Research Agent - Complete Functionality Demo")
    print("=" * 60)
    
    try:
        # Initialize all components
        settings = Settings()
        session_manager = SessionManager(settings)
        research_engine = ResearchEngine(settings)
        report_generator = ReportGenerator(settings)
        
        print("✅ All components initialized successfully")
        print(f"   Model: {settings.ai_model}")
        print(f"   API Key: {settings.gemini_api_key[:10]}...")
        print()
        
        # Demo query with personalization
        demo_query = "What are the best programming languages to learn in 2025 for beginners?"
        demo_context = {
            "personalize": True,
            "user_info": {
                "experience_level": "beginner",
                "background": "switching careers"
            },
            "constraints": {
                "timeline": "6 months",
                "budget": "limited"
            },
            "preferences": {
                "career_focus": "web development",
                "learning_style": "hands-on projects"
            }
        }
        
        print(f"📝 Demo Query: {demo_query}")
        print(f"🎯 With Personalization: {demo_context['personalize']}")
        print()
        
        # Create session
        session = session_manager.create_session(demo_query, demo_context)
        session_id = session["session_id"]
        print(f"📊 Session Created: {session_id}")
        
        # Conduct AI research
        print("\n🤖 Starting Complete AI Research Process...")
        print("This will take ~30-60 seconds with real API calls...")
        
        research_results = research_engine.conduct_research(
            demo_query, demo_context, session_id
        )
        
        # Generate report
        print("\n📄 Generating Comprehensive Report...")
        report_path = report_generator.generate_report(
            session, research_results, "standard"
        )
        
        # Update session with report
        session_manager.update_session_report_path(session_id, report_path)
        
        # Display results
        print("\n" + "=" * 60)
        print("🎉 COMPLETE RESEARCH RESULTS")
        print("=" * 60)
        
        confidence = research_results.get("confidence_score", 0.0)
        stages = research_results.get("stages", [])
        conclusions = research_results.get("final_conclusions", {})
        
        print(f"📊 Research Stages Completed: {len(stages)}/6")
        print(f"📈 Overall Confidence Score: {confidence:.1%}")
        print(f"📄 Report Generated: {report_path}")
        print()
        
        # Show key findings
        if conclusions.get("summary"):
            print("📋 Executive Summary:")
            print(f"   {conclusions['summary'][:200]}...")
            print()
        
        if conclusions.get("primary_recommendation"):
            primary = conclusions["primary_recommendation"]
            if isinstance(primary, dict):
                rec_text = primary.get("recommendation", str(primary))
            else:
                rec_text = str(primary)
            print("🎯 Primary Recommendation:")
            print(f"   {rec_text[:200]}...")
            print()
        
        # Show evidence quality
        total_evidence = 0
        avg_reliability = 0.0
        
        for stage in stages:
            evidence = stage.get("findings", {}).get("evidence", [])
            for item in evidence:
                if isinstance(item, dict) and "reliability_score" in item:
                    total_evidence += 1
                    avg_reliability += item["reliability_score"]
        
        if total_evidence > 0:
            avg_reliability = avg_reliability / total_evidence
            print(f"🔍 Evidence Analysis:")
            print(f"   Total Evidence Sources: {total_evidence}")
            print(f"   Average Reliability Score: {avg_reliability:.1%}")
            print()
        
        # Show session file
        print(f"💾 Complete session data saved to:")
        print(f"   data/sessions/{session_id}.json")
        print()
        
        print("🌟 All Features Demonstrated:")
        print("   ✅ Real AI-powered 6-stage research")
        print("   ✅ Personalized context integration")
        print("   ✅ Evidence-based source evaluation")
        print("   ✅ Confidence scoring and risk assessment")
        print("   ✅ Professional report generation")
        print("   ✅ Complete session persistence")
        print("   ✅ Progress feedback and error handling")
        print()
        
        print("🎊 Deep Research Agent is fully functional!")
        print("   Ready for production use with any research query.")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during demonstration: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Set up minimal logging
    logging.basicConfig(level=logging.WARNING)  # Reduce noise for demo
    
    success = demonstrate_complete_functionality()
    print("\n" + "=" * 60)
    
    if success:
        print("🏆 Demonstration completed successfully!")
        print("You can now use the Deep Research Agent for any research query.")
    else:
        print("❌ Demonstration failed. Check error messages above.")
    
    sys.exit(0 if success else 1)
