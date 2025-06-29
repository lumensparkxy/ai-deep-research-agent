"""
Conversation Memory System for Deep Research Agent
Comprehensive conversation history tracking and memory system for continuous learning and context-aware question generation.
"""

import json
import logging
import copy
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional, Set, Tuple, Union
from datetime import datetime, timedelta
from collections import defaultdict, deque
from pathlib import Path

from .conversation_state import ConversationState, QuestionAnswer, QuestionType


@dataclass
class QuestionMetrics:
    """Metrics for tracking question effectiveness."""
    question_id: str
    session_id: str
    question_text: str
    question_type: QuestionType
    category: str
    asked_at: datetime
    response_text: str = ""
    response_received: bool = False
    response_length: int = 0
    response_quality_score: float = 0.0  # 0-1 based on informativeness
    user_engagement_score: float = 0.0  # 0-1 based on response enthusiasm
    follow_up_triggered: bool = False
    information_gained: float = 0.0  # 0-1 based on new information
    context_relevance: float = 0.0  # 0-1 based on relevance to user query
    effectiveness_score: float = 0.0  # Overall calculated effectiveness


@dataclass
class ResponsePattern:
    """Pattern analysis for user responses."""
    average_length: float = 0.0
    detail_preference: str = "medium"  # low, medium, high
    communication_style: str = "mixed"  # direct, detailed, questioning, uncertain
    certainty_level: float = 0.5  # 0-1 confidence in responses
    technical_comfort: float = 0.5  # 0-1 comfort with technical language
    engagement_trend: str = "stable"  # increasing, stable, decreasing
    response_time_pattern: str = "normal"  # quick, normal, thoughtful
    question_asking_frequency: float = 0.0  # Questions per response
    
    
@dataclass
class ContextEvolution:
    """Tracking how context understanding evolves over time."""
    timestamp: datetime
    confidence_score: float
    priority_insights: List[str]
    new_information_categories: List[str]
    preference_updates: Dict[str, Any]
    understanding_breakthroughs: List[str]
    context_shifts: List[str]
    decision_criteria_updates: List[str]


@dataclass
class ConversationInsight:
    """Key insights derived from conversation analysis."""
    insight_type: str  # preference, constraint, priority, style, context
    insight_content: str
    confidence: float  # 0-1
    supporting_evidence: List[str]
    first_detected: datetime
    last_confirmed: datetime
    stability: float  # How consistent this insight has been


@dataclass
class ConversationSummary:
    """Concise summary of conversation key points."""
    session_id: str
    created_at: datetime
    user_query: str
    key_preferences: Dict[str, Any]
    main_constraints: List[str]
    communication_style: str
    confidence_evolution: List[Tuple[datetime, float]]
    breakthrough_moments: List[str]
    final_understanding: str
    question_effectiveness: Dict[str, float]


class ConversationHistory:
    """Comprehensive conversation history management system."""
    
    def __init__(self, max_history_size: int = 1000, storage_path: Optional[str] = None):
        """
        Initialize conversation history system.
        
        Args:
            max_history_size: Maximum number of conversations to keep in memory
            storage_path: Optional path for persistent storage
        """
        self.logger = logging.getLogger(__name__)
        self.max_history_size = max_history_size
        self.storage_path = Path(storage_path) if storage_path else None
        
        # Core data structures
        self.conversations: Dict[str, ConversationState] = {}
        self.question_metrics: Dict[str, QuestionMetrics] = {}
        self.response_patterns: Dict[str, ResponsePattern] = {}
        self.context_evolution: Dict[str, List[ContextEvolution]] = {}
        self.conversation_insights: Dict[str, List[ConversationInsight]] = {}
        self.conversation_summaries: Dict[str, ConversationSummary] = {}
        
        # Optimization data structures
        self.asked_questions: Dict[str, Set[str]] = defaultdict(set)  # session_id -> question hashes
        self.question_patterns: Dict[str, int] = defaultdict(int)  # question pattern -> count
        self.user_patterns: Dict[str, Dict[str, Any]] = {}  # cross-session user patterns
        
        # Recent context cache for fast access
        self.recent_conversations = deque(maxlen=50)
        
        # Load existing data if available
        if self.storage_path and self.storage_path.exists():
            self._load_from_storage()
    
    def add_conversation_state(self, conversation_state: ConversationState) -> None:
        """
        Add or update conversation state in memory.
        
        Args:
            conversation_state: Current conversation state to track
        """
        try:
            session_id = conversation_state.session_id
            
            # Store conversation state
            self.conversations[session_id] = copy.deepcopy(conversation_state)
            
            # Update recent conversations cache
            if session_id not in [conv.session_id for conv in self.recent_conversations]:
                self.recent_conversations.append(conversation_state)
            else:
                # Update existing entry
                for i, conv in enumerate(self.recent_conversations):
                    if conv.session_id == session_id:
                        self.recent_conversations[i] = conversation_state
                        break
            
            # Initialize response pattern if new session
            if session_id not in self.response_patterns:
                self.response_patterns[session_id] = ResponsePattern()
            
            # Import question history into question metrics if available
            if hasattr(conversation_state, 'question_history') and conversation_state.question_history:
                for qa in conversation_state.question_history:
                    if qa.answer:  # Only import if there's an answer
                        question_id = f"{session_id}_{hash(qa.question)}"
                        if question_id not in self.question_metrics:
                            metrics = QuestionMetrics(
                                question_id=question_id,
                                session_id=session_id,
                                question_text=qa.question,
                                question_type=qa.question_type,
                                category=qa.category,
                                asked_at=qa.timestamp,
                                response_text=qa.answer,
                                response_received=True,
                                response_length=len(qa.answer.split()),
                                response_quality_score=0.8,  # Default quality score
                                user_engagement_score=0.7,   # Default engagement
                                information_gained=0.8,      # Default information gain
                                context_relevance=0.9,       # Default relevance
                                effectiveness_score=0.8      # Default effectiveness
                            )
                            self.question_metrics[question_id] = metrics
            
            # Update response patterns
            self._update_response_patterns(conversation_state)
            
            # Track context evolution
            self._track_context_evolution(conversation_state)
            
            # Update conversation insights
            self._update_conversation_insights(conversation_state)
            
            self.logger.debug(f"Updated conversation memory for session {session_id}")
            
        except Exception as e:
            self.logger.error(f"Error adding conversation state to memory: {e}")
    
    def track_question_effectiveness(self, session_id: str, question: str, 
                                   response: str, question_type: QuestionType,
                                   category: str = "general") -> None:
        """
        Track the effectiveness of a specific question.
        
        Args:
            session_id: Session identifier
            question: The question that was asked
            response: User's response
            question_type: Type of question asked
            category: Question category
        """
        try:
            question_id = f"{session_id}_{hash(question)}"
            
            # Calculate response metrics
            response_length = len(response.split())
            response_quality = self._assess_response_quality(response)
            engagement_score = self._assess_user_engagement(response)
            information_gained = self._assess_information_gain(response)
            context_relevance = self._assess_context_relevance(question, response, session_id)
            
            # Calculate overall effectiveness
            effectiveness = (
                response_quality * 0.3 +
                engagement_score * 0.2 +
                information_gained * 0.3 +
                context_relevance * 0.2
            )
            
            # Create question metrics
            metrics = QuestionMetrics(
                question_id=question_id,
                session_id=session_id,
                question_text=question,
                response_text=response,  # Store the actual response text
                question_type=question_type,
                category=category,
                asked_at=datetime.now(),
                response_received=True,
                response_length=response_length,
                response_quality_score=response_quality,
                user_engagement_score=engagement_score,
                information_gained=information_gained,
                context_relevance=context_relevance,
                effectiveness_score=effectiveness
            )
            
            self.question_metrics[question_id] = metrics
            
            # Update question pattern tracking
            question_pattern = self._extract_question_pattern(question)
            self.question_patterns[question_pattern] += 1
            
            # Track asked questions to prevent duplicates
            question_hash = str(hash(question.lower().strip()))
            self.asked_questions[session_id].add(question_hash)
            
            self.logger.debug(f"Tracked question effectiveness: {effectiveness:.2f} for session {session_id}")
            
        except Exception as e:
            self.logger.error(f"Error tracking question effectiveness: {e}")
    
    def is_question_duplicate(self, session_id: str, question: str, similarity_threshold: float = 0.8) -> bool:
        """
        Check if a question is too similar to previously asked questions.
        
        Args:
            session_id: Session identifier
            question: Question to check
            similarity_threshold: Similarity threshold for duplicate detection
            
        Returns:
            True if question is likely a duplicate
        """
        try:
            question_hash = str(hash(question.lower().strip()))
            
            # Simple hash-based duplicate detection
            if question_hash in self.asked_questions[session_id]:
                return True
            
            # More sophisticated similarity check
            question_lower = question.lower()
            for existing_hash in self.asked_questions[session_id]:
                # Find original question from metrics
                for metrics in self.question_metrics.values():
                    if str(hash(metrics.question_text.lower().strip())) == existing_hash:
                        if self._calculate_question_similarity(question_lower, metrics.question_text.lower()) > similarity_threshold:
                            return True
                        break
            
            return False
            
        except Exception as e:
            self.logger.warning(f"Error checking question duplicate: {e}")
            return False
    
    def get_conversation_summary(self, session_id: str) -> Optional[ConversationSummary]:
        """
        Get or generate conversation summary.
        
        Args:
            session_id: Session identifier
            
        Returns:
            ConversationSummary or None if session not found
        """
        try:
            # Return cached summary if available
            if session_id in self.conversation_summaries:
                return self.conversation_summaries[session_id]
            
            # Generate summary if conversation exists
            if session_id in self.conversations:
                summary = self._generate_conversation_summary(session_id)
                self.conversation_summaries[session_id] = summary
                return summary
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting conversation summary: {e}")
            return None
    
    def get_response_pattern(self, session_id: str) -> Optional[ResponsePattern]:
        """
        Get response pattern analysis for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            ResponsePattern or None if not found
        """
        return self.response_patterns.get(session_id)
    
    def get_context_evolution(self, session_id: str) -> List[ContextEvolution]:
        """
        Get context evolution timeline for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of context evolution points
        """
        return self.context_evolution.get(session_id, [])
    
    def get_conversation_insights(self, session_id: str) -> List[ConversationInsight]:
        """
        Get derived insights for a conversation.
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of conversation insights
        """
        return self.conversation_insights.get(session_id, [])
    
    def get_question_recommendations(self, session_id: str, category: Optional[str] = None) -> List[str]:
        """
        Get recommended questions based on conversation history and patterns.
        
        Args:
            session_id: Session identifier
            category: Optional category filter
            
        Returns:
            List of recommended questions
        """
        try:
            recommendations = []
            
            # Get current conversation state
            if session_id not in self.conversations:
                return recommendations
            
            conversation = self.conversations[session_id]
            response_pattern = self.response_patterns.get(session_id)
            
            # Analyze what information is still needed
            missing_categories = self._identify_missing_information(conversation)
            
            # Generate recommendations based on patterns
            for missing_cat in missing_categories:
                if category and missing_cat != category:
                    continue
                
                # Find effective questions for this category
                effective_questions = self._find_effective_questions_for_category(missing_cat)
                
                # Adapt questions to user's communication style
                if response_pattern:
                    adapted_questions = self._adapt_questions_to_style(effective_questions, response_pattern)
                    recommendations.extend(adapted_questions)
                else:
                    recommendations.extend(effective_questions)
            
            # Remove duplicates and limit recommendations
            unique_recommendations = []
            for rec in recommendations:
                if not self.is_question_duplicate(session_id, rec) and rec not in unique_recommendations:
                    unique_recommendations.append(rec)
            
            return unique_recommendations[:5]  # Limit to top 5 recommendations
            
        except Exception as e:
            self.logger.error(f"Error getting question recommendations: {e}")
            return []
    
    def save_to_storage(self) -> bool:
        """
        Save conversation history to persistent storage.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.storage_path:
                return False
            
            # Prepare data for serialization
            storage_data = {
                'conversations': {k: asdict(v) for k, v in self.conversations.items()},
                'question_metrics': {k: asdict(v) for k, v in self.question_metrics.items()},
                'response_patterns': {k: asdict(v) for k, v in self.response_patterns.items()},
                'context_evolution': {k: [asdict(ev) for ev in evs] for k, evs in self.context_evolution.items()},
                'conversation_insights': {k: [asdict(ins) for ins in insights] for k, insights in self.conversation_insights.items()},
                'conversation_summaries': {k: asdict(v) for k, v in self.conversation_summaries.items()},
                'asked_questions': {k: list(v) for k, v in self.asked_questions.items()},
                'question_patterns': dict(self.question_patterns),
                'user_patterns': self.user_patterns,
                'metadata': {
                    'saved_at': datetime.now().isoformat(),
                    'version': '1.0'
                }
            }
            
            # Save to file
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.storage_path, 'w') as f:
                json.dump(storage_data, f, indent=2, default=str)
            
            self.logger.info(f"Conversation history saved to {self.storage_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving conversation history: {e}")
            return False
    
    def cleanup_old_conversations(self, days_to_keep: int = 30) -> int:
        """
        Clean up old conversations to manage memory usage.
        
        Args:
            days_to_keep: Number of days of conversations to keep
            
        Returns:
            Number of conversations cleaned up
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            cleaned_count = 0
            
            # Find old conversations
            old_sessions = []
            for session_id, conversation in self.conversations.items():
                # Check conversation timestamp (use first question timestamp as proxy)
                if conversation.question_history:
                    oldest_timestamp = min(qa.timestamp for qa in conversation.question_history)
                    if oldest_timestamp < cutoff_date:
                        old_sessions.append(session_id)
            
            # Remove old conversations
            for session_id in old_sessions:
                self._remove_conversation(session_id)
                cleaned_count += 1
            
            self.logger.info(f"Cleaned up {cleaned_count} old conversations")
            return cleaned_count
            
        except Exception as e:
            self.logger.error(f"Error cleaning up conversations: {e}")
            return 0
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """
        Get memory usage statistics.
        
        Returns:
            Dictionary with memory statistics
        """
        try:
            total_conversations = len(self.conversations)
            total_questions = len(self.question_metrics)
            recent_conversations = len(self.recent_conversations)
            
            # Calculate average metrics
            avg_effectiveness = 0.0
            if self.question_metrics:
                avg_effectiveness = sum(m.effectiveness_score for m in self.question_metrics.values()) / len(self.question_metrics)
            
            return {
                'total_conversations': total_conversations,
                'total_questions_tracked': total_questions,
                'recent_conversations_cached': recent_conversations,
                'average_question_effectiveness': avg_effectiveness,
                'memory_usage_estimate_mb': self._estimate_memory_usage(),
                'storage_available': self.storage_path is not None,
                'question_patterns_learned': len(self.question_patterns)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting memory stats: {e}")
            return {}
    
    # Private helper methods
    
    def _load_from_storage(self) -> None:
        """Load conversation history from persistent storage."""
        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
            
            # Restore conversations (simplified for now)
            # Note: Would need proper deserialization for full implementation
            self.logger.info(f"Loaded conversation history from {self.storage_path}")
            
        except Exception as e:
            self.logger.warning(f"Could not load conversation history: {e}")
    
    def _update_response_patterns(self, conversation_state: ConversationState) -> None:
        """Update response patterns based on conversation state."""
        try:
            session_id = conversation_state.session_id
            pattern = self.response_patterns[session_id]
            
            # Get question metrics for this session that have responses
            session_questions = [q for q in self.question_metrics.values() 
                               if q.session_id == session_id and q.response_text]
            
            if not session_questions:
                return
            
            responses = [q.response_text for q in session_questions]
            
            if responses:
                # Update average length (word count)
                word_counts = [len(r.split()) for r in responses]
                pattern.average_length = sum(word_counts) / len(word_counts)
                
                # Assess detail preference
                if pattern.average_length > 50:
                    pattern.detail_preference = "high"
                elif pattern.average_length > 20:
                    pattern.detail_preference = "medium"
                else:
                    pattern.detail_preference = "low"
                
                # Assess communication style
                question_count = sum(r.count('?') for r in responses)
                uncertainty_words = ['maybe', 'perhaps', 'not sure', 'i think', 'probably']
                has_uncertainty = any(any(word in r.lower() for word in uncertainty_words) for r in responses)
                
                if question_count > len(responses):
                    pattern.communication_style = "questioning"
                elif has_uncertainty:
                    pattern.communication_style = "uncertain"
                elif pattern.average_length > 30:
                    pattern.communication_style = "detailed"
                else:
                    pattern.communication_style = "direct"
                
                # Update certainty level
                certainty_indicators = sum(1 for r in responses if any(word in r.lower() 
                                         for word in ['definitely', 'absolutely', 'exactly', 'yes', 'no']))
                pattern.certainty_level = min(1.0, certainty_indicators / len(responses))
                
                # Update technical comfort
                tech_words = ['api', 'database', 'algorithm', 'framework', 'software', 'hardware', 'technical']
                tech_usage = sum(1 for r in responses if any(word in r.lower() for word in tech_words))
                pattern.technical_comfort = min(1.0, tech_usage / len(responses))
                
                # Calculate question asking frequency
                total_questions = sum(r.count('?') for r in responses)
                pattern.question_asking_frequency = total_questions / len(responses) if responses else 0.0
            
        except Exception as e:
            self.logger.error(f"Error updating response patterns: {e}")
    
    def _track_context_evolution(self, conversation_state: ConversationState) -> None:
        """Track how context understanding evolves."""
        try:
            session_id = conversation_state.session_id
            
            if session_id not in self.context_evolution:
                self.context_evolution[session_id] = []
            
            # Create evolution snapshot
            evolution = ContextEvolution(
                timestamp=datetime.now(),
                confidence_score=conversation_state.completion_confidence,
                priority_insights=[],  # Would be populated from context analysis
                new_information_categories=list(conversation_state.user_profile.keys()),
                preference_updates=conversation_state.user_profile,
                understanding_breakthroughs=[],
                context_shifts=[],
                decision_criteria_updates=[]
            )
            
            self.context_evolution[session_id].append(evolution)
            
        except Exception as e:
            self.logger.warning(f"Error tracking context evolution: {e}")
    
    def _update_conversation_insights(self, conversation_state: ConversationState) -> None:
        """Update conversation insights based on current state."""
        try:
            session_id = conversation_state.session_id
            
            if session_id not in self.conversation_insights:
                self.conversation_insights[session_id] = []
            
            # Analyze for new insights (simplified)
            insights = self.conversation_insights[session_id]
            
            # Add preference insights
            for key, value in conversation_state.user_profile.items():
                if isinstance(value, str) and len(value) > 10:
                    insight = ConversationInsight(
                        insight_type="preference",
                        insight_content=f"{key}: {value}",
                        confidence=0.8,
                        supporting_evidence=[value],
                        first_detected=datetime.now(),
                        last_confirmed=datetime.now(),
                        stability=0.8
                    )
                    insights.append(insight)
            
        except Exception as e:
            self.logger.warning(f"Error updating conversation insights: {e}")
    
    def _generate_conversation_summary(self, session_id: str) -> ConversationSummary:
        """Generate a conversation summary."""
        conversation = self.conversations[session_id]
        
        # Extract key information
        key_preferences = {k: v for k, v in conversation.user_profile.items() if isinstance(v, (str, int, float))}
        
        # Generate confidence evolution timeline
        evolution_timeline = [(ev.timestamp, ev.confidence_score) for ev in self.context_evolution.get(session_id, [])]
        
        return ConversationSummary(
            session_id=session_id,
            created_at=datetime.now(),
            user_query=conversation.user_query,
            key_preferences=key_preferences,
            main_constraints=[],
            communication_style=self.response_patterns.get(session_id, ResponsePattern()).communication_style,
            confidence_evolution=evolution_timeline,
            breakthrough_moments=[],
            final_understanding=f"Understanding level: {conversation.completion_confidence:.1%}",
            question_effectiveness={}
        )
    
    def _assess_response_quality(self, response: str) -> float:
        """Assess the quality of a response (0-1)."""
        # Simple heuristic - could be enhanced with AI analysis
        if len(response.strip()) == 0:
            return 0.0
        elif len(response.split()) < 3:
            return 0.3
        elif len(response.split()) < 10:
            return 0.6
        else:
            return 0.9
    
    def _assess_user_engagement(self, response: str) -> float:
        """Assess user engagement level (0-1)."""
        # Look for engagement indicators
        engagement_words = ['excited', 'interested', 'love', 'great', 'perfect', 'exactly']
        disengagement_words = ['fine', 'whatever', 'sure', 'ok', 'meh']
        
        response_lower = response.lower()
        engagement_score = sum(1 for word in engagement_words if word in response_lower)
        disengagement_score = sum(1 for word in disengagement_words if word in response_lower)
        
        if engagement_score > disengagement_score:
            return min(1.0, 0.5 + engagement_score * 0.2)
        elif disengagement_score > 0:
            return max(0.0, 0.5 - disengagement_score * 0.2)
        else:
            return 0.5
    
    def _assess_information_gain(self, response: str) -> float:
        """Assess how much new information was gained (0-1)."""
        # Simple metric based on response length and specificity
        word_count = len(response.split())
        
        # Look for specific information indicators
        specific_indicators = ['$', '%', 'years', 'months', 'exactly', 'specifically', 'prefer']
        specificity_score = sum(1 for indicator in specific_indicators if indicator in response.lower())
        
        base_score = min(1.0, word_count / 50)  # Longer responses generally have more info
        specificity_bonus = min(0.3, specificity_score * 0.1)
        
        return min(1.0, base_score + specificity_bonus)
    
    def _assess_context_relevance(self, question: str, response: str, session_id: str) -> float:
        """Assess how relevant the question was to the user's context (0-1)."""
        # Simplified assessment - could be enhanced with semantic analysis
        if session_id in self.conversations:
            user_query = self.conversations[session_id].user_query.lower()
            question_lower = question.lower()
            
            # Check if question relates to original user query
            query_words = set(user_query.split())
            question_words = set(question_lower.split())
            
            overlap = len(query_words.intersection(question_words))
            max_words = max(len(query_words), len(question_words))
            
            if max_words > 0:
                return min(1.0, overlap / max_words * 2)  # Boost relevance scoring
        
        return 0.5  # Default relevance
    
    def _extract_question_pattern(self, question: str) -> str:
        """Extract a pattern from a question for duplicate detection."""
        # Remove specific details but keep structure
        question_lower = question.lower()
        
        # Replace specific words with placeholders
        pattern = question_lower
        
        # Replace numbers with placeholder
        import re
        pattern = re.sub(r'\d+', '[NUM]', pattern)
        
        # Replace proper nouns (simplified)
        pattern = re.sub(r'\b[A-Z][a-z]+\b', '[NAME]', pattern)
        
        return pattern
    
    def _calculate_question_similarity(self, q1: str, q2: str) -> float:
        """Calculate similarity between two questions (0-1)."""
        # Simple word overlap similarity
        words1 = set(q1.lower().split())
        words2 = set(q2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _identify_missing_information(self, conversation: ConversationState) -> List[str]:
        """Identify what information categories are still missing."""
        gathered_categories = set(conversation.user_profile.keys())
        
        # Important categories for most research
        important_categories = {
            'budget', 'timeline', 'context', 'preferences', 
            'constraints', 'experience_level', 'goals'
        }
        
        return list(important_categories - gathered_categories)
    
    def _find_effective_questions_for_category(self, category: str) -> List[str]:
        """Find effective questions for a specific information category."""
        # Template questions for different categories
        question_templates = {
            'budget': [
                "What's your budget range for this?",
                "Do you have any budget constraints I should know about?",
                "Are you looking for something cost-effective or premium?"
            ],
            'timeline': [
                "When do you need this by?",
                "Is this urgent or can we take time to find the best option?",
                "What's your timeline for making this decision?"
            ],
            'context': [
                "What will you be using this for primarily?",
                "Is this for personal use, work, or something else?",
                "Can you tell me more about how you plan to use this?"
            ],
            'preferences': [
                "What features are most important to you?",
                "Do you have any specific preferences I should consider?",
                "What would make this perfect for your needs?"
            ],
            'experience_level': [
                "What's your experience level with this type of product?",
                "Are you a beginner or do you have experience with this?",
                "How familiar are you with the technical aspects?"
            ]
        }
        
        return question_templates.get(category, ["Could you tell me more about your requirements?"])
    
    def _adapt_questions_to_style(self, questions: List[str], pattern: ResponsePattern) -> List[str]:
        """Adapt questions to match user's communication style."""
        adapted = []
        
        for question in questions:
            if pattern.communication_style == "direct" and pattern.detail_preference == "low":
                # Make questions more direct and concise
                adapted_q = question.replace("Could you tell me more about", "What is")
                adapted_q = adapted_q.replace("I should know about", "to consider")
                adapted.append(adapted_q)
            elif pattern.communication_style == "detailed" and pattern.detail_preference == "high":
                # Make questions more detailed and exploratory
                adapted_q = question.replace("What's", "Could you provide details about")
                adapted_q = adapted_q.replace("?", " and any related considerations?")
                adapted.append(adapted_q)
            else:
                adapted.append(question)
        
        return adapted
    
    def _remove_conversation(self, session_id: str) -> None:
        """Remove all data for a conversation session."""
        # Remove from all data structures
        self.conversations.pop(session_id, None)
        self.response_patterns.pop(session_id, None)
        self.context_evolution.pop(session_id, None)
        self.conversation_insights.pop(session_id, None)
        self.conversation_summaries.pop(session_id, None)
        self.asked_questions.pop(session_id, None)
        
        # Remove from recent conversations cache
        self.recent_conversations = deque(
            [conv for conv in self.recent_conversations if conv.session_id != session_id],
            maxlen=self.recent_conversations.maxlen
        )
        
        # Remove related question metrics
        to_remove = [qid for qid in self.question_metrics if qid.startswith(session_id)]
        for qid in to_remove:
            self.question_metrics.pop(qid, None)
    
    def _estimate_memory_usage(self) -> float:
        """Estimate memory usage in MB."""
        # Rough estimate based on data structure sizes
        import sys
        
        total_size = 0
        total_size += sys.getsizeof(self.conversations)
        total_size += sys.getsizeof(self.question_metrics)
        total_size += sys.getsizeof(self.response_patterns)
        total_size += sys.getsizeof(self.context_evolution)
        total_size += sys.getsizeof(self.conversation_insights)
        
        return total_size / (1024 * 1024)  # Convert to MB


class ConversationMemory:
    """Main interface for conversation memory system."""
    
    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize conversation memory system.
        
        Args:
            storage_path: Optional path for persistent storage
        """
        self.logger = logging.getLogger(__name__)
        self.history = ConversationHistory(storage_path=storage_path)
    
    def update_conversation(self, conversation_state: ConversationState) -> None:
        """
        Update conversation in memory.
        
        Args:
            conversation_state: Current conversation state
        """
        self.history.add_conversation_state(conversation_state)
    
    def track_question_response(self, session_id: str, question: str, response: str,
                               question_type: QuestionType, category: str = "general") -> None:
        """
        Track a question and its response for effectiveness analysis.
        
        Args:
            session_id: Session identifier
            question: Question that was asked
            response: User's response
            question_type: Type of question
            category: Question category
        """
        self.history.track_question_effectiveness(session_id, question, response, question_type, category)
    
    def should_ask_question(self, session_id: str, question: str) -> bool:
        """
        Check if a question should be asked (not a duplicate).
        
        Args:
            session_id: Session identifier
            question: Question to check
            
        Returns:
            True if question should be asked, False if it's a duplicate
        """
        return not self.history.is_question_duplicate(session_id, question)
    
    def get_question_suggestions(self, session_id: str, category: Optional[str] = None) -> List[str]:
        """
        Get question suggestions based on conversation history.
        
        Args:
            session_id: Session identifier
            category: Optional category filter
            
        Returns:
            List of suggested questions
        """
        return self.history.get_question_recommendations(session_id, category)
    
    def get_conversation_insights(self, session_id: str) -> Dict[str, Any]:
        """
        Get comprehensive insights about a conversation.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Dictionary with conversation insights
        """
        return {
            'summary': self.history.get_conversation_summary(session_id),
            'response_pattern': self.history.get_response_pattern(session_id),
            'context_evolution': self.history.get_context_evolution(session_id),
            'insights': self.history.get_conversation_insights(session_id)
        }
    
    def save_memory(self) -> bool:
        """
        Save conversation memory to persistent storage.
        
        Returns:
            True if successful
        """
        return self.history.save_to_storage()
    
    def cleanup_old_data(self, days_to_keep: int = 30) -> int:
        """
        Clean up old conversation data.
        
        Args:
            days_to_keep: Number of days to keep
            
        Returns:
            Number of conversations cleaned up
        """
        return self.history.cleanup_old_conversations(days_to_keep)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get memory system statistics.
        
        Returns:
            Dictionary with statistics
        """
        return self.history.get_memory_stats()
