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
            import google.generativeai as genai
            genai.configure(api_key=settings.gemini_api_key)
            gemini_client = genai.GenerativeModel('gemini-1.5-flash')
            self.personalization_engine = DynamicPersonalizationEngine(gemini_client)
        except Exception as e:
            self.logger.warning(f"Could not initialize personalization engine: {e}")
            self.personalization_engine = None
        
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
        Gather personalization information using dynamic AI-driven conversation.
        
        Args:
            query: User's research query
            
        Returns:
            Dictionary of personalization data
        """
        if not self.personalization_engine:
            # Fallback to static questions if personalization engine not available
            return self._gather_static_personalization(query)
        
        print("\n🤖 Let me ask you some intelligent questions to personalize your research:")
        print("   I'll adapt my questions based on your responses for better recommendations.")
        print()
        
        try:
            # Initialize dynamic conversation
            session_id = temp_session_id or f"personalization_{int(datetime.now().timestamp() * 1000)}"
            conversation_state = self.personalization_engine.initialize_conversation(query, session_id)
            self.current_conversation_state = conversation_state
            
            # Conduct intelligent conversation with dynamic question limit
            # The personalization engine will determine when to stop based on information quality
            conversation_state = self.personalization_engine.initialize_conversation(query, session_id)
            self.current_conversation_state = conversation_state
            
            context = {"personalize": True}
            
            question_count = 0
            max_absolute_questions = 10  # Safety limit to prevent infinite loops
            
            while question_count < max_absolute_questions:
                # Generate next intelligent question
                question = self.personalization_engine.generate_next_question(conversation_state)
                
                if not question:
                    print("✅ I have enough information to provide personalized recommendations!")
                    break
                
                # Ask the question
                print(f"\n💭 Question {question_count + 1}:")
                try:
                    response = input(f"{question}\n➤ ").strip()
                    
                    if not response:
                        print("   (Skipped)")
                        question_count += 1
                        continue
                    
                    # Process the response
                    result = self.personalization_engine.process_user_response(
                        conversation_state, question, response
                    )
                    
                    # Show brief acknowledgment
                    if result.get('extracted_info'):
                        print("   ✓ Got it! This helps me understand your needs better.")
                    
                    question_count += 1
                    
                except (KeyboardInterrupt, EOFError):
                    print("\n   Personalization cancelled by user")
                    break
            
            # Get conversation summary
            summary = self.personalization_engine.get_conversation_summary(conversation_state)
            
            # Convert to expected format
            extracted_context = self._convert_conversation_to_context(conversation_state, summary)
            
            print(f"\n🎯 Personalization complete! Gathered insights on {len(conversation_state.user_profile)} key areas.")
            
            return extracted_context
            
        except Exception as e:
            self.logger.error(f"Error in dynamic personalization: {e}")
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
    
    def _show_completion_message(self, session_id: str, report_path: str, 
                                research_results: Dict[str, Any]) -> None:
        """Show completion message with results."""
        confidence = research_results.get('confidence_score', 0.0)
        
        print("\n" + "=" * 60)
        print("✅ Research Complete!")
        print("=" * 60)
        print(f"Session ID: {session_id}")
        print(f"Confidence Score: {confidence:.1%}")
        print(f"Report Location: {report_path}")
        print()
        print("🎉 Your personalized research report is ready!")
        print("You can find detailed findings and recommendations in the report file.")
        print()
        print("Thank you for using Deep Research Agent!")
        print("=" * 60)
    
    def display_progress(self, stage: int, stage_name: str, message: str) -> None:
        """
        Display research progress to user.
        
        Args:
            stage: Current stage number
            stage_name: Name of current stage
            message: Progress message
        """
        total_stages = len(self.settings.research_stages)
        
        print(f"\n🔬 STAGE {stage}/{total_stages}: {stage_name}")
        print(f"   {message}")
        
        # Show progress bar
        progress = stage / total_stages
        bar_length = 40
        filled_length = int(bar_length * progress)
        bar = "█" * filled_length + "░" * (bar_length - filled_length)
        
        print(f"   [{bar}] {progress:.0%}")
    
    def display_error(self, error_message: str, is_recoverable: bool = True) -> None:
        """
        Display error message to user.
        
        Args:
            error_message: Error description
            is_recoverable: Whether the error is recoverable
        """
        print(f"\n❌ {error_message}")
        
        if is_recoverable:
            print("   Attempting to continue with available information...")
        else:
            print("   This error cannot be recovered from automatically.")
    
    def confirm_action(self, message: str) -> bool:
        """
        Ask user to confirm an action.
        
        Args:
            message: Confirmation message
            
        Returns:
            True if confirmed
        """
        try:
            response = input(f"{message} (y/n): ").strip().lower()
            return response in ['y', 'yes', '']
        except (KeyboardInterrupt, EOFError):
            return False
