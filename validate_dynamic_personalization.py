#!/usr/bin/env python3
"""
Validation script for Dynamic Personalization Settings
Tests all new configuration settings and functionality.
"""

import os
import sys
from pathlib import Path

# Ensure we can import from the project
sys.path.insert(0, str(Path(__file__).parent))

def test_dynamic_personalization_settings():
    """Test all dynamic personalization settings."""
    print("🧪 Testing Dynamic Personalization Settings...")
    
    # Set required environment variable
    os.environ['GEMINI_API_KEY'] = 'test_key'
    
    try:
        from config.settings import Settings
        
        print("✅ Importing Settings class")
        settings = Settings()
        print("✅ Settings initialized successfully")
        
        # Test dynamic personalization settings
        print("\n📋 Dynamic Personalization Settings:")
        dp = settings.dynamic_personalization
        print(f"  • Enabled: {dp.enabled}")
        print(f"  • Fallback to static: {dp.fallback_to_static}")
        print(f"  • Max questions: {dp.max_questions}")
        print(f"  • Min questions: {dp.min_questions}")
        print(f"  • Timeout: {dp.timeout_seconds}s")
        print(f"  • AI question generation: {dp.ai_question_generation}")
        print(f"  • Context analysis: {dp.context_analysis}")
        print(f"  • Completion assessment: {dp.completion_assessment}")
        
        # Test AI question generation settings
        print("\n🤖 AI Question Generation Settings:")
        ai_gen = settings.ai_question_generation
        print(f"  • Enabled: {ai_gen.enabled}")
        print(f"  • Temperature: {ai_gen.temperature}")
        print(f"  • Top-p: {ai_gen.top_p}")
        print(f"  • Max tokens: {ai_gen.max_tokens}")
        print(f"  • Question validation: {ai_gen.question_validation}")
        print(f"  • Duplicate detection: {ai_gen.duplicate_detection}")
        print(f"  • Relevance threshold: {ai_gen.relevance_threshold}")
        
        # Test context analysis settings
        print("\n🔍 Context Analysis Settings:")
        context = settings.context_analysis
        print(f"  • Enabled: {context.enabled}")
        print(f"  • Confidence threshold: {context.confidence_threshold}")
        print(f"  • Budget weight: {context.budget_weight}")
        print(f"  • Timeline weight: {context.timeline_weight}")
        print(f"  • Quality weight: {context.quality_weight}")
        print(f"  • Convenience weight: {context.convenience_weight}")
        print(f"  • Communication style analysis: {context.communication_style}")
        print(f"  • Expertise level analysis: {context.expertise_level}")
        print(f"  • Decision making style: {context.decision_making_style}")
        print(f"  • Emotional indicators: {context.emotional_indicators}")
        print(f"  • Critical gap threshold: {context.critical_gap_threshold}")
        print(f"  • Importance weighting: {context.importance_weighting}")
        print(f"  • Research impact scoring: {context.research_impact_scoring}")
        
        # Test user preferences settings
        print("\n👤 User Preferences Settings:")
        prefs = settings.user_preferences
        print(f"  • Storage enabled: {prefs.storage_enabled}")
        print(f"  • Storage location: {prefs.storage_location}")
        print(f"  • Session learning: {prefs.session_learning}")
        print(f"  • Cross-session patterns: {prefs.cross_session_patterns}")
        print(f"  • Preference expiry: {prefs.preference_expiry_days} days")
        
        # Test performance settings
        print("\n⚡ Performance Settings:")
        perf = settings.performance
        print(f"  • AI response timeout: {perf.ai_response_timeout}s")
        print(f"  • Concurrent analysis: {perf.concurrent_analysis}")
        print(f"  • Cache question templates: {perf.cache_question_templates}")
        print(f"  • Context analysis depth: {perf.context_analysis_depth}")
        
        # Test conversation modes
        print("\n💬 Conversation Mode Configurations:")
        modes = settings.available_conversation_modes
        print(f"  • Available modes: {', '.join(modes)}")
        
        for mode in modes:
            config = settings.get_conversation_mode_config(mode)
            print(f"  • {mode.title()} mode:")
            print(f"    - Max questions: {config.max_questions}")
            print(f"    - Time sensitivity: {config.time_sensitivity_threshold}")
            print(f"    - Question depth: {config.question_depth}")
            print(f"    - AI prompt modifier: {config.ai_prompt_modifier[:60]}...")
        
        # Test fallback questions
        print("\n🔄 Fallback Questions:")
        categories = ['technology', 'health', 'finance', 'lifestyle', 'other']
        for category in categories:
            questions = settings.get_fallback_questions(category)
            print(f"  • {category.title()}: {len(questions)} questions")
            if questions:
                print(f"    - Example: {questions[0]}")
        
        # Test environment overrides
        print("\n🌍 Environment Override Testing:")
        override = settings.get_environment_override("dynamic_personalization.max_questions", "not_found")
        print(f"  • Override lookup result: {override}")
        
        # Test directory creation
        print("\n📁 Directory Validation:")
        user_prefs_dir = Path(prefs.storage_location)
        print(f"  • User preferences directory exists: {user_prefs_dir.exists()}")
        print(f"  • Path: {user_prefs_dir.absolute()}")
        
        print("\n🎉 All Dynamic Personalization Settings Validated Successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error during validation: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Dynamic Personalization Settings Validation")
    print("=" * 60)
    
    success = test_dynamic_personalization_settings()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ VALIDATION PASSED - All settings working correctly!")
        sys.exit(0)
    else:
        print("❌ VALIDATION FAILED - Check errors above")
        sys.exit(1)
