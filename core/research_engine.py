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

from google import genai
from google.genai import types
from rich.console import Console
from rich.panel import Panel

from config.settings import Settings
from utils.session_manager import SessionManager
from utils.validators import InputValidator, ValidationError
from utils.cache_manager import CacheManager
from core.models import (
    ResearchResult, ResearchStageResult, KnowledgeBase,
    Stage1Findings, Stage2Findings, Stage3Findings,
    Stage4Findings, Stage5Findings, Stage6Findings
)
from core.prompts import PromptManager
from core.exceptions import GeminiAPIError, ResearchStageError


class ResearchEngine:
    """AI-powered research engine with 6-stage iterative process."""
    
    def __init__(self, settings: Settings):
        """Initialize research engine with Gemini AI."""
        self.settings = settings
        self.session_manager = SessionManager(settings)
        self.validator = InputValidator(settings)
        self.logger = logging.getLogger(__name__)
        self.cache_manager = CacheManager(settings.cache_dir, settings.cache_enabled)
        self.prompt_manager = PromptManager(settings)
        self.console = Console()
        
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
            # Create Gemini client with API key
            self.client = genai.Client(api_key=self.settings.gemini_api_key)
            
            # Store model name for use in requests
            self.model_name = self.settings.ai_model
            
            self.logger.info(f"Initialized Gemini client with model: {self.model_name}")
            
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
            Complete research results (as a dictionary for compatibility)
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
        
        # Initialize research state using Pydantic model
        research_result = ResearchResult()
        
        # Keep a local state for passing between stages (legacy support/ease of use)
        research_state = {
            "query": query,
            "context": context,
            "session_id": session_id,
            "stages": [], # Will be populated with dicts for compatibility
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
                    stage_findings = stage_method(research_state)
                    
                    # Create stage result
                    stage_result = ResearchStageResult(
                        stage=stage_num,
                        name=stage_name,
                        findings=stage_findings["findings"]
                    )
                    
                    # Add to result model
                    research_result.stages.append(stage_result)
                    
                    # Update legacy state
                    research_state["stages"].append(stage_result.model_dump())
                    
                    # Update session with stage progress
                    self.session_manager.update_session_stage(session_id, stage_result.model_dump())
                    
                    # Add small delay to respect rate limits
                    time.sleep(self.settings.rate_limit_delay)
                    
                except Exception as e:
                    self.logger.error(f"Error in Stage {stage_num}: {e}")
                    # Continue with degraded functionality
                    fallback_result = ResearchStageResult(
                        stage=stage_num,
                        name=stage_name,
                        findings={
                            "summary": f"Stage {stage_num} encountered an error but research continues",
                            "evidence": [],
                            "gaps_identified": [f"Error in {stage_name}: {str(e)}"]
                        },
                        error=str(e)
                    )
                    research_result.stages.append(fallback_result)
                    research_state["stages"].append(fallback_result.model_dump())
            
            # Calculate overall confidence score
            confidence_score = self._calculate_confidence_score(research_state)
            research_result.confidence_score = confidence_score
            
            # Set final conclusions
            if research_result.stages:
                last_stage = research_result.stages[-1]
                # Convert findings to Stage6Findings if possible, or just use the dict
                research_result.final_conclusions = last_stage.findings
            
            # Prepare final results dict
            final_results = research_result.model_dump()
            
            # Update session with final results
            self.session_manager.update_session_conclusions(
                session_id, final_results.get("final_conclusions", {}), confidence_score
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
        
        # Build context-aware prompt using PromptManager
        prompt = self.prompt_manager.get_stage_1_prompt(query, context)
        
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
        
        prompt = self.prompt_manager.get_stage_2_prompt(research_state["query"], previous_findings)
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
        
        prompt = self.prompt_manager.get_stage_3_prompt(research_state["query"], gaps)
        response = self._call_gemini_with_retry(prompt)
        findings = self._parse_clarification_response(response)
        
        return {
            "findings": findings
        }
    
    def _stage_4_comparative_analysis(self, research_state: Dict[str, Any]) -> Dict[str, Any]:
        """Stage 4: Systematic comparison of options."""
        all_findings = [stage["findings"] for stage in research_state["stages"]]
        
        prompt = self.prompt_manager.get_stage_4_prompt(research_state["query"], all_findings, research_state["context"])
        response = self._call_gemini_with_retry(prompt)
        findings = self._parse_comparative_analysis_response(response)
        
        return {
            "findings": findings
        }
    
    def _stage_5_synthesis(self, research_state: Dict[str, Any]) -> Dict[str, Any]:
        """Stage 5: Synthesis and integration."""
        all_findings = [stage["findings"] for stage in research_state["stages"]]
        
        prompt = self.prompt_manager.get_stage_5_prompt(research_state["query"], all_findings)
        response = self._call_gemini_with_retry(prompt)
        findings = self._parse_synthesis_response(response)
        
        return {
            "findings": findings
        }
    
    def _stage_6_final_conclusions(self, research_state: Dict[str, Any]) -> Dict[str, Any]:
        """Stage 6: Final conclusions and recommendations."""
        all_findings = [stage["findings"] for stage in research_state["stages"]]
        context = research_state["context"]
        
        prompt = self.prompt_manager.get_stage_6_prompt(research_state["query"], all_findings, context)
        response = self._call_gemini_with_retry(prompt)
        findings = self._parse_final_conclusions_response(response)
        
        return {
            "findings": findings
        }
    
    def _call_gemini_with_retry(self, prompt: str, max_retries: int = None) -> str:
        """Call Gemini API with retry logic."""
        # Check cache first
        cache_key = f"{self.model_name}:{prompt}"
        cached_response = self.cache_manager.get(cache_key)
        if cached_response:
            return cached_response

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
                # Configure tools (Google Search Grounding)
                tools = None
                if self.settings.enable_search or self.settings.enable_grounding:
                    tools = [types.Tool(google_search=types.GoogleSearch())]

                # Use new google-genai client API with safety settings
                config = types.GenerateContentConfig(
                    safety_settings=[
                        types.SafetySetting(
                            category='HARM_CATEGORY_HATE_SPEECH',
                            threshold='BLOCK_MEDIUM_AND_ABOVE',
                        ),
                        types.SafetySetting(
                            category='HARM_CATEGORY_DANGEROUS_CONTENT',
                            threshold='BLOCK_MEDIUM_AND_ABOVE',
                        ),
                        types.SafetySetting(
                            category='HARM_CATEGORY_SEXUALLY_EXPLICIT',
                            threshold='BLOCK_MEDIUM_AND_ABOVE',
                        ),
                        types.SafetySetting(
                            category='HARM_CATEGORY_HARASSMENT',
                            threshold='BLOCK_MEDIUM_AND_ABOVE',
                        )
                    ],
                    tools=tools
                )
                
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=config
                )
                
                if response.text:
                    # Cache the successful response
                    self.cache_manager.set(cache_key, response.text)
                    return response.text
                # Empty response is a terminal validation error
                raise GeminiAPIError("Empty response from Gemini")
            except GeminiAPIError:
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
                    raise GeminiAPIError(f"Gemini API failed after {max_retries} attempts: {e}")
    
    # Note: _build_stage_X_prompt methods have been moved to PromptManager
    
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
        
        # Stage-specific messages
        messages = {
            1: "🔍 Gathering initial information and evidence...",
            2: "✅ Validating findings and fact-checking...",
            3: "❓ Filling knowledge gaps with targeted research...",
            4: "⚖️  Conducting comparative analysis of options...",
            5: "🧩 Synthesizing insights from all research...",
            6: "🎯 Generating final conclusions and recommendations..."
        }
        
        message = messages.get(stage_num, 'Processing...')
        
        # Use rich panel for better visibility
        self.console.print()
        self.console.print(Panel(
            f"[bold cyan]STAGE {stage_num}/{total_stages}:[/bold cyan] {stage_name}\n"
            f"[italic]{message}[/italic]",
            title=f"Research Progress: {int(progress*100)}%",
            border_style="blue"
        ))
