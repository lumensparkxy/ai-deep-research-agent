"""
Intent Analysis Integration for AI-Driven Conversation System

This module provides fluid, AI-powered intent analysis without rigid classifications.
Uses Gemini's intelligence to understand context, complexity, and conversation strategy.
"""

import logging
import json
from typing import Dict, Any, Optional
from dataclasses import dataclass

from config.settings import get_settings


@dataclass
class IntentInsights:
    """
    Fluid container for AI-generated intent insights.
    No rigid categories - pure AI understanding.
    """
    raw_analysis: str                    # Complete AI analysis text
    key_insights: Dict[str, Any]         # Extracted key insights
    conversation_strategy: str           # AI-recommended approach
    question_focus_areas: list          # What to explore
    estimated_complexity: str           # AI's complexity assessment
    confidence_level: float             # AI's confidence (0-1)
    contextual_notes: str              # Additional context
    
    def get_insight(self, key: str, default: Any = None) -> Any:
        """Get specific insight with fallback"""
        return self.key_insights.get(key, default)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'raw_analysis': self.raw_analysis,
            'key_insights': self.key_insights,
            'conversation_strategy': self.conversation_strategy,
            'question_focus_areas': self.question_focus_areas,
            'estimated_complexity': self.estimated_complexity,
            'confidence_level': self.confidence_level,
            'contextual_notes': self.contextual_notes
        }


class IntentAnalyzer:
    """
    AI-first intent analyzer that leverages Gemini's intelligence
    to understand user queries without rigid classification systems.
    """
    
    def __init__(self, gemini_client, model_name: str = "gemini-pro"):
        self.gemini_client = gemini_client
        self.model_name = model_name
        self.settings = get_settings()
        self.logger = logging.getLogger(__name__)
        
    def analyze_user_intent(self, query: str, context: Optional[Dict[str, Any]] = None) -> IntentInsights:
        """
        Analyze user intent using pure AI intelligence.
        No rigid categories - fluid understanding.
        """
        try:
            # Create rich context for AI analysis
            analysis_prompt = self._create_intent_analysis_prompt(query, context)
            
            # Get AI analysis
            response = self.gemini_client.generate_content(analysis_prompt)
            raw_analysis = response.text.strip()
            
            # Extract structured insights from AI response
            insights = self._extract_insights_from_analysis(raw_analysis)
            
            return IntentInsights(
                raw_analysis=raw_analysis,
                key_insights=insights.get('key_insights', {}),
                conversation_strategy=insights.get('conversation_strategy', 'standard'),
                question_focus_areas=insights.get('question_focus_areas', []),
                estimated_complexity=insights.get('estimated_complexity', 'moderate'),
                confidence_level=insights.get('confidence_level', 0.7),
                contextual_notes=insights.get('contextual_notes', '')
            )
            
        except Exception as e:
            self.logger.error(f"Intent analysis failed: {e}")
            # Return basic fallback insights
            return self._create_fallback_insights(query)
    
    def _create_intent_analysis_prompt(self, query: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Create intelligent prompt for intent analysis"""
        
        context_info = ""
        if context:
            context_info = f"""
ADDITIONAL CONTEXT:
{json.dumps(context, indent=2)}
"""
        
        prompt = f"""
You are an expert strategic consultant analyzing a user's research query. Your goal is to decode the user's request to understand their deeper intent, context, and the optimal strategy to assist them.

USER QUERY: "{query}"
{context_info}

Perform a deep analysis of this query covering the following dimensions:

1. **CORE INTENT**: What is the user's fundamental objective? (e.g., "Making a high-stakes purchase decision", "Learning a new complex skill", "Solving a critical technical error"). Look beyond the surface words.
2. **DECISION CONTEXT**: What is the likely scenario? (e.g., "Corporate procurement", "Personal hobby project", "Academic research").
3. **IMPLICIT NEEDS**: What does the user need that they haven't explicitly asked for? (e.g., "Needs validation of assumptions", "Needs a roadmap, not just a list").
4. **EMOTIONAL STATE**: Detect signals of urgency, frustration, curiosity, or caution.
5. **COMPLEXITY & SCOPE**: Assess the depth required. Is this a quick fact-check or a multi-faceted research project?
6. **STAKEHOLDERS**: Who else might be influenced by this result?
7. **CONVERSATION STRATEGY**: Define the persona and approach (e.g., "Authoritative and concise", "Exploratory and supportive").
8. **KEY INFORMATION GAPS**: What are the top 3 most critical missing pieces of information?

Provide your analysis in a structured, professional, and consultative tone.

ANALYSIS:
"""
        return prompt
    
    def _extract_insights_from_analysis(self, analysis: str) -> Dict[str, Any]:
        """Extract structured insights from AI analysis"""
        try:
            # Use AI to extract structured data from the analysis
            extraction_prompt = f"""
You are a data extraction specialist. Extract key insights from the following intent analysis and format them into a precise JSON object.

ANALYSIS:
{analysis}

Output JSON format:
{{
    "key_insights": {{
        "core_intent": "Concise statement of the user's goal",
        "decision_context": "The scenario or environment", 
        "emotional_undertones": "Detected emotions",
        "implicit_needs": "Needs not explicitly stated",
        "stakeholder_implications": "Who is affected",
        "potential_challenges": "Likely obstacles"
    }},
    "conversation_strategy": "Recommended tone and approach",
    "question_focus_areas": ["Specific Area 1", "Specific Area 2", "Specific Area 3"],
    "estimated_complexity": "One of: [simple, moderate, complex, critical]",
    "confidence_level": 0.0 to 1.0,
    "contextual_notes": "Any other crucial context"
}}

Ensure the JSON is valid and strictly follows the structure.
JSON:
"""
            
            response = self.gemini_client.generate_content(extraction_prompt)
            json_text = response.text.strip()
            
            # Clean up JSON (remove markdown formatting if present)
            if json_text.startswith('```json'):
                json_text = json_text.replace('```json', '').replace('```', '').strip()
            
            return json.loads(json_text)
            
        except Exception as e:
            self.logger.warning(f"Could not extract structured insights: {e}")
            # Return basic structure with analysis text
            return {
                'key_insights': {'core_intent': 'research request'},
                'conversation_strategy': 'standard',
                'question_focus_areas': ['preferences', 'constraints'],
                'estimated_complexity': 'moderate',
                'confidence_level': 0.5,
                'contextual_notes': analysis[:200] + '...' if len(analysis) > 200 else analysis
            }
    
    def _create_fallback_insights(self, query: str) -> IntentInsights:
        """Create basic insights when AI analysis fails"""
        return IntentInsights(
            raw_analysis=f"Basic analysis of query: {query}",
            key_insights={
                'core_intent': 'information gathering',
                'decision_context': 'research request',
                'estimated_complexity': 'moderate'
            },
            conversation_strategy='standard',
            question_focus_areas=['preferences', 'constraints'],
            estimated_complexity='moderate',
            confidence_level=0.3,
            contextual_notes='Fallback analysis due to processing error'
        )
    
    def generate_conversation_opener(self, insights: IntentInsights) -> str:
        """Generate AI-powered conversation opener based on intent insights"""
        try:
            opener_prompt = f"""
You are an intelligent research assistant. Based on the following intent analysis, generate a natural, engaging conversation opener.

INTENT ANALYSIS:
{insights.raw_analysis}

KEY INSIGHTS:
- Core Intent: {insights.get_insight('core_intent')}
- Strategy: {insights.conversation_strategy}

Your Goal:
1. Acknowledge the user's goal to show you understand.
2. Adopt the recommended conversation strategy/tone.
3. Transition smoothly into the first phase of information gathering.
4. Keep it concise (under 50 words) and professional.

OPENER:
"""
            
            response = self.gemini_client.generate_content(opener_prompt)
            return response.text.strip()
            
        except Exception as e:
            self.logger.error(f"Could not generate opener: {e}")
            return "I'd like to understand your needs better so I can provide the most relevant research. Let me ask you a few questions to personalize my recommendations."
    
    def update_insights_with_response(self, insights: IntentInsights, question: str, answer: str) -> IntentInsights:
        """Update intent insights based on user response"""
        try:
            update_prompt = f"""
You are refining your understanding of a user's intent. Update the original analysis based on their latest response.

ORIGINAL ANALYSIS:
{insights.raw_analysis}

NEW INTERACTION:
Question: {question}
Answer: {answer}

Task:
1. Evaluate how the new answer changes or confirms the original analysis.
2. Identify any new constraints, preferences, or goals revealed.
3. Adjust the complexity assessment or conversation strategy if needed.

Provide a concise updated analysis.

UPDATED ANALYSIS:
"""
            
            response = self.gemini_client.generate_content(update_prompt)
            updated_analysis = response.text.strip()
            
            # Extract updated insights
            updated_insights = self._extract_insights_from_analysis(updated_analysis)
            
            # Create updated IntentInsights
            return IntentInsights(
                raw_analysis=updated_analysis,
                key_insights=updated_insights.get('key_insights', insights.key_insights),
                conversation_strategy=updated_insights.get('conversation_strategy', insights.conversation_strategy),
                question_focus_areas=updated_insights.get('question_focus_areas', insights.question_focus_areas),
                estimated_complexity=updated_insights.get('estimated_complexity', insights.estimated_complexity),
                confidence_level=min(insights.confidence_level + 0.1, 1.0),  # Increase confidence
                contextual_notes=updated_insights.get('contextual_notes', insights.contextual_notes)
            )
            
        except Exception as e:
            self.logger.error(f"Could not update insights: {e}")
            return insights  # Return original insights if update fails
