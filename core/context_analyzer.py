"""
Context Analysis Engine for Deep Research Agent
Intelligent conversation context understanding that analyzes user responses to build deeper insights.
"""

import re
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple, Set
from datetime import datetime
from enum import Enum

# Import dependencies from existing foundation components
from .conversation_state import ConversationState, QuestionAnswer, QuestionType


class PriorityLevel(Enum):
    """Priority levels for different aspects of user context."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AnalysisConfidence(Enum):
    """Confidence levels for analysis results."""
    VERY_HIGH = "very_high"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    VERY_LOW = "very_low"


class CommunicationStyle(Enum):
    """User communication style patterns."""
    ANALYTICAL = "analytical"  # Detailed, logical responses
    INTUITIVE = "intuitive"    # Feeling-based, preference-driven
    DIRECT = "direct"         # Short, to-the-point responses
    EXPLORATORY = "exploratory"  # Asks questions, explores options
    DECISIVE = "decisive"     # Clear preferences, quick decisions
    UNCERTAIN = "uncertain"   # Indecisive, seeks guidance


@dataclass
class PriorityInsight:
    """Represents a priority detected from user responses."""
    category: str
    importance: PriorityLevel
    confidence: AnalysisConfidence
    supporting_evidence: List[str]
    keywords: List[str]
    weight: float  # 0.0-1.0 relative importance


@dataclass
class EmotionalIndicator:
    """Represents emotional state indicators detected in responses."""
    emotion_type: str  # urgency, anxiety, excitement, frustration, etc.
    intensity: float  # 0.0-1.0
    confidence: AnalysisConfidence
    triggering_phrases: List[str]
    context: str


@dataclass
class PatternInsight:
    """Represents communication pattern insights."""
    pattern_type: str
    confidence: AnalysisConfidence
    supporting_evidence: List[str]
    implications: List[str]  # What this means for question generation


@dataclass
class ContextualGap:
    """Represents an identified information gap with context."""
    category: str
    priority: PriorityLevel
    confidence: AnalysisConfidence
    impact_on_research: str
    suggested_approach: str
    related_patterns: List[str]


@dataclass
class ContextAnalysisResult:
    """Complete result of context analysis."""
    priority_insights: List[PriorityInsight]
    emotional_indicators: List[EmotionalIndicator]
    communication_style: CommunicationStyle
    pattern_insights: List[PatternInsight]
    contextual_gaps: List[ContextualGap]
    overall_confidence: float  # 0.0-1.0
    analysis_timestamp: datetime
    recommendations: List[str]
    evolution_notes: List[str]  # How understanding has evolved


class ContextAnalyzer:
    """
    Intelligent context analysis engine for conversation understanding.
    
    Analyzes user responses to extract priorities, patterns, emotional indicators,
    and contextual insights that guide personalized question generation.
    """
    
    def __init__(self):
        """Initialize the context analyzer."""
        self.logger = logging.getLogger(__name__)
        
        # Analysis patterns and keywords
        self._initialize_analysis_patterns()
        
        # Analysis history for evolution tracking
        self._analysis_history: List[ContextAnalysisResult] = []
        
    def analyze_context(self, conversation_state: ConversationState) -> ContextAnalysisResult:
        """
        Perform comprehensive context analysis of the conversation.
        
        Args:
            conversation_state: Current conversation state with user responses
            
        Returns:
            ContextAnalysisResult with detailed insights
        """
        self.logger.info(f"Analyzing context for session: {conversation_state.session_id}")
        
        try:
            # Extract all user responses for analysis
            user_responses = self._extract_user_responses(conversation_state)
            combined_text = " ".join(user_responses)
            
            # Perform different types of analysis
            priority_insights = self._analyze_priorities(user_responses, conversation_state)
            emotional_indicators = self._analyze_emotional_state(combined_text)
            communication_style = self._determine_communication_style(user_responses)
            pattern_insights = self._detect_patterns(user_responses, conversation_state)
            contextual_gaps = self._identify_contextual_gaps(conversation_state, priority_insights)
            
            # Calculate overall confidence
            overall_confidence = self._calculate_overall_confidence(
                priority_insights, emotional_indicators, pattern_insights
            )
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                priority_insights, communication_style, contextual_gaps
            )
            
            # Track evolution
            evolution_notes = self._track_context_evolution(conversation_state)
            
            result = ContextAnalysisResult(
                priority_insights=priority_insights,
                emotional_indicators=emotional_indicators,
                communication_style=communication_style,
                pattern_insights=pattern_insights,
                contextual_gaps=contextual_gaps,
                overall_confidence=overall_confidence,
                analysis_timestamp=datetime.now(),
                recommendations=recommendations,
                evolution_notes=evolution_notes
            )
            
            # Store for evolution tracking
            self._analysis_history.append(result)
            
            self.logger.info(f"Context analysis complete: confidence={overall_confidence:.2f}, "
                           f"style={communication_style.value}, gaps={len(contextual_gaps)}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error during context analysis: {e}")
            return self._create_fallback_result()
    
    def analyze_response_patterns(self, response: str) -> Dict[str, Any]:
        """
        Analyze patterns in a single response.
        
        Args:
            response: User response text
            
        Returns:
            Dictionary of detected patterns
        """
        patterns = {
            'length': len(response.split()),
            'detail_level': self._assess_detail_level(response),
            'certainty_indicators': self._detect_certainty_level(response),
            'technical_language': self._assess_technical_language(response),
            'emotional_language': self._detect_emotional_language(response),
            'questions_asked': len(re.findall(r'\?', response)),
            'specificity': self._assess_specificity(response)
        }
        
        return patterns
    
    def extract_priorities_from_response(self, response: str, context: Dict[str, Any]) -> List[PriorityInsight]:
        """
        Extract priority insights from a single response.
        
        Args:
            response: User response text
            context: Additional context information
            
        Returns:
            List of detected priority insights
        """
        priorities = []
        response_lower = response.lower()
        
        # Budget priority detection
        budget_insight = self._analyze_budget_priority(response_lower)
        if budget_insight:
            priorities.append(budget_insight)
        
        # Timeline priority detection
        timeline_insight = self._analyze_timeline_priority(response_lower)
        if timeline_insight:
            priorities.append(timeline_insight)
        
        # Feature importance detection
        feature_insights = self._analyze_feature_priorities(response_lower)
        priorities.extend(feature_insights)
        
        # Quality vs. convenience trade-offs
        tradeoff_insights = self._analyze_tradeoff_priorities(response_lower)
        priorities.extend(tradeoff_insights)
        
        return priorities
    
    def detect_information_gaps(self, conversation_state: ConversationState) -> List[ContextualGap]:
        """
        Detect information gaps that would improve research quality.
        
        Args:
            conversation_state: Current conversation state
            
        Returns:
            List of contextual gaps with priorities
        """
        return self._identify_contextual_gaps(conversation_state, [])
    
    def assess_response_confidence(self, response: str) -> Tuple[float, List[str]]:
        """
        Assess confidence level in a user response.
        
        Args:
            response: User response text
            
        Returns:
            Tuple of (confidence_score, confidence_indicators)
        """
        confidence_indicators = []
        confidence_score = 0.5  # Base confidence
        
        response_lower = response.lower()
        
        # High confidence indicators
        high_confidence_phrases = [
            'definitely', 'absolutely', 'certainly', 'for sure', 'without a doubt',
            'exactly', 'precisely', 'clearly', 'obviously'
        ]
        
        # Low confidence indicators
        low_confidence_phrases = [
            'maybe', 'perhaps', 'might', 'could be', 'not sure', 'uncertain',
            'possibly', 'probably', 'i think', 'i guess', 'sort of'
        ]
        
        # Count indicators
        high_count = sum(1 for phrase in high_confidence_phrases if phrase in response_lower)
        low_count = sum(1 for phrase in low_confidence_phrases if phrase in response_lower)
        
        # Adjust confidence
        confidence_score += (high_count * 0.2) - (low_count * 0.15)
        confidence_score = max(0.0, min(1.0, confidence_score))
        
        # Record indicators found
        if high_count > 0:
            confidence_indicators.append(f"High confidence language detected ({high_count} indicators)")
        if low_count > 0:
            confidence_indicators.append(f"Uncertainty language detected ({low_count} indicators)")
        
        return confidence_score, confidence_indicators
    
    def _initialize_analysis_patterns(self):
        """Initialize pattern matching data structures."""
        # Priority keywords
        self.budget_keywords = [
            'budget', 'cost', 'price', 'expensive', 'cheap', 'affordable', 'money',
            'free', 'premium', 'value', 'investment', '$', '€', '£'
        ]
        
        self.timeline_keywords = [
            'urgent', 'asap', 'quickly', 'fast', 'deadline', 'timeline', 'schedule',
            'soon', 'immediately', 'time', 'delay', 'rush', 'hurry'
        ]
        
        self.quality_keywords = [
            'quality', 'best', 'excellent', 'perfect', 'reliable', 'durable',
            'premium', 'professional', 'robust', 'solid', 'top-tier'
        ]
        
        # Emotional indicators
        self.urgency_patterns = [
            r'need.{0,5}(asap|urgently|quickly|immediately)',
            r'(urgent|critical|emergency)',
            r'deadline.{0,10}(tomorrow|today|soon)'
        ]
        
        self.anxiety_patterns = [
            r'(worried|concerned|anxious|nervous)',
            r'hope.{0,5}(works|right)',
            r'(scared|afraid).{0,10}(wrong|mistake)'
        ]
        
        self.excitement_patterns = [
            r'(excited|thrilled|amazing|fantastic)',
            r'can\'t wait',
            r'(love|adore).{0,5}(idea|concept)'
        ]
        
        # Technical language indicators
        self.technical_terms = {
            'technology': ['api', 'framework', 'algorithm', 'database', 'protocol'],
            'finance': ['roi', 'portfolio', 'diversification', 'yield', 'equity'],
            'health': ['metabolism', 'cardiovascular', 'diagnosis', 'treatment'],
            'general': ['specification', 'optimization', 'integration', 'methodology']
        }
    
    def _extract_user_responses(self, conversation_state: ConversationState) -> List[str]:
        """Extract all user responses from conversation history."""
        responses = [conversation_state.user_query]  # Include initial query
        
        for qa in conversation_state.question_history:
            if qa.answer:
                responses.append(qa.answer)
        
        return [r for r in responses if r.strip()]
    
    def _analyze_priorities(self, responses: List[str], conversation_state: ConversationState) -> List[PriorityInsight]:
        """Analyze priority insights from all responses."""
        all_priorities = []
        combined_text = " ".join(responses).lower()
        
        # Budget analysis
        budget_priority = self._analyze_budget_priority(combined_text)
        if budget_priority:
            all_priorities.append(budget_priority)
        
        # Timeline analysis
        timeline_priority = self._analyze_timeline_priority(combined_text)
        if timeline_priority:
            all_priorities.append(timeline_priority)
        
        # Feature priorities
        feature_priorities = self._analyze_feature_priorities(combined_text)
        all_priorities.extend(feature_priorities)
        
        # Quality vs convenience
        tradeoff_priorities = self._analyze_tradeoff_priorities(combined_text)
        all_priorities.extend(tradeoff_priorities)
        
        # Risk tolerance
        risk_priority = self._analyze_risk_tolerance(combined_text)
        if risk_priority:
            all_priorities.append(risk_priority)
        
        return all_priorities
    
    def _analyze_budget_priority(self, text: str) -> Optional[PriorityInsight]:
        """Analyze budget-related priorities."""
        budget_mentions = sum(1 for keyword in self.budget_keywords if keyword in text)
        
        if budget_mentions == 0:
            return None
        
        # Determine priority level based on language
        if any(phrase in text for phrase in ['tight budget', 'limited funds', 'as cheap as possible']):
            priority = PriorityLevel.CRITICAL
            weight = 0.9
        elif any(phrase in text for phrase in ['budget conscious', 'good value', 'reasonable price']):
            priority = PriorityLevel.HIGH
            weight = 0.7
        else:
            priority = PriorityLevel.MEDIUM
            weight = 0.5
        
        return PriorityInsight(
            category='budget',
            importance=priority,
            confidence=AnalysisConfidence.HIGH if budget_mentions >= 2 else AnalysisConfidence.MEDIUM,
            supporting_evidence=[f"Budget mentioned {budget_mentions} times"],
            keywords=[kw for kw in self.budget_keywords if kw in text],
            weight=weight
        )
    
    def _analyze_timeline_priority(self, text: str) -> Optional[PriorityInsight]:
        """Analyze timeline-related priorities."""
        timeline_mentions = sum(1 for keyword in self.timeline_keywords if keyword in text)
        
        if timeline_mentions == 0:
            return None
        
        # Check for urgency patterns
        urgency_detected = any(re.search(pattern, text, re.IGNORECASE) for pattern in self.urgency_patterns)
        
        if urgency_detected or 'urgent' in text:
            priority = PriorityLevel.CRITICAL
            weight = 0.95
        elif any(word in text for word in ['soon', 'quickly', 'fast']):
            priority = PriorityLevel.HIGH
            weight = 0.8
        else:
            priority = PriorityLevel.MEDIUM
            weight = 0.6
        
        return PriorityInsight(
            category='timeline',
            importance=priority,
            confidence=AnalysisConfidence.HIGH if urgency_detected else AnalysisConfidence.MEDIUM,
            supporting_evidence=[f"Timeline mentioned {timeline_mentions} times"],
            keywords=[kw for kw in self.timeline_keywords if kw in text],
            weight=weight
        )
    
    def _analyze_feature_priorities(self, text: str) -> List[PriorityInsight]:
        """Analyze feature importance priorities."""
        features = []
        
        # Quality emphasis
        quality_mentions = sum(1 for keyword in self.quality_keywords if keyword in text)
        if quality_mentions > 0:
            features.append(PriorityInsight(
                category='quality',
                importance=PriorityLevel.HIGH if quality_mentions >= 2 else PriorityLevel.MEDIUM,
                confidence=AnalysisConfidence.MEDIUM,
                supporting_evidence=[f"Quality emphasized {quality_mentions} times"],
                keywords=[kw for kw in self.quality_keywords if kw in text],
                weight=0.7 if quality_mentions >= 2 else 0.5
            ))
        
        # Convenience indicators
        convenience_words = ['easy', 'simple', 'convenient', 'user-friendly', 'intuitive']
        convenience_mentions = sum(1 for word in convenience_words if word in text)
        if convenience_mentions > 0:
            features.append(PriorityInsight(
                category='convenience',
                importance=PriorityLevel.MEDIUM,
                confidence=AnalysisConfidence.MEDIUM,
                supporting_evidence=[f"Convenience mentioned {convenience_mentions} times"],
                keywords=[word for word in convenience_words if word in text],
                weight=0.6
            ))
        
        return features
    
    def _analyze_tradeoff_priorities(self, text: str) -> List[PriorityInsight]:
        """Analyze trade-off preferences."""
        tradeoffs = []
        
        # Speed vs quality
        if 'quick' in text and 'quality' in text:
            if text.find('quick') < text.find('quality'):
                priority = 'speed_over_quality'
            else:
                priority = 'quality_over_speed'
            
            tradeoffs.append(PriorityInsight(
                category=priority,
                importance=PriorityLevel.MEDIUM,
                confidence=AnalysisConfidence.MEDIUM,
                supporting_evidence=['Trade-off preference detected'],
                keywords=['quick', 'quality'],
                weight=0.6
            ))
        
        return tradeoffs
    
    def _analyze_risk_tolerance(self, text: str) -> Optional[PriorityInsight]:
        """Analyze risk tolerance indicators."""
        conservative_words = ['safe', 'secure', 'reliable', 'proven', 'established', 'conservative']
        adventurous_words = ['experimental', 'cutting-edge', 'innovative', 'new', 'latest', 'risky']
        
        conservative_count = sum(1 for word in conservative_words if word in text)
        adventurous_count = sum(1 for word in adventurous_words if word in text)
        
        if conservative_count > adventurous_count and conservative_count > 0:
            return PriorityInsight(
                category='risk_tolerance',
                importance=PriorityLevel.MEDIUM,
                confidence=AnalysisConfidence.MEDIUM,
                supporting_evidence=[f"Conservative language detected ({conservative_count} indicators)"],
                keywords=[word for word in conservative_words if word in text],
                weight=0.7
            )
        elif adventurous_count > conservative_count and adventurous_count > 0:
            return PriorityInsight(
                category='risk_tolerance',
                importance=PriorityLevel.MEDIUM,
                confidence=AnalysisConfidence.MEDIUM,
                supporting_evidence=[f"Adventurous language detected ({adventurous_count} indicators)"],
                keywords=[word for word in adventurous_words if word in text],
                weight=0.7
            )
        
        return None
    
    def _analyze_emotional_state(self, text: str) -> List[EmotionalIndicator]:
        """Analyze emotional indicators in the text."""
        indicators = []
        
        # Urgency detection
        urgency_matches = []
        for pattern in self.urgency_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            urgency_matches.extend(matches)
        
        if urgency_matches:
            indicators.append(EmotionalIndicator(
                emotion_type='urgency',
                intensity=min(1.0, len(urgency_matches) * 0.3),
                confidence=AnalysisConfidence.HIGH,
                triggering_phrases=urgency_matches,
                context='Timeline pressure detected'
            ))
        
        # Anxiety detection
        anxiety_matches = []
        for pattern in self.anxiety_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            anxiety_matches.extend(matches)
        
        if anxiety_matches:
            indicators.append(EmotionalIndicator(
                emotion_type='anxiety',
                intensity=min(1.0, len(anxiety_matches) * 0.4),
                confidence=AnalysisConfidence.MEDIUM,
                triggering_phrases=anxiety_matches,
                context='Concern or worry detected'
            ))
        
        # Excitement detection
        excitement_matches = []
        for pattern in self.excitement_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            excitement_matches.extend(matches)
        
        if excitement_matches:
            indicators.append(EmotionalIndicator(
                emotion_type='excitement',
                intensity=min(1.0, len(excitement_matches) * 0.5),
                confidence=AnalysisConfidence.MEDIUM,
                triggering_phrases=excitement_matches,
                context='Enthusiasm or excitement detected'
            ))
        
        return indicators
    
    def _determine_communication_style(self, responses: List[str]) -> CommunicationStyle:
        """Determine the user's communication style."""
        if not responses:
            return CommunicationStyle.UNCERTAIN
        
        # Calculate response characteristics
        avg_length = sum(len(r.split()) for r in responses) / len(responses)
        total_text = " ".join(responses).lower()
        
        # Count style indicators
        analytical_indicators = sum(1 for word in ['because', 'analysis', 'compare', 'evaluate', 'criteria'] if word in total_text)
        intuitive_indicators = sum(1 for word in ['feel', 'sense', 'intuition', 'gut', 'prefer'] if word in total_text)
        uncertainty_indicators = sum(1 for phrase in ['not sure', 'maybe', 'perhaps', 'might'] if phrase in total_text)
        question_count = sum(response.count('?') for response in responses)
        
        # Determine style based on patterns
        if avg_length > 30 and analytical_indicators > 1:
            return CommunicationStyle.ANALYTICAL
        elif uncertainty_indicators > 2 or (question_count > len(responses)):
            return CommunicationStyle.UNCERTAIN
        elif avg_length < 10:
            return CommunicationStyle.DIRECT
        elif question_count > 0 and 'what' in total_text:
            return CommunicationStyle.EXPLORATORY
        elif intuitive_indicators > analytical_indicators:
            return CommunicationStyle.INTUITIVE
        else:
            return CommunicationStyle.DECISIVE
    
    def _detect_patterns(self, responses: List[str], conversation_state: ConversationState) -> List[PatternInsight]:
        """Detect communication and response patterns."""
        patterns = []
        
        if not responses:
            return patterns
        
        # Response length consistency
        lengths = [len(r.split()) for r in responses]
        if len(lengths) > 1:
            length_variance = max(lengths) - min(lengths)
            if length_variance < 5:
                patterns.append(PatternInsight(
                    pattern_type='consistent_response_length',
                    confidence=AnalysisConfidence.MEDIUM,
                    supporting_evidence=[f"Response lengths vary by only {length_variance} words"],
                    implications=['User has consistent communication style', 'Predictable engagement level']
                ))
        
        # Technical language usage
        total_text = " ".join(responses).lower()
        technical_score = 0
        for domain, terms in self.technical_terms.items():
            technical_score += sum(1 for term in terms if term in total_text)
        
        if technical_score > 2:
            patterns.append(PatternInsight(
                pattern_type='technical_language_usage',
                confidence=AnalysisConfidence.HIGH,
                supporting_evidence=[f"Technical terms used: {technical_score}"],
                implications=['User has domain expertise', 'Can handle technical questions']
            ))
        
        # Decision-making pattern
        decision_words = ['decided', 'choice', 'option', 'alternative', 'compare']
        decision_mentions = sum(1 for word in decision_words if word in total_text)
        if decision_mentions > 1:
            patterns.append(PatternInsight(
                pattern_type='decision_focused',
                confidence=AnalysisConfidence.MEDIUM,
                supporting_evidence=[f"Decision language used {decision_mentions} times"],
                implications=['User is in active decision-making mode', 'Focus on comparison and evaluation']
            ))
        
        return patterns
    
    def _identify_contextual_gaps(self, conversation_state: ConversationState, 
                                priorities: List[PriorityInsight]) -> List[ContextualGap]:
        """Identify contextual information gaps."""
        gaps = []
        user_profile = conversation_state.user_profile
        user_query = conversation_state.user_query.lower()
        
        # Budget gap
        budget_priority = next((p for p in priorities if p.category == 'budget'), None)
        if budget_priority and budget_priority.importance in [PriorityLevel.CRITICAL, PriorityLevel.HIGH]:
            if 'budget' not in user_profile and 'cost' not in user_profile:
                gaps.append(ContextualGap(
                    category='budget_specifics',
                    priority=PriorityLevel.HIGH,
                    confidence=AnalysisConfidence.HIGH,
                    impact_on_research='Critical for filtering recommendations by price range',
                    suggested_approach='Ask for specific budget range or constraints',
                    related_patterns=['budget_priority_detected']
                ))
        
        # Expertise level gap
        if 'expertise' not in user_profile and 'experience' not in user_profile:
            if any(word in user_query for word in ['learn', 'new', 'beginner', 'expert']):
                gaps.append(ContextualGap(
                    category='expertise_level',
                    priority=PriorityLevel.MEDIUM,
                    confidence=AnalysisConfidence.MEDIUM,
                    impact_on_research='Determines appropriate recommendation complexity',
                    suggested_approach='Assess experience level with domain-specific questions',
                    related_patterns=['learning_context_detected']
                ))
        
        # Context specificity gap
        if 'context' not in user_profile and 'use_case' not in user_profile:
            gaps.append(ContextualGap(
                category='usage_context',
                priority=PriorityLevel.MEDIUM,
                confidence=AnalysisConfidence.MEDIUM,
                impact_on_research='Ensures recommendations fit actual use case',
                suggested_approach='Clarify intended use, environment, or application',
                related_patterns=['context_clarification_needed']
            ))
        
        # Stakeholder consideration gap
        if len(conversation_state.question_history) > 2:  # Later in conversation
            if not any(word in str(user_profile) for word in ['family', 'team', 'others', 'colleagues']):
                gaps.append(ContextualGap(
                    category='stakeholder_considerations',
                    priority=PriorityLevel.LOW,
                    confidence=AnalysisConfidence.LOW,
                    impact_on_research='May affect decision criteria and preferences',
                    suggested_approach='Ask about others who might be involved or affected',
                    related_patterns=['decision_complexity_indicators']
                ))
        
        return gaps
    
    def _calculate_overall_confidence(self, priorities: List[PriorityInsight], 
                                   emotions: List[EmotionalIndicator],
                                   patterns: List[PatternInsight]) -> float:
        """Calculate overall confidence in the analysis."""
        confidence_scores = []
        
        # Factor in priority confidence
        if priorities:
            priority_confidences = [self._confidence_to_score(p.confidence) for p in priorities]
            confidence_scores.extend(priority_confidences)
        
        # Factor in emotional detection confidence
        if emotions:
            emotion_confidences = [self._confidence_to_score(e.confidence) for e in emotions]
            confidence_scores.extend(emotion_confidences)
        
        # Factor in pattern detection confidence
        if patterns:
            pattern_confidences = [self._confidence_to_score(p.confidence) for p in patterns]
            confidence_scores.extend(pattern_confidences)
        
        if not confidence_scores:
            return 0.3  # Low default confidence
        
        # Calculate weighted average
        overall_confidence = sum(confidence_scores) / len(confidence_scores)
        
        # Boost confidence if we have diverse types of evidence
        evidence_types = sum([
            len(priorities) > 0,
            len(emotions) > 0,
            len(patterns) > 0
        ])
        
        if evidence_types > 1:
            overall_confidence = min(1.0, overall_confidence * 1.1)
        
        return overall_confidence
    
    def _confidence_to_score(self, confidence: AnalysisConfidence) -> float:
        """Convert confidence enum to numeric score."""
        mapping = {
            AnalysisConfidence.VERY_HIGH: 0.95,
            AnalysisConfidence.HIGH: 0.8,
            AnalysisConfidence.MEDIUM: 0.6,
            AnalysisConfidence.LOW: 0.4,
            AnalysisConfidence.VERY_LOW: 0.2
        }
        return mapping.get(confidence, 0.5)
    
    def _generate_recommendations(self, priorities: List[PriorityInsight],
                                style: CommunicationStyle,
                                gaps: List[ContextualGap]) -> List[str]:
        """Generate recommendations for question generation and conversation flow."""
        recommendations = []
        
        # Priority-based recommendations
        high_priority_count = sum(1 for p in priorities if p.importance in [PriorityLevel.CRITICAL, PriorityLevel.HIGH])
        if high_priority_count > 0:
            recommendations.append(f"Focus on {high_priority_count} high-priority areas identified")
        
        # Style-based recommendations
        style_recommendations = {
            CommunicationStyle.ANALYTICAL: "Provide detailed explanations and comparison frameworks",
            CommunicationStyle.INTUITIVE: "Focus on preferences and feelings about options",
            CommunicationStyle.DIRECT: "Keep questions concise and specific",
            CommunicationStyle.EXPLORATORY: "Encourage exploration with open-ended questions",
            CommunicationStyle.DECISIVE: "Present clear options for quick decisions",
            CommunicationStyle.UNCERTAIN: "Provide guidance and structure to reduce uncertainty"
        }
        
        if style in style_recommendations:
            recommendations.append(style_recommendations[style])
        
        # Gap-based recommendations
        critical_gaps = [g for g in gaps if g.priority == PriorityLevel.HIGH]
        if critical_gaps:
            recommendations.append(f"Address {len(critical_gaps)} critical information gaps immediately")
        
        # General flow recommendations
        if len(gaps) > 3:
            recommendations.append("Prioritize gap resolution to improve research quality")
        
        return recommendations
    
    def _track_context_evolution(self, conversation_state: ConversationState) -> List[str]:
        """Track how context understanding has evolved."""
        evolution_notes = []
        
        # Compare with previous analysis if available
        if len(self._analysis_history) > 0:
            prev_analysis = self._analysis_history[-1]
            
            # Check if communication style changed
            # Note: We'd need to store previous style, this is simplified
            evolution_notes.append("Context understanding deepened with additional responses")
            
            # Note gap resolution
            evolution_notes.append("Information gaps being progressively addressed")
        else:
            evolution_notes.append("Initial context analysis established")
        
        # Note conversation length
        turn_count = len(conversation_state.question_history)
        if turn_count > 5:
            evolution_notes.append("Extended conversation providing rich context")
        elif turn_count > 2:
            evolution_notes.append("Good conversation depth achieved")
        
        return evolution_notes
    
    def _assess_detail_level(self, response: str) -> str:
        """Assess the detail level of a response."""
        word_count = len(response.split())
        
        if word_count > 50:
            return 'very_detailed'
        elif word_count > 20:
            return 'detailed'
        elif word_count > 10:
            return 'moderate'
        elif word_count > 3:
            return 'brief'
        else:
            return 'minimal'
    
    def _detect_certainty_level(self, response: str) -> Dict[str, int]:
        """Detect certainty/uncertainty indicators in response."""
        certain_phrases = ['definitely', 'absolutely', 'certainly', 'for sure', 'exactly']
        uncertain_phrases = ['maybe', 'perhaps', 'might', 'could be', 'not sure', 'probably']
        
        response_lower = response.lower()
        
        certain_count = sum(1 for phrase in certain_phrases if phrase in response_lower)
        uncertain_count = sum(1 for phrase in uncertain_phrases if phrase in response_lower)
        
        return {
            'certain_indicators': certain_count,
            'uncertain_indicators': uncertain_count,
            'net_certainty': certain_count - uncertain_count
        }
    
    def _assess_technical_language(self, response: str) -> Dict[str, Any]:
        """Assess technical language usage in response."""
        response_lower = response.lower()
        technical_score = 0
        domains_detected = []
        
        for domain, terms in self.technical_terms.items():
            domain_score = sum(1 for term in terms if term in response_lower)
            if domain_score > 0:
                technical_score += domain_score
                domains_detected.append(domain)
        
        return {
            'technical_score': technical_score,
            'domains_detected': domains_detected,
            'technical_level': 'high' if technical_score > 3 else 'medium' if technical_score > 0 else 'low'
        }
    
    def _detect_emotional_language(self, response: str) -> Dict[str, Any]:
        """Detect emotional language in response."""
        positive_words = ['love', 'great', 'excellent', 'amazing', 'perfect', 'wonderful']
        negative_words = ['hate', 'terrible', 'awful', 'horrible', 'worst', 'disappointing']
        
        response_lower = response.lower()
        
        positive_count = sum(1 for word in positive_words if word in response_lower)
        negative_count = sum(1 for word in negative_words if word in response_lower)
        
        return {
            'positive_language': positive_count,
            'negative_language': negative_count,
            'emotional_tone': 'positive' if positive_count > negative_count else 'negative' if negative_count > 0 else 'neutral'
        }
    
    def _assess_specificity(self, response: str) -> Dict[str, Any]:
        """Assess specificity of response."""
        specific_indicators = ['exactly', 'specifically', 'precisely', 'in particular']
        general_indicators = ['generally', 'usually', 'typically', 'overall']
        
        response_lower = response.lower()
        
        specific_count = sum(1 for indicator in specific_indicators if indicator in response_lower)
        general_count = sum(1 for indicator in general_indicators if indicator in response_lower)
        
        # Count numbers and specific details
        number_count = len(re.findall(r'\d+', response))
        
        return {
            'specific_language': specific_count,
            'general_language': general_count,
            'numbers_mentioned': number_count,
            'specificity_level': 'high' if specific_count > 0 or number_count > 1 else 'medium' if number_count > 0 else 'low'
        }
    
    def _create_fallback_result(self) -> ContextAnalysisResult:
        """Create a safe fallback result when analysis fails."""
        return ContextAnalysisResult(
            priority_insights=[],
            emotional_indicators=[],
            communication_style=CommunicationStyle.UNCERTAIN,
            pattern_insights=[],
            contextual_gaps=[],
            overall_confidence=0.2,
            analysis_timestamp=datetime.now(),
            recommendations=["Continue gathering basic information"],
            evolution_notes=["Analysis system encountered an error"]
        )
