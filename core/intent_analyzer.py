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
You are an expert consultant analyzing a user's research query to understand their deeper intent and context.

USER QUERY: "{query}"
{context_info}

Analyze this query to understand:

1. CORE INTENT: What is the user really trying to achieve? Look beyond the surface request.

2. DECISION CONTEXT: What kind of decision or situation is driving this query? 

3. EMOTIONAL UNDERTONES: What emotional signals do you detect? (urgency, anxiety, excitement, confusion, etc.)

4. STAKEHOLDER IMPLICATIONS: Who might be affected by or involved in this decision?

5. COMPLEXITY ASSESSMENT: How complex is this likely to be? What makes it complex or simple?

6. CONVERSATION STRATEGY: How should we approach the conversation to best help this user?

7. QUESTION FOCUS AREAS: What are the most important areas to explore through questions?

8. SUCCESS CRITERIA: What would make this research truly valuable for the user?

9. POTENTIAL CHALLENGES: What obstacles or complications might arise?

10. CONTEXTUAL INSIGHTS: Any other important context that would guide the conversation?

Provide your analysis in a natural, consultative tone. Focus on actionable insights that will guide an intelligent conversation.

ANALYSIS:
"""
        return prompt
    
    def _extract_insights_from_analysis(self, analysis: str) -> Dict[str, Any]:
        """Extract structured insights from AI analysis"""
        try:
            # Use AI to extract structured data from the analysis
            extraction_prompt = f"""
Extract key insights from this intent analysis and format as JSON:

ANALYSIS:
{analysis}

Extract these insights as JSON:
{{
    "key_insights": {{
        "core_intent": "what user really wants to achieve",
        "decision_context": "type of decision/situation", 
        "emotional_undertones": "detected emotions/urgency",
        "stakeholder_implications": "who else is involved",
        "potential_challenges": "obstacles or complications"
    }},
    "conversation_strategy": "recommended approach (conversational/analytical/supportive/etc)",
    "question_focus_areas": ["area1", "area2", "area3"],
    "estimated_complexity": "simple/moderate/complex/critical",
    "confidence_level": 0.8,
    "contextual_notes": "additional important context"
}}

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
Based on this intent analysis, generate a natural conversation opener that shows understanding and begins the personalization process.

INTENT ANALYSIS:
{insights.raw_analysis}

KEY INSIGHTS:
- Core Intent: {insights.get_insight('core_intent')}
- Decision Context: {insights.get_insight('decision_context')}
- Complexity: {insights.estimated_complexity}
- Strategy: {insights.conversation_strategy}

Generate a conversation opener that:
1. Shows you understand their deeper intent
2. Feels consultative and professional
3. Naturally leads to the first question
4. Sets the right tone for the conversation

Keep it conversational, not robotic. Make them feel understood.

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
Update your understanding based on this new information:

ORIGINAL ANALYSIS:
{insights.raw_analysis}

NEW INFORMATION:
Question: {question}
Answer: {answer}

Provide an updated analysis that incorporates this new information. What new insights emerge? What should we focus on next?

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
