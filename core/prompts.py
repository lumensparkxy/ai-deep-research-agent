"""
Prompt Manager for Deep Research Agent.
Handles generation of prompts for different research stages.
"""

import json
from typing import Dict, Any, List
from .exceptions import PromptGenerationError

class PromptManager:
    """Manages prompt templates and generation."""

    def __init__(self, settings: Any):
        self.settings = settings

    def get_stage_1_prompt(self, query: str, context: Dict[str, Any]) -> str:
        """Build prompt for Stage 1: Information Gathering."""
        context_str = ""
        if context.get("personalize") and context.get("user_info"):
            context_str = f"\nUser Context: {json.dumps(context['user_info'], indent=2)}"
        
        return f"""You are a senior research analyst conducting a comprehensive initial investigation.

QUERY: {query}
{context_str}

Your goal is to gather a broad and deep foundation of information. Do not settle for surface-level facts.

Task:
1. Identify the core concepts and entities associated with the query.
2. Gather key facts, statistics, and definitions.
3. Search for diverse perspectives and potential controversies.
4. Identify primary sources of authority in this domain.

Provide a JSON response:
{{
    "summary": "A high-level executive summary of the initial landscape.",
    "key_facts": [
        "Fact 1 (with context)",
        "Fact 2 (with context)"
    ],
    "evidence": [
        {{
            "source_description": "Specific report, study, or authority",
            "reliability_score": 0.0-1.0,
            "extracted_text": "Direct quote or specific data point",
            "relevance_score": 0.0-1.0
        }}
    ],
    "gaps_identified": [
        "Specific missing data point 1",
        "Unclear relationship between X and Y"
    ],
    "research_areas": [
        "Sub-topic 1 to explore in depth",
        "Sub-topic 2 to explore in depth"
    ]
}}"""

    def get_stage_2_prompt(self, query: str, previous_findings: Dict[str, Any]) -> str:
        """Build prompt for Stage 2: Validation."""
        return f"""You are a rigorous fact-checker and auditor. Your job is to validate the initial research findings and challenge assumptions.

QUERY: {query}

INITIAL FINDINGS:
{json.dumps(previous_findings, indent=2)}

Task:
1. Verify the accuracy of the key facts. Are they up-to-date? Are they from biased sources?
2. Identify any logical inconsistencies or contradictions.
3. Flag information that lacks sufficient evidence.
4. Distinguish between objective facts and subjective opinions.

Provide a JSON response:
{{
    "summary": "Assessment of the research validity so far.",
    "validated_facts": [
        "Fact 1 (Verified)",
        "Fact 2 (Verified)"
    ],
    "questionable_information": [
        "Claim X is disputed by Source Y",
        "Statistic Z is outdated (from 2019)"
    ],
    "additional_gaps": [
        "New gap discovered during verification"
    ],
    "reliability_assessment": {{
        "overall_confidence": 0.0-1.0,
        "strong_evidence": ["List of solid points"],
        "weak_evidence": ["List of shaky points"]
    }}
}}"""

    def get_stage_3_prompt(self, query: str, gaps: List[str]) -> str:
        """Build prompt for Stage 3: Clarification."""
        gaps_str = "\n".join([f"- {gap}" for gap in gaps[:self.settings.max_gaps_per_stage]])
        
        return f"""You are a targeted research specialist. Your goal is to close specific knowledge gaps.

QUERY: {query}

MISSING INFORMATION (GAPS):
{gaps_str}

Task:
1. Conduct focused research to answer EACH specific gap.
2. If a gap cannot be fully resolved, explain why (e.g., data unavailability).
3. Look for niche or specialized sources that might hold these specific answers.

Provide a JSON response:
{{
    "summary": "Progress report on filling knowledge gaps.",
    "gap_responses": [
        {{
            "gap": "The specific gap being addressed",
            "findings": "Detailed answer or explanation",
            "confidence": 0.0-1.0
        }}
    ],
    "additional_evidence": [
        {{
            "source_description": "Source used for this gap",
            "reliability_score": 0.0-1.0,
            "extracted_text": "Relevant excerpt",
            "relevance_score": 0.0-1.0
        }}
    ],
    "remaining_gaps": [
        "Gaps that are still critical and unaddressed"
    ]
}}"""

    def get_stage_4_prompt(self, query: str, all_findings: List[Dict], context: Dict[str, Any]) -> str:
        """Build prompt for Stage 4: Comparative Analysis."""
        context_str = ""
        if context.get("constraints"):
            context_str = f"\nUser Constraints: {json.dumps(context['constraints'], indent=2)}"
        
        return f"""You are a decision support analyst. Your goal is to systematically compare options to aid decision-making.

QUERY: {query}
{context_str}

Task:
1. Identify distinct options, solutions, or pathways relevant to the query.
2. Define clear criteria for comparison (e.g., cost, efficiency, risk, longevity).
3. Evaluate each option against these criteria using the research findings.
4. Highlight trade-offs and "best for X" scenarios.

Provide a JSON response:
{{
    "summary": "Overview of the competitive landscape.",
    "options_identified": [
        {{
            "option": "Name of option",
            "description": "Brief description",
            "pros": ["Pro 1", "Pro 2"],
            "cons": ["Con 1", "Con 2"],
            "score": 0.0-1.0 (overall suitability)
        }}
    ],
    "comparison_criteria": [
        "Criterion 1",
        "Criterion 2"
    ],
    "comparison_matrix": {{
        "Option 1": {{"Criterion 1": 8, "Criterion 2": 6}},
        "Option 2": {{"Criterion 1": 6, "Criterion 2": 9}}
    }},
    "standout_recommendations": [
        "Option A is best for budget-conscious users",
        "Option B is the performance leader"
    ]
}}"""

    def get_stage_5_prompt(self, query: str, all_findings: List[Dict]) -> str:
        """Build prompt for Stage 5: Synthesis."""
        return f"""You are a lead strategist. Your goal is to synthesize scattered findings into a coherent narrative.

QUERY: {query}

Task:
1. Integrate findings from all previous stages.
2. Identify cross-cutting patterns, trends, and causal relationships.
3. Resolve any remaining conflicts in the data.
4. Assess the overall strength of the conclusion we are building towards.

Provide a JSON response:
{{
    "summary": "A powerful synthesis of the entire research journey.",
    "key_insights": [
        "Deep insight 1 (connecting multiple facts)",
        "Deep insight 2"
    ],
    "patterns_identified": [
        "Trend X is accelerating",
        "Correlation between A and B"
    ],
    "confidence_assessment": {{
        "overall_confidence": 0.0-1.0,
        "high_confidence_areas": ["Areas where evidence is solid"],
        "low_confidence_areas": ["Areas where we are speculating"]
    }},
    "decision_factors": [
        {{
            "factor": "Critical variable",
            "importance": "high/medium/low",
            "evidence_strength": "strong/weak"
        }}
    ]
}}"""

    def get_stage_6_prompt(self, query: str, all_findings: List[Dict], context: Dict[str, Any]) -> str:
        """Build prompt for Stage 6: Final Conclusions."""
        user_info = context.get("user_info", {})
        constraints = context.get("constraints", {})
        preferences = context.get("preferences", {})
        
        personalization = ""
        if user_info or constraints or preferences:
            personalization = f"""
PERSONALIZATION CONTEXT:
User Info: {json.dumps(user_info, indent=2)}
Constraints: {json.dumps(constraints, indent=2)}
Preferences: {json.dumps(preferences, indent=2)}
"""
        
        return f"""You are the final authority on this research project. Your goal is to provide a definitive answer and actionable roadmap.

QUERY: {query}
{personalization}

Task:
1. Provide a direct answer to the user's core question.
2. Make specific, prioritized recommendations.
3. Create a step-by-step implementation plan.
4. Anticipate risks and provide mitigation strategies.
5. Define what "success" looks like.

Provide a JSON response:
{{
    "summary": "The final verdict. Clear, concise, and authoritative.",
    "primary_recommendation": "The single best course of action.",
    "recommendations": [
        {{
            "recommendation": "Actionable advice",
            "reasoning": "Why this is recommended",
            "priority": "high/medium/low",
            "confidence": 0.0-1.0
        }}
    ],
    "implementation_plan": [
        {{
            "step": "Step 1",
            "description": "Actionable instruction",
            "timeline": "Estimated time"
        }}
    ],
    "risk_assessment": [
        {{
            "risk": "Potential pitfall",
            "likelihood": "high/medium/low",
            "impact": "high/medium/low",
            "mitigation": "How to avoid or fix it"
        }}
    ],
    "success_metrics": [
        "Metric 1 to track",
        "Metric 2 to track"
    ],
    "confidence_factors": [
        "Why we are confident in this result",
        "Where caution is needed"
    ]
}}"""
