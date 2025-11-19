"""
Conversation Handler for Deep Research Agent
Manages user interaction and guides through the research process.
"""

import logging
import re
from typing import Dict, Any, List, Optional
from datetime import datetime

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn

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
        self.console = Console()
        
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
            
            self.console.print(f"\n[bold blue]🔬 Starting Research Session:[/bold blue] {session_id}")
            self.console.rule()
            
            # Import here to avoid circular imports when modules are being created
            try:
                from core.research_engine import ResearchEngine
                from core.report_generator import ReportGenerator
                
                # Conduct research with progress feedback
                research_engine = ResearchEngine(self.settings)
                
                # Show research start message
                self.console.print(f"\n[bold green]🔬 Starting Iterative Research Process for:[/bold green] '{query}'")
                self.console.rule()
                
                research_results = research_engine.conduct_research(
                    query, context, session_id
                )
                
                # Generate report
                report_generator = ReportGenerator(self.settings)
                
                # Ask for report depth
                depth = self._ask_report_depth()
                
                with self.console.status("[bold green]Generating report...[/bold green]", spinner="dots"):
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
                self.console.print("[yellow]🚧 Core research modules are being implemented...[/yellow]")
                self.console.print("This is the foundation setup. Research functionality will be available soon!")
                self.console.print(f"\nSession created: {session_id}")
                self.console.print(f"Query: {query}")
                self.console.print(f"Context: {context}")
                
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
            self.console.print("\n\n[bold red]👋 Research session cancelled. Goodbye![/bold red]")
        except Exception as e:
            # Clear session tracking on error
            try:
                from main import clear_current_session
                clear_current_session()
            except ImportError:
                pass
            self.logger.error(f"Error in interactive session: {e}")
            self.console.print(f"\n[bold red]❌ An error occurred:[/bold red] {e}")
            self.console.print("The session has been saved and can be resumed later.")
    
    def _print_welcome(self) -> None:
        """Print welcome message and instructions."""
        welcome_text = """
[bold cyan]Welcome to Deep Research Agent![/bold cyan]

I'll help you make informed decisions through comprehensive research.
I can assist with any topic: health, finance, technology, lifestyle, and more.

Let's start by understanding what you need help with...
"""
        self.console.print(Panel(welcome_text.strip(), title="🤖 Deep Research Agent", border_style="blue"))
        self.console.print()
    
    def _get_research_query(self) -> str:
        """Get and validate the research query from user."""
        while True:
            try:
                self.console.print("[bold]💭 What decision do you need help with today?[/bold]")
                self.console.print("   (Example: 'Best smartphone under $500 for photography')")
                self.console.print()
                
                query = Prompt.ask("Your question").strip()
                
                if not query:
                    self.console.print("[yellow]Please enter a research question.[/yellow]\n")
                    continue
                
                # Validate query
                validated_query = self.validator.validate_query(query)
                
                # Confirm query understanding
                self.console.print(f"\n[bold]📝 I understand you want to research:[/bold] '{validated_query}'")
                if Confirm.ask("Is this correct?"):
                    return validated_query
                
                self.console.print("Let's try again...\n")
                
            except ValidationError as e:
                self.console.print(f"[red]❌ {e}[/red]\n")
            except (KeyboardInterrupt, EOFError):
                raise
    
    def _ask_personalization(self) -> bool:
        """Ask if user wants personalized recommendations."""
        while True:
            try:
                self.console.print("\n[bold]🎯 Should I personalize recommendations based on your profile?[/bold]")
                self.console.print("   This helps me provide more relevant and actionable advice.")
                self.console.print("   (All information is stored locally and private)")
                self.console.print()
                
                return Confirm.ask("Personalize recommendations?")
                    
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
        
        self.console.print("\n[bold]🤖 Let me ask you some intelligent questions to personalize your research:[/bold]")
        self.console.print("   I'll adapt my questions based on your responses for better recommendations.")
        self.console.print()
        
        try:
            # Analyze user signals to determine optimal conversation mode
            with self.console.status("[cyan]Analyzing research needs...[/cyan]", spinner="dots"):
                user_signals = self.mode_intelligence.analyze_user_signals(query)
                mode_recommendation = self.mode_intelligence.recommend_conversation_mode(user_signals)
            
            self.console.print(f"[bold green]🎯 Detected conversation style:[/bold green] {mode_recommendation.recommended_mode.value.title()} Mode")
            self.console.print(f"   {mode_recommendation.reasoning}")
            self.console.print()
            
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
            
            self.console.print(f"📋 I'll ask up to {max_questions} questions to understand your needs:")
            
            while question_count < max_questions:
                # Generate next intelligent question with mode-specific prompting
                mode_context = {
                    'user_query': query,
                    'context_type': user_signals.context_type,
                    'current_mode': current_mode.value
                }
                
                # Apply mode-specific prompt
                mode_prompt = self.mode_intelligence.create_mode_specific_prompt(current_mode, mode_context)
                
                with self.console.status("[cyan]Thinking...[/cyan]", spinner="dots"):
                    question = self.personalization_engine.generate_next_question(
                        conversation_state, 
                        additional_context=mode_prompt
                    )
                
                if not question:
                    self.console.print("[bold green]✅ I have enough information to provide personalized recommendations![/bold green]")
                    break
                
                # Ask the question with mode-appropriate formatting
                question_prefix = self._get_mode_question_prefix(current_mode, question_count + 1, max_questions)
                self.console.print(f"\n[bold]{question_prefix}[/bold]")
                
                try:
                    start_time = datetime.now()
                    response = Prompt.ask(question).strip()
                    response_time = (datetime.now() - start_time).total_seconds()
                    
                    if not response:
                        self.console.print("   (Skipped)")
                        question_count += 1
                        continue
                    
                    # Track user response patterns
                    user_responses.append(response)
                    response_times.append(response_time)
                    
                    # Process the response
                    with self.console.status("[cyan]Processing...[/cyan]", spinner="dots"):
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
                                    self.console.print(f"\n[yellow]🔄 {transition.transition_message}[/yellow]")
                                
                                current_mode = new_mode
                                max_questions = transition.new_questioning_depth
                                
                                self.console.print(f"   Switching to {current_mode.value.title()} Mode ({max_questions} questions max)")
                    
                    # Show brief acknowledgment based on mode
                    if result.get('extracted_info'):
                        acknowledgment = self._get_mode_acknowledgment(current_mode, question_count + 1)
                        self.console.print(f"   [italic]{acknowledgment}[/italic]")
                    
                    question_count += 1
                    
                except (KeyboardInterrupt, EOFError):
                    self.console.print("\n   [yellow]Personalization cancelled by user[/yellow]")
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
            self.console.print("[yellow]🔄 Falling back to standard questions...[/yellow]")
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
        self.console.print("\n[bold]📋 Let me gather some information to personalize recommendations:[/bold]")
        self.console.print("   (You can skip any question by pressing Enter)")
        self.console.print()
        
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
            response = Prompt.ask(f"{question.title()}").strip()
            return response if response else None
        except (KeyboardInterrupt, EOFError):
            raise
    
    def _ask_optional(self, question: str) -> Optional[str]:
        """Ask an optional question."""
        try:
            response = Prompt.ask(f"{question} (optional)").strip()
            return response if response else None
        except (KeyboardInterrupt, EOFError):
            raise
    
    def _ask_report_depth(self) -> str:
        """Ask user for preferred report depth."""
        while True:
            try:
                self.console.print("\n[bold]📊 Choose your report depth:[/bold]")
                self.console.print("   1. [cyan]Quick[/cyan] (2-3 pages) - Key findings and top recommendations")
                self.console.print("   2. [cyan]Standard[/cyan] (5-7 pages) - Balanced detail with actionable insights") 
                self.console.print("   3. [cyan]Detailed[/cyan] (10+ pages) - Comprehensive analysis with methodology")
                self.console.print()
                
                choice = Prompt.ask("Report depth", choices=["1", "2", "3", "quick", "standard", "detailed", "q", "s", "d"], default="standard")
                
                if choice in ['1', 'quick', 'q']:
                    return 'quick'
                elif choice in ['2', 'standard', 's']:
                    return 'standard'
                elif choice in ['3', 'detailed', 'd']:
                    return 'detailed'
                    
            except (KeyboardInterrupt, EOFError):
                raise
    
    def _get_mode_question_prefix(self, mode: ConversationMode, current: int, total: int) -> str:
        """Get mode-specific question prefix."""
        if mode == ConversationMode.QUICK:
            return f"⚡ Quick Question {current}/{total}:"
        elif mode == ConversationMode.DEEP:
            return f"🔍 Deep Dive {current}/{total}:"
        elif mode == ConversationMode.ADAPTIVE:
            return f"🔄 Adaptive Question {current}:"
        else:
            return f"❓ Question {current}/{total}:"
    
    def _get_mode_acknowledgment(self, mode: ConversationMode, current: int) -> str:
        """Get mode-specific acknowledgment."""
        acknowledgments = {
            ConversationMode.QUICK: ["Got it.", "Noted.", "Okay."],
            ConversationMode.STANDARD: ["Thanks, that helps.", "Understood.", "Good to know."],
            ConversationMode.DEEP: ["That's very helpful context.", "I appreciate that detail.", "This is important for the analysis."],
            ConversationMode.ADAPTIVE: ["Interesting.", "I see.", "That guides my next question."]
        }
        import random
        return random.choice(acknowledgments.get(mode, ["Got it."]))
    
    def _determine_new_mode(self, current_mode: ConversationMode, metrics: EngagementMetrics, signals: UserSignals) -> ConversationMode:
        """Determine the new mode based on engagement and signals."""
        # Simple logic for now, can be expanded
        if metrics.average_response_length > 50 and current_mode == ConversationMode.QUICK:
            return ConversationMode.STANDARD
        elif metrics.average_response_length > 100 and current_mode == ConversationMode.STANDARD:
            return ConversationMode.DEEP
        elif metrics.average_response_length < 10 and current_mode == ConversationMode.DEEP:
            return ConversationMode.STANDARD
        return current_mode
    
    def _show_personalization_completion(self, mode: ConversationMode, count: int, context: Dict[str, Any]) -> None:
        """Show personalization completion summary."""
        self.console.print("\n[bold green]✅ Personalization Complete![/bold green]")
        self.console.print(f"   Mode used: {mode.value.title()}")
        self.console.print(f"   Questions asked: {count}")
        
        insights = context.get('conversation_insights', {}).get('key_insights', [])
        if insights:
            self.console.print("\n[bold]🔑 Key Insights Gathered:[/bold]")
            for insight in insights[:3]:
                self.console.print(f"   • {insight}")
        self.console.print()
    
    def _show_completion_message(self, session_id: str, report_path: str, research_results: Dict[str, Any]) -> None:
        """
        Show completion message with session details.
        
        Args:
            session_id: The session ID
            report_path: Path to the generated report
            research_results: The results of the research
        """
        self.console.print("\n[bold green]✅ Research Session Completed Successfully![/bold green]")
        self.console.rule()
        self.console.print(f"🆔 Session ID: [cyan]{session_id}[/cyan]")
        self.console.print(f"📄 Report: [blue]{report_path}[/blue]")
        
        confidence = research_results.get('confidence_score', 0.0)
        self.console.print(f"🎯 Confidence Score: {confidence:.2f}")
        
        self.console.print("\nYou can view the full report in the path above.")
        self.console.print("[italic]Thank you for using Deep Research Agent![/italic]")
