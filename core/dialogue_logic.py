"""
Multi-Turn Dialogue Logic for AI-Driven Conversation System

This module provides sophisticated conversation management that maintains coherence,
builds context progressively, and handles complex dialogue scenarios using pure AI intelligence.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

from config.settings import get_settings
from core.conversation_state import ConversationState, QuestionAnswer


@dataclass
class ConversationThread:
    """Represents a coherent thread of conversation"""
    thread_id: str
    topic: str
    questions: List[QuestionAnswer] = field(default_factory=list)
    coherence_score: float = 1.0
    last_updated: datetime = field(default_factory=datetime.now)
    
    def add_qa(self, qa: QuestionAnswer):
        """Add question-answer pair to thread"""
        self.questions.append(qa)
        self.last_updated = datetime.now()


@dataclass 
class DialogueInsights:
    """AI-generated insights about the conversation state"""
    conversation_assessment: str           # AI's assessment of conversation flow
    coherence_analysis: str               # How well conversation flows
    topic_shifts: List[str]               # Detected topic changes
    contradictions: List[str]             # Conflicting information
    information_gaps: List[str]           # What's still missing
    next_question_guidance: str           # AI guidance for next question
    conversation_quality: float          # Overall quality score (0-1)
    suggested_approach: str               # Recommended conversation approach


class DialogueStateManager:
    """
    AI-first dialogue state management that maintains conversation coherence
    and builds context progressively without rigid rules.
    """
    
    def __init__(self, gemini_client, conversation_state: ConversationState):
        self.gemini_client = gemini_client
        self.conversation_state = conversation_state
        self.settings = get_settings()
        self.logger = logging.getLogger(__name__)
        self.conversation_threads: List[ConversationThread] = []
        
    def analyze_conversation_state(self) -> DialogueInsights:
        """
        Use AI to analyze current conversation state and provide insights
        for maintaining coherent dialogue flow.
        """
        try:
            # Create comprehensive prompt for conversation analysis
            analysis_prompt = self._create_conversation_analysis_prompt()
            
            # Get AI analysis
            response = self.gemini_client.generate_content(analysis_prompt)
            raw_analysis = response.text.strip()
            
            # Extract structured insights
            insights = self._extract_dialogue_insights(raw_analysis)
            
            return insights
            
        except Exception as e:
            self.logger.error(f"Conversation analysis failed: {e}")
            return self._create_fallback_insights()
    
    def track_conversation_thread(self, question: str, response: str) -> ConversationThread:
        """
        Track conversation threads using AI to understand topic coherence
        """
        from core.conversation_state import QuestionType
        
        qa = QuestionAnswer(
            question=question,
            answer=response,
            question_type=QuestionType.FOLLOW_UP,
            category="dialogue",
            timestamp=datetime.now(),
            context={}
        )
        
        # Add to conversation state
        self.conversation_state.question_history.append(qa)
        
        # Use AI to determine if this continues existing thread or starts new one
        thread = self._determine_conversation_thread(qa)
        thread.add_qa(qa)
        
        return thread
    
    def generate_coherent_followup(self, context: Dict[str, Any] = None) -> str:
        """
        Generate a coherent follow-up question that builds on the conversation naturally
        """
        try:
            followup_prompt = self._create_followup_generation_prompt(context)
            
            response = self.gemini_client.generate_content(followup_prompt)
            question = response.text.strip()
            
            # Clean up the question (remove any formatting)
            question = self._clean_generated_question(question)
            
            return question
            
        except Exception as e:
            self.logger.error(f"Follow-up generation failed: {e}")
            # Generate a more contextual fallback based on conversation state
            return self._generate_contextual_fallback_question()
    
    def detect_conversation_issues(self) -> List[str]:
        """
        Use AI to detect conversation issues like contradictions, drift, or confusion
        """
        try:
            if len(self.conversation_state.question_history) < 2:
                return []
            
            issues_prompt = self._create_issues_detection_prompt()
            
            response = self.gemini_client.generate_content(issues_prompt)
            analysis = response.text.strip()
            
            # Extract specific issues
            issues = self._extract_conversation_issues(analysis)
            
            return issues
            
        except Exception as e:
            self.logger.error(f"Issues detection failed: {e}")
            return []
    
    def generate_clarification_question(self, issue: str) -> str:
        """
        Generate a clarification question to resolve conversation issues
        """
        try:
            clarification_prompt = f"""
Based on this conversation context, generate a natural clarification question to resolve this issue:

CONVERSATION HISTORY:
{self._format_conversation_history()}

ISSUE TO RESOLVE:
{issue}

Generate a question that:
1. Addresses the issue naturally
2. Doesn't make the user feel confused or questioned
3. Helps clarify without being confrontational
4. Maintains conversation flow

CLARIFICATION QUESTION:
"""
            
            response = self.gemini_client.generate_content(clarification_prompt)
            question = response.text.strip()
            
            return self._clean_generated_question(question)
            
        except Exception as e:
            self.logger.error(f"Clarification generation failed: {e}")
            return "I want to make sure I understand correctly - could you help me clarify something?"
    
    def assess_conversation_completeness(self) -> Tuple[bool, float, str]:
        """
        Use AI to assess if conversation has gathered sufficient information
        Returns: (is_complete, confidence_score, reasoning)
        """
        try:
            completeness_prompt = self._create_completeness_assessment_prompt()
            
            response = self.gemini_client.generate_content(completeness_prompt)
            analysis = response.text.strip()
            
            # Extract completeness assessment
            is_complete, confidence, reasoning = self._extract_completeness_assessment(analysis)
            
            return is_complete, confidence, reasoning
            
        except Exception as e:
            self.logger.error(f"Completeness assessment failed: {e}")
            return False, 0.3, "Unable to assess conversation completeness"
    
    def _create_conversation_analysis_prompt(self) -> str:
        """Create prompt for comprehensive conversation analysis"""
        
        conversation_history = self._format_conversation_history()
        user_profile = self._format_user_profile()
        
        prompt = f"""
Analyze this ongoing conversation to understand its flow, coherence, and next steps:

CONVERSATION HISTORY:
{conversation_history}

CURRENT USER UNDERSTANDING:
{user_profile}

CONVERSATION GAPS:
{', '.join(self.conversation_state.information_gaps)}

Analyze this conversation and provide insights on:

1. CONVERSATION FLOW: How well does the conversation flow? Are questions building logically?

2. COHERENCE ANALYSIS: Are we maintaining a coherent thread of inquiry?

3. TOPIC MANAGEMENT: Have there been any topic shifts? How are we handling them?

4. CONTRADICTION DETECTION: Any conflicting information from the user?

5. INFORMATION GAPS: What important information is still missing?

6. NEXT QUESTION GUIDANCE: What should the next question focus on?

7. CONVERSATION QUALITY: Rate the overall conversation quality (0-10).

8. SUGGESTED APPROACH: How should we approach the next part of the conversation?

Provide practical insights for maintaining intelligent dialogue flow.

ANALYSIS:
"""
        return prompt
    
    def _create_followup_generation_prompt(self, context: Dict[str, Any] = None) -> str:
        """Create prompt for generating coherent follow-up questions"""
        
        conversation_history = self._format_conversation_history()
        last_qa = self.conversation_state.question_history[-1] if self.conversation_state.question_history else None
        
        context_info = ""
        if context:
            context_info = f"ADDITIONAL CONTEXT:\n{context}\n\n"
        
        prompt = f"""
Generate the next question in this conversation that builds naturally on what we've learned:

{context_info}CONVERSATION SO FAR:
{conversation_history}

CURRENT UNDERSTANDING:
{self._format_user_profile()}

INFORMATION STILL NEEDED:
{', '.join(self.conversation_state.information_gaps)}

Generate a question that:
1. Builds naturally on the last response
2. Gathers valuable missing information
3. Feels like expert consultation
4. Maintains conversation momentum
5. Shows understanding of their responses

Focus on the most important information gap while maintaining natural flow.

NEXT QUESTION:
"""
        return prompt
    
    def _create_issues_detection_prompt(self) -> str:
        """Create prompt for detecting conversation issues"""
        
        conversation_history = self._format_conversation_history()
        
        prompt = f"""
Analyze this conversation for potential issues that might need clarification:

CONVERSATION HISTORY:
{conversation_history}

Look for:
1. CONTRADICTIONS: Has the user given conflicting information?
2. AMBIGUITY: Are any responses unclear or could be interpreted multiple ways?
3. TOPIC DRIFT: Has the conversation drifted from the original intent?
4. CONFUSION SIGNALS: Does the user seem confused or uncertain?
5. INCOMPLETE RESPONSES: Are there responses that need follow-up?

For each issue found, explain it clearly and briefly.

ISSUES ANALYSIS:
"""
        return prompt
    
    def _create_completeness_assessment_prompt(self) -> str:
        """Create prompt for assessing conversation completeness"""
        
        conversation_history = self._format_conversation_history()
        user_profile = self._format_user_profile()
        
        prompt = f"""
Assess whether we have sufficient information to provide quality research:

CONVERSATION HISTORY:
{conversation_history}

CURRENT UNDERSTANDING:
{user_profile}

REMAINING GAPS:
{', '.join(self.conversation_state.information_gaps)}

Assess:
1. Do we understand their core needs and priorities?
2. Do we have sufficient context for quality research?
3. Are there critical gaps that would significantly impact research quality?
4. Would additional questions provide meaningful value?

Provide assessment in this format:
COMPLETE: Yes/No
CONFIDENCE: 0.0-1.0
REASONING: Brief explanation of assessment

ASSESSMENT:
"""
        return prompt
    
    def _determine_conversation_thread(self, qa: QuestionAnswer) -> ConversationThread:
        """Use AI to determine which conversation thread this QA belongs to"""
        try:
            # Simple logic for now - could be enhanced with AI topic analysis
            if not self.conversation_threads:
                # Create first thread
                thread = ConversationThread(
                    thread_id="main_001",
                    topic="primary_inquiry"
                )
                self.conversation_threads.append(thread)
                return thread
            else:
                # For now, use the most recent thread
                # In future, could use AI to determine topic similarity
                return self.conversation_threads[-1]
                
        except Exception as e:
            self.logger.error(f"Thread determination failed: {e}")
            # Return main thread as fallback
            if not self.conversation_threads:
                thread = ConversationThread(thread_id="main_fallback", topic="general")
                self.conversation_threads.append(thread)
            return self.conversation_threads[0]
    
    def _extract_dialogue_insights(self, analysis: str) -> DialogueInsights:
        """Extract structured insights from AI analysis"""
        try:
            # Use AI to extract structured data
            extraction_prompt = f"""
Extract key insights from this conversation analysis and format as structured data:

ANALYSIS:
{analysis}

Extract:
- Conversation assessment summary
- Coherence analysis
- Topic shifts (if any)
- Contradictions (if any) 
- Information gaps
- Next question guidance
- Quality score (0-1)
- Suggested approach

Format as natural text sections, not JSON.

STRUCTURED INSIGHTS:
"""
            
            response = self.gemini_client.generate_content(extraction_prompt)
            structured_text = response.text.strip()
            
            # Parse the structured response
            return self._parse_dialogue_insights(structured_text)
            
        except Exception as e:
            self.logger.warning(f"Could not extract dialogue insights: {e}")
            return self._create_fallback_insights()
    
    def _parse_dialogue_insights(self, text: str) -> DialogueInsights:
        """Parse dialogue insights from structured text"""
        # Simple parsing - could be enhanced
        lines = text.split('\n')
        
        insights = DialogueInsights(
            conversation_assessment="Ongoing conversation analysis",
            coherence_analysis="Maintaining coherent flow",
            topic_shifts=[],
            contradictions=[],
            information_gaps=self.conversation_state.information_gaps.copy(),
            next_question_guidance="Continue gathering key information",
            conversation_quality=0.7,
            suggested_approach="consultative"
        )
        
        # Extract specific insights from text
        for line in lines:
            line = line.strip().lower()
            if 'contradiction' in line and 'none' not in line:
                insights.contradictions.append(line)
            elif 'topic shift' in line and 'none' not in line:
                insights.topic_shifts.append(line)
        
        return insights
    
    def _extract_conversation_issues(self, analysis: str) -> List[str]:
        """Extract specific conversation issues from analysis"""
        issues = []
        lines = analysis.split('\n')
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith('ISSUES') and not line.startswith('Look for'):
                if any(keyword in line.lower() for keyword in ['contradiction', 'ambiguity', 'drift', 'confusion', 'incomplete']):
                    issues.append(line)
        
        return issues
    
    def _extract_completeness_assessment(self, analysis: str) -> Tuple[bool, float, str]:
        """Extract completeness assessment from AI analysis"""
        lines = analysis.split('\n')
        
        is_complete = False
        confidence = 0.5
        reasoning = "Standard assessment"
        
        for line in lines:
            line = line.strip()
            if line.startswith('COMPLETE:'):
                is_complete = 'yes' in line.lower()
            elif line.startswith('CONFIDENCE:'):
                try:
                    confidence = float(line.split(':')[1].strip())
                except:
                    confidence = 0.5
            elif line.startswith('REASONING:'):
                reasoning = line.split(':', 1)[1].strip()
        
        return is_complete, confidence, reasoning
    
    def _format_conversation_history(self) -> str:
        """Format conversation history for prompts"""
        if not self.conversation_state.question_history:
            return "No conversation history yet."
        
        formatted = []
        for i, qa in enumerate(self.conversation_state.question_history[-5:], 1):  # Last 5 QAs
            formatted.append(f"Q{i}: {qa.question}")
            formatted.append(f"A{i}: {qa.answer}")
            formatted.append("")
        
        return "\n".join(formatted)
    
    def _format_user_profile(self) -> str:
        """Format current user profile understanding"""
        if not self.conversation_state.user_profile:
            return "No user profile information yet."
        
        formatted = []
        for key, value in self.conversation_state.user_profile.items():
            formatted.append(f"- {key}: {value}")
        
        return "\n".join(formatted)
    
    def _clean_generated_question(self, question: str) -> str:
        """Clean up AI-generated questions"""
        # Remove common AI response prefixes
        prefixes_to_remove = [
            "NEXT QUESTION:",
            "Question:",
            "CLARIFICATION QUESTION:",
            "Here's a question:",
            "I would ask:"
        ]
        
        for prefix in prefixes_to_remove:
            if question.startswith(prefix):
                question = question[len(prefix):].strip()
        
        # Ensure question ends with question mark
        if question and not question.endswith('?'):
            question += '?'
        
        return question
    
    def _create_fallback_insights(self) -> DialogueInsights:
        """Create fallback insights when AI analysis fails"""
        return DialogueInsights(
            conversation_assessment="Basic conversation flow maintained",
            coherence_analysis="Conversation proceeding normally",
            topic_shifts=[],
            contradictions=[],
            information_gaps=self.conversation_state.information_gaps.copy(),
            next_question_guidance="Continue with standard information gathering",
            conversation_quality=0.6,
            suggested_approach="standard consultative approach"
        )
    
    def _generate_contextual_fallback_question(self) -> str:
        """Generate a contextual fallback question based on conversation history"""
        # Analyze conversation length to determine appropriate fallback
        question_count = len(self.conversation_state.question_history)
        
        if question_count == 0:
            return "What brings you to look into this today?"
        elif question_count < 3:
            return "What specific aspects are you most curious about?"
        elif question_count < 5:
            return "Are there any particular requirements I should keep in mind?"
        else:
            return "What other factors should I consider for your situation?"
