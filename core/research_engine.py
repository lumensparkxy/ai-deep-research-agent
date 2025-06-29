"""
Research Engine for Deep Research Agent
6-stage iterative research process with Gemini AI integration.
"""

import logging
import time
import json
import re
from typing import Dict, Any, List, Optional
from datetime import datetime

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from config.settings import Settings
from utils.session_manager import SessionManager
from utils.validators import InputValidator, ValidationError


class ResearchEngine:
    """AI-powered research engine with 6-stage iterative process."""
    
    def __init__(self, settings: Settings):
        """Initialize research engine with Gemini AI."""
        self.settings = settings
        self.session_manager = SessionManager(settings)
        self.validator = InputValidator(settings)
        self.logger = logging.getLogger(__name__)
        
        # Configure Gemini AI
        self._setup_gemini()
        
        # Stage configurations: store method names to allow dynamic patching
        self.stages = [
            {"number": 1, "name": "Information Gathering", "method_name": "_stage_1_information_gathering"},
            {"number": 2, "name": "Validation & Fact-Checking", "method_name": "_stage_2_validation"},
            {"number": 3, "name": "Clarification & Follow-up", "method_name": "_stage_3_clarification"},
            {"number": 4, "name": "Comparative Analysis", "method_name": "_stage_4_comparative_analysis"},
            {"number": 5, "name": "Synthesis & Integration", "method_name": "_stage_5_synthesis"},
            {"number": 6, "name": "Final Conclusions", "method_name": "_stage_6_final_conclusions"}
        ]
    
    def _setup_gemini(self) -> None:
        """Configure Gemini AI client."""
        try:
            genai.configure(api_key=self.settings.gemini_api_key)
            
            # Configure model with safety settings
            self.model = genai.GenerativeModel(
                model_name=self.settings.ai_model,
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                }
            )
            
            self.logger.info(f"Initialized Gemini model: {self.settings.ai_model}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Gemini: {e}")
            raise ValidationError(f"Could not initialize AI model: {e}")
    
    def conduct_research(self, query: str, context: Dict[str, Any], 
                        session_id: str) -> Dict[str, Any]:
        """
        Conduct comprehensive 6-stage research process.
        
        Args:
            query: Research question
            context: User context and personalization
            session_id: Session identifier
            
        Returns:
            Complete research results
        """
        # Validate input query and create a new session to ensure proper session setup
        validated_query = self.validator.validate_query(query)
        try:
            session_data = self.session_manager.create_session(validated_query, context)
            session_id = session_data.get("session_id", session_id)
        except ValidationError:
            # Propagate session creation or validation errors
            raise
        self.logger.info(f"Starting 6-stage research for session {session_id}")
        
        # Initialize research state
        research_state = {
            "query": query,
            "context": context,
            "session_id": session_id,
            "stages": [],
            "knowledge_base": {
                "entities": [],
                "relationships": [],
                "key_facts": []
            },
            "gaps_identified": [],
            "sources": [],
            "confidence_factors": []
        }
        
        try:
            # Execute each stage sequentially
            for stage_config in self.stages:
                stage_num = stage_config["number"]
                stage_name = stage_config["name"]
                # Lookup method dynamically to allow test patching
                method_name = stage_config.get("method_name")
                stage_method = getattr(self, method_name)
                
                self.logger.info(f"Executing Stage {stage_num}: {stage_name}")
                
                # Display progress to user
                self._display_stage_progress(stage_num, stage_name)
                
                try:
                    # Execute stage
                    stage_result = stage_method(research_state)
                    
                    # Validate stage result
                    if not isinstance(stage_result, dict):
                        raise ValidationError(f"Stage {stage_num} returned invalid result")
                    
                    # Add stage metadata
                    stage_result.update({
                        "stage": stage_num,
                        "name": stage_name,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    # Store stage result
                    research_state["stages"].append(stage_result)
                    
                    # Update session with stage progress
                    self.session_manager.update_session_stage(session_id, stage_result)
                    
                    # Add small delay to respect rate limits
                    time.sleep(self.settings.rate_limit_delay)
                    
                except Exception as e:
                    self.logger.error(f"Error in Stage {stage_num}: {e}")
                    # Continue with degraded functionality
                    fallback_result = {
                        "stage": stage_num,
                        "name": stage_name,
                        "findings": {
                            "summary": f"Stage {stage_num} encountered an error but research continues",
                            "evidence": [],
                            "gaps_identified": [f"Error in {stage_name}: {str(e)}"]
                        },
                        "timestamp": datetime.now().isoformat(),
                        "error": str(e)
                    }
                    research_state["stages"].append(fallback_result)
            
            # Calculate overall confidence score
            confidence_score = self._calculate_confidence_score(research_state)
            
            # Prepare final results
            final_results = {
                "stages": research_state["stages"],
                "final_conclusions": research_state["stages"][-1]["findings"] if research_state["stages"] else {},
                "confidence_score": confidence_score,
                "knowledge_base": research_state["knowledge_base"]
            }
            
            # Update session with final results
            self.session_manager.update_session_conclusions(
                session_id, final_results["final_conclusions"], confidence_score
            )
            
            self.logger.info(f"Research completed for session {session_id} with confidence {confidence_score:.2f}")
            return final_results
            
        except Exception as e:
            self.logger.error(f"Critical error in research process: {e}")
            # Return minimal results to allow graceful degradation
            return {
                "stages": research_state.get("stages", []),
                "final_conclusions": {
                    "summary": f"Research encountered errors but partial results available",
                    "recommendations": ["Review error logs for details"],
                    "error": str(e)
                },
                "confidence_score": self.settings.min_confidence_fallback,
                "knowledge_base": research_state.get("knowledge_base", {})
            }
    
    def _stage_1_information_gathering(self, research_state: Dict[str, Any]) -> Dict[str, Any]:
        """Stage 1: Broad exploration and initial research."""
        query = research_state["query"]
        context = research_state["context"]
        
        # Build context-aware prompt
        prompt = self._build_stage_1_prompt(query, context)
        
        # Get AI response
        response = self._call_gemini_with_retry(prompt)
        
        # Parse response and extract structured data
        findings = self._parse_information_gathering_response(response)
        
        # Update research state with findings
        research_state["knowledge_base"]["key_facts"].extend(
            findings.get("key_facts", [])
        )
        research_state["gaps_identified"].extend(
            findings.get("gaps_identified", [])
        )
        
        return {
            "findings": findings
        }
    
    def _stage_2_validation(self, research_state: Dict[str, Any]) -> Dict[str, Any]:
        """Stage 2: Validation and fact-checking."""
        previous_findings = research_state["stages"][-1]["findings"] if research_state["stages"] else {}
        
        prompt = self._build_stage_2_prompt(research_state["query"], previous_findings)
        response = self._call_gemini_with_retry(prompt)
        findings = self._parse_validation_response(response)
        
        # Update gaps identified
        research_state["gaps_identified"].extend(
            findings.get("additional_gaps", [])
        )
        
        return {
            "findings": findings
        }
    
    def _stage_3_clarification(self, research_state: Dict[str, Any]) -> Dict[str, Any]:
        """Stage 3: Clarification and follow-up research."""
        gaps = research_state["gaps_identified"]
        
        prompt = self._build_stage_3_prompt(research_state["query"], gaps)
        response = self._call_gemini_with_retry(prompt)
        findings = self._parse_clarification_response(response)
        
        return {
            "findings": findings
        }
    
    def _stage_4_comparative_analysis(self, research_state: Dict[str, Any]) -> Dict[str, Any]:
        """Stage 4: Systematic comparison of options."""
        all_findings = [stage["findings"] for stage in research_state["stages"]]
        
        prompt = self._build_stage_4_prompt(research_state["query"], all_findings, research_state["context"])
        response = self._call_gemini_with_retry(prompt)
        findings = self._parse_comparative_analysis_response(response)
        
        return {
            "findings": findings
        }
    
    def _stage_5_synthesis(self, research_state: Dict[str, Any]) -> Dict[str, Any]:
        """Stage 5: Synthesis and integration."""
        all_findings = [stage["findings"] for stage in research_state["stages"]]
        
        prompt = self._build_stage_5_prompt(research_state["query"], all_findings)
        response = self._call_gemini_with_retry(prompt)
        findings = self._parse_synthesis_response(response)
        
        return {
            "findings": findings
        }
    
    def _stage_6_final_conclusions(self, research_state: Dict[str, Any]) -> Dict[str, Any]:
        """Stage 6: Final conclusions and recommendations."""
        all_findings = [stage["findings"] for stage in research_state["stages"]]
        context = research_state["context"]
        
        prompt = self._build_stage_6_prompt(research_state["query"], all_findings, context)
        response = self._call_gemini_with_retry(prompt)
        findings = self._parse_final_conclusions_response(response)
        
        return {
            "findings": findings
        }
    
    def _call_gemini_with_retry(self, prompt: str, max_retries: int = None) -> str:
        """Call Gemini API with retry logic."""
        # Determine number of retries; coerce to int and fallback to default 3
        try:
            max_retries = int(max_retries) if isinstance(max_retries, (int, str)) else None
        except Exception:
            max_retries = None
        if max_retries is None:
            try:
                max_retries = int(self.settings.max_retries)
            except Exception:
                max_retries = self.settings.fallback_max_retries
        
        for attempt in range(max_retries):
            try:
                response = self.model.generate_content(prompt)
                if response.text:
                    return response.text
                # Empty response is a terminal validation error
                raise ValidationError("Empty response from Gemini")
            except ValidationError:
                # Propagate validation errors immediately
                raise
            except Exception as e:
                self.logger.warning(f"Gemini API attempt {attempt + 1} failed: {e}")
                # Exponential backoff with safe delay
                try:
                    delay = float(self.settings.retry_delay)
                except Exception:
                    delay = self.settings.fallback_retry_delay
                if attempt < max_retries - 1:
                    time.sleep(delay * (self.settings.exponential_backoff_base ** attempt))
                else:
                    raise ValidationError(f"Gemini API failed after {max_retries} attempts: {e}")
    
    def _build_stage_1_prompt(self, query: str, context: Dict[str, Any]) -> str:
        """Build prompt for Stage 1: Information Gathering."""
        context_str = ""
        if context.get("personalize") and context.get("user_info"):
            context_str = f"\nUser Context: {json.dumps(context['user_info'], indent=2)}"
        
        return f"""You are a professional research analyst conducting initial information gathering for the following query:

QUERY: {query}
{context_str}

Please provide a comprehensive initial research analysis in the following JSON format:

{{
    "summary": "Brief overview of the topic and key considerations",
    "key_facts": [
        "Important fact 1",
        "Important fact 2"
    ],
    "evidence": [
        {{
            "source_description": "Description of information source",
            "reliability_score": 0.8,
            "extracted_text": "Relevant information or data point",
            "relevance_score": 0.9
        }}
    ],
    "gaps_identified": [
        "What specific information is needed?",
        "What questions remain unanswered?"
    ],
    "research_areas": [
        "Area 1 to explore further",
        "Area 2 to investigate"
    ]
}}

Focus on providing factual, evidence-based information with reliable sources. Be thorough but concise."""
    
    def _build_stage_2_prompt(self, query: str, previous_findings: Dict[str, Any]) -> str:
        """Build prompt for Stage 2: Validation."""
        return f"""You are fact-checking and validating previous research findings for this query:

QUERY: {query}

PREVIOUS FINDINGS TO VALIDATE:
{json.dumps(previous_findings, indent=2)}

Please validate these findings and provide your analysis in JSON format:

{{
    "summary": "Overview of validation results",
    "validated_facts": [
        "Confirmed accurate fact 1",
        "Confirmed accurate fact 2"
    ],
    "questionable_information": [
        "Information that needs verification",
        "Conflicting or unclear data"
    ],
    "additional_gaps": [
        "New gaps discovered during validation",
        "Areas needing more research"
    ],
    "reliability_assessment": {{
        "overall_confidence": 0.8,
        "strong_evidence": ["Well-supported finding 1"],
        "weak_evidence": ["Finding needing more support"]
    }}
}}

Be critical and thorough in your validation process."""
    
    def _build_stage_3_prompt(self, query: str, gaps: List[str]) -> str:
        """Build prompt for Stage 3: Clarification."""
        gaps_str = "\n".join([f"- {gap}" for gap in gaps[:self.settings.max_gaps_per_stage]])  # Limit to avoid token limits
        
        return f"""You are conducting follow-up research to fill knowledge gaps for this query:

QUERY: {query}

KNOWLEDGE GAPS TO ADDRESS:
{gaps_str}

Please provide targeted research to fill these gaps in JSON format:

{{
    "summary": "Overview of follow-up research findings",
    "gap_responses": [
        {{
            "gap": "The gap being addressed",
            "findings": "Specific information found to address this gap",
            "confidence": 0.8
        }}
    ],
    "additional_evidence": [
        {{
            "source_description": "New source description",
            "reliability_score": 0.9,
            "extracted_text": "New evidence found",
            "relevance_score": 0.8
        }}
    ],
    "remaining_gaps": [
        "Gaps that still need research"
    ]
}}

Focus on providing specific, actionable information to address each gap."""
    
    def _build_stage_4_prompt(self, query: str, all_findings: List[Dict], context: Dict[str, Any]) -> str:
        """Build prompt for Stage 4: Comparative Analysis."""
        context_str = ""
        if context.get("constraints"):
            context_str = f"\nUser Constraints: {json.dumps(context['constraints'], indent=2)}"
        
        return f"""You are conducting comparative analysis for this decision query:

QUERY: {query}
{context_str}

Based on all previous research, please provide a systematic comparison in JSON format:

{{
    "summary": "Overview of options and comparison approach",
    "options_identified": [
        {{
            "option": "Option name",
            "description": "Brief description",
            "pros": ["Advantage 1", "Advantage 2"],
            "cons": ["Disadvantage 1", "Disadvantage 2"],
            "score": 0.8
        }}
    ],
    "comparison_criteria": [
        "Criteria 1 (e.g., cost, quality, ease of use)",
        "Criteria 2"
    ],
    "comparison_matrix": {{
        "Option 1": {{"criteria_1": 8, "criteria_2": 6}},
        "Option 2": {{"criteria_1": 6, "criteria_2": 9}}
    }},
    "standout_recommendations": [
        "Top option for specific use case",
        "Best value option"
    ]
}}

Provide objective, data-driven comparisons."""
    
    def _build_stage_5_prompt(self, query: str, all_findings: List[Dict]) -> str:
        """Build prompt for Stage 5: Synthesis."""
        return f"""You are synthesizing all research findings to create coherent insights for:

QUERY: {query}

Please integrate all previous research into a comprehensive synthesis in JSON format:

{{
    "summary": "Executive summary of all research",
    "key_insights": [
        "Major insight 1 from combined research",
        "Major insight 2"
    ],
    "patterns_identified": [
        "Pattern or trend discovered",
        "Relationship between factors"
    ],
    "confidence_assessment": {{
        "overall_confidence": 0.85,
        "high_confidence_areas": ["Well-researched area 1"],
        "low_confidence_areas": ["Area needing more research"]
    }},
    "decision_factors": [
        {{
            "factor": "Important decision factor",
            "importance": "high",
            "evidence_strength": "strong"
        }}
    ]
}}

Focus on creating a coherent, actionable synthesis of all research."""
    
    def _build_stage_6_prompt(self, query: str, all_findings: List[Dict], context: Dict[str, Any]) -> str:
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
        
        return f"""You are providing final conclusions and recommendations for:

QUERY: {query}
{personalization}

Based on all 5 stages of research, provide final conclusions in JSON format:

{{
    "summary": "Final executive summary with clear conclusion",
    "primary_recommendation": "Top recommendation with reasoning",
    "recommendations": [
        {{
            "recommendation": "Specific recommendation",
            "reasoning": "Why this is recommended",
            "priority": "high",
            "confidence": 0.9
        }}
    ],
    "implementation_plan": [
        {{
            "step": "Step 1",
            "description": "What to do",
            "timeline": "When to do it"
        }}
    ],
    "risk_assessment": [
        {{
            "risk": "Potential risk",
            "likelihood": "medium",
            "impact": "low",
            "mitigation": "How to mitigate"
        }}
    ],
    "success_metrics": [
        "How to measure success",
        "Key indicators to track"
    ],
    "confidence_factors": [
        "Factor supporting high confidence",
        "Area of uncertainty"
    ]
}}

Provide clear, actionable, personalized recommendations."""
    
    def _parse_information_gathering_response(self, response: str) -> Dict[str, Any]:
        """Parse Stage 1 response into structured data."""
        return self._parse_json_response(response, {
            "summary": "Initial research completed",
            "key_facts": [],
            "evidence": [],
            "gaps_identified": [],
            "research_areas": []
        })
    
    def _parse_validation_response(self, response: str) -> Dict[str, Any]:
        """Parse Stage 2 response into structured data."""
        return self._parse_json_response(response, {
            "summary": "Validation completed",
            "validated_facts": [],
            "questionable_information": [],
            "additional_gaps": [],
            "reliability_assessment": {"overall_confidence": 0.5}
        })
    
    def _parse_clarification_response(self, response: str) -> Dict[str, Any]:
        """Parse Stage 3 response into structured data."""
        return self._parse_json_response(response, {
            "summary": "Follow-up research completed",
            "gap_responses": [],
            "additional_evidence": [],
            "remaining_gaps": []
        })
    
    def _parse_comparative_analysis_response(self, response: str) -> Dict[str, Any]:
        """Parse Stage 4 response into structured data."""
        return self._parse_json_response(response, {
            "summary": "Comparative analysis completed",
            "options_identified": [],
            "comparison_criteria": [],
            "comparison_matrix": {},
            "standout_recommendations": []
        })
    
    def _parse_synthesis_response(self, response: str) -> Dict[str, Any]:
        """Parse Stage 5 response into structured data."""
        return self._parse_json_response(response, {
            "summary": "Research synthesis completed",
            "key_insights": [],
            "patterns_identified": [],
            "confidence_assessment": {"overall_confidence": 0.5},
            "decision_factors": []
        })
    
    def _parse_final_conclusions_response(self, response: str) -> Dict[str, Any]:
        """Parse Stage 6 response into structured data."""
        return self._parse_json_response(response, {
            "summary": "Final conclusions completed",
            "primary_recommendation": "See detailed recommendations",
            "recommendations": [],
            "implementation_plan": [],
            "risk_assessment": [],
            "success_metrics": [],
            "confidence_factors": []
        })
    
    def _parse_json_response(self, response: str, default_structure: Dict[str, Any]) -> Dict[str, Any]:
        """Parse JSON response with fallback to default structure."""
        try:
            # Try to extract JSON from the response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                parsed = json.loads(json_str)
                
                # Merge with default structure to ensure all fields exist
                result = default_structure.copy()
                result.update(parsed)
                return result
            else:
                # No JSON found, create basic structure from text
                return {
                    **default_structure,
                    "summary": response[:500] if response else "No response received",
                    "raw_response": response
                }
                
        except json.JSONDecodeError:
            self.logger.warning("Failed to parse JSON response, using fallback")
            return {
                **default_structure,
                "summary": response[:500] if response else "Failed to parse response",
                "raw_response": response
            }
    
    def _calculate_confidence_score(self, research_state: Dict[str, Any]) -> float:
        """Calculate overall confidence score based on research quality."""
        stages = research_state["stages"]
        if not stages:
            return 0.1
        
        # Base confidence on successful stages
        successful_stages = len([s for s in stages if not s.get("error")])
        stage_confidence = successful_stages / len(self.stages)
        
        # Factor in evidence quality
        evidence_count = 0
        total_reliability = 0.0
        
        for stage in stages:
            evidence = stage.get("findings", {}).get("evidence", [])
            for item in evidence:
                if isinstance(item, dict) and "reliability_score" in item:
                    evidence_count += 1
                    total_reliability += item["reliability_score"]
        
        evidence_confidence = (total_reliability / evidence_count) if evidence_count > 0 else 0.5
        
        # Combine factors
        final_confidence = (stage_confidence * 0.6) + (evidence_confidence * 0.4)
        
        # Ensure confidence is between 0.1 and 1.0
        return max(self.settings.min_confidence_fallback, min(1.0, final_confidence))
    
    def _display_stage_progress(self, stage_num: int, stage_name: str) -> None:
        """Display research stage progress to user."""
        total_stages = len(self.stages)
        progress = stage_num / total_stages
        
        # Progress bar
        bar_length = self.settings.progress_bar_length
        filled_length = int(bar_length * progress)
        bar = "█" * filled_length + "░" * (bar_length - filled_length)
        
        print(f"\n📊 STAGE {stage_num}/{total_stages}: {stage_name}")
        print(f"   [{bar}] {progress:.0%}")
        
        # Stage-specific messages
        messages = {
            1: "🔍 Gathering initial information and evidence...",
            2: "✅ Validating findings and fact-checking...",
            3: "❓ Filling knowledge gaps with targeted research...",
            4: "⚖️  Conducting comparative analysis of options...",
            5: "🧩 Synthesizing insights from all research...",
            6: "🎯 Generating final conclusions and recommendations..."
        }
        
        print(f"   {messages.get(stage_num, 'Processing...')}")
