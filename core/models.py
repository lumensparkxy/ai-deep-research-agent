"""
Pydantic models for Deep Research Agent.
Defines the data structures for research findings, stages, and results.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class Evidence(BaseModel):
    """Evidence supporting a finding."""
    source_description: str
    reliability_score: float = Field(ge=0.0, le=1.0)
    extracted_text: str
    relevance_score: float = Field(ge=0.0, le=1.0)

class ResearchFinding(BaseModel):
    """Base class for research findings."""
    summary: str
    raw_response: Optional[str] = None

class Stage1Findings(ResearchFinding):
    """Findings from Information Gathering stage."""
    key_facts: List[str] = Field(default_factory=list)
    evidence: List[Evidence] = Field(default_factory=list)
    gaps_identified: List[str] = Field(default_factory=list)
    research_areas: List[str] = Field(default_factory=list)

class Stage2Findings(ResearchFinding):
    """Findings from Validation stage."""
    validated_facts: List[str] = Field(default_factory=list)
    questionable_information: List[str] = Field(default_factory=list)
    additional_gaps: List[str] = Field(default_factory=list)
    reliability_assessment: Dict[str, Any] = Field(default_factory=dict)

class GapResponse(BaseModel):
    """Response to a specific knowledge gap."""
    gap: str
    findings: str
    confidence: float = Field(ge=0.0, le=1.0)

class Stage3Findings(ResearchFinding):
    """Findings from Clarification stage."""
    gap_responses: List[GapResponse] = Field(default_factory=list)
    additional_evidence: List[Evidence] = Field(default_factory=list)
    remaining_gaps: List[str] = Field(default_factory=list)

class Option(BaseModel):
    """An option identified in comparative analysis."""
    option: str
    description: str
    pros: List[str] = Field(default_factory=list)
    cons: List[str] = Field(default_factory=list)
    score: float = Field(ge=0.0, le=1.0)

class Stage4Findings(ResearchFinding):
    """Findings from Comparative Analysis stage."""
    options_identified: List[Option] = Field(default_factory=list)
    comparison_criteria: List[str] = Field(default_factory=list)
    comparison_matrix: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    standout_recommendations: List[str] = Field(default_factory=list)

class DecisionFactor(BaseModel):
    """Factor influencing the decision."""
    factor: str
    importance: str
    evidence_strength: str

class Stage5Findings(ResearchFinding):
    """Findings from Synthesis stage."""
    key_insights: List[str] = Field(default_factory=list)
    patterns_identified: List[str] = Field(default_factory=list)
    confidence_assessment: Dict[str, Any] = Field(default_factory=dict)
    decision_factors: List[DecisionFactor] = Field(default_factory=list)

class Recommendation(BaseModel):
    """Specific recommendation."""
    recommendation: str
    reasoning: str
    priority: str
    confidence: float = Field(ge=0.0, le=1.0)

class ImplementationStep(BaseModel):
    """Step in implementation plan."""
    step: str
    description: str
    timeline: str

class Risk(BaseModel):
    """Risk assessment item."""
    risk: str
    likelihood: str
    impact: str
    mitigation: str

class Stage6Findings(ResearchFinding):
    """Findings from Final Conclusions stage."""
    primary_recommendation: str
    recommendations: List[Recommendation] = Field(default_factory=list)
    implementation_plan: List[ImplementationStep] = Field(default_factory=list)
    risk_assessment: List[Risk] = Field(default_factory=list)
    success_metrics: List[str] = Field(default_factory=list)
    confidence_factors: List[str] = Field(default_factory=list)

class ResearchStageResult(BaseModel):
    """Result of a single research stage."""
    stage: int
    name: str
    findings: Dict[str, Any]  # Can be one of the specific finding types
    timestamp: datetime = Field(default_factory=datetime.now)
    error: Optional[str] = None

class KnowledgeBase(BaseModel):
    """Accumulated knowledge."""
    entities: List[str] = Field(default_factory=list)
    relationships: List[str] = Field(default_factory=list)
    key_facts: List[str] = Field(default_factory=list)

class ResearchResult(BaseModel):
    """Final result of the research process."""
    stages: List[ResearchStageResult] = Field(default_factory=list)
    final_conclusions: Optional[Stage6Findings] = None
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    knowledge_base: KnowledgeBase = Field(default_factory=KnowledgeBase)
