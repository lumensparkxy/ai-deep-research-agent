"""
Completion Assessment System for Deep Research Agent
AI-driven conversation completion detection to determine when enough personalization information has been gathered.
"""

import json
import logging
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime

from google import genai
from google.genai import types

# Import the proper conversation state from Task 1.1
from .conversation_state import ConversationState


@dataclass
class InformationGap:
    """Represents a gap in the conversation that needs to be filled."""
    category: str
    importance: str  # 'critical' | 'important' | 'nice_to_have'
    suggested_question: str
    context_dependency: List[str]


@dataclass
class CompletionResult:
    """Result of conversation completeness assessment."""
    confidence_score: float
    information_gaps: List[InformationGap]
    missing_categories: List[str]
    sufficiency_assessment: str
    recommendation: str  # 'continue' | 'sufficient' | 'minimal_sufficient'
    reasoning: str


class CompletionAssessment:
    """AI-driven conversation completion assessment system."""
    
    def __init__(self, gemini_client: Optional[genai.Client] = None, model_name: str = "gemini-2.0-flash-001"):
        """
        Initialize the completion assessment system.
        
        Args:
            gemini_client: Configured Gemini client for AI analysis
            model_name: Name of the Gemini model to use for analysis
        """
        self.logger = logging.getLogger(__name__)
        self.gemini_client = gemini_client
        self.model_name = model_name
        
        # Assessment thresholds
        self.critical_confidence_threshold = 0.65  # Lowered from 0.8
        self.minimal_confidence_threshold = 0.35   # Lowered from 0.5
        self.max_conversation_turns = 10
        
    def assess_conversation_completeness(self, conversation_state: ConversationState) -> CompletionResult:
        """
        Assess the completeness of conversation information for effective research.
        
        Args:
            conversation_state: Current state of the conversation
            
        Returns:
            CompletionResult with assessment details
        """
        try:
            self.logger.debug(f"Assessing conversation completeness for session: {conversation_state.session_id}")
            
            # Calculate base confidence score
            base_confidence = self._calculate_base_confidence(conversation_state)
            
            # Identify information gaps using AI
            information_gaps = self.identify_information_gaps(
                conversation_state.user_query,
                conversation_state.user_profile
            )
            
            # Calculate final confidence considering gaps
            final_confidence = self._adjust_confidence_for_gaps(base_confidence, information_gaps)
            
            # Determine missing categories
            missing_categories = self._identify_missing_categories(
                conversation_state.user_query,
                conversation_state.user_profile
            )
            
            # Generate assessment and recommendation
            sufficiency_assessment = self._generate_sufficiency_assessment(
                final_confidence, information_gaps, missing_categories
            )
            
            recommendation = self._generate_recommendation(
                final_confidence, len(conversation_state.question_history)
            )
            
            # Generate reasoning
            reasoning = self._generate_reasoning(
                final_confidence, information_gaps, missing_categories, conversation_state
            )
            
            result = CompletionResult(
                confidence_score=final_confidence,
                information_gaps=information_gaps,
                missing_categories=missing_categories,
                sufficiency_assessment=sufficiency_assessment,
                recommendation=recommendation,
                reasoning=reasoning
            )
            
            self.logger.info(f"Assessment complete: confidence={final_confidence:.2f}, recommendation={recommendation}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error assessing conversation completeness: {e}")
            # Return safe fallback
            return self._create_fallback_result()
    
    def identify_information_gaps(self, user_query: str, gathered_info: Dict[str, Any]) -> List[InformationGap]:
        """
        Identify critical information gaps using AI analysis.
        
        Args:
            user_query: Original user query
            gathered_info: Currently gathered personalization information
            
        Returns:
            List of identified information gaps
        """
        try:
            if not self.gemini_client:
                # Fallback to rule-based gap detection
                return self._identify_gaps_rule_based(user_query, gathered_info)
            
            # Prepare AI prompt
            prompt = self._create_gap_identification_prompt(user_query, gathered_info)
            
            # Query Gemini
            response = self.gemini_client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            
            # Parse response
            gaps = self._parse_gap_response(response.text)
            
            self.logger.debug(f"Identified {len(gaps)} information gaps")
            return gaps
            
        except Exception as e:
            self.logger.warning(f"AI gap identification failed, using fallback: {e}")
            return self._identify_gaps_rule_based(user_query, gathered_info)
    
    def calculate_confidence_score(self, conversation_state: ConversationState) -> float:
        """
        Calculate confidence score for conversation completeness.
        
        Args:
            conversation_state: Current conversation state
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        return self._calculate_base_confidence(conversation_state)
    
    def should_continue_conversation(self, assessment_result: CompletionResult) -> bool:
        """
        Determine if conversation should continue based on assessment.
        
        Args:
            assessment_result: Result from assess_conversation_completeness
            
        Returns:
            True if conversation should continue, False otherwise
        """
        return assessment_result.recommendation == 'continue'
    
    def _calculate_base_confidence(self, conversation_state: ConversationState) -> float:
        """Calculate base confidence score based on gathered information."""
        gathered_info = conversation_state.user_profile
        
        # Score components
        info_breadth_score = self._score_information_breadth(gathered_info)
        info_depth_score = self._score_information_depth(gathered_info)
        conversation_progress_score = self._score_conversation_progress(conversation_state)
        
        # Weighted combination
        base_confidence = (
            info_breadth_score * 0.4 +
            info_depth_score * 0.4 +
            conversation_progress_score * 0.2
        )
        
        return min(1.0, max(0.0, base_confidence))
    
    def _score_information_breadth(self, gathered_info: Dict[str, Any]) -> float:
        """Score based on breadth of information categories covered."""
        if not gathered_info:
            return 0.0
        
        # Key categories for personalization
        important_categories = [
            'expertise_level', 'context', 'preferences', 'constraints',
            'timeline', 'budget', 'goals', 'background'
        ]
        
        covered_categories = sum(1 for cat in important_categories if cat in gathered_info)
        breadth_score = covered_categories / len(important_categories)
        
        # Give bonus for having any information at all
        if gathered_info:
            breadth_score = max(breadth_score, 0.3)  # Minimum score for having some info
            
        return breadth_score
    
    def _score_information_depth(self, gathered_info: Dict[str, Any]) -> float:
        """Score based on depth of information in each category."""
        if not gathered_info:
            return 0.0
        
        depth_scores = []
        for key, value in gathered_info.items():
            if isinstance(value, str):
                # Score string length (more detailed responses)
                depth_score = min(1.0, len(value) / 100)  # Normalize to ~100 chars
            elif isinstance(value, list):
                # Score list completeness
                depth_score = min(1.0, len(value) / 5)  # Normalize to ~5 items
            elif isinstance(value, dict):
                # Score nested information
                depth_score = min(1.0, len(value) / 3)  # Normalize to ~3 sub-items
            else:
                depth_score = 0.5  # Default for other types
            
            depth_scores.append(depth_score)
        
        return sum(depth_scores) / len(depth_scores) if depth_scores else 0.0
    
    def _score_conversation_progress(self, conversation_state: ConversationState) -> float:
        """Score based on conversation progress and natural flow."""
        conversation_turns = len(conversation_state.question_history)
        
        if conversation_turns == 0:
            return 0.0
        elif conversation_turns < 3:
            return 0.3  # Early stage
        elif conversation_turns < 6:
            return 0.7  # Good progress
        elif conversation_turns < self.max_conversation_turns:
            return 1.0  # Comprehensive
        else:
            return 0.8  # Too long, diminishing returns
    
    def _adjust_confidence_for_gaps(self, base_confidence: float, gaps: List[InformationGap]) -> float:
        """Adjust confidence score based on identified gaps."""
        if not gaps:
            return base_confidence
        
        # Penalize based on gap importance
        critical_gaps = sum(1 for gap in gaps if gap.importance == 'critical')
        important_gaps = sum(1 for gap in gaps if gap.importance == 'important')
        
        # Calculate penalty
        penalty = (critical_gaps * 0.2) + (important_gaps * 0.1)
        
        adjusted_confidence = max(0.0, base_confidence - penalty)
        return adjusted_confidence
    
    def _identify_missing_categories(self, user_query: str, gathered_info: Dict[str, Any]) -> List[str]:
        """Identify missing information areas using AI analysis instead of predefined categories."""
        try:
            # Create AI prompt for dynamic category discovery
            prompt = f"""Analyze this research conversation and identify what key information areas are missing.

USER'S ORIGINAL QUERY: {user_query}

INFORMATION ALREADY GATHERED:
{json.dumps(gathered_info, indent=2) if gathered_info else "No information gathered yet"}

Based on the user's query, identify what areas of information are missing that would be crucial for providing excellent research. Think about:
- What context about their situation is missing?
- What practical constraints haven't been explored? 
- What preferences or requirements are unclear?
- What success criteria or goals need clarification?

Return only a JSON array of missing information area names (as strings), focusing on what would genuinely improve research quality for THIS specific query.

Example format: ["budget_constraints", "usage_context", "experience_level", "decision_timeline"]

Avoid generic categories - be specific to what this user actually needs based on their query."""

            response = self.research_engine.gemini_client._make_request(prompt)
            
            # Parse the response
            if response and '[' in response and ']' in response:
                start = response.find('[')
                end = response.rfind(']') + 1
                json_text = response[start:end]
                
                try:
                    missing_areas = json.loads(json_text)
                    # Validate that we got a list of strings
                    if isinstance(missing_areas, list) and all(isinstance(item, str) for item in missing_areas):
                        self.logger.debug(f"AI identified missing areas: {missing_areas}")
                        return missing_areas[:6]  # Limit to 6 areas
                except json.JSONDecodeError:
                    pass
            
            # Fallback to context-aware analysis if AI fails
            return self._analyze_natural_gaps(user_query, gathered_info)
            
        except Exception as e:
            self.logger.warning(f"AI gap identification failed: {e}")
            return self._analyze_natural_gaps(user_query, gathered_info)
    
    def _analyze_natural_gaps(self, user_query: str, gathered_info: Dict[str, Any]) -> List[str]:
        """Analyze natural information gaps without predefined categories."""
        gaps = []
        query_words = user_query.lower().split()
        
        # If very little info gathered, identify core decision factors
        if len(gathered_info) < 2:
            # Analyze query intent to suggest relevant information needs
            if any(word in query_words for word in ['buy', 'purchase', 'cost', 'price']):
                gaps.append('budget_parameters')
            if any(word in query_words for word in ['best', 'recommend', 'choose']):
                gaps.append('selection_criteria')
            if any(word in query_words for word in ['need', 'want', 'looking']):
                gaps.append('specific_requirements')
            if any(word in query_words for word in ['work', 'business', 'personal', 'home']):
                gaps.append('usage_context')
        else:
            # Analyze what themes are present vs what might be missing
            covered_themes = set()
            for key, value in gathered_info.items():
                # Extract semantic themes from existing information
                value_str = str(value).lower()
                if any(word in value_str for word in ['budget', 'cost', 'price', 'money']):
                    covered_themes.add('financial_considerations')
                if any(word in value_str for word in ['time', 'urgent', 'deadline', 'soon']):
                    covered_themes.add('timing_constraints')
                if any(word in value_str for word in ['quality', 'performance', 'reliability']):
                    covered_themes.add('quality_expectations')
                if any(word in value_str for word in ['experience', 'skill', 'expert', 'beginner']):
                    covered_themes.add('experience_context')
            
            # Suggest complementary areas based on query type
            potential_themes = {
                'financial_considerations', 'timing_constraints', 
                'quality_expectations', 'usage_patterns', 'experience_context',
                'success_metrics', 'constraint_factors'
            }
            
            missing_themes = potential_themes - covered_themes
            gaps.extend(list(missing_themes)[:4])
        
        return gaps[:5]
    
    def _generate_sufficiency_assessment(self, confidence: float, gaps: List[InformationGap], missing_categories: List[str]) -> str:
        """Generate human-readable sufficiency assessment."""
        if confidence >= self.critical_confidence_threshold:
            return "Comprehensive information gathered. Ready for high-quality research."
        elif confidence >= self.minimal_confidence_threshold:
            return "Sufficient information for basic research. Some gaps remain."
        else:
            return "Insufficient information. Critical gaps need addressing."
    
    def _generate_recommendation(self, confidence: float, conversation_turns: int) -> str:
        """Generate recommendation for next action."""
        if conversation_turns >= self.max_conversation_turns:
            return 'sufficient'  # Prevent infinite conversations
        elif confidence >= self.critical_confidence_threshold:
            return 'sufficient'
        elif confidence >= self.minimal_confidence_threshold:
            return 'minimal_sufficient'
        else:
            return 'continue'
    
    def _generate_reasoning(self, confidence: float, gaps: List[InformationGap], 
                          missing_categories: List[str], conversation_state: ConversationState) -> str:
        """Generate reasoning explanation for the assessment."""
        reasoning_parts = []
        
        # Confidence assessment
        if confidence >= 0.8:
            reasoning_parts.append("High confidence in information completeness")
        elif confidence >= 0.5:
            reasoning_parts.append("Moderate confidence in information completeness")
        else:
            reasoning_parts.append("Low confidence in information completeness")
        
        # Gap analysis
        if gaps:
            critical_count = sum(1 for gap in gaps if gap.importance == 'critical')
            if critical_count > 0:
                reasoning_parts.append(f"{critical_count} critical information gaps identified")
        
        # Missing categories
        if missing_categories:
            reasoning_parts.append(f"Missing categories: {', '.join(missing_categories)}")
        
        # Conversation length
        turns = len(conversation_state.question_history)
        if turns >= self.max_conversation_turns:
            reasoning_parts.append("Maximum conversation length reached")
        
        return ". ".join(reasoning_parts) + "."
    
    def _create_gap_identification_prompt(self, user_query: str, gathered_info: Dict[str, Any]) -> str:
        """Create AI prompt for dynamic gap identification."""
        gathered_info_str = json.dumps(gathered_info, indent=2) if gathered_info else "None"
        
        return f"""Analyze this research conversation and identify information gaps that would significantly improve research quality:

USER'S QUERY: {user_query}
CURRENT INFORMATION: {gathered_info_str}

Identify specific information gaps that are genuinely missing and would help provide better research. Focus on:
1. What practical context about their situation is unclear?
2. What constraints or requirements haven't been explored?
3. What would help understand their success criteria?
4. What background would improve recommendation relevance?

Respond with a JSON array of gaps. Each gap should have:
- area_description: what information area is missing (be specific, not generic)
- importance_level: "critical", "important", or "helpful"  
- suggested_question: a natural follow-up question to gather this info
- research_impact: how this would improve research quality

Focus on gaps that are actually relevant to THIS user's specific query. Avoid generic categories.

Example format:
[
  {{
    "area_description": "budget_constraints_for_purchase",
    "importance_level": "critical",
    "suggested_question": "What's your budget range for this purchase?",
    "research_impact": "Filters recommendations to affordable options"
  }}
]
"""
    
    def _parse_gap_response(self, response_text: str) -> List[InformationGap]:
        """Parse AI response into InformationGap objects with dynamic categories."""
        try:
            # Extract JSON from response
            start = response_text.find('[')
            end = response_text.rfind(']') + 1
            
            if start == -1 or end == 0:
                return []
            
            json_text = response_text[start:end]
            gaps_data = json.loads(json_text)
            
            gaps = []
            for gap_data in gaps_data:
                # Handle both old and new formats
                if 'area_description' in gap_data:
                    # New dynamic format
                    gap = InformationGap(
                        category=gap_data.get('area_description', 'unknown'),
                        importance=gap_data.get('importance_level', 'helpful'),
                        suggested_question=gap_data.get('suggested_question', ''),
                        context_dependency=[gap_data.get('research_impact', '')]
                    )
                else:
                    # Fallback to old format
                    gap = InformationGap(
                        category=gap_data.get('category', 'unknown'),
                        importance=gap_data.get('importance', 'nice_to_have'),
                        suggested_question=gap_data.get('suggested_question', ''),
                        context_dependency=gap_data.get('context_dependency', [])
                    )
                gaps.append(gap)
            
            return gaps
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            self.logger.warning(f"Failed to parse gap response: {e}")
            return []
    
    def _identify_gaps_rule_based(self, user_query: str, gathered_info: Dict[str, Any]) -> List[InformationGap]:
        """Fallback rule-based gap identification without predefined categories."""
        gaps = []
        query_lower = user_query.lower()
        
        # Dynamic gap detection based on query analysis
        query_themes = {
            'learning_context': ['learn', 'understand', 'new', 'beginner', 'how to'],
            'purchase_decision': ['buy', 'purchase', 'cost', 'budget', '$', 'price'],
            'time_sensitive': ['urgent', 'quick', 'soon', 'deadline', 'asap'],
            'comparative_choice': ['best', 'better', 'compare', 'vs', 'difference'],
            'technical_implementation': ['implement', 'setup', 'configure', 'install']
        }
        
        detected_themes = []
        for theme, keywords in query_themes.items():
            if any(keyword in query_lower for keyword in keywords):
                detected_themes.append(theme)
        
        # Generate contextual gaps based on detected themes
        if 'learning_context' in detected_themes and not any('experience' in str(v) for v in gathered_info.values()):
            gaps.append(InformationGap(
                category='experience_and_background_context',
                importance='important',
                suggested_question='What is your current experience level with this topic?',
                context_dependency=['learning_path_optimization']
            ))
        
        if 'purchase_decision' in detected_themes and not any('budget' in str(v) or 'cost' in str(v) for v in gathered_info.values()):
            gaps.append(InformationGap(
                category='financial_constraints_and_budget',
                importance='critical',
                suggested_question='Do you have a budget range in mind for this?',
                context_dependency=['option_filtering', 'value_assessment']
            ))
        
        if 'time_sensitive' in detected_themes and not any('timeline' in str(v) or 'deadline' in str(v) for v in gathered_info.values()):
            gaps.append(InformationGap(
                category='timeline_and_urgency_factors',
                importance='important',
                suggested_question='What is your timeline for making this decision?',
                context_dependency=['priority_sequencing', 'quick_wins']
            ))
        
        if 'comparative_choice' in detected_themes and not any('criteria' in str(v) or 'important' in str(v) for v in gathered_info.values()):
            gaps.append(InformationGap(
                category='decision_criteria_and_priorities',
                importance='important',
                suggested_question='What factors are most important to you in making this choice?',
                context_dependency=['comparison_framework', 'weighting_factors']
            ))
        
        # Context-specific gaps if little information gathered
        if len(gathered_info) < 2:
            gaps.append(InformationGap(
                category='usage_context_and_requirements',
                importance='important',
                suggested_question='Can you tell me more about how you plan to use this?',
                context_dependency=['personalization', 'requirement_matching']
            ))
        
        return gaps
    
    def _create_fallback_result(self) -> CompletionResult:
        """Create a safe fallback result when assessment fails."""
        return CompletionResult(
            confidence_score=0.3,
            information_gaps=[],
            missing_categories=[],
            sufficiency_assessment="Unable to assess completeness due to technical error",
            recommendation='continue',
            reasoning="Assessment system encountered an error, continuing conversation for safety"
        )
