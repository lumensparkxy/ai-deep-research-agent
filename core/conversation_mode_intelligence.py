#!/usr/bin/env python3
"""
Conversation Mode Intelligence: AI-driven conversation mode detection and adaptation.

This module implements intelligent conversation mode selection and dynamic adaptation
based on user signals, context analysis, and engagement patterns using AI.
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Optional, Any
from google import genai

logger = logging.getLogger(__name__)


class ConversationMode(Enum):
    """Available conversation modes with different depths and pacing."""
    QUICK = "quick"      # 2-3 essential questions, fast decisions
    STANDARD = "standard"  # 5-7 balanced questions, thorough but efficient
    DEEP = "deep"        # 10+ comprehensive questions, exhaustive exploration
    ADAPTIVE = "adaptive"  # Dynamic switching based on context


class UrgencyLevel(Enum):
    """User urgency indicators."""
    LOW = "low"          # No time pressure, exploratory
    MEDIUM = "medium"    # Some time constraints, moderate urgency
    HIGH = "high"        # Immediate need, time-sensitive
    CRITICAL = "critical"  # Emergency situation, minimal questions


class ComplexityPreference(Enum):
    """User preference for decision complexity."""
    SIMPLE = "simple"    # High-level, quick overview
    BALANCED = "balanced"  # Mix of detail and efficiency
    DETAILED = "detailed"  # Comprehensive, thorough exploration


@dataclass
class UserSignals:
    """Container for analyzed user signals and preferences."""
    urgency_level: UrgencyLevel
    complexity_preference: ComplexityPreference
    context_type: str  # business, personal, technical, etc.
    language_indicators: List[str]
    engagement_score: float  # 0.0 to 1.0
    patience_indicators: List[str]


@dataclass
class ModeRecommendation:
    """AI recommendation for conversation mode."""
    recommended_mode: ConversationMode
    confidence_score: float  # 0.0 to 1.0
    reasoning: str
    fallback_mode: ConversationMode
    adaptation_triggers: List[str]


@dataclass
class TransitionStrategy:
    """Strategy for transitioning between conversation modes."""
    transition_message: str
    new_questioning_depth: int
    pace_adjustment: str  # "accelerate", "maintain", "deepen"
    user_notification: bool


@dataclass
class QuestioningStrategy:
    """AI-driven questioning strategy for specific modes."""
    max_questions: int
    question_depth: str  # "surface", "moderate", "comprehensive"
    follow_up_style: str  # "minimal", "balanced", "extensive"
    ai_prompt_modifier: str


@dataclass
class EngagementMetrics:
    """Real-time engagement monitoring."""
    response_length_trend: str  # "increasing", "stable", "decreasing"
    response_time_trend: str    # "fast", "normal", "slow"
    detail_request_frequency: int
    impatience_indicators: List[str]
    interest_indicators: List[str]


class ConversationModeIntelligence:
    """
    AI-powered conversation mode detection and management.
    
    This class analyzes user behavior, language patterns, and context to
    intelligently select and adapt conversation modes for optimal user experience.
    """
    
    def __init__(self, gemini_client: genai.Client, model_name: str = "gemini-1.5-flash"):
        """Initialize the conversation mode intelligence system."""
        self.gemini_client = gemini_client
        self.model_name = model_name
        
        # Mode-specific configurations
        self.mode_configs = {
            ConversationMode.QUICK: QuestioningStrategy(
                max_questions=3,
                question_depth="surface",
                follow_up_style="minimal",
                ai_prompt_modifier="Focus on 1-2 most critical decision factors. Be concise and direct."
            ),
            ConversationMode.STANDARD: QuestioningStrategy(
                max_questions=6,
                question_depth="moderate", 
                follow_up_style="balanced",
                ai_prompt_modifier="Generate thoughtful questions covering key decision aspects. Balance depth with efficiency."
            ),
            ConversationMode.DEEP: QuestioningStrategy(
                max_questions=12,
                question_depth="comprehensive",
                follow_up_style="extensive",
                ai_prompt_modifier="Explore all relevant decision factors comprehensively. Generate detailed follow-up questions."
            ),
            ConversationMode.ADAPTIVE: QuestioningStrategy(
                max_questions=8,
                question_depth="moderate",
                follow_up_style="balanced",
                ai_prompt_modifier="Adapt questioning depth based on user responses and engagement. Be flexible."
            )
        }
    
    def analyze_user_signals(self, user_query: str, conversation_history: List[str] = None) -> UserSignals:
        """
        Analyze user language patterns and context to detect preferences and urgency.
        
        Args:
            user_query: The initial user query
            conversation_history: Previous conversation exchanges
            
        Returns:
            UserSignals: Analyzed user preferences and indicators
        """
        try:
            # Prepare context for AI analysis
            history_context = ""
            if conversation_history:
                history_context = f"Previous conversation: {' '.join(conversation_history[-6:])}"
            
            analysis_prompt = f"""
            Analyze the user's communication style and preferences from their query and conversation history.
            
            User Query: "{user_query}"
            {history_context}
            
            Analyze and return in this exact format:
            URGENCY: [low/medium/high/critical]
            COMPLEXITY: [simple/balanced/detailed] 
            CONTEXT: [business/personal/technical/educational/other]
            LANGUAGE_INDICATORS: [comma-separated list of key phrases indicating style]
            ENGAGEMENT: [0.0-1.0 score]
            PATIENCE: [comma-separated list of patience/impatience indicators]
            
            Consider:
            - Urgency words: "ASAP", "urgent", "quickly", "deadline", "today", "immediately"
            - Complexity preferences: "thorough", "detailed", "just the basics", "comprehensive"
            - Context clues: business terminology, personal decisions, technical language
            - Engagement indicators: question length, detail level, enthusiasm
            """
            
            response = self.gemini_client.models.generate_content(
                model=self.model_name,
                contents=analysis_prompt
            )
            
            # Parse AI response
            analysis_text = response.text.strip()
            signals = self._parse_user_signals_response(analysis_text)
            
            logger.info(f"User signals analyzed: {signals}")
            return signals
            
        except Exception as e:
            logger.error(f"Error analyzing user signals: {e}")
            # Return default moderate signals
            return UserSignals(
                urgency_level=UrgencyLevel.MEDIUM,
                complexity_preference=ComplexityPreference.BALANCED,
                context_type="general",
                language_indicators=["standard"],
                engagement_score=0.7,
                patience_indicators=["moderate"]
            )
    
    def detect_urgency_indicators(self, user_query: str, conversation_history: List[str] = None) -> UrgencyLevel:
        """
        Detect urgency level from user language patterns.
        
        Args:
            user_query: The user's query
            conversation_history: Recent conversation context
            
        Returns:
            UrgencyLevel: Detected urgency level
        """
        try:
            urgency_prompt = f"""
            Analyze the urgency level in this user communication:
            
            Query: "{user_query}"
            Recent context: {conversation_history[-3:] if conversation_history else "None"}
            
            Return only one word: low, medium, high, or critical
            
            Consider:
            - Critical: emergency, crisis, "right now", "immediately"
            - High: "ASAP", "urgent", "deadline today", "time-sensitive"
            - Medium: "soon", "this week", "when possible", mild time pressure
            - Low: "eventually", "exploring options", "no rush", research mode
            """
            
            response = self.gemini_client.models.generate_content(
                model=self.model_name,
                contents=urgency_prompt
            )
            
            urgency_text = response.text.strip().lower()
            
            if urgency_text in ["critical"]:
                return UrgencyLevel.CRITICAL
            elif urgency_text in ["high"]:
                return UrgencyLevel.HIGH
            elif urgency_text in ["medium"]:
                return UrgencyLevel.MEDIUM
            else:
                return UrgencyLevel.LOW
                
        except Exception as e:
            logger.error(f"Error detecting urgency: {e}")
            return UrgencyLevel.MEDIUM
    
    def assess_complexity_preference(self, user_responses: List[str]) -> ComplexityPreference:
        """
        Assess user's preference for decision complexity based on their responses.
        
        Args:
            user_responses: List of user responses in conversation
            
        Returns:
            ComplexityPreference: Detected complexity preference
        """
        if not user_responses:
            return ComplexityPreference.BALANCED
            
        try:
            complexity_prompt = f"""
            Analyze these user responses to determine their preference for decision complexity:
            
            User responses: {user_responses}
            
            Return only one word: simple, balanced, or detailed
            
            Consider:
            - Detailed: long responses, asks follow-up questions, wants comprehensive info
            - Simple: short responses, wants quick answers, avoids complexity
            - Balanced: moderate responses, wants good coverage without overwhelming detail
            """
            
            response = self.gemini_client.models.generate_content(
                model=self.model_name,
                contents=complexity_prompt
            )
            
            complexity_text = response.text.strip().lower()
            
            if complexity_text in ["detailed"]:
                return ComplexityPreference.DETAILED
            elif complexity_text in ["simple"]:
                return ComplexityPreference.SIMPLE
            else:
                return ComplexityPreference.BALANCED
                
        except Exception as e:
            logger.error(f"Error assessing complexity preference: {e}")
            return ComplexityPreference.BALANCED
    
    def recommend_conversation_mode(self, signals: UserSignals) -> ModeRecommendation:
        """
        Generate AI-powered recommendation for optimal conversation mode.
        
        Args:
            signals: Analyzed user signals and preferences
            
        Returns:
            ModeRecommendation: AI recommendation with reasoning
        """
        try:
            recommendation_prompt = f"""
            Based on these user signals, recommend the optimal conversation mode:
            
            Urgency Level: {signals.urgency_level.value}
            Complexity Preference: {signals.complexity_preference.value}
            Context Type: {signals.context_type}
            Language Indicators: {signals.language_indicators}
            Engagement Score: {signals.engagement_score}
            
            Available modes:
            - QUICK: 2-3 essential questions, fast decisions (for urgent, simple needs)
            - STANDARD: 5-7 balanced questions, thorough but efficient (most common)
            - DEEP: 10+ comprehensive questions, exhaustive exploration (complex, non-urgent)
            - ADAPTIVE: Dynamic switching based on user engagement (mixed signals)
            
            Return in this exact format:
            MODE: [quick/standard/deep/adaptive]
            CONFIDENCE: [0.0-1.0]
            REASONING: [brief explanation]
            FALLBACK: [alternative mode if primary fails]
            TRIGGERS: [comma-separated adaptation triggers]
            """
            
            response = self.gemini_client.models.generate_content(
                model=self.model_name,
                contents=recommendation_prompt
            )
            
            recommendation = self._parse_mode_recommendation(response.text.strip())
            logger.info(f"Mode recommendation: {recommendation}")
            return recommendation
            
        except Exception as e:
            logger.error(f"Error generating mode recommendation: {e}")
            # Return safe default
            return ModeRecommendation(
                recommended_mode=ConversationMode.STANDARD,
                confidence_score=0.5,
                reasoning="Default mode due to analysis error",
                fallback_mode=ConversationMode.QUICK,
                adaptation_triggers=["user_feedback", "engagement_drop"]
            )
    
    def should_switch_mode(self, current_mode: ConversationMode, 
                          engagement_metrics: EngagementMetrics,
                          conversation_length: int) -> bool:
        """
        Determine if conversation mode should be switched based on user engagement.
        
        Args:
            current_mode: Current conversation mode
            engagement_metrics: Real-time engagement data
            conversation_length: Number of exchanges so far
            
        Returns:
            bool: Whether to switch modes
        """
        try:
            # Quick rules for obvious switches
            if engagement_metrics.impatience_indicators and current_mode != ConversationMode.QUICK:
                return True
                
            if engagement_metrics.detail_request_frequency > 2 and current_mode == ConversationMode.QUICK:
                return True
                
            # AI-powered decision for complex cases
            switch_prompt = f"""
            Should we switch conversation mode based on this engagement data?
            
            Current Mode: {current_mode.value}
            Conversation Length: {conversation_length} exchanges
            Response Length Trend: {engagement_metrics.response_length_trend}
            Response Time Trend: {engagement_metrics.response_time_trend}
            Detail Requests: {engagement_metrics.detail_request_frequency}
            Impatience Indicators: {engagement_metrics.impatience_indicators}
            Interest Indicators: {engagement_metrics.interest_indicators}
            
            Return only: YES or NO
            
            Switch if:
            - User shows impatience in detailed mode
            - User requests more detail in quick mode
            - Engagement is dropping significantly
            - Mode mismatch is evident
            """
            
            response = self.gemini_client.models.generate_content(
                model=self.model_name,
                contents=switch_prompt
            )
            
            return response.text.strip().upper() == "YES"
            
        except Exception as e:
            logger.error(f"Error determining mode switch: {e}")
            return False
    
    def create_mode_specific_prompt(self, mode: ConversationMode, context: Dict[str, Any]) -> str:
        """
        Create AI prompt tailored to specific conversation mode.
        
        Args:
            mode: Target conversation mode
            context: Decision context and user information
            
        Returns:
            str: Mode-specific AI prompting strategy
        """
        config = self.mode_configs.get(mode, self.mode_configs[ConversationMode.STANDARD])
        
        base_prompt = f"""
        {config.ai_prompt_modifier}
        
        Maximum questions: {config.max_questions}
        Question depth: {config.question_depth}
        Follow-up style: {config.follow_up_style}
        
        User context: {context.get('user_query', 'Decision assistance needed')}
        Decision context: {context.get('context_type', 'general')}
        """
        
        return base_prompt
    
    def _parse_user_signals_response(self, response_text: str) -> UserSignals:
        """Parse AI response into UserSignals object."""
        lines = response_text.split('\n')
        signals_data = {}
        
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                signals_data[key.strip().upper()] = value.strip()
        
        # Normalize enum values to lowercase
        urgency_value = signals_data.get('URGENCY', 'medium').lower()
        complexity_value = signals_data.get('COMPLEXITY', 'balanced').lower()
        
        return UserSignals(
            urgency_level=UrgencyLevel(urgency_value),
            complexity_preference=ComplexityPreference(complexity_value),
            context_type=signals_data.get('CONTEXT', 'general'),
            language_indicators=signals_data.get('LANGUAGE_INDICATORS', '').split(','),
            engagement_score=float(signals_data.get('ENGAGEMENT', '0.7')),
            patience_indicators=signals_data.get('PATIENCE', '').split(',')
        )
    
    def _parse_mode_recommendation(self, response_text: str) -> ModeRecommendation:
        """Parse AI response into ModeRecommendation object."""
        lines = response_text.split('\n')
        rec_data = {}
        
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                rec_data[key.strip().upper()] = value.strip()
        
        # Normalize mode values to lowercase
        mode_value = rec_data.get('MODE', 'standard').lower()
        fallback_value = rec_data.get('FALLBACK', 'quick').lower()
        
        return ModeRecommendation(
            recommended_mode=ConversationMode(mode_value),
            confidence_score=float(rec_data.get('CONFIDENCE', '0.7')),
            reasoning=rec_data.get('REASONING', 'Standard recommendation'),
            fallback_mode=ConversationMode(fallback_value),
            adaptation_triggers=rec_data.get('TRIGGERS', '').split(',')
        )


class AdaptiveModeManager:
    """
    Manages dynamic conversation mode switching and transitions.
    
    This class handles the practical aspects of changing conversation modes
    during an active conversation, ensuring smooth transitions and user experience.
    """
    
    def __init__(self, mode_intelligence: ConversationModeIntelligence):
        """Initialize the adaptive mode manager."""
        self.mode_intelligence = mode_intelligence
        self.current_mode = ConversationMode.STANDARD
        self.mode_history = []
        self.transition_count = 0
        
    def transition_between_modes(self, from_mode: ConversationMode, 
                                to_mode: ConversationMode,
                                reason: str = "") -> TransitionStrategy:
        """
        Create smooth transition strategy between conversation modes.
        
        Args:
            from_mode: Current conversation mode
            to_mode: Target conversation mode
            reason: Reason for mode change
            
        Returns:
            TransitionStrategy: Transition execution plan
        """
        # Track transition
        self.mode_history.append((from_mode, to_mode, reason))
        self.transition_count += 1
        self.current_mode = to_mode
        
        # Create appropriate transition message
        transition_messages = {
            (ConversationMode.DEEP, ConversationMode.QUICK): 
                "I notice you might prefer a quicker approach. Let me focus on the key essentials.",
            (ConversationMode.QUICK, ConversationMode.DEEP):
                "It seems like you'd like to explore this more thoroughly. Let me ask some detailed questions.",
            (ConversationMode.STANDARD, ConversationMode.QUICK):
                "Let me streamline this and focus on the most important factors.",
            (ConversationMode.QUICK, ConversationMode.STANDARD):
                "I'll expand a bit to make sure we cover the important aspects.",
        }
        
        default_message = f"Adjusting our conversation approach to better match your needs."
        message = transition_messages.get((from_mode, to_mode), default_message)
        
        # Determine questioning adjustments
        config = self.mode_intelligence.mode_configs[to_mode]
        
        pace_mapping = {
            ConversationMode.QUICK: "accelerate",
            ConversationMode.STANDARD: "maintain", 
            ConversationMode.DEEP: "deepen",
            ConversationMode.ADAPTIVE: "maintain"
        }
        
        return TransitionStrategy(
            transition_message=message,
            new_questioning_depth=config.max_questions,
            pace_adjustment=pace_mapping[to_mode],
            user_notification=self.transition_count <= 2  # Only notify for first few transitions
        )
    
    def monitor_engagement(self, user_responses: List[str], 
                          response_times: List[float] = None) -> EngagementMetrics:
        """
        Monitor user engagement patterns for mode adaptation.
        
        Args:
            user_responses: Recent user responses
            response_times: Response time data
            
        Returns:
            EngagementMetrics: Current engagement assessment
        """
        if not user_responses:
            return EngagementMetrics(
                response_length_trend="stable",
                response_time_trend="normal", 
                detail_request_frequency=0,
                impatience_indicators=[],
                interest_indicators=[]
            )
        
        # Analyze response length trend
        lengths = [len(response.split()) for response in user_responses[-3:]]
        if len(lengths) >= 2:
            if lengths[-1] > lengths[-2] * 1.5:
                length_trend = "increasing"
            elif lengths[-1] < lengths[-2] * 0.6:
                length_trend = "decreasing"
            else:
                length_trend = "stable"
        else:
            length_trend = "stable"
        
        # Detect impatience and interest indicators
        recent_text = " ".join(user_responses[-3:]).lower()
        
        impatience_words = ["quick", "fast", "hurry", "time", "rush", "brief", "short"]
        interest_words = ["tell me more", "details", "explain", "how", "why", "interesting"]
        
        impatience_indicators = [word for word in impatience_words if word in recent_text]
        interest_indicators = [word for word in interest_words if word in recent_text]
        
        # Count detail requests
        detail_requests = sum(1 for response in user_responses 
                            if any(phrase in response.lower() 
                                 for phrase in ["more detail", "tell me more", "explain", "how does"]))
        
        return EngagementMetrics(
            response_length_trend=length_trend,
            response_time_trend="normal",  # Would need actual timing data
            detail_request_frequency=detail_requests,
            impatience_indicators=impatience_indicators,
            interest_indicators=interest_indicators
        )
