"""
Conversation Handler for Deep Research Agent
Manages user interaction and guides through the research process.
"""

import logging
import re
from typing import Dict, Any, List, Optional
from datetime import datetime

from config.settings import Settings
from utils.session_manager import SessionManager
from utils.validators import InputValidator, ValidationError
from .dynamic_personalization import DynamicPersonalizationEngine
from .conversation_mode_intelligence import (
    ConversationModeIntelligence, 
    AdaptiveModeManager,
    ConversationMode,
    UserSignals,
    EngagementMetrics
)


class ConversationHandler:
    """Handles user interaction and conversation flow."""
    
    def __init__(self, settings: Settings):
        """
        Initialize conversation handler.
        
        Args:
            settings: Configuration settings
        """
        self.settings = settings
        self.session_manager = SessionManager(settings)
        self.validator = InputValidator(settings)
        self.logger = logging.getLogger(__name__)
        
        # Initialize Dynamic Personalization Engine
        try:
            from google import genai
            gemini_client = genai.Client(api_key=settings.gemini_api_key)
            self.personalization_engine = DynamicPersonalizationEngine(
                gemini_client=gemini_client,
                model_name=settings.ai_model
            )
            
            # Initialize Conversation Mode Intelligence
            self.mode_intelligence = ConversationModeIntelligence(
                gemini_client=gemini_client,
                model_name=settings.ai_model
            )
            self.adaptive_manager = AdaptiveModeManager(self.mode_intelligence)
            
        except Exception as e:
            self.logger.warning(f"Could not initialize AI engines: {e}")
            self.personalization_engine = None
            self.mode_intelligence = None
            self.adaptive_manager = None
        
        # Conversation state
        self.current_session = None
        self.user_context = {}
        self.current_conversation_state = None
    
    def start_interactive_session(self) -> None:
        """Start an interactive research session with the user."""
        try:
            # Welcome and introduction
            self._print_welcome()
            
            # Get research query
            query = self._get_research_query()
            
            # Ask about personalization
            personalize = self._ask_personalization()
            
            # Gather context if requested
            context = {"personalize": personalize}
            if personalize:
                # Create a temporary session ID for personalization
                temp_session_id = f"temp_{int(datetime.now().timestamp() * 1000)}"
                context.update(self._gather_personalization(query, temp_session_id))
            
            # Create session with complete context
            self.current_session = self.session_manager.create_session(query, context)
            session_id = self.current_session["session_id"]
            
            # Register session for signal handling
            try:
                from main import set_current_session
                set_current_session(self.session_manager, session_id)
            except ImportError:
                # This might happen in tests or other contexts
                pass
            
            print(f"\n🔬 Starting Research Session: {session_id}")
            print("=" * 60)
            
            # Import here to avoid circular imports when modules are being created
            try:
                from core.research_engine import ResearchEngine
                from core.report_generator import ReportGenerator
                
                # Conduct research with progress feedback
                research_engine = ResearchEngine(self.settings)
                
                # Show research start message
                print(f"\n🔬 Starting Iterative Research Process for: '{query}'")
                print("=" * 60)
                
                research_results = research_engine.conduct_research(
                    query, context, session_id
                )
                
                # Generate report
                report_generator = ReportGenerator(self.settings)
                
                # Ask for report depth
                depth = self._ask_report_depth()
                
                report_path = report_generator.generate_report(
                    self.current_session, research_results, depth
                )
                
                # Update session with report path
                self.session_manager.update_session_report_path(session_id, report_path)
                
                # Show completion message
                self._show_completion_message(session_id, report_path, research_results)
                
                # Clear session tracking as research completed successfully
                try:
                    from main import clear_current_session
                    clear_current_session()
                except ImportError:
                    pass
                
            except ImportError:
                # Modules not yet created - show placeholder message
                print("🚧 Core research modules are being implemented...")
                print("This is the foundation setup. Research functionality will be available soon!")
                print(f"\nSession created: {session_id}")
                print(f"Query: {query}")
                print(f"Context: {context}")
                
                # Clear session tracking as foundation mode completed
                try:
                    from main import clear_current_session
                    clear_current_session()
                except ImportError:
                    pass
                
        except (KeyboardInterrupt, EOFError):
            # Clear session tracking, but don't mark as interrupted here
            # as the signal handler will take care of that
            try:
                from main import clear_current_session
                clear_current_session()
            except ImportError:
                pass
            print("\n\n👋 Research session cancelled. Goodbye!")
        except Exception as e:
            # Clear session tracking on error
            try:
                from main import clear_current_session
                clear_current_session()
            except ImportError:
                pass
            self.logger.error(f"Error in interactive session: {e}")
            print(f"\n❌ An error occurred: {e}")
            print("The session has been saved and can be resumed later.")
    
    def _print_welcome(self) -> None:
        """Print welcome message and instructions."""
        print("🤖 Welcome to Deep Research Agent!")
        print("\nI'll help you make informed decisions through comprehensive research.")
        print("I can assist with any topic: health, finance, technology, lifestyle, and more.")
        print("\nLet's start by understanding what you need help with...")
        print()
    
    def _get_research_query(self) -> str:
        """Get and validate the research query from user."""
        while True:
            try:
                print("💭 What decision do you need help with today?")
                print("   (Example: 'Best smartphone under $500 for photography')")
                print()
                
                query = input("Your question: ").strip()
                
                if not query:
                    print("Please enter a research question.\n")
                    continue
                
                # Validate query
                validated_query = self.validator.validate_query(query)
                
                # Confirm query understanding
                print(f"\n📝 I understand you want to research: '{validated_query}'")
                confirm = input("Is this correct? (y/n): ").strip().lower()
                
                if confirm in ['y', 'yes', '']:
                    return validated_query
                
                print("Let's try again...\n")
                
            except ValidationError as e:
                print(f"❌ {e}\n")
            except (KeyboardInterrupt, EOFError):
                raise
    
    def _ask_personalization(self) -> bool:
        """Ask if user wants personalized recommendations."""
        while True:
            try:
                print("\n🎯 Should I personalize recommendations based on your profile?")
                print("   This helps me provide more relevant and actionable advice.")
                print("   (All information is stored locally and private)")
                print()
                
                response = input("Personalize recommendations? (y/n): ").strip().lower()
                
                if response in ['y', 'yes', '']:
                    return True
                elif response in ['n', 'no']:
                    return False
                else:
                    print("Please answer 'y' for yes or 'n' for no.\n")
                    
            except (KeyboardInterrupt, EOFError):
                raise
    
    def _gather_personalization(self, query: str, temp_session_id: str = None) -> Dict[str, Any]:
        """
        Gather personalization information using dynamic AI-driven conversation with intelligent mode selection.
        
        Args:
            query: User's research query
            temp_session_id: Temporary session ID for conversation tracking
            
        Returns:
            Dictionary of personalization data
        """
        if not self.personalization_engine or not self.mode_intelligence:
            # Fallback to static questions if AI engines not available
            return self._gather_static_personalization(query)
        
        print("\n🤖 Let me ask you some intelligent questions to personalize your research:")
        print("   I'll adapt my questions based on your responses for better recommendations.")
        print()
        
        try:
            # Analyze user signals to determine optimal conversation mode
            user_signals = self.mode_intelligence.analyze_user_signals(query)
            mode_recommendation = self.mode_intelligence.recommend_conversation_mode(user_signals)
            
            print(f"🎯 Detected conversation style: {mode_recommendation.recommended_mode.value.title()} Mode")
            print(f"   {mode_recommendation.reasoning}")
            print()
            
            # Initialize dynamic conversation with mode intelligence
            session_id = temp_session_id or f"personalization_{int(datetime.now().timestamp() * 1000)}"
            conversation_state = self.personalization_engine.initialize_conversation(query, session_id)
            self.current_conversation_state = conversation_state
            
            # Set initial conversation mode
            current_mode = mode_recommendation.recommended_mode
            self.adaptive_manager.current_mode = current_mode
            
            # Get mode-specific configuration
            mode_config = self.mode_intelligence.mode_configs[current_mode]
            max_questions = mode_config.max_questions
            
            context = {"personalize": True}
            user_responses = []
            response_times = []
            question_count = 0
            
            print(f"📋 I'll ask up to {max_questions} questions to understand your needs:")
            
            while question_count < max_questions:
                # Generate next intelligent question with mode-specific prompting
                mode_context = {
                    'user_query': query,
                    'context_type': user_signals.context_type,
                    'current_mode': current_mode.value
                }
                
                # Apply mode-specific prompt
                mode_prompt = self.mode_intelligence.create_mode_specific_prompt(current_mode, mode_context)
                
                question = self.personalization_engine.generate_next_question(
                    conversation_state, 
                    additional_context=mode_prompt
                )
                
                if not question:
                    print("✅ I have enough information to provide personalized recommendations!")
                    break
                
                # Ask the question with mode-appropriate formatting
                question_prefix = self._get_mode_question_prefix(current_mode, question_count + 1, max_questions)
                print(f"\n{question_prefix}")
                
                try:
                    start_time = datetime.now()
                    response = input(f"{question}\n➤ ").strip()
                    response_time = (datetime.now() - start_time).total_seconds()
                    
                    if not response:
                        print("   (Skipped)")
                        question_count += 1
                        continue
                    
                    # Track user response patterns
                    user_responses.append(response)
                    response_times.append(response_time)
                    
                    # Process the response
                    result = self.personalization_engine.process_user_response(
                        conversation_state, question, response
                    )
                    
                    # Monitor engagement and check for mode switching
                    if question_count >= 2:  # Need some history for engagement analysis
                        engagement_metrics = self.adaptive_manager.monitor_engagement(
                            user_responses, response_times
                        )
                        
                        should_switch = self.mode_intelligence.should_switch_mode(
                            current_mode, engagement_metrics, question_count + 1
                        )
                        
                        if should_switch:
                            # Determine new mode based on engagement
                            new_mode = self._determine_new_mode(current_mode, engagement_metrics, user_signals)
                            
                            if new_mode != current_mode:
                                transition = self.adaptive_manager.transition_between_modes(
                                    current_mode, new_mode, "Engagement-based adaptation"
                                )
                                
                                if transition.user_notification:
                                    print(f"\n🔄 {transition.transition_message}")
                                
                                current_mode = new_mode
                                max_questions = transition.new_questioning_depth
                                
                                print(f"   Switching to {current_mode.value.title()} Mode ({max_questions} questions max)")
                    
                    # Show brief acknowledgment based on mode
                    if result.get('extracted_info'):
                        acknowledgment = self._get_mode_acknowledgment(current_mode, question_count + 1)
                        print(f"   {acknowledgment}")
                    
                    question_count += 1
                    
                except (KeyboardInterrupt, EOFError):
                    print("\n   Personalization cancelled by user")
                    break
            
            # Get conversation summary
            summary = self.personalization_engine.get_conversation_summary(conversation_state)
            
            # Add mode intelligence insights to summary
            summary['conversation_mode_used'] = current_mode.value
            summary['mode_transitions'] = len(self.adaptive_manager.mode_history)
            summary['final_engagement'] = self.adaptive_manager.monitor_engagement(user_responses, response_times)
            
            # Convert to expected format
            extracted_context = self._convert_conversation_to_context(conversation_state, summary)
            
            # Show completion message with mode intelligence summary
            self._show_personalization_completion(current_mode, question_count, extracted_context)
            
            return extracted_context
            
        except Exception as e:
            self.logger.error(f"Error in dynamic personalization with mode intelligence: {e}")
            print("🔄 Falling back to standard questions...")
            return self._gather_static_personalization(query)
    
    def _convert_conversation_to_context(self, conversation_state, summary: Dict[str, Any]) -> Dict[str, Any]:
        """Convert conversation state to expected context format."""
        context = {"personalize": True}
        
        # Extract user information
        user_info = {}
        constraints = {}
        preferences = {}
        
        # Categorize the gathered profile information
        for key, value in conversation_state.user_profile.items():
            if key.lower() in ['age', 'weight', 'height', 'income', 'budget', 'experience_level']:
                user_info[key] = value
            elif key.lower() in ['timeline', 'location', 'constraints', 'deadline']:
                constraints[key] = value
            else:
                preferences[key] = value
        
        # Add structured context
        if user_info:
            context['user_info'] = user_info
        if constraints:
            context['constraints'] = constraints
        if preferences:
            context['preferences'] = preferences
        
        # Add intelligent insights
        context['conversation_insights'] = {
            'priority_factors': conversation_state.priority_factors,
            'confidence_scores': conversation_state.confidence_scores,
            'completion_confidence': conversation_state.completion_confidence,
            'key_insights': summary.get('key_insights', []),
            'research_recommendations': summary.get('research_recommendations', [])
        }
        
        return context
    
    def _gather_static_personalization(self, query: str) -> Dict[str, Any]:
        """
        Fallback method for static personalization questions.
        
        Args:
            query: User's research query
            
        Returns:
            Dictionary of personalization data
        """
        print("\n📋 Let me gather some information to personalize recommendations:")
        print("   (You can skip any question by pressing Enter)")
        print()
        
        # Classify query to determine relevant questions
        category = self._classify_query(query)
        questions = self.settings.get_category_questions(category)
        
        user_info = {}
        constraints = {}
        preferences = {}
        
        # Ask category-specific questions
        for question in questions:
            response = self._ask_personalization_question(question)
            if response:
                # Categorize the response
                if question.lower() in ['age', 'weight', 'height', 'income', 'budget']:
                    user_info[question] = response
                elif question.lower() in ['timeline', 'location', 'constraints']:
                    constraints[question] = response
                else:
                    preferences[question] = response
        
        # Ask general constraint questions
        budget = self._ask_optional("Budget range (if applicable)")
        if budget:
            constraints['budget'] = budget
        
        timeline = self._ask_optional("Timeline for decision")
        if timeline:
            constraints['timeline'] = timeline
        
        location = self._ask_optional("Location (if relevant)")
        if location:
            constraints['location'] = location
        
        context = {}
        if user_info:
            context['user_info'] = user_info
        if constraints:
            context['constraints'] = constraints
        if preferences:
            context['preferences'] = preferences
        
        return context
    
    def _classify_query(self, query: str) -> str:
        """
        Classify query into category for personalization.
        
        Args:
            query: User's research query
            
        Returns:
            Category string
        """
        # Simple keyword-based classification
        query_lower = query.lower()
        
        health_keywords = ['health', 'exercise', 'diet', 'fitness', 'medical', 'workout', 'nutrition']
        finance_keywords = ['money', 'investment', 'budget', 'loan', 'credit', 'insurance', 'financial']
        tech_keywords = ['software', 'app', 'computer', 'phone', 'technology', 'digital', 'online', 'smartphone', 'laptop', 'marketing']
        lifestyle_keywords = ['travel', 'food', 'restaurant', 'hobby', 'entertainment', 'shopping', 'destinations', 'hobbies', 'services']
        
        if any(keyword in query_lower for keyword in health_keywords):
            return 'health'
        elif any(keyword in query_lower for keyword in finance_keywords):
            return 'finance'
        elif any(keyword in query_lower for keyword in tech_keywords):
            return 'technology'
        elif any(keyword in query_lower for keyword in lifestyle_keywords):
            return 'lifestyle'
        else:
            return 'other'
    
    def _ask_personalization_question(self, question: str) -> Optional[str]:
        """Ask a specific personalization question."""
        try:
            response = input(f"{question.title()}: ").strip()
            return response if response else None
        except (KeyboardInterrupt, EOFError):
            raise
    
    def _ask_optional(self, question: str) -> Optional[str]:
        """Ask an optional question."""
        try:
            response = input(f"{question} (optional): ").strip()
            return response if response else None
        except (KeyboardInterrupt, EOFError):
            raise
    
    def _ask_report_depth(self) -> str:
        """Ask user for preferred report depth."""
        while True:
            try:
                print("\n📊 Choose your report depth:")
                print("   1. Quick (2-3 pages) - Key findings and top recommendations")
                print("   2. Standard (5-7 pages) - Balanced detail with actionable insights") 
                print("   3. Detailed (10+ pages) - Comprehensive analysis with methodology")
                print()
                
                choice = input("Report depth (1/2/3 or quick/standard/detailed): ").strip().lower()
                
                if choice in ['1', 'quick', 'q']:
                    return 'quick'
                elif choice in ['2', 'standard', 's', '']:
                    return 'standard'
                elif choice in ['3', 'detailed', 'd']:
                    return 'detailed'
                else:
                    print("Please choose 1, 2, or 3.\n")
                    
            except (KeyboardInterrupt, EOFError):
                raise
