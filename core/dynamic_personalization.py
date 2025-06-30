"""
Dynamic Personalization Engine for Deep Research Agent
Main orchestration class that integrates conversation state, AI question generation, 
context analysis, and conversation memory to create intelligent, adaptive conversations.
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import asdict
from datetime import datetime

from google import genai
from google.genai import types

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
                 model_name: str = "gemini-2.0-flash-001"):
        """
        Initialize the Dynamic Personalization Engine.
        
        Args:
            gemini_client: Configured Gemini client for AI operations
            conversation_history: Optional existing conversation history
            model_name: Name of the Gemini model to use for generation
        """
        self.logger = logging.getLogger(__name__)
        self.model_name = model_name
        
        # Initialize Phase 1 components
        self.question_generator = AIQuestionGenerator(gemini_client, model_name)
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
    
    def generate_next_question(self, conversation_state: ConversationState) -> Optional[str]:
        """
        Generate the next intelligent question based on conversation context using AI.
        
        Args:
            conversation_state: Current state of the conversation
            
        Returns:
            str: Next question to ask, or None if conversation is complete
        """
        try:
            # Check if we should continue the conversation
            if not self._should_continue_conversation(conversation_state):
                self.logger.info("Conversation deemed complete, no more questions needed")
                return None
            
            # Get already asked questions to avoid repetition
            asked_questions = [qa.question for qa in conversation_state.question_history]
            
            # Generate intelligent question using AI without rigid categories
            question = self._generate_intelligent_ai_question(conversation_state, asked_questions)
            
            if question:
                self.logger.debug(f"Generated intelligent question: {question[:50]}...")
                
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
        Process user response and update conversation state.
        
        Args:
            conversation_state: Current conversation state
            question: The question that was asked
            response: User's response to the question
            
        Returns:
            Dict containing extracted information and analysis
        """
        try:
            self.logger.debug(f"Processing response to: {question[:50]}...")
            
            # Create question-answer pair - let AI determine the category if needed
            qa_pair = QuestionAnswer(
                question=question,
                answer=response,
                question_type=QuestionType.OPEN_ENDED,  # Default type
                timestamp=datetime.now(),
                category='ai_determined',  # Let AI categorize naturally
                confidence=0.5,  # Will be updated after analysis
                importance=0.7,  # Personalization is important
                context={}
            )
            
            # Analyze the response using the available ContextAnalyzer method
            # First, update the conversation state with this new Q&A
            conversation_state.question_history.append(qa_pair)
            
            # Now use analyze_context to get full context analysis
            context_analysis_result = self.context_analyzer.analyze_context(conversation_state)
            
            # Extract response analysis from the context analysis result
            response_analysis = {
                'priorities': [p.__dict__ for p in context_analysis_result.priority_insights],
                'emotional_indicators': [e.__dict__ for e in context_analysis_result.emotional_indicators],
                'communication_style': context_analysis_result.communication_style.value,
                'confidence_score': context_analysis_result.overall_confidence,
                'extracted_info': self._extract_info_from_priorities(context_analysis_result.priority_insights),
                'new_topics': self._extract_new_topics_from_analysis(context_analysis_result)
            }
            
            # Extract personalization information from the analysis
            extracted_info = self._extract_personalization_info(response, response_analysis)
            
            # Update user profile with new information
            self._update_user_profile(conversation_state, extracted_info)
            
            # Add to conversation history
            conversation_state.add_question_answer(
                question=question,
                answer=response,
                category='ai_determined',  # Let AI categorize naturally
                question_type=QuestionType.OPEN_ENDED,
                confidence=response_analysis.get('confidence_score', 0.5)
            )
            
            # Update priority factors based on response analysis
            self._update_priority_factors(conversation_state, response_analysis)
            
            # Store in conversation history
            self.conversation_history.track_question_effectiveness(
                session_id=conversation_state.session_id,
                question=question,
                response=response,
                question_type=QuestionType.OPEN_ENDED,
                category='ai_determined'  # Let AI categorize naturally
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
        
        Args:
            conversation_state: Current conversation state
            
        Returns:
            Dict containing conversation summary and insights
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
        
        Args:
            conversation_state: Current conversation state
            
        Returns:
            Dict containing strategy adaptations and recommendations
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
        """Determine if conversation should continue based on AI-driven assessment."""
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
        """Identify key information gaps that need to be filled."""
        # Start with predefined essential categories
        essential_categories = [
            'budget', 'preferences', 'timeline', 'constraints', 
            'context', 'experience_level'
        ]
        
        # Get categories we've already covered
        covered_categories = set(qa.category for qa in conversation_state.question_history)
        
        # Priority 1: Essential categories we haven't covered
        priority_gaps = [cat for cat in essential_categories if cat not in covered_categories]
        
        # Priority 2: Domain-specific categories based on query
        domain = self._classify_domain(conversation_state.user_query)
        domain_specific = []
        
        if domain == 'technology':
            tech_categories = ['performance_requirements', 'brand_preferences', 'technical_requirements']
            if 'smartphone' in conversation_state.user_query.lower() or 'phone' in conversation_state.user_query.lower():
                tech_categories.extend(['camera_needs', 'storage_needs', 'size_preferences'])
            elif 'laptop' in conversation_state.user_query.lower() or 'computer' in conversation_state.user_query.lower():
                tech_categories.extend(['usage_type', 'portability_needs', 'software_requirements'])
            
            domain_specific = [cat for cat in tech_categories if cat not in covered_categories]
        
        elif domain == 'health':
            health_categories = ['health_status', 'fitness_goals', 'dietary_restrictions']
            domain_specific = [cat for cat in health_categories if cat not in covered_categories]
        
        elif domain == 'travel':
            travel_categories = ['travel_style', 'accommodation_preferences', 'activity_preferences']
            domain_specific = [cat for cat in travel_categories if cat not in covered_categories]
        
        # Priority 3: Follow-up categories for deeper insights
        follow_up_categories = []
        user_profile = conversation_state.user_profile
        
        if 'budget' in user_profile and 'budget_flexibility' not in covered_categories:
            follow_up_categories.append('budget_flexibility')
        if 'preferences' in user_profile and 'preference_priorities' not in covered_categories:
            follow_up_categories.append('preference_priorities')
        if 'timeline' in user_profile and 'urgency_factors' not in covered_categories:
            follow_up_categories.append('urgency_factors')
        
        # Combine all gaps with priority ordering
        all_gaps = priority_gaps + domain_specific + follow_up_categories
        
        # Remove duplicates while preserving order
        unique_gaps = []
        seen = set()
        for gap in all_gaps:
            if gap not in seen:
                unique_gaps.append(gap)
                seen.add(gap)
        
        self.logger.debug(f"Identified information gaps: {unique_gaps[:7]}")
        return unique_gaps[:7]  # Return top 7 gaps
    
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
    
    def _classify_domain(self, query: str) -> str:
        """Simple domain classification for basic context."""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['smartphone', 'phone', 'laptop', 'computer', 'tech']):
            return 'technology'
        elif any(word in query_lower for word in ['travel', 'trip', 'vacation']):
            return 'travel'
        elif any(word in query_lower for word in ['health', 'medical', 'doctor']):
            return 'health'
        else:
            return 'general'
    
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
    
    def _generate_intelligent_ai_question(self, conversation_state: ConversationState, asked_questions: List[str]) -> Optional[str]:
        """Generate an intelligent question using pure AI without rigid categories."""
        try:
            # Try to use Gemini AI for intelligent question generation
            if self.question_generator.gemini_client:
                return self._generate_pure_ai_question(conversation_state, asked_questions)
            else:
                # Simple fallback if Gemini not available
                return self._generate_simple_fallback_question(conversation_state, asked_questions)
                
        except Exception as e:
            self.logger.warning(f"AI question generation failed, using fallback: {e}")
            return self._generate_simple_fallback_question(conversation_state, asked_questions)
    
    def _generate_pure_ai_question(self, conversation_state: ConversationState, asked_questions: List[str]) -> Optional[str]:
        """Use Gemini AI to generate the next intelligent question without category constraints."""
        try:
            # Create a comprehensive prompt for Gemini
            prompt = self._create_intelligent_ai_prompt(conversation_state, asked_questions)
            
            # Query Gemini for the next question
            response = self.question_generator.gemini_client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            
            if response and response.text:
                # Extract the question from the response
                generated_question = self._extract_question_from_response(response.text)
                
                if generated_question and not self._is_similar_question(generated_question, asked_questions):
                    self.logger.debug(f"AI generated intelligent question: {generated_question[:50]}...")
                    return generated_question
                else:
                    self.logger.warning("AI generated similar or invalid question, using fallback")
                    return self._generate_simple_fallback_question(conversation_state, asked_questions)
            
        except Exception as e:
            self.logger.error(f"Error in AI question generation: {e}")
            
        return None
    
    def _create_intelligent_ai_prompt(self, conversation_state: ConversationState, asked_questions: List[str]) -> str:
        """Create a comprehensive prompt for Gemini to generate intelligent questions."""
        user_profile_str = "None" if not conversation_state.user_profile else "\n".join([f"- {k}: {v}" for k, v in conversation_state.user_profile.items()])
        asked_questions_str = "None" if not asked_questions else "\n".join([f"- {q}" for q in asked_questions])
        
        # Get recent responses to understand conversation flow
        recent_responses = [qa.answer for qa in conversation_state.question_history[-3:]] if len(conversation_state.question_history) >= 3 else [qa.answer for qa in conversation_state.question_history]
        recent_responses_str = "None" if not recent_responses else "\n".join([f"- {resp}" for resp in recent_responses])
        
        prompt = f"""You are an expert research consultant helping someone make an informed decision. Your goal is to gather the most valuable information to provide personalized recommendations.

USER'S RESEARCH QUERY: "{conversation_state.user_query}"

CONVERSATION PROGRESS:
- Questions Asked So Far: {len(asked_questions)}
- Information Gathered: {len(conversation_state.user_profile)} data points

PREVIOUS QUESTIONS (AVOID SIMILAR):
{asked_questions_str}

RECENT USER RESPONSES:
{recent_responses_str}

CURRENT PROFILE:
{user_profile_str}

YOUR TASK:
Generate ONE intelligent follow-up question that will help you provide the best possible recommendation for "{conversation_state.user_query}".

THINK LIKE AN EXPERT CONSULTANT:
- What critical information are you still missing?
- What would help you narrow down the best options?
- What might reveal important preferences or constraints?
- What would an expert in this field naturally ask next?

GUIDELINES:
1. Be conversational and natural
2. Build on what you already know from their responses
3. Ask about ONE specific aspect that matters most for recommendations
4. Keep it concise (under 25 words)
5. Focus on actionable information
6. Avoid repeating similar questions

IMPORTANT:
- Do NOT ask questions similar to those already asked
- Do NOT ask for information you already have
- Focus on what will most help you make better recommendations
- Make it specific to their query: "{conversation_state.user_query}"

Generate ONLY the question text (no explanations or additional text):"""

        return prompt
    
    def _generate_simple_fallback_question(self, conversation_state: ConversationState, asked_questions: List[str]) -> Optional[str]:
        """Generate a simple fallback question when AI fails."""
        fallback_questions = [
            "What's most important to you in making this decision?",
            "Are there any specific requirements or constraints I should know about?",
            "What would make this choice perfect for your needs?",
            "How do you plan to use this?",
            "What's your timeline for making this decision?",
            "What's your budget range for this?",
            "Are there any deal-breakers I should be aware of?"
        ]
        
        # Find a question that hasn't been asked (or similar)
        for question in fallback_questions:
            if not self._is_similar_question(question, asked_questions):
                return question
        
        # If all are similar, return a generic one
        return "Can you tell me more about what you're looking for?"
    
    def _generate_ai_question(self, category: str, conversation_state: ConversationState, asked_questions: List[str]) -> Optional[str]:
        """Use Gemini AI to generate the next intelligent question."""
        try:
            # Create a comprehensive prompt for Gemini
            prompt = self._create_ai_question_prompt(category, conversation_state, asked_questions)
            
            # Query Gemini for the next question
            response = self.question_generator.gemini_client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            
            if response and response.text:
                # Extract the question from the response
                generated_question = self._extract_question_from_response(response.text)
                
                if generated_question and not self._is_similar_question(generated_question, asked_questions):
                    self.logger.debug(f"AI generated question for category '{category}': {generated_question[:50]}...")
                    return generated_question
                else:
                    self.logger.warning("AI generated similar or invalid question, using fallback")
                    return self._generate_fallback_question(category, conversation_state, asked_questions)
            
        except Exception as e:
            self.logger.error(f"Error in AI question generation: {e}")
            
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
4. Make the question specific to their research query: "{conversation_state.user_query}"
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
            
            # Ensure it ends with a question mark
            if question and not question.endswith('?'):
                question += '?'
            
            # Basic validation
            if len(question) > 5 and len(question) < 200:
                return question
                
        except Exception as e:
            self.logger.error(f"Error extracting question from response: {e}")
            
        return None
    
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
        
        for asked in asked_questions:
            asked_words = set(asked.lower().split())
            
            # Calculate word overlap
            common_words = new_words.intersection(asked_words)
            # Exclude common question words
            meaningful_common = common_words - {'what', 'is', 'your', 'the', 'do', 'you', 'how', 'are', 'for', 'to', 'a', 'an'}
            
            # If more than 2 meaningful words overlap, consider it similar
            if len(meaningful_common) >= 2:
                return True
        
        return False
    
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
