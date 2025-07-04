"""
Dynamic Personalization Engine for Deep Research Agent
Main orchestration class that integrates conversation state, AI question generation, 
context analysis, and conversation memory to create intelligent, adaptive conversations.
"""

import json
import logging
import time
import re
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import asdict
from datetime import datetime

from google import genai
try:
    from google.genai import types
except ImportError:
    # Fallback for older versions
    types = None

# Import Phase 1 components
from .conversation_state import ConversationState, QuestionAnswer, QuestionType
from .ai_question_generator import AIQuestionGenerator
from .context_analyzer import ContextAnalyzer
from .conversation_memory import ConversationHistory


class DynamicPersonalizationEngine:
    """
    Main orchestration class for intelligent conversation personalization.
    
    Integrates all Phase 1 components to provide adaptive, context-aware
    conversation management that learns and evolves with each interaction.
    """
    
    def __init__(self, 
                 gemini_client: Optional[genai.Client] = None,
                 conversation_history: Optional[ConversationHistory] = None,
                 model_name: str = "gemini-2.0-flash-001",
                 settings: Optional[Any] = None):
        """
        Initialize the Dynamic Personalization Engine.
        
        Args:
            gemini_client: Configured Gemini client for AI operations
            conversation_history: Optional existing conversation history
            model_name: Name of the Gemini model to use for generation
            settings: Configuration settings for the engine
        """
        self.logger = logging.getLogger(__name__)
        self.model_name = model_name
        
        # Initialize Phase 1 components
        self.question_generator = AIQuestionGenerator(gemini_client, model_name, settings)
        self.context_analyzer = ContextAnalyzer()  # ContextAnalyzer doesn't take gemini_client
        self.conversation_history = conversation_history or ConversationHistory()
        
        # Engine configuration
        self.max_questions_per_session = 10
        self.min_confidence_threshold = 0.6
        self.adaptive_depth_enabled = True
        
        self.logger.info("Dynamic Personalization Engine initialized")
    
    def initialize_conversation(self, user_query: str, session_id: str) -> ConversationState:
        """
        Initialize a new dynamic conversation session.
        
        Args:
            user_query: The user's initial research query
            session_id: Unique identifier for the conversation session
            
        Returns:
            ConversationState: Initialized conversation state
        """
        try:
            self.logger.info(f"Initializing conversation session: {session_id}")
            
            # Create initial conversation state
            conversation_state = ConversationState(
                session_id=session_id,
                user_query=user_query
            )
            
            # Initialize metadata
            conversation_state.metadata = {
                'started_at': datetime.now().isoformat(),
                'engine_version': '2.1.0',
                'adaptive_mode': True
            }
            
            # Perform initial analysis and store topics as domain expertise
            initial_topics = self._extract_topics_from_query(user_query)
            for topic in initial_topics:
                conversation_state.context_understanding.domain_expertise[topic] = 0.3  # Low initial expertise
            
            # Set initial focus areas using priority factors
            for topic in initial_topics[:5]:  # Limit to top 5
                conversation_state.priority_factors[topic] = 0.5  # Initial moderate priority
            
            # Store in conversation history
            self.conversation_history.add_conversation_state(conversation_state)
            
            self.logger.debug(f"Conversation initialized with {len(conversation_state.priority_factors)} priority areas")
            return conversation_state
            
        except Exception as e:
            self.logger.error(f"Error initializing conversation: {e}")
            raise
    
    def generate_next_question(self, conversation_state: ConversationState, additional_context: Optional[str] = None) -> Optional[str]:
        """
        Generate the next intelligent question using pure AI without category constraints.
        
        Uses advanced AI-driven analysis to determine the most valuable next question
        based on conversation flow, user engagement, and information gaps without
        relying on predefined categories or templates.
        
        Parameters:
            conversation_state: Current state of the conversation including history,
                              user profile, and priority factors
            additional_context: Optional additional context string to guide question 
                              generation (e.g., specific focus areas)
            
        Returns:
            Next question to ask as a string, or None if conversation is deemed
            complete based on information sufficiency and user engagement metrics
            
        Example:
            ```python
            engine = DynamicPersonalizationEngine()
            state = engine.initialize_conversation("laptop for gaming", "session_123")
            question = engine.generate_next_question(state)
            # Returns: "What's most important to you when choosing a gaming laptop?"
            ```
        """
        try:
            # Check if we should continue the conversation
            if not self._should_continue_conversation(conversation_state):
                self.logger.info("Conversation deemed complete, no more questions needed")
                return None
            
            # Get already asked questions to avoid repetition
            asked_questions = [qa.question for qa in conversation_state.question_history]
            
            # Generate intelligent question using pure AI - no category constraints
            question = self._generate_pure_ai_question_unconstrained(conversation_state, asked_questions, additional_context)
            
            if question:
                self.logger.debug(f"Generated pure AI question: {question[:50]}...")
                
                # Update conversation metadata
                conversation_state.metadata['last_question_generated'] = datetime.now().isoformat()
                conversation_state.metadata['question_count'] = len(conversation_state.question_history) + 1
                
                return question
            else:
                self.logger.warning("Failed to generate a valid question")
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error generating next question: {e}")
            return None
    
    def process_user_response(self, 
                            conversation_state: ConversationState, 
                            question: str, 
                            response: str) -> Dict[str, Any]:
        """
        Process user response using pure AI analysis without category constraints.
        
        Analyzes user responses using contextual AI to extract personalization
        information, update conversation state, and track question effectiveness
        without relying on predefined categories.
        
        Parameters:
            conversation_state: Current conversation state to be updated
            question: The question that was asked to the user
            response: User's response text to analyze
            
        Returns:
            Dictionary containing:
            - extracted_info: New personalization data extracted from response
            - response_analysis: AI analysis including priorities and emotional indicators
            - updated_priority_factors: Current priority factors after update
            - conversation_progress: Progress metrics and completion estimates
            
        Raises:
            Exception: If response processing fails, returns empty dict
            
        Example:
            ```python
            result = engine.process_user_response(
                conversation_state,
                "What's most important to you?",
                "I need something reliable for work presentations"
            )
            # Returns: {'extracted_info': {'reliability_priority': '...'}, ...}
            ```
        """
        try:
            self.logger.debug(f"Processing response to: {question[:50]}...")
            
            # Create question-answer pair - let AI determine everything naturally
            qa_pair = QuestionAnswer(
                question=question,
                answer=response,
                question_type=QuestionType.OPEN_ENDED,  # Default type
                timestamp=datetime.now(),
                category='ai_discovered',  # Let AI categorize naturally
                confidence=0.5,  # Will be updated after analysis
                importance=0.7,  # Personalization is important
                context={}
            )
            
            # Update the conversation state with this new Q&A first
            conversation_state.question_history.append(qa_pair)
            
            # Use context analyzer to extract insights
            context_analysis_result = self.context_analyzer.analyze_context(conversation_state)
            
            # Extract response analysis from the context analysis result
            response_analysis = {
                'priorities': [p.__dict__ for p in context_analysis_result.priority_insights],
                'emotional_indicators': [e.__dict__ for e in context_analysis_result.emotional_indicators],
                'communication_style': context_analysis_result.communication_style.value,
                'confidence_score': context_analysis_result.overall_confidence,
                'extracted_info': self._extract_info_from_priorities(context_analysis_result.priority_insights),
                'discovered_themes': self._extract_themes_from_analysis(context_analysis_result)
            }
            
            # Extract personalization information using AI-driven analysis
            extracted_info = self._extract_personalization_info_ai_driven(response, response_analysis, conversation_state)
            
            # Update user profile with new information
            self._update_user_profile(conversation_state, extracted_info)
            
            # Update the Q&A pair with better categorization from AI analysis
            conversation_state.question_history[-1].category = self._determine_natural_category(question, response, extracted_info)
            conversation_state.question_history[-1].confidence = response_analysis.get('confidence_score', 0.5)
            
            # Update priority factors based on discovered themes
            self._update_priority_factors_from_themes(conversation_state, response_analysis)
            
            # Store in conversation history
            self.conversation_history.track_question_effectiveness(
                session_id=conversation_state.session_id,
                question=question,
                response=response,
                question_type=QuestionType.OPEN_ENDED,
                category=conversation_state.question_history[-1].category
            )
            
            # Update the conversation history with the latest state
            self.conversation_history.add_conversation_state(conversation_state)
            
            # Update conversation metadata
            conversation_state.metadata['last_response_processed'] = datetime.now().isoformat()
            conversation_state.metadata['total_responses'] = len(conversation_state.question_history)
            
            result = {
                'extracted_info': extracted_info,
                'response_analysis': response_analysis,
                'updated_priority_factors': conversation_state.priority_factors,
                'conversation_progress': self._calculate_conversation_progress(conversation_state)
            }
            
            self.logger.debug(f"Response processed, extracted {len(extracted_info)} info items")
            return result
            
        except Exception as e:
            self.logger.error(f"Error processing user response: {e}")
            return {}
    
    def get_conversation_summary(self, conversation_state: ConversationState) -> Dict[str, Any]:
        """
        Generate a comprehensive summary of the conversation state.
        
        Creates a detailed summary including conversation metrics, quality assessment,
        key insights, and research recommendations based on the full conversation
        history and user profile data.
        
        Parameters:
            conversation_state: Current conversation state to summarize
            
        Returns:
            Dictionary containing:
            - session_id: Session identifier
            - conversation_length: Number of questions asked
            - user_profile_completeness: Amount of profile information gathered
            - priority_factors: Current priority factor mapping
            - progress_metrics: Conversation progress and depth metrics
            - quality_assessment: Quality indicators for the conversation
            - key_insights: Important insights discovered during conversation
            - research_recommendations: Suggested focus areas for research
            - metadata: Additional conversation metadata
            
        Example:
            ```python
            summary = engine.get_conversation_summary(conversation_state)
            print(f"Gathered {summary['user_profile_completeness']} data points")
            print(f"Key insights: {summary['key_insights']}")
            ```
        """
        try:
            # Calculate conversation metrics
            progress_metrics = self._calculate_conversation_progress(conversation_state)
            
            # Analyze conversation quality
            quality_assessment = self._assess_conversation_quality(conversation_state)
            
            # Identify key insights
            key_insights = self._extract_key_insights(conversation_state)
            
            # Generate recommendations for research
            research_recommendations = self._generate_research_recommendations(conversation_state)
            
            summary = {
                'session_id': conversation_state.session_id,
                'conversation_length': len(conversation_state.question_history),
                'user_profile_completeness': len(conversation_state.user_profile),
                'priority_factors': conversation_state.priority_factors,
                'progress_metrics': progress_metrics,
                'quality_assessment': quality_assessment,
                'key_insights': key_insights,
                'research_recommendations': research_recommendations,
                'metadata': conversation_state.metadata
            }
            
            self.logger.info(f"Generated conversation summary for session {conversation_state.session_id}")
            return summary
            
        except Exception as e:
            self.logger.error(f"Error generating conversation summary: {e}")
            return {}
    
    def adapt_conversation_strategy(self, conversation_state: ConversationState) -> Dict[str, Any]:
        """
        Adapt conversation strategy based on current progress and user patterns.
        
        Analyzes conversation patterns, user engagement, and efficiency metrics
        to provide strategic recommendations for optimizing the conversation flow
        and improving information gathering.
        
        Parameters:
            conversation_state: Current conversation state to analyze
            
        Returns:
            Dictionary containing:
            - detected_patterns: Conversation patterns and trends identified
            - engagement_level: Current user engagement assessment (high/medium/low)
            - recommended_question_types: Optimal question types for current state
            - efficiency_metrics: Conversation efficiency measurements
            - strategy_recommendations: Specific strategic recommendations for improvement
            
        Example:
            ```python
            strategy = engine.adapt_conversation_strategy(conversation_state)
            if strategy['engagement_level'] == 'low':
                # Implement strategy recommendations
                for rec in strategy['strategy_recommendations']:
                    print(f"Strategy: {rec}")
            ```
        """
        try:
            # Analyze conversation patterns
            patterns = self._analyze_conversation_patterns(conversation_state)
            
            # Assess user engagement
            engagement_level = self._assess_user_engagement(conversation_state)
            
            # Determine optimal question types
            optimal_question_types = self._determine_optimal_question_types(conversation_state)
            
            # Calculate conversation efficiency
            efficiency_metrics = self._calculate_conversation_efficiency(conversation_state)
            
            adaptations = {
                'detected_patterns': patterns,
                'engagement_level': engagement_level,
                'recommended_question_types': optimal_question_types,
                'efficiency_metrics': efficiency_metrics,
                'strategy_recommendations': self._generate_strategy_recommendations(
                    patterns, engagement_level, efficiency_metrics
                )
            }
            
            self.logger.debug(f"Conversation strategy adapted with {len(adaptations['strategy_recommendations'])} recommendations")
            return adaptations
            
        except Exception as e:
            self.logger.error(f"Error adapting conversation strategy: {e}")
            return {}
    
    # Private helper methods
    
    def _should_continue_conversation(self, conversation_state: ConversationState) -> bool:
        """
        Determine if conversation should continue based on AI-driven assessment.
        
        Evaluates conversation progress using multiple criteria including question
        count, information density, user engagement patterns, and response quality
        to make intelligent decisions about conversation completion.
        
        Parameters:
            conversation_state: Current conversation state to evaluate
            
        Returns:
            True if conversation should continue, False if sufficient information
            has been gathered or user engagement is declining
            
        Notes:
            - Hard limit of 8 questions maximum
            - Stops early if high information density (4+ data points with 70%+ density)
            - Considers user engagement based on response patterns
            - Balances thoroughness with user experience
        """
        questions_asked = len(conversation_state.question_history)
        info_gathered = len(conversation_state.user_profile)
        
        # Basic limits
        if questions_asked >= 8:  # Hard limit
            self.logger.info(f"Reached maximum question limit: {questions_asked}")
            return False
        
        # If we have good information density, we can be more selective
        info_density = info_gathered / max(1, questions_asked)
        
        # Stop if we have sufficient information (4+ data points with good responses)
        if info_gathered >= 4 and info_density > 0.7:
            self.logger.info(f"Sufficient high-quality information gathered: {info_gathered} data points")
            return False
        
        # Stop if we have reasonable information and many questions asked
        if info_gathered >= 3 and questions_asked >= 5:
            self.logger.info(f"Reasonable information with sufficient questions: {info_gathered} data points, {questions_asked} questions")
            return False
        
        # Check user engagement - if responses are getting very minimal, stop
        if questions_asked >= 4:
            recent_responses = [qa.answer for qa in conversation_state.question_history[-3:]]
            avg_recent_length = sum(len(resp.split()) for resp in recent_responses) / len(recent_responses)
            # Very conservative threshold - only stop if consistently minimal
            if avg_recent_length < 1.2 and all(len(resp.split()) == 1 for resp in recent_responses):
                self.logger.info("User engagement appears consistently minimal, ending conversation")
                return False
        
        self.logger.debug(f"Continuing conversation: {questions_asked} questions, {info_gathered} data points, density: {info_density:.2f}")
        return True
    
    def _analyze_current_context(self, conversation_state: ConversationState) -> Dict[str, Any]:
        """Analyze current conversation context for question generation."""
        context = {
            'conversation_flow': len(conversation_state.question_history),
            'information_density': len(conversation_state.user_profile),
            'priority_factors': conversation_state.priority_factors,
            'completion_confidence': conversation_state.completion_confidence,
            'information_gaps': conversation_state.information_gaps,
            'questions_asked': len(conversation_state.question_history),
            'last_responses': [qa.answer for qa in conversation_state.question_history[-3:]] if conversation_state.question_history else [],
            'asked_questions': [qa.question for qa in conversation_state.question_history] if conversation_state.question_history else []
        }
        
        return context
    
    def _identify_information_gaps(self, conversation_state: ConversationState) -> List[str]:
        """Identify key information gaps using AI-driven analysis rather than predefined categories."""
        try:
            # Use AI to discover what's missing contextually
            prompt = f"""Analyze this research conversation to identify what key information is missing:

USER'S ORIGINAL QUERY: {conversation_state.user_query}

CONVERSATION HISTORY:
{self._format_conversation_for_analysis(conversation_state)}

CURRENT USER PROFILE:
{json.dumps(conversation_state.user_profile, indent=2) if conversation_state.user_profile else "No profile information yet"}

Based on the user's specific query and what's been discussed, identify 3-5 information areas that are missing and would genuinely improve research quality. Think about:
- What context about their specific situation is unclear?
- What practical factors haven't been explored?
- What would help understand their success criteria?
- What constraints or preferences are unknown?

Return only a JSON array of specific information gap descriptions (as strings). Be specific to this user's actual needs, not generic categories.

Example: ["budget_constraints_for_software", "team_size_and_collaboration_needs", "integration_requirements_with_existing_systems"]
"""

            response = self.research_engine.gemini_client._make_request(prompt)
            
            if response and '[' in response and ']' in response:
                start = response.find('[')
                end = response.rfind(']') + 1
                json_text = response[start:end]
                
                try:
                    gaps = json.loads(json_text)
                    if isinstance(gaps, list) and all(isinstance(item, str) for item in gaps):
                        self.logger.debug(f"AI identified contextual gaps: {gaps}")
                        return gaps[:5]
                except json.JSONDecodeError:
                    pass
            
            # Fallback to contextual analysis
            return self._analyze_contextual_gaps(conversation_state)
            
        except Exception as e:
            self.logger.warning(f"AI gap identification failed: {e}")
            return self._analyze_contextual_gaps(conversation_state)
    
    def _analyze_contextual_gaps(self, conversation_state: ConversationState) -> List[str]:
        """Analyze information gaps based on conversation context without predefined categories."""
        gaps = []
        
        # Analyze conversation flow for natural gaps
        questions_asked = len(conversation_state.question_history)
        info_gathered = len(conversation_state.user_profile)
        
        # Early conversation - focus on foundational understanding
        if info_gathered < 2:
            query_lower = conversation_state.user_query.lower()
            
            # Infer what might be missing based on query intent
            if any(word in query_lower for word in ['buy', 'purchase', 'cost']):
                gaps.append('financial_parameters_and_constraints')
            if any(word in query_lower for word in ['best', 'recommend', 'choose']):
                gaps.append('selection_criteria_and_priorities')
            if any(word in query_lower for word in ['work', 'business', 'team']):
                gaps.append('organizational_context_and_requirements')
            if any(word in query_lower for word in ['learn', 'understand', 'new']):
                gaps.append('background_and_experience_context')
            
            gaps.append('specific_use_case_and_requirements')
            
        else:
            # Later conversation - analyze what themes are covered vs missing
            profile_content = ' '.join(str(v) for v in conversation_state.user_profile.values()).lower()
            
            # Check for missing thematic areas
            covered_themes = set()
            if any(word in profile_content for word in ['budget', 'cost', 'price', 'money']):
                covered_themes.add('financial_aspects')
            if any(word in profile_content for word in ['time', 'deadline', 'urgent', 'timeline']):
                covered_themes.add('temporal_constraints')
            if any(word in profile_content for word in ['team', 'organization', 'company', 'work']):
                covered_themes.add('organizational_context')
            if any(word in profile_content for word in ['quality', 'performance', 'reliability']):
                covered_themes.add('quality_expectations')
            if any(word in profile_content for word in ['experience', 'skill', 'background']):
                covered_themes.add('expertise_context')
            
            # Suggest complementary information areas
            potential_gaps = []
            if 'financial_aspects' not in covered_themes:
                potential_gaps.append('budget_and_cost_considerations')
            if 'temporal_constraints' not in covered_themes:
                potential_gaps.append('timeline_and_urgency_factors')
            if 'organizational_context' not in covered_themes:
                potential_gaps.append('organizational_environment_and_constraints')
            if 'quality_expectations' not in covered_themes:
                potential_gaps.append('quality_and_performance_requirements')
            if 'expertise_context' not in covered_themes:
                potential_gaps.append('experience_level_and_technical_background')
            
            # Add general decision-making gaps
            potential_gaps.extend([
                'success_criteria_and_measurement',
                'decision_constraints_and_limitations',
                'stakeholder_considerations'
            ])
            
            # Filter out already covered areas and return most relevant
            gaps = [gap for gap in potential_gaps if not any(
                theme in gap.lower() for theme in covered_themes
            )][:4]
        
        self.logger.debug(f"Identified contextual information gaps: {gaps}")
        return gaps
    
    def _format_conversation_for_analysis(self, conversation_state: ConversationState) -> str:
        """Format conversation history for AI analysis."""
        if not conversation_state.question_history:
            return "No conversation history yet"
        
        formatted = []
        for i, (question, answer) in enumerate(conversation_state.question_history):
            formatted.append(f"Q{i+1}: {question}")
            formatted.append(f"A{i+1}: {answer}")
        
        return '\n'.join(formatted)
    
    def _extract_focus_areas(self, initial_context: Dict[str, Any]) -> List[str]:
        """Extract focus areas from initial context analysis."""
        # Extract from context analysis results
        focus_areas = []
        
        if 'detected_topics' in initial_context:
            focus_areas.extend(initial_context['detected_topics'])
        
        # Remove duplicates and return top areas
        return list(set(focus_areas))[:5]
    
    def _update_priority_factors(self, conversation_state: ConversationState, analysis: Dict[str, Any]):
        """Update priority factors based on latest response analysis."""
        if 'new_topics' in analysis:
            for topic in analysis['new_topics']:
                if topic not in conversation_state.priority_factors:
                    conversation_state.priority_factors[topic] = 0.6  # New topics get moderate priority
        
        # Update confidence scores for existing priorities
        if 'confidence_score' in analysis:
            for topic in conversation_state.priority_factors.keys():
                if topic in conversation_state.confidence_scores:
                    # Update existing confidence
                    conversation_state.confidence_scores[topic] = analysis['confidence_score']
                else:
                    # Add new confidence score
                    conversation_state.confidence_scores[topic] = analysis['confidence_score']
    
    def _extract_personalization_info(self, response: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Extract personalization information from user response."""
        extracted = {}
        
        # Extract from context analysis
        if 'extracted_info' in analysis:
            extracted.update(analysis['extracted_info'])
        
        # Add response length as engagement indicator
        extracted['response_engagement'] = len(response.split())
        
        # Add timestamp
        extracted['extracted_at'] = datetime.now().isoformat()
        
        return extracted
    
    def _update_user_profile(self, conversation_state: ConversationState, new_info: Dict[str, Any]):
        """Update user profile with new information."""
        for key, value in new_info.items():
            if key not in ['response_engagement', 'extracted_at']:  # Skip metadata
                conversation_state.user_profile[key] = value
    
    def _update_focus_areas(self, conversation_state: ConversationState, analysis: Dict[str, Any]):
        """Update focus areas based on latest response analysis."""
        if 'new_topics' in analysis:
            for topic in analysis['new_topics']:
                if topic not in conversation_state.current_focus_areas:
                    conversation_state.current_focus_areas.append(topic)
        
        # Keep only top 5 focus areas
        conversation_state.current_focus_areas = conversation_state.current_focus_areas[:5]
    
    def _calculate_conversation_progress(self, conversation_state: ConversationState) -> Dict[str, Any]:
        """Calculate conversation progress metrics."""
        return {
            'questions_asked': len(conversation_state.question_history),
            'information_gathered': len(conversation_state.user_profile),
            'priority_factors_explored': len(conversation_state.priority_factors),
            'conversation_depth_score': self._calculate_depth_score(conversation_state),
            'completeness_estimate': conversation_state.completion_confidence
        }
    
    def _assess_conversation_quality(self, conversation_state: ConversationState) -> Dict[str, Any]:
        """Assess the quality of the conversation."""
        return {
            'response_quality': 'high' if len(conversation_state.question_history) > 0 else 'unknown',
            'information_density': len(conversation_state.user_profile) / max(1, len(conversation_state.question_history)),
            'priority_consistency': len(set(conversation_state.priority_factors.keys())) / max(1, len(conversation_state.priority_factors))
        }
    
    def _extract_key_insights(self, conversation_state: ConversationState) -> List[str]:
        """Extract key insights from the conversation."""
        insights = []
        
        # Basic insights based on gathered information
        if 'expertise_level' in conversation_state.user_profile:
            insights.append(f"User expertise: {conversation_state.user_profile['expertise_level']}")
        
        if 'context' in conversation_state.user_profile:
            insights.append(f"Usage context: {conversation_state.user_profile['context']}")
        
        return insights
    
    def _generate_research_recommendations(self, conversation_state: ConversationState) -> List[str]:
        """Generate recommendations for the research phase."""
        recommendations = []
        
        # Basic recommendations based on priority factors
        for area, priority in conversation_state.priority_factors.items():
            if priority > 0.6:  # High priority areas
                recommendations.append(f"Prioritize research on: {area}")
        
        return recommendations
    
    def _analyze_conversation_patterns(self, conversation_state: ConversationState) -> Dict[str, Any]:
        """Analyze patterns in the conversation."""
        return {
            'avg_response_length': sum(len(qa.answer.split()) for qa in conversation_state.question_history) / max(1, len(conversation_state.question_history)),
            'response_trend': 'stable',  # Would need more sophisticated analysis
            'engagement_pattern': 'consistent'  # Would need more sophisticated analysis
        }
    
    def _assess_user_engagement(self, conversation_state: ConversationState) -> str:
        """Assess user engagement level."""
        if not conversation_state.question_history:
            return 'unknown'
        
        avg_response_length = sum(len(qa.answer.split()) for qa in conversation_state.question_history) / len(conversation_state.question_history)
        
        if avg_response_length > 20:
            return 'high'
        elif avg_response_length > 10:
            return 'medium'
        else:
            return 'low'
    
    def _determine_optimal_question_types(self, conversation_state: ConversationState) -> List[str]:
        """Determine optimal question types for current conversation state."""
        question_types = []
        
        # Basic question type determination
        if len(conversation_state.question_history) < 3:
            question_types.append('open_ended')
        else:
            question_types.extend(['specific', 'clarifying'])
        
        return question_types
    
    def _calculate_conversation_efficiency(self, conversation_state: ConversationState) -> Dict[str, float]:
        """Calculate conversation efficiency metrics."""
        questions_count = len(conversation_state.question_history)
        info_count = len(conversation_state.user_profile)
        
        return {
            'information_per_question': info_count / max(1, questions_count),
            'priority_coverage': len(conversation_state.priority_factors) / max(1, questions_count),
            'conversation_velocity': questions_count / 10  # Normalize by expected max
        }
    
    def _generate_strategy_recommendations(self, patterns: Dict, engagement: str, efficiency: Dict) -> List[str]:
        """Generate strategy recommendations based on analysis."""
        recommendations = []
        
        if engagement == 'low':
            recommendations.append("Consider shorter, more focused questions")
        
        if efficiency['information_per_question'] < 0.5:
            recommendations.append("Focus on more information-rich questions")
        
        return recommendations
    
    def _analyze_focus_evolution(self, conversation_state: ConversationState) -> Dict[str, Any]:
        """Analyze how focus areas have evolved."""
        return {
            'focus_stability': 'stable',  # Would need historical comparison
            'new_areas_discovered': 0,    # Would need to track evolution
            'areas_abandoned': 0          # Would need to track evolution
        }
    
    def _calculate_depth_score(self, conversation_state: ConversationState) -> float:
        """Calculate conversation depth score."""
        if not conversation_state.question_history:
            return 0.0
        
        # Simple depth calculation based on follow-up questions and detail level
        depth_score = len(conversation_state.question_history) * 0.1
        depth_score += len(conversation_state.user_profile) * 0.05
        
        return min(1.0, depth_score)
    
    def _extract_topics_from_query(self, query: str) -> List[str]:
        """Extract basic topics from initial query using simple keyword analysis."""
        topics = []
        query_lower = query.lower()
        
        # Simple topic extraction
        topic_keywords = {
            'laptop': ['laptop', 'computer', 'notebook'],
            'programming': ['programming', 'coding', 'development', 'software'],
            'budget': ['budget', 'cost', 'price', 'money', '$'],
            'gaming': ['gaming', 'games', 'game'],
            'work': ['work', 'business', 'office', 'professional'],
            'photography': ['photography', 'photo', 'camera'],
            'music': ['music', 'audio', 'sound'],
            'design': ['design', 'graphics', 'creative']
        }
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                topics.append(topic)
        
        return topics[:5]  # Limit to top 5 topics
    
    def _extract_info_from_priorities(self, priority_insights) -> Dict[str, Any]:
        """Extract information from priority insights."""
        extracted = {}
        
        for priority in priority_insights:
            if hasattr(priority, 'category') and hasattr(priority, 'keywords'):
                # Use the category as key and keywords as evidence
                if priority.keywords:
                    extracted[priority.category] = priority.keywords[0] if priority.keywords else priority.category
        
        return extracted
    
    def _extract_new_topics_from_analysis(self, analysis_result) -> List[str]:
        """Extract new topics from context analysis result."""
        new_topics = []
        
        # Extract from priority insights
        for priority in analysis_result.priority_insights:
            if hasattr(priority, 'category'):
                new_topics.append(priority.category)
        
        # Extract from pattern insights
        for pattern in analysis_result.pattern_insights:
            if hasattr(pattern, 'category'):
                new_topics.append(pattern.category)
        
        return list(set(new_topics))  # Remove duplicates
    

    
    def _get_follow_up_categories(self, conversation_state: ConversationState) -> List[str]:
        """Get follow-up categories for deeper conversation."""
        follow_ups = []
        
        # Based on what we already have, suggest deeper questions
        user_profile = conversation_state.user_profile
        
        if 'budget' in user_profile:
            follow_ups.extend(['budget_flexibility', 'value_priorities'])
        if 'preferences' in user_profile:
            follow_ups.extend(['preference_priorities', 'deal_breakers'])
        if 'timeline' in user_profile:
            follow_ups.extend(['timeline_flexibility', 'urgency_factors'])
        if 'context' in user_profile:
            follow_ups.extend(['usage_scenarios', 'environment_factors'])
        
        return follow_ups[:3]  # Return top 3 follow-ups
    
    def _select_dynamic_category(self, conversation_state: ConversationState) -> str:
        """Select a category dynamically based on conversation context."""
        query_lower = conversation_state.user_query.lower()
        asked_categories = [qa.category for qa in conversation_state.question_history]
        
        # Domain-specific category selection
        if 'smartphone' in query_lower or 'phone' in query_lower:
            tech_categories = ['camera_needs', 'performance_requirements', 'brand_preferences', 'size_preferences', 'storage_needs']
            available = [cat for cat in tech_categories if cat not in asked_categories]
            if available:
                return available[0]
        
        if 'laptop' in query_lower or 'computer' in query_lower:
            laptop_categories = ['usage_type', 'portability_needs', 'performance_level', 'software_requirements']
            available = [cat for cat in laptop_categories if cat not in asked_categories]
            if available:
                return available[0]
        
        # Fallback categories
        fallback_categories = ['experience_level', 'decision_factors', 'concerns', 'must_haves']
        available = [cat for cat in fallback_categories if cat not in asked_categories]
        
        return available[0] if available else 'general_feedback'
    
    def _generate_pure_ai_question_unconstrained(self, conversation_state: ConversationState, asked_questions: List[str], additional_context: Optional[str] = None) -> Optional[str]:
        """
        Use pure AI to generate the next intelligent question without constraints.
        
        Employs advanced AI prompting to generate natural, contextual questions
        that build on conversation flow without relying on predefined categories
        or templates. Includes fallback mechanisms for reliability.
        
        Parameters:
            conversation_state: Current conversation state for context
            asked_questions: List of previously asked questions to avoid repetition
            additional_context: Optional additional context for question generation
            
        Returns:
            Generated question string, or None if generation fails
            
        Notes:
            - Uses conversation-aware prompting for natural progression
            - Implements retry logic with progressive backoff
            - Falls back to contextual questions if AI generation fails
            - Checks for question conflicts with conversation flow
        """
        try:
            # Check if Gemini client is available
            if not self.question_generator.gemini_client:
                self.logger.info("Gemini client not available, using simple fallback")
                return self._generate_contextual_fallback_question(conversation_state, asked_questions)
            
            # Create pure AI prompt that encourages natural discovery
            prompt = self._create_pure_ai_discovery_prompt(conversation_state, asked_questions, additional_context)
            
            # Generate question with improved error handling
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    start_time = time.time()
                    
                    response = self.question_generator.gemini_client.models.generate_content(
                        model=self.model_name,
                        contents=prompt
                    )
                    
                    response_time = time.time() - start_time
                    
                    if response and response.text:
                        generated_question = self._extract_question_from_response(response.text)
                        
                        if generated_question:
                            # Check for natural progression (not just word similarity)
                            if not self._conflicts_with_conversation_flow(generated_question, conversation_state, asked_questions):
                                self.logger.debug(f"Pure AI generated question in {response_time:.2f}s: {generated_question[:50]}...")
                                return generated_question
                            else:
                                self.logger.debug(f"Question conflicts with conversation flow (attempt {attempt + 1})")
                        else:
                            self.logger.warning(f"Could not extract valid question from AI response (attempt {attempt + 1})")
                    
                    # If this was the last attempt, use fallback
                    if attempt == max_retries - 1:
                        self.logger.info("All AI attempts failed, using contextual fallback")
                        return self._generate_contextual_fallback_question(conversation_state, asked_questions)
                        
                except Exception as e:
                    self.logger.warning(f"AI attempt {attempt + 1} failed: {str(e)[:100]}...")
                    if attempt == max_retries - 1:
                        return self._generate_contextual_fallback_question(conversation_state, asked_questions)
                    time.sleep(min(2 ** attempt, 3))  # Progressive backoff
            
        except Exception as e:
            self.logger.error(f"Error in pure AI question generation: {str(e)[:100]}...")
            
        return None
    
    def _create_pure_ai_discovery_prompt(self, conversation_state: ConversationState, asked_questions: List[str], additional_context: Optional[str] = None) -> str:
        """Create a pure AI discovery prompt that encourages natural question generation."""
        questions_count = len(conversation_state.question_history)
        
        # Build natural conversation context
        conversation_flow = []
        if conversation_state.question_history:
            # Show last 2-3 exchanges for context
            recent_exchanges = conversation_state.question_history[-3:]
            for qa in recent_exchanges:
                conversation_flow.append(f"You: {qa.question}")
                conversation_flow.append(f"Them: {qa.answer}")
        
        # Extract what we've learned naturally
        insights_discovered = []
        if conversation_state.user_profile:
            for key, value in list(conversation_state.user_profile.items())[:4]:
                insights_discovered.append(f"• {key.replace('_', ' ')}: {str(value)[:60]}...")
        
        # Create natural, discovery-focused prompt
        if questions_count == 0:
            # First question - focus on natural opening
            prompt = f"""You are having a friendly conversation with someone who wants personalized advice about: "{conversation_state.user_query}"

This is your first question to them. Think like a helpful friend who genuinely wants to understand their situation to give the best possible advice.

GOAL: Ask ONE natural question that opens the conversation and helps you understand what matters most to them.

GUIDELINES:
• Be warm and conversational 
• Focus on understanding their real-world needs
• Don't use formal categories or templates
• Ask what you would genuinely want to know to help them
• 10-25 words, natural tone
• End with a question mark

Think: "What would I ask a friend to really understand their situation and give great advice?"

Generate ONE natural opening question:"""

        elif questions_count <= 2:
            # Early conversation - build on what they've shared
            prompt = f"""You're having a helpful conversation about: "{conversation_state.user_query}"

CONVERSATION SO FAR:
{chr(10).join(conversation_flow)}

INSIGHTS YOU'VE GATHERED:
{chr(10).join(insights_discovered) if insights_discovered else "Just getting to know them"}

GOAL: Ask ONE thoughtful follow-up question that builds naturally on what they've shared.

APPROACH:
• Show you're listening to what they've said
• Dig deeper into something they mentioned
• Or explore a related aspect that would help you advise them
• Be genuinely curious about their specific situation
• Avoid repeating what you already know

Think: "Based on what they just told me, what would help me give them better advice?"

Generate ONE natural follow-up question (10-25 words):"""

        else:
            # Deeper conversation - focus on gaps and decision-making factors
            prompt = f"""You're in a helpful conversation about: "{conversation_state.user_query}"

RECENT EXCHANGE:
{chr(10).join(conversation_flow[-4:]) if conversation_flow else "No recent exchanges"}

WHAT YOU'VE LEARNED:
{chr(10).join(insights_discovered) if insights_discovered else "Limited insights gathered"}

CONVERSATION STAGE: You've asked {questions_count} questions. Focus on what would be most valuable for making a great recommendation.

GOAL: Ask ONE strategic question that fills an important gap in your understanding.

FOCUS AREAS TO CONSIDER:
• Deal-breakers or absolute requirements
• Real-world usage scenarios  
• Decision-making priorities
• Concerns or hesitations
• Success criteria
• Practical constraints

Think: "What key piece of information would help me give them the most valuable advice?"

Generate ONE focused question (10-25 words):"""

        return prompt
    
    def _generate_contextual_fallback_question(self, conversation_state: ConversationState, asked_questions: List[str]) -> Optional[str]:
        """Generate a contextual fallback question when AI is unavailable."""
        questions_count = len(conversation_state.question_history)
        query_words = conversation_state.user_query.lower().split()
        
        # Progressive question strategy based on conversation stage
        if questions_count == 0:
            # Opening questions - focus on what matters most
            opening_questions = [
                f"What's most important to you when choosing {self._extract_main_subject(conversation_state.user_query)}?",
                f"What would make your {self._extract_main_subject(conversation_state.user_query)} decision feel like a real win?",
                f"What specific needs are driving your search for {self._extract_main_subject(conversation_state.user_query)}?",
                "What's the main challenge you're hoping this will solve for you?",
                "Tell me what success would look like for you in this decision."
            ]
            
            for question in opening_questions:
                if not self._is_similar_question_simple(question, asked_questions):
                    return question
        
        elif questions_count <= 2:
            # Early follow-up questions - build on conversation
            if conversation_state.question_history:
                last_response = conversation_state.question_history[-1].answer.lower()
                
                # Generate contextual follow-ups based on their last response
                follow_up_questions = [
                    "That's helpful! What other factors are important in your decision?",
                    "I see. Are there any specific requirements or constraints I should know about?",
                    "Got it. What would be an absolute deal-breaker for you?",
                    "Thanks for sharing that. How do you typically make decisions like this?",
                    "That makes sense. What's your timeline looking like for this decision?"
                ]
                
                for question in follow_up_questions:
                    if not self._is_similar_question_simple(question, asked_questions):
                        return question
        
        else:
            # Deeper questions - focus on decision-making factors
            deeper_questions = [
                "What would give you the most confidence in your final choice?",
                "Are there any concerns or hesitations you have about the options?",
                "How will you know you've made the right decision?",
                "What would make you feel completely satisfied with your choice?",
                "Is there anything else that would be valuable for me to understand?"
            ]
            
            for question in deeper_questions:
                if not self._is_similar_question_simple(question, asked_questions):
                    return question
        
        # Final fallback
        return "What else would be helpful for me to know to give you the best possible advice?"
    
    def _conflicts_with_conversation_flow(self, question: str, conversation_state: ConversationState, asked_questions: List[str]) -> bool:
        """Check if question conflicts with natural conversation flow."""
        # Simple similarity check
        return self._is_similar_question_simple(question, asked_questions)
    
    def _is_similar_question_simple(self, new_question: str, asked_questions: List[str]) -> bool:
        """Simple similarity check for fallback scenarios."""
        if not asked_questions:
            return False
        
        new_words = set(new_question.lower().split())
        
        for asked in asked_questions:
            asked_words = set(asked.lower().split())
            
            # Remove common words
            meaningful_new = new_words - {'what', 'is', 'the', 'do', 'you', 'how', 'are', 'for', 'to', 'a', 'an', 'your', 'would', 'could', 'should'}
            meaningful_asked = asked_words - {'what', 'is', 'the', 'do', 'you', 'how', 'are', 'for', 'to', 'a', 'an', 'your', 'would', 'could', 'should'}
            
            if meaningful_new and meaningful_asked:
                overlap = meaningful_new.intersection(meaningful_asked)
                overlap_ratio = len(overlap) / max(len(meaningful_new), len(meaningful_asked))
                
                if overlap_ratio > 0.6:  # 60% meaningful word overlap
                    return True
        
        return False
    
    def _extract_main_subject(self, query: str) -> str:
        """Extract the main subject from the query for natural conversation."""
        query_lower = query.lower()
        
        # Common patterns
        if 'smartphone' in query_lower or 'phone' in query_lower:
            return 'smartphone'
        elif 'laptop' in query_lower:
            return 'laptop'
        elif 'camera' in query_lower:
            return 'camera'
        elif 'car' in query_lower or 'vehicle' in query_lower:
            return 'vehicle'
        elif 'software' in query_lower or 'app' in query_lower:
            return 'software'
        elif 'service' in query_lower:
            return 'service'
        elif 'course' in query_lower or 'education' in query_lower:
            return 'learning option'
        else:
            # Extract the first noun-like word
            words = query.split()
            for word in words:
                if len(word) > 3 and word.lower() not in ['best', 'good', 'find', 'help', 'need', 'want', 'should']:
                    return word.lower()
            return 'choice'
    
    def _extract_personalization_info_ai_driven(self, response: str, analysis: Dict[str, Any], conversation_state: ConversationState) -> Dict[str, Any]:
        """Extract personalization information using AI-driven analysis without categories."""
        extracted = {}
        
        # Extract from AI analysis
        if 'extracted_info' in analysis:
            extracted.update(analysis['extracted_info'])
        
        # Extract discovered themes naturally
        if 'discovered_themes' in analysis:
            for theme in analysis['discovered_themes']:
                if isinstance(theme, str) and theme not in extracted:
                    extracted[theme] = response[:100] + "..." if len(response) > 100 else response
        
        # Natural language processing for common patterns
        response_lower = response.lower()
        
        # Budget patterns
        if any(word in response_lower for word in ['$', 'dollar', 'cost', 'price', 'budget', 'afford', 'spend']):
            extracted['budget_consideration'] = response
        
        # Timeline patterns  
        if any(word in response_lower for word in ['soon', 'quickly', 'asap', 'urgent', 'month', 'week', 'year', 'timeline']):
            extracted['timeline_preference'] = response
        
        # Quality patterns
        if any(word in response_lower for word in ['quality', 'best', 'premium', 'high-end', 'professional', 'reliable']):
            extracted['quality_priority'] = response
        
        # Convenience patterns
        if any(word in response_lower for word in ['easy', 'simple', 'convenient', 'user-friendly', 'straightforward']):
            extracted['convenience_preference'] = response
        
        # Experience patterns
        if any(word in response_lower for word in ['beginner', 'expert', 'experienced', 'new to', 'familiar', 'advanced']):
            extracted['experience_level'] = response
        
        # Add response metadata
        extracted['response_length'] = len(response.split())
        extracted['analysis_timestamp'] = datetime.now().isoformat()
        
        return extracted
    
    def _determine_natural_category(self, question: str, response: str, extracted_info: Dict[str, Any]) -> str:
        """Determine category naturally based on content, not predefined buckets."""
        # Let the AI naturally categorize based on what was actually discussed
        question_lower = question.lower()
        response_lower = response.lower()
        
        # Natural categorization based on actual content
        if any(word in question_lower + response_lower for word in ['budget', 'cost', 'price', 'afford', '$']):
            return 'budget_discussion'
        elif any(word in question_lower + response_lower for word in ['time', 'when', 'soon', 'urgency', 'deadline']):
            return 'timing_discussion'
        elif any(word in question_lower + response_lower for word in ['quality', 'performance', 'feature', 'capability']):
            return 'quality_discussion'
        elif any(word in question_lower + response_lower for word in ['use', 'purpose', 'need', 'requirement']):
            return 'usage_discussion'
        elif any(word in question_lower + response_lower for word in ['experience', 'familiar', 'level', 'knowledge']):
            return 'experience_discussion'
        elif any(word in question_lower + response_lower for word in ['important', 'priority', 'matter', 'crucial']):
            return 'priority_discussion'
        else:
            return 'open_discussion'
    
    def _extract_themes_from_analysis(self, analysis_result) -> List[str]:
        """Extract themes from context analysis without category constraints."""
        themes = []
        
        # Extract from priority insights
        for priority in analysis_result.priority_insights:
            if hasattr(priority, 'category') and priority.category not in themes:
                themes.append(priority.category)
        
        # Extract from pattern insights
        for pattern in analysis_result.pattern_insights:
            if hasattr(pattern, 'theme') and pattern.theme not in themes:
                themes.append(pattern.theme)
            elif hasattr(pattern, 'category') and pattern.category not in themes:
                themes.append(pattern.category)
        
        return themes[:5]  # Limit to top 5 themes
    
    def _update_priority_factors_from_themes(self, conversation_state: ConversationState, analysis: Dict[str, Any]):
        """Update priority factors based on discovered themes rather than predefined categories."""
        if 'discovered_themes' in analysis:
            for theme in analysis['discovered_themes']:
                if theme not in conversation_state.priority_factors:
                    conversation_state.priority_factors[theme] = 0.6  # New themes get moderate priority
        
        # Update confidence scores for discovered themes
        if 'confidence_score' in analysis:
            for theme in conversation_state.priority_factors.keys():
                if theme in conversation_state.confidence_scores:
                    conversation_state.confidence_scores[theme] = analysis['confidence_score']
                else:
                    conversation_state.confidence_scores[theme] = analysis['confidence_score']
    
    def _generate_pure_ai_question(self, conversation_state: ConversationState, asked_questions: List[str], additional_context: Optional[str] = None) -> Optional[str]:
        """Use Gemini AI to generate the next intelligent question without category constraints."""
        try:
            # Use optimized prompt to prevent context overload and improve consistency
            questions_count = len(conversation_state.question_history)
            
            # Switch to concise prompts after 2 questions to prevent AI confusion
            if questions_count >= 2:
                prompt = self._create_concise_intelligent_ai_prompt(conversation_state, asked_questions, additional_context)
                self.logger.debug(f"Using concise prompt for question {questions_count + 1} (length: {len(prompt)} chars)")
            else:
                prompt = self._create_intelligent_ai_prompt(conversation_state, asked_questions, additional_context)
                self.logger.debug(f"Using full prompt for question {questions_count + 1} (length: {len(prompt)} chars)")
            
            # Improved timeout handling and retry logic
            max_retries = 3  # Increased from 2
            timeout_seconds = 20  # Increased from 15
            
            for attempt in range(max_retries):
                try:
                    start_time = time.time()
                    
                    # Query Gemini for the next question - use simple call without config for now
                    response = self.question_generator.gemini_client.models.generate_content(
                        model=self.model_name,
                        contents=prompt
                    )
                    
                    response_time = time.time() - start_time
                    
                    if response_time > 15:
                        self.logger.warning(f"Slow AI response: {response_time:.2f}s")
                    
                    if response and response.text:
                        # Extract the question from the response
                        generated_question = self._extract_question_from_response(response.text)
                        
                        if generated_question:
                            # Use context-aware similarity check for better progression
                            if not self._is_similar_question_context_aware(generated_question, asked_questions, conversation_state):
                                self.logger.debug(f"AI generated intelligent question in {response_time:.2f}s: {generated_question[:50]}...")
                                return generated_question
                            else:
                                self.logger.debug(f"AI generated similar question (attempt {attempt + 1}): {generated_question[:50]}...")
                                # If similar, try again instead of immediately falling back
                                if attempt < max_retries - 1:
                                    continue
                                else:
                                    self.logger.info("AI generated similar questions after all attempts, using fallback")
                                    return self._generate_simple_fallback_question(conversation_state, asked_questions)
                        else:
                            self.logger.warning(f"Could not extract valid question from AI response (attempt {attempt + 1}): '{response.text[:100]}...'")
                    else:
                        # More detailed debugging of response content
                        if response:
                            text_value = getattr(response, 'text', 'No text attribute')
                            candidates = getattr(response, 'candidates', 'No candidates')
                            self.logger.warning(f"Empty AI response (attempt {attempt + 1}) - text: {text_value}, candidates: {len(candidates) if hasattr(candidates, '__len__') else candidates}")
                            
                            # Check if candidates exist and have content
                            if hasattr(response, 'candidates') and response.candidates:
                                for i, candidate in enumerate(response.candidates):
                                    if hasattr(candidate, 'content') and candidate.content:
                                        if hasattr(candidate.content, 'parts') and candidate.content.parts:
                                            for j, part in enumerate(candidate.content.parts):
                                                if hasattr(part, 'text'):
                                                    self.logger.debug(f"Found text in candidate {i}, part {j}: '{part.text[:100]}...'")
                                                    # Try to use this text directly
                                                    if part.text and part.text.strip():
                                                        generated_question = self._extract_question_from_response(part.text)
                                                        if generated_question and not self._is_similar_question_context_aware(generated_question, asked_questions, conversation_state):
                                                            self.logger.info(f"Recovered question from candidate parts: {generated_question[:50]}...")
                                                            return generated_question
                        else:
                            self.logger.warning(f"No response object received (attempt {attempt + 1})")
                    
                except Exception as e:
                    response_time = time.time() - start_time
                    self.logger.warning(f"AI attempt {attempt + 1} failed after {response_time:.2f}s: {str(e)[:100]}...")
                    
                    # If this was the last attempt, fall back
                    if attempt == max_retries - 1:
                        self.logger.error(f"All AI attempts failed, using fallback")
                        return self._generate_simple_fallback_question(conversation_state, asked_questions)
                    
                    # Progressive backoff with jitter
                    wait_time = min(2 ** attempt, 5)  # Max 5 seconds wait
                    self.logger.debug(f"Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
            
        except Exception as e:
            self.logger.error(f"Error in AI question generation: {str(e)[:100]}...")
            
        return None
    
    def _create_intelligent_ai_prompt(self, conversation_state: ConversationState, asked_questions: List[str], additional_context: Optional[str] = None) -> str:
        """Create an engaging, conversational prompt for Gemini to generate natural questions."""
        # Build rich conversational context
        recent_qa = conversation_state.question_history[-2:] if len(conversation_state.question_history) >= 2 else conversation_state.question_history
        
        # Create natural conversation flow context
        conversation_context = []
        if recent_qa:
            for qa in recent_qa:
                conversation_context.append(f"You asked: '{qa.question}' and they shared: '{qa.answer}'")
        
        # Build user insight summary
        user_insights = []
        if conversation_state.user_profile:
            for key, value in list(conversation_state.user_profile.items())[:4]:  # Show more context
                user_insights.append(f"{key}: {value}")
        
        # Create warm, engaging prompt that encourages natural conversation
        prompt = f"""You are having a friendly, helpful conversation with someone seeking personalized advice about: "{conversation_state.user_query}"

CONVERSATION SO FAR:
{chr(10).join(conversation_context) if conversation_context else "This is the beginning of your conversation."}

WHAT YOU'VE LEARNED ABOUT THEM:
{chr(10).join(user_insights) if user_insights else "You're just getting to know them."}

QUESTIONS ALREADY ASKED:
{chr(10).join([f"• {q}" for q in asked_questions[-5:]]) if asked_questions else "• None yet"}

YOUR TASK: Ask ONE thoughtful follow-up question that feels natural and helps you understand what matters most to them for making a great recommendation.

CONVERSATION STYLE:
• Be warm, curious, and genuinely interested
• Use natural language like you're talking to a friend
• Build on what they've already shared
• Ask about their real-world needs and preferences
• Make them feel heard and understood
• Show you care about getting them the right advice

QUESTION GUIDELINES:
• 10-30 words (natural conversation length)
• Avoid repeating similar questions or topics already covered
• Focus on their specific situation and needs
• Use "you" and "your" to make it personal
• Ask about ONE specific aspect at a time
• Make it conversational, not formal or robotic

EXAMPLES OF GREAT QUESTIONS:
• "What's been your biggest frustration with what you're currently using?"
• "How do you picture yourself using this on a typical day?"
• "What would make you feel really confident about your choice?"
• "Is there anything that would be an absolute deal-breaker for you?"

Generate ONE natural, engaging question that builds on the conversation:"""

        return prompt
    
    def _create_concise_intelligent_ai_prompt(self, conversation_state: ConversationState, asked_questions: List[str], additional_context: str = "") -> str:
        """Create a concise, focused prompt optimized for consistent AI performance."""
        # Limit context to prevent AI confusion and improve consistency
        questions_count = len(conversation_state.question_history)
        
        # Build focused context based on conversation stage
        if questions_count <= 2:
            # Early stage: Focus on original query and basic context
            context_info = self._get_early_stage_context(conversation_state)
        else:
            # Later stage: Focus on key insights and gaps
            context_info = self._get_focused_context(conversation_state, asked_questions)
        
        # Create streamlined prompt
        prompt = f"""You are helping someone choose: "{conversation_state.user_query}"

CURRENT CONTEXT:
{context_info['context_summary']}

AVOID REPEATING: {context_info['topics_covered']}

FOCUS ON: {context_info['next_focus']}

Generate ONE specific question (10-25 words) that helps them make a confident decision:"""

        return prompt
    
    def _get_early_stage_context(self, conversation_state: ConversationState) -> Dict[str, str]:
        """Get context for early conversation stage (questions 1-2)."""
        # Simple context for early questions
        recent_response = ""
        if conversation_state.question_history:
            last_qa = conversation_state.question_history[-1]
            recent_response = f"They shared: {last_qa.answer[:80]}..."
        
        # Key insights so far
        key_insights = []
        for key, value in list(conversation_state.user_profile.items())[:2]:
            key_insights.append(f"{key.replace('_', ' ')}: {str(value)[:40]}...")
        
        return {
            'context_summary': recent_response or "Starting conversation",
            'topics_covered': ", ".join([qa.category for qa in conversation_state.question_history[-3:]]),
            'next_focus': "their specific needs and preferences"
        }
    
    def _get_focused_context(self, conversation_state: ConversationState, asked_questions: List[str]) -> Dict[str, str]:
        """Get focused context for later conversation stage (questions 3+)."""
        # Most important recent insights (max 2)
        key_insights = []
        priority_keys = ['budget', 'preferences', 'timeline', 'constraints', 'current_device']
        
        for key in priority_keys:
            if key in conversation_state.user_profile:
                value = str(conversation_state.user_profile[key])
                key_insights.append(f"{key}: {value[:50]}...")
                if len(key_insights) >= 2:
                    break
        
        # Recent meaningful exchange
        recent_context = ""
        if conversation_state.question_history:
            last_qa = conversation_state.question_history[-1]
            recent_context = f"Recent: Asked about {last_qa.category}, they said: {last_qa.answer[:60]}..."
        
        # Topics covered (categories only)
        covered_topics = list(set([qa.category for qa in conversation_state.question_history]))
        
        # Identify what's missing
        essential_areas = ['budget', 'preferences', 'timeline', 'constraints', 'context']
        missing_areas = [area for area in essential_areas if area not in covered_topics]
        next_focus = missing_areas[0] if missing_areas else "decision confidence factors"
        
        context_summary = recent_context
        if key_insights:
            context_summary += f" | Key info: {'; '.join(key_insights[:2])}"
        
        return {
            'context_summary': context_summary[:200] + "..." if len(context_summary) > 200 else context_summary,
            'topics_covered': ", ".join(covered_topics[-4:]),  # Last 4 topics only
            'next_focus': next_focus.replace('_', ' ')
        }
    
    def _generate_simple_fallback_question(self, conversation_state: ConversationState, asked_questions: List[str]) -> Optional[str]:
        """Generate engaging, conversational fallback questions when AI fails."""
        
        # Get conversation context for personalization
        query_lower = conversation_state.user_query.lower()
        user_has_shared = len(conversation_state.question_history) > 0
        recent_response = conversation_state.question_history[-1].answer if conversation_state.question_history else ""
        
        # Technology/Product questions - warm and engaging
        if any(word in query_lower for word in ['phone', 'laptop', 'computer', 'camera', 'device', 'gadget', 'smartphone']):
            if user_has_shared:
                tech_questions = [
                    f"That's really helpful! Now, what's the main thing you'll be doing with your {self._extract_product_type(query_lower)}?",
                    "I'm curious - do you have any specific features that are absolutely must-haves for you?",
                    "What's been your experience with similar products? Any particular likes or dislikes?",
                    "Tell me about your typical day - how would this fit into your routine?",
                    "Are there any brands you've had great experiences with, or any you'd prefer to avoid?",
                    "What's prompting this decision right now? Is there something specific that's not working for you currently?",
                    "I want to make sure we find the perfect fit - are there any deal-breakers or limitations I should know about?"
                ]
            else:
                tech_questions = [
                    f"I'd love to help you find the perfect {self._extract_product_type(query_lower)}! What's the main way you're planning to use it?",
                    "What's most important to you in this decision - is it performance, value, specific features, or something else?",
                    "Tell me about your experience level with this type of product. Are you pretty tech-savvy or do you prefer something straightforward?",
                    "What's driving this purchase right now? Is it an upgrade, a new need, or replacing something that's not working?",
                    "I'm curious about your preferences - do you have any specific requirements or features you absolutely need?",
                    "What would make this purchase feel like a real win for you?",
                    "Are there any constraints we should work within, like budget range or timing?"
                ]
            fallback_questions = tech_questions
        
        # Service/Experience questions - supportive and goal-oriented
        elif any(word in query_lower for word in ['service', 'course', 'learning', 'travel', 'experience', 'education']):
            if user_has_shared:
                service_questions = [
                    "That makes a lot of sense! What would success look like to you in this area?",
                    "I'm really interested in understanding your goals better - what's the main outcome you're hoping for?",
                    "Tell me about your current experience level. Are you starting fresh or building on existing knowledge?",
                    "What's your realistic timeline looking like? Are you hoping to see results quickly or can you take a more gradual approach?",
                    "How much time and energy can you realistically dedicate to this right now?",
                    "What's motivating this decision for you at this moment in your life?",
                    "Are there any specific challenges or obstacles you're hoping this will help you overcome?"
                ]
            else:
                service_questions = [
                    "I'm excited to help you with this! What's the main goal you're hoping to achieve?",
                    "Tell me what success would look like for you in this area.",
                    "What's your current experience level? Are you starting from scratch or building on what you already know?",
                    "How much time can you realistically invest in this right now?",
                    "What's driving this decision for you? Is there something specific you want to change or improve?",
                    "I want to understand your situation better - what would make this feel really worthwhile for you?",
                    "Are there any particular approaches or styles that tend to work well for you when learning or trying new things?"
                ]
            fallback_questions = service_questions
            
        # Investment/Financial questions - thoughtful and empowering
        elif any(word in query_lower for word in ['invest', 'financial', 'money', 'cost', 'price', 'budget', 'finance']):
            if user_has_shared:
                financial_questions = [
                    "Thanks for sharing that! How does this decision fit into your bigger financial picture?",
                    "I want to make sure we find something that feels comfortable for you - what's your risk tolerance like?",
                    "What timeline are you thinking about for seeing results or benefits from this?",
                    "Tell me about your experience with similar financial decisions - what's worked well for you before?",
                    "What would need to happen for you to feel really confident about moving forward?",
                    "Are there any financial constraints or guidelines you like to follow when making decisions like this?",
                    "What factors typically help you feel good about a financial choice?"
                ]
            else:
                financial_questions = [
                    "I'd love to help you make a smart financial decision here! How comfortable are you with different levels of risk?",
                    "Tell me how this fits into your overall financial goals and situation.",
                    "What's your timeline looking like? Are you thinking short-term or long-term benefits?",
                    "What would make this investment feel really worthwhile and smart for you?",
                    "How familiar are you with the options available in this area?",
                    "I'm curious about your decision-making style - what factors usually help you feel confident about financial choices?",
                    "Are there any financial principles or constraints that guide your decisions?"
                ]
            fallback_questions = financial_questions
            
        # General questions - warm and exploratory
        else:
            if user_has_shared:
                general_questions = [
                    "That's really insightful! What other aspects of this decision are important to you?",
                    "I'm getting a better picture now - what would make this choice feel absolutely right for you?",
                    "Based on what you've shared, what information would be most valuable as you make this decision?",
                    "Tell me more about your specific situation - are there any unique factors I should consider?",
                    "What's your gut feeling telling you about the direction you want to go?",
                    "If we could address any concerns or questions you have, what would be most helpful?",
                    "I want to make sure I understand what matters most to you - what would success look like?"
                ]
            else:
                general_questions = [
                    "I'm really interested in understanding your specific situation better - what's most important to you in this decision?",
                    "Tell me what would make this choice feel like a real win for you.",
                    "What's the main challenge or need you're hoping to address?",
                    "I'd love to get a sense of your priorities - what factors matter most as you think through this?",
                    "What's driving this decision for you right now? Is there something specific that's prompted this?",
                    "How much flexibility do you have in your approach to this?",
                    "What would need to happen for you to feel completely confident about moving forward?"
                ]
            fallback_questions = general_questions
        
        # Find an engaging question that hasn't been asked
        for question in fallback_questions:
            if not self._is_similar_question(question, asked_questions):
                return question
        
        # Thoughtful backup options that build on conversation
        if user_has_shared:
            thoughtful_backups = [
                "You've given me some great insights! What other details would help me understand your needs even better?",
                "I really appreciate what you've shared so far. Is there anything else about your situation that would be helpful for me to know?",
                "Based on our conversation, what questions are coming up for you about the available options?",
                "What aspects of this decision would you like to explore a bit more deeply?"
            ]
        else:
            thoughtful_backups = [
                "I'd love to learn more about what matters most to you in this decision - what should I know about your situation?",
                "Tell me more about what you're hoping to achieve and what would make this choice feel right for you.",
                "What's the most important thing for me to understand about your needs and preferences?",
                "I want to make sure I give you the best possible advice - what would be most helpful for you to share?"
            ]
        
        for question in thoughtful_backups:
            if not self._is_similar_question(question, asked_questions):
                return question
                
        # Final warm fallback
        return f"I really want to help you find the perfect solution for your {conversation_state.user_query} - what else would be helpful for me to know about what you're looking for?"
    
    def _generate_ai_question(self, category: str, conversation_state: ConversationState, asked_questions: List[str]) -> Optional[str]:
        """Use Gemini AI to generate the next intelligent question with timeout handling."""
        try:
            # Create a comprehensive prompt for Gemini
            prompt = self._create_ai_question_prompt(category, conversation_state, asked_questions)
            
            start_time = time.time()
            
            # Query Gemini for the next question
            response = self.question_generator.gemini_client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            
            response_time = time.time() - start_time
            
            if response_time > 8:
                self.logger.warning(f"Slow AI response for category '{category}': {response_time:.2f}s")
            
            if response and response.text:
                # Extract the question from the response
                generated_question = self._extract_question_from_response(response.text)
                
                if generated_question and not self._is_similar_question(generated_question, asked_questions):
                    self.logger.debug(f"AI generated question for category '{category}' in {response_time:.2f}s: {generated_question[:50]}...")
                    return generated_question
                else:
                    self.logger.warning("AI generated similar or invalid question, using fallback")
                    return self._generate_fallback_question(category, conversation_state, asked_questions)
            
        except Exception as e:
            self.logger.error(f"Error in AI question generation for category '{category}': {e}")
            
        return None
    
    def _create_ai_question_prompt(self, category: str, conversation_state: ConversationState, asked_questions: List[str]) -> str:
        """Create a comprehensive prompt for Gemini to generate the next question."""
        user_profile_str = "None" if not conversation_state.user_profile else "\n".join([f"- {k}: {v}" for k, v in conversation_state.user_profile.items()])
        asked_questions_str = "None" if not asked_questions else "\n".join([f"- {q}" for q in asked_questions])
        
        # Get recent responses to understand conversation flow
        recent_responses = [qa.answer for qa in conversation_state.question_history[-2:]] if len(conversation_state.question_history) >= 2 else []
        recent_responses_str = "None" if not recent_responses else "\n".join([f"- {resp}" for resp in recent_responses])
        
        # Identify what categories we've covered
        covered_categories = [qa.category for qa in conversation_state.question_history] if conversation_state.question_history else []
        covered_categories_str = ", ".join(covered_categories) if covered_categories else "None"
        
        prompt = f"""You are an expert conversation agent helping to personalize research recommendations. Generate ONE intelligent follow-up question to gather important information.

CONTEXT:
- User's Original Query: "{conversation_state.user_query}"
- Target Category for THIS question: {category}
- Total Questions Asked: {len(asked_questions)}
- Information Gathered: {len(conversation_state.user_profile)} data points
- Categories Already Covered: {covered_categories_str}

CONVERSATION FLOW:
Recent User Responses: {recent_responses_str}

ALREADY ASKED QUESTIONS (AVOID SIMILAR):
{asked_questions_str}

CURRENT USER PROFILE:
{user_profile_str}

TASK: Generate a question specifically for the category "{category}" that will help personalize the research for "{conversation_state.user_query}".

CATEGORY GUIDANCE:
- budget: Ask about spending comfort, budget flexibility, value vs premium preferences
- preferences: Ask about specific features, must-have requirements, priorities  
- timeline: Ask about urgency, decision timeframe, flexibility
- constraints: Ask about limitations, deal-breakers, requirements
- experience_level: Ask about familiarity, technical needs, expertise
- context: Ask about usage scenarios, environment, specific needs
- camera_needs: Ask about photography types, quality expectations, features needed
- performance_requirements: Ask about usage demands, speed needs, multitasking
- brand_preferences: Ask about brand loyalty, past experiences, preferences

INSTRUCTIONS:
1. Generate ONE natural question SPECIFICALLY for the category: {category}
2. Make it conversational and build on previous responses if available
3. Avoid repeating information already gathered
4. Make the question directly relevant to "{conversation_state.user_query}"
5. Keep it concise (under 25 words)
6. Focus on actionable information that helps with recommendations

IMPORTANT RULES:
- Do NOT ask questions similar to ones already asked
- Do NOT repeat information we already have in the user profile
- Make the question directly relevant to "{conversation_state.user_query}"
- Ensure the question fits the category: {category}
- Be conversational and build on the conversation flow

Generate ONLY the question text (no explanations, quotes, or additional text):"""

        return prompt
    
    def _extract_question_from_response(self, response_text: str) -> Optional[str]:
        """Extract the question from Gemini's response."""
        try:
            # Clean up the response
            question = response_text.strip()
            
            # Remove any markdown formatting
            question = question.replace("**", "").replace("*", "")
            
            # Remove any prefixes like "Question:" or numbering
            import re
            question = re.sub(r'^(Question|Q|\d+\.?)\s*:?\s*', '', question, flags=re.IGNORECASE)
            
            # Handle multi-line responses - take the first line that looks like a question
            lines = question.split('\n')
            for line in lines:
                line = line.strip()
                if line and (line.endswith('?') or any(word in line.lower() for word in ['what', 'how', 'when', 'where', 'why', 'which', 'who', 'can', 'do', 'would', 'could', 'should'])):
                    question = line
                    break
            
            # Ensure it ends with a question mark if it doesn't already
            if question and not question.endswith('?'):
                question += '?'
            
            # More lenient validation - allow questions from 10 to 300 characters
            if question and len(question) >= 10 and len(question) <= 300:
                # Additional quality checks
                if self._is_valid_question_content(question):
                    return question
                else:
                    self.logger.debug(f"Question failed content validation: {question[:50]}...")
            else:
                self.logger.debug(f"Question failed length validation (len={len(question) if question else 0}): {question[:50] if question else 'None'}...")
                
        except Exception as e:
            self.logger.error(f"Error extracting question from response: {e}")
            
        return None
    
    def _is_valid_question_content(self, question: str) -> bool:
        """Validate question content quality."""
        question_lower = question.lower()
        
        # Check for basic question indicators
        question_words = ['what', 'how', 'when', 'where', 'why', 'which', 'who', 'can', 'do', 'would', 'could', 'should', 'are', 'is', 'will']
        has_question_word = any(word in question_lower for word in question_words)
        
        # Check it's not just generic phrases
        generic_phrases = ['let me know', 'tell me more', 'anything else', 'any other']
        is_generic = any(phrase in question_lower for phrase in generic_phrases)
        
        # Check for reasonable word count (questions should have substance)
        word_count = len(question.split())
        
        return has_question_word and not is_generic and word_count >= 4
    
    def _is_similar_question_context_aware(self, new_question: str, asked_questions: List[str], conversation_state: ConversationState) -> bool:
        """Context-aware similarity detection that accounts for conversation progression."""
        if not asked_questions:
            return False
        
        # For later questions (3+), be more lenient to allow natural progression
        questions_count = len(conversation_state.question_history)
        if questions_count >= 2:
            return self._is_similar_question_lenient(new_question, asked_questions)
        else:
            return self._is_similar_question(new_question, asked_questions)
    
    def _is_similar_question_lenient(self, new_question: str, asked_questions: List[str]) -> bool:
        """More lenient similarity detection for advanced conversation stages."""
        new_words = set(new_question.lower().split())
        new_lower = new_question.lower()
        
        # Define semantic patterns but require MORE overlap for similarity
        importance_patterns = ['important', 'priority', 'matter most', 'key factor', 'crucial', 'essential']
        requirements_patterns = ['requirement', 'constraint', 'need', 'must have', 'criteria']
        usage_patterns = ['use', 'using', 'usage', 'utilize', 'application', 'purpose']
        preference_patterns = ['prefer', 'preference', 'like', 'want', 'choice', 'option']
        decision_patterns = ['decision', 'choose', 'select', 'pick', 'deciding']
        
        # Check semantic patterns for new question
        new_patterns = []
        if any(pattern in new_lower for pattern in importance_patterns):
            new_patterns.append('importance')
        if any(pattern in new_lower for pattern in requirements_patterns):
            new_patterns.append('requirements')
        if any(pattern in new_lower for pattern in usage_patterns):
            new_patterns.append('usage')
        if any(pattern in new_lower for pattern in preference_patterns):
            new_patterns.append('preferences')
        if any(pattern in new_lower for pattern in decision_patterns):
            new_patterns.append('decision')
        
        for asked in asked_questions:
            asked_lower = asked.lower()
            asked_words = set(asked_lower.split())
            
            # Only check recent questions (last 3) for similarity to allow topic evolution
            if len(asked_questions) > 3 and asked not in asked_questions[-3:]:
                continue
            
            # Check semantic similarity - require ALL patterns to match (more strict)
            asked_patterns = []
            if any(pattern in asked_lower for pattern in importance_patterns):
                asked_patterns.append('importance')
            if any(pattern in asked_lower for pattern in requirements_patterns):
                asked_patterns.append('requirements')
            if any(pattern in asked_lower for pattern in usage_patterns):
                asked_patterns.append('usage')
            if any(pattern in asked_lower for pattern in preference_patterns):
                asked_patterns.append('preferences')
            if any(pattern in asked_lower for pattern in decision_patterns):
                asked_patterns.append('decision')
            
            # Require exact semantic pattern match AND significant word overlap
            if new_patterns and asked_patterns and set(new_patterns) == set(asked_patterns):
                # Calculate meaningful word overlap
                common_words = new_words.intersection(asked_words)
                meaningful_common = common_words - {
                    'what', 'is', 'the', 'do', 'you', 'how', 'are', 'for', 'to', 'a', 'an', 'your'
                }
                
                # Only mark as similar if VERY high overlap (70%+)
                if len(meaningful_common) >= 4:
                    overlap_ratio = len(meaningful_common) / max(len(new_words), len(asked_words))
                    if overlap_ratio > 0.7:
                        return True
            
            # Check for near-identical questions (90%+ similarity)
            if self._calculate_similarity_ratio(new_lower, asked_lower) > 0.9:
                return True
        
        return False
    
    def _generate_fallback_question(self, category: str, conversation_state: ConversationState, asked_questions: List[str]) -> Optional[str]:
        """Generate a fallback question using simple templates when AI fails."""
        # Simple category-based questions as fallback
        fallback_templates = {
            'budget': "What's your budget range for this?",
            'timeline': "When do you need to make this decision?", 
            'preferences': "What features are most important to you?",
            'constraints': "Are there any limitations we should consider?",
            'experience_level': "What's your experience level with this type of product?",
            'context': "How do you plan to use this?",
            'camera_needs': "How important is camera quality to you?",
            'performance_requirements': "What kind of performance do you need?",
            'brand_preferences': "Do you have any brand preferences?",
            'decision_factors': "What will be the deciding factor in your choice?"
        }
        
        base_question = fallback_templates.get(category, f"Can you tell me more about your {category}?")
        
        # Check if this question is too similar to asked questions
        if not self._is_similar_question(base_question, asked_questions):
            return base_question
        
        # If similar, try to make it more specific
        return self._generate_contextual_question(category, conversation_state)
    
    def _is_similar_question(self, new_question: str, asked_questions: List[str]) -> bool:
        """Check if a question is too similar to already asked questions."""
        new_words = set(new_question.lower().split())
        new_lower = new_question.lower()
        
        # Define semantic patterns that indicate similar intent
        importance_patterns = ['important', 'priority', 'matter most', 'key factor', 'crucial', 'essential']
        requirements_patterns = ['requirement', 'constraint', 'need', 'must have', 'criteria']
        usage_patterns = ['use', 'using', 'usage', 'utilize', 'application', 'purpose']
        preference_patterns = ['prefer', 'preference', 'like', 'want', 'choice', 'option']
        decision_patterns = ['decision', 'choose', 'select', 'pick', 'deciding']
        
        # Check if new question matches any semantic pattern
        new_patterns = []
        if any(pattern in new_lower for pattern in importance_patterns):
            new_patterns.append('importance')
        if any(pattern in new_lower for pattern in requirements_patterns):
            new_patterns.append('requirements')
        if any(pattern in new_lower for pattern in usage_patterns):
            new_patterns.append('usage')
        if any(pattern in new_lower for pattern in preference_patterns):
            new_patterns.append('preferences')
        if any(pattern in new_lower for pattern in decision_patterns):
            new_patterns.append('decision')
        
        for asked in asked_questions:
            asked_lower = asked.lower()
            asked_words = set(asked_lower.split())
            
            # Check semantic similarity first
            asked_patterns = []
            if any(pattern in asked_lower for pattern in importance_patterns):
                asked_patterns.append('importance')
            if any(pattern in asked_lower for pattern in requirements_patterns):
                asked_patterns.append('requirements')
            if any(pattern in asked_lower for pattern in usage_patterns):
                asked_patterns.append('usage')
            if any(pattern in asked_lower for pattern in preference_patterns):
                asked_patterns.append('preferences')
            if any(pattern in asked_lower for pattern in decision_patterns):
                asked_patterns.append('decision')
            
            # Only consider similar if they share MULTIPLE semantic patterns AND have high word overlap
            if new_patterns and asked_patterns:
                common_patterns = set(new_patterns).intersection(set(asked_patterns))
                # Require at least 2 shared patterns for semantic similarity
                if len(common_patterns) >= 2:
                    return True
            
            # Calculate word overlap for additional check (make it more lenient)
            common_words = new_words.intersection(asked_words)
            # Exclude common question words (but keep fewer to allow more variety)
            meaningful_common = common_words - {
                'what', 'is', 'the', 'do', 'you', 'how', 'are', 'for', 'to', 'a', 'an'
            }
            
            # Require at least 3 meaningful words to overlap AND high similarity ratio
            if len(meaningful_common) >= 3:
                overlap_ratio = len(meaningful_common) / max(len(new_words), len(asked_words))
                # Only mark as similar if over 50% overlap
                if overlap_ratio > 0.5:
                    return True
            
            # Additional check: very similar sentence structure
            # Use basic edit distance for near-exact matches
            if self._calculate_similarity_ratio(new_lower, asked_lower) > 0.8:
                return True
        
        return False
    
    def _calculate_similarity_ratio(self, text1: str, text2: str) -> float:
        """Calculate similarity ratio between two text strings."""
        # Simple character-based similarity for very similar questions
        if len(text1) == 0 or len(text2) == 0:
            return 0.0
        
        # Calculate character overlap
        chars1 = set(text1.replace(' ', ''))
        chars2 = set(text2.replace(' ', ''))
        common_chars = chars1.intersection(chars2)
        
        total_chars = chars1.union(chars2)
        if len(total_chars) == 0:
            return 0.0
            
        return len(common_chars) / len(total_chars)
    
    def _generate_contextual_question(self, category: str, conversation_state: ConversationState) -> str:
        """Generate a contextual question when templates don't work."""
        user_query = conversation_state.user_query.lower()
        
        # Generate more specific questions based on the original query
        if 'smartphone' in user_query or 'phone' in user_query:
            if category == 'preferences':
                return "What specific features in a smartphone matter most to you - camera, battery life, screen quality, or something else?"
            elif category == 'budget':
                return "Considering your photography needs, are you willing to invest more for better camera quality?"
            elif category == 'timeline':
                return "Are you looking to upgrade soon, or can you wait for newer models to be released?"
        
        elif 'laptop' in user_query or 'computer' in user_query:
            if category == 'preferences':
                return "What will you primarily use this laptop for - work, gaming, creative tasks, or general use?"
            elif category == 'performance_requirements':
                return "Do you need high performance for demanding tasks or is basic performance sufficient?"
        
        # Generic fallback based on category
        contextual_questions = {
            'budget': f"Given that you're researching {user_query}, what budget range feels comfortable to you?",
            'timeline': f"For your {user_query} decision, what's your ideal timeline?",
            'preferences': f"What aspects of {user_query} matter most to you?",
            'constraints': f"Are there any specific limitations for your {user_query} choice?",
            'experience_level': f"How familiar are you with {user_query}?",
            'context': f"In what situations will you be using your {user_query}?"
        }
        
        return contextual_questions.get(category, f"Can you share more details about your {category} regarding {user_query}?")
    
    def _extract_product_type(self, query_lower: str) -> str:
        """Extract product type from query for natural conversation."""
        if 'smartphone' in query_lower or 'phone' in query_lower:
            return 'smartphone'
        elif 'laptop' in query_lower:
            return 'laptop'
        elif 'computer' in query_lower:
            return 'computer'
        elif 'camera' in query_lower:
            return 'camera'
        elif any(word in query_lower for word in ['device', 'gadget']):
            return 'device'
        else:
            return 'product'
