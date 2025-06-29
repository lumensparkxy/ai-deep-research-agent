"""
Conversation State Data Models for Deep Research Agent
Core data structures for conversation tracking in the dynamic personalization system.
"""

import json
import logging
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from enum import Enum


class ConversationMode(Enum):
    """Enumeration of conversation modes for different interaction types."""
    QUICK = "quick"
    STANDARD = "standard"
    DEEP = "deep"
    ITERATIVE = "iterative"


class QuestionType(Enum):
    """Enumeration of question types for categorization."""
    OPEN_ENDED = "open_ended"
    MULTIPLE_CHOICE = "multiple_choice"
    SCALE = "scale"
    BOOLEAN = "boolean"
    CLARIFICATION = "clarification"
    FOLLOW_UP = "follow_up"


@dataclass
class QuestionAnswer:
    """Represents a single question-answer pair in the conversation."""
    question: str
    answer: str
    question_type: QuestionType
    timestamp: datetime
    category: str  # Which information category this Q&A addresses
    confidence: float = 0.0  # Confidence in the answer (0.0-1.0)
    importance: float = 0.5  # Importance of this information (0.0-1.0)
    follow_up_needed: bool = False
    context: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'question': self.question,
            'answer': self.answer,
            'question_type': self.question_type.value,
            'timestamp': self.timestamp.isoformat(),
            'category': self.category,
            'confidence': self.confidence,
            'importance': self.importance,
            'follow_up_needed': self.follow_up_needed,
            'context': self.context
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QuestionAnswer':
        """Create from dictionary for deserialization."""
        return cls(
            question=data['question'],
            answer=data['answer'],
            question_type=QuestionType(data['question_type']),
            timestamp=datetime.fromisoformat(data['timestamp']),
            category=data['category'],
            confidence=data.get('confidence', 0.0),
            importance=data.get('importance', 0.5),
            follow_up_needed=data.get('follow_up_needed', False),
            context=data.get('context', {})
        )


@dataclass
class EmotionalIndicators:
    """Tracks emotional indicators detected during conversation."""
    urgency_level: float = 0.0  # 0.0-1.0 scale
    anxiety_level: float = 0.0  # 0.0-1.0 scale
    confidence_level: float = 0.5  # 0.0-1.0 scale
    enthusiasm_level: float = 0.5  # 0.0-1.0 scale
    frustration_level: float = 0.0  # 0.0-1.0 scale
    decision_pressure: float = 0.0  # 0.0-1.0 scale
    time_sensitivity: float = 0.0  # 0.0-1.0 scale
    indicators_detected: List[str] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'urgency_level': self.urgency_level,
            'anxiety_level': self.anxiety_level,
            'confidence_level': self.confidence_level,
            'enthusiasm_level': self.enthusiasm_level,
            'frustration_level': self.frustration_level,
            'decision_pressure': self.decision_pressure,
            'time_sensitivity': self.time_sensitivity,
            'indicators_detected': self.indicators_detected,
            'last_updated': self.last_updated.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EmotionalIndicators':
        """Create from dictionary for deserialization."""
        return cls(
            urgency_level=data.get('urgency_level', 0.0),
            anxiety_level=data.get('anxiety_level', 0.0),
            confidence_level=data.get('confidence_level', 0.5),
            enthusiasm_level=data.get('enthusiasm_level', 0.5),
            frustration_level=data.get('frustration_level', 0.0),
            decision_pressure=data.get('decision_pressure', 0.0),
            time_sensitivity=data.get('time_sensitivity', 0.0),
            indicators_detected=data.get('indicators_detected', []),
            last_updated=datetime.fromisoformat(data.get('last_updated', datetime.now().isoformat()))
        )


@dataclass
class ContextUnderstanding:
    """Represents deeper understanding of the user's context and situation."""
    domain_expertise: Dict[str, float] = field(default_factory=dict)  # Domain -> expertise level
    communication_style: Dict[str, float] = field(default_factory=dict)  # Style preferences
    decision_making_style: str = "unknown"  # analytical, intuitive, collaborative, quick
    information_processing_preference: str = "unknown"  # visual, textual, structured, narrative
    risk_tolerance: float = 0.5  # 0.0-1.0 scale
    detail_preference: float = 0.5  # 0.0 (high-level) to 1.0 (detailed)
    stakeholders: List[str] = field(default_factory=list)  # Who else is involved
    external_constraints: Dict[str, Any] = field(default_factory=dict)  # Organizational, regulatory, etc.
    cultural_context: Dict[str, Any] = field(default_factory=dict)  # Cultural considerations
    temporal_context: Dict[str, Any] = field(default_factory=dict)  # Time-related factors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ContextUnderstanding':
        """Create from dictionary for deserialization."""
        return cls(**data)


@dataclass
class ConversationState:
    """
    Comprehensive conversation state tracking for dynamic personalization.
    
    This is the core data structure that maintains all information about
    the ongoing conversation, user understanding, and system state.
    """
    
    # Session identification
    session_id: str
    user_query: str
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    
    # User profile and understanding
    user_profile: Dict[str, Any] = field(default_factory=dict)
    information_gaps: List[str] = field(default_factory=list)
    priority_factors: Dict[str, float] = field(default_factory=dict)
    confidence_scores: Dict[str, float] = field(default_factory=dict)
    
    # Conversation tracking
    question_history: List[QuestionAnswer] = field(default_factory=list)
    conversation_mode: ConversationMode = ConversationMode.STANDARD
    
    # Advanced understanding
    context_understanding: ContextUnderstanding = field(default_factory=ContextUnderstanding)
    emotional_indicators: EmotionalIndicators = field(default_factory=EmotionalIndicators)
    
    # System state
    completion_confidence: float = 0.0  # Overall confidence in gathered information
    next_question_suggestions: List[str] = field(default_factory=list)
    conversation_summary: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate and initialize the conversation state."""
        self.validate_state()
        if not self.session_id:
            raise ValueError("session_id is required")
        if not self.user_query:
            raise ValueError("user_query is required")
    
    def validate_state(self) -> None:
        """Validate the current conversation state."""
        # Validate confidence scores are in valid range
        for key, score in self.confidence_scores.items():
            if not 0.0 <= score <= 1.0:
                raise ValueError(f"Confidence score for '{key}' must be between 0.0 and 1.0, got {score}")
        
        # Validate priority factors are in valid range
        for key, priority in self.priority_factors.items():
            if not 0.0 <= priority <= 1.0:
                raise ValueError(f"Priority factor for '{key}' must be between 0.0 and 1.0, got {priority}")
        
        # Validate completion confidence
        if not 0.0 <= self.completion_confidence <= 1.0:
            raise ValueError(f"Completion confidence must be between 0.0 and 1.0, got {self.completion_confidence}")
        
        # Validate conversation mode
        if not isinstance(self.conversation_mode, ConversationMode):
            if isinstance(self.conversation_mode, str):
                try:
                    self.conversation_mode = ConversationMode(self.conversation_mode)
                except ValueError:
                    raise ValueError(f"Invalid conversation mode: {self.conversation_mode}")
            else:
                raise ValueError(f"conversation_mode must be ConversationMode enum, got {type(self.conversation_mode)}")
    
    def add_question_answer(self, question: str, answer: str, category: str, 
                           question_type: QuestionType = QuestionType.OPEN_ENDED,
                           confidence: float = 0.0, importance: float = 0.5,
                           context: Optional[Dict[str, Any]] = None) -> None:
        """Add a new question-answer pair to the conversation history."""
        qa = QuestionAnswer(
            question=question,
            answer=answer,
            question_type=question_type,
            timestamp=datetime.now(),
            category=category,
            confidence=confidence,
            importance=importance,
            context=context or {}
        )
        self.question_history.append(qa)
        self.last_updated = datetime.now()
        
        # Update user profile with the answer
        if category not in self.user_profile:
            self.user_profile[category] = {}
        
        if isinstance(self.user_profile[category], dict):
            self.user_profile[category]['latest_answer'] = answer
            self.user_profile[category]['confidence'] = confidence
        else:
            # If it's not a dict, make it one
            self.user_profile[category] = {
                'value': self.user_profile[category],
                'latest_answer': answer,
                'confidence': confidence
            }
        
        # Update confidence scores
        self.confidence_scores[category] = confidence
    
    def update_user_profile(self, category: str, value: Any, confidence: float = 0.5) -> None:
        """Update user profile information with confidence tracking."""
        self.user_profile[category] = value
        self.confidence_scores[category] = confidence
        self.last_updated = datetime.now()
    
    def set_priority_factor(self, factor: str, priority: float) -> None:
        """Set priority factor with validation."""
        if not 0.0 <= priority <= 1.0:
            raise ValueError(f"Priority must be between 0.0 and 1.0, got {priority}")
        self.priority_factors[factor] = priority
        self.last_updated = datetime.now()
    
    def add_information_gap(self, gap: str) -> None:
        """Add an information gap to track."""
        if gap not in self.information_gaps:
            self.information_gaps.append(gap)
            self.last_updated = datetime.now()
    
    def remove_information_gap(self, gap: str) -> None:
        """Remove an information gap when it's been filled."""
        if gap in self.information_gaps:
            self.information_gaps.remove(gap)
            self.last_updated = datetime.now()
    
    def get_category_confidence(self, category: str) -> float:
        """Get confidence score for a specific category."""
        return self.confidence_scores.get(category, 0.0)
    
    def get_overall_confidence(self) -> float:
        """Calculate overall confidence based on all categories."""
        if not self.confidence_scores:
            return 0.0
        
        # Weight by priority factors if available
        if self.priority_factors:
            weighted_sum = 0.0
            total_weight = 0.0
            for category, confidence in self.confidence_scores.items():
                weight = self.priority_factors.get(category, 0.5)
                weighted_sum += confidence * weight
                total_weight += weight
            
            return weighted_sum / total_weight if total_weight > 0 else 0.0
        else:
            # Simple average if no priority factors
            return sum(self.confidence_scores.values()) / len(self.confidence_scores)
    
    def get_conversation_summary(self) -> str:
        """Generate a summary of the conversation so far."""
        if self.conversation_summary:
            return self.conversation_summary
        
        if not self.question_history:
            return f"Initial query: {self.user_query}"
        
        summary_parts = [f"Query: {self.user_query}"]
        
        # Group Q&As by category
        categories = {}
        for qa in self.question_history:
            if qa.category not in categories:
                categories[qa.category] = []
            categories[qa.category].append(qa)
        
        for category, qas in categories.items():
            if qas:
                latest_qa = qas[-1]  # Most recent answer in this category
                summary_parts.append(f"{category.title()}: {latest_qa.answer[:100]}...")
        
        return "; ".join(summary_parts)
    
    def update_conversation_mode(self, mode: Union[ConversationMode, str]) -> None:
        """Update the conversation mode with validation."""
        if isinstance(mode, str):
            mode = ConversationMode(mode)
        self.conversation_mode = mode
        self.last_updated = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert conversation state to dictionary for serialization."""
        return {
            'session_id': self.session_id,
            'user_query': self.user_query,
            'created_at': self.created_at.isoformat(),
            'last_updated': self.last_updated.isoformat(),
            'user_profile': self.user_profile,
            'information_gaps': self.information_gaps,
            'priority_factors': self.priority_factors,
            'confidence_scores': self.confidence_scores,
            'question_history': [qa.to_dict() for qa in self.question_history],
            'conversation_mode': self.conversation_mode.value,
            'context_understanding': self.context_understanding.to_dict(),
            'emotional_indicators': self.emotional_indicators.to_dict(),
            'completion_confidence': self.completion_confidence,
            'next_question_suggestions': self.next_question_suggestions,
            'conversation_summary': self.conversation_summary,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationState':
        """Create conversation state from dictionary for deserialization."""
        # Convert question history
        question_history = [QuestionAnswer.from_dict(qa_data) for qa_data in data.get('question_history', [])]
        
        # Convert datetime fields
        created_at = datetime.fromisoformat(data['created_at']) if 'created_at' in data else datetime.now()
        last_updated = datetime.fromisoformat(data['last_updated']) if 'last_updated' in data else datetime.now()
        
        # Convert conversation mode
        conversation_mode = ConversationMode(data.get('conversation_mode', 'standard'))
        
        # Convert complex objects
        context_understanding = ContextUnderstanding.from_dict(data.get('context_understanding', {}))
        emotional_indicators = EmotionalIndicators.from_dict(data.get('emotional_indicators', {}))
        
        return cls(
            session_id=data['session_id'],
            user_query=data['user_query'],
            created_at=created_at,
            last_updated=last_updated,
            user_profile=data.get('user_profile', {}),
            information_gaps=data.get('information_gaps', []),
            priority_factors=data.get('priority_factors', {}),
            confidence_scores=data.get('confidence_scores', {}),
            question_history=question_history,
            conversation_mode=conversation_mode,
            context_understanding=context_understanding,
            emotional_indicators=emotional_indicators,
            completion_confidence=data.get('completion_confidence', 0.0),
            next_question_suggestions=data.get('next_question_suggestions', []),
            conversation_summary=data.get('conversation_summary', ''),
            metadata=data.get('metadata', {})
        )
    
    def to_json(self) -> str:
        """Convert to JSON string for storage."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'ConversationState':
        """Create from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)


class ConversationStateManager:
    """Manager class for conversation state operations and utilities."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def create_new_state(self, session_id: str, user_query: str, 
                        conversation_mode: ConversationMode = ConversationMode.STANDARD) -> ConversationState:
        """Create a new conversation state with validation."""
        if not session_id:
            raise ValueError("session_id cannot be empty")
        if not user_query.strip():
            raise ValueError("user_query cannot be empty")
        
        state = ConversationState(
            session_id=session_id,
            user_query=user_query.strip(),
            conversation_mode=conversation_mode
        )
        
        self.logger.info(f"Created new conversation state for session: {session_id}")
        return state
    
    def merge_states(self, primary: ConversationState, secondary: ConversationState) -> ConversationState:
        """Merge two conversation states, with primary taking precedence."""
        if primary.session_id != secondary.session_id:
            raise ValueError("Cannot merge states from different sessions")
        
        # Use primary as base and selectively merge from secondary
        merged = ConversationState.from_dict(primary.to_dict())
        
        # Merge question histories (avoid duplicates)
        existing_questions = {qa.question for qa in merged.question_history}
        for qa in secondary.question_history:
            if qa.question not in existing_questions:
                merged.question_history.append(qa)
        
        # Merge user profile (primary takes precedence)
        for key, value in secondary.user_profile.items():
            if key not in merged.user_profile:
                merged.user_profile[key] = value
        
        # Merge confidence scores (take higher confidence)
        for key, confidence in secondary.confidence_scores.items():
            if key not in merged.confidence_scores or confidence > merged.confidence_scores[key]:
                merged.confidence_scores[key] = confidence
        
        # Merge information gaps (combine unique gaps)
        for gap in secondary.information_gaps:
            if gap not in merged.information_gaps:
                merged.information_gaps.append(gap)
        
        merged.last_updated = datetime.now()
        return merged
    
    def validate_serialization(self, state: ConversationState) -> bool:
        """Test that a state can be serialized and deserialized without loss."""
        try:
            # Test JSON serialization
            json_str = state.to_json()
            restored_state = ConversationState.from_json(json_str)
            
            # Test dict serialization
            state_dict = state.to_dict()
            restored_from_dict = ConversationState.from_dict(state_dict)
            
            # Basic validation that key fields match
            return (
                state.session_id == restored_state.session_id == restored_from_dict.session_id and
                state.user_query == restored_state.user_query == restored_from_dict.user_query and
                len(state.question_history) == len(restored_state.question_history) == len(restored_from_dict.question_history)
            )
        except Exception as e:
            self.logger.error(f"Serialization validation failed: {e}")
            return False
    
    def calculate_state_completeness(self, state: ConversationState) -> float:
        """Calculate how complete the conversation state is (0.0-1.0)."""
        # Define minimum expected categories for completeness
        essential_categories = [
            'context', 'preferences', 'constraints', 'timeline', 'expertise_level'
        ]
        
        completeness_factors = []
        
        # Factor 1: Coverage of essential categories
        covered_categories = sum(1 for cat in essential_categories if cat in state.user_profile)
        category_completeness = covered_categories / len(essential_categories)
        completeness_factors.append(category_completeness * 0.4)
        
        # Factor 2: Average confidence across categories
        avg_confidence = state.get_overall_confidence()
        completeness_factors.append(avg_confidence * 0.3)
        
        # Factor 3: Number of Q&A exchanges (diminishing returns)
        qa_completeness = min(1.0, len(state.question_history) / 5)  # 5 Q&As for full score
        completeness_factors.append(qa_completeness * 0.2)
        
        # Factor 4: Information gaps (fewer gaps = more complete)
        gap_completeness = max(0.0, 1.0 - (len(state.information_gaps) / 10))  # 10+ gaps = 0 score
        completeness_factors.append(gap_completeness * 0.1)
        
        return sum(completeness_factors)
