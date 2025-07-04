"""
AI Question Generator Foundation for Deep Research Agent
Gemini-powered question generation system for dynamic, context-aware conversations.
"""

import json
import logging
import asyncio
import time
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum

from google import genai
from google.genai import types

from .conversation_state import ConversationState, QuestionType, ConversationMode


class IntentType(Enum):
    """Types of user intents for question generation."""
    RESEARCH = "research"
    PURCHASE = "purchase"
    LEARNING = "learning"
    COMPARISON = "comparison"
    TROUBLESHOOTING = "troubleshooting"
    RECOMMENDATION = "recommendation"
    EXPLORATION = "exploration"


@dataclass
class IntentAnalysis:
    """Result of user intent analysis."""
    primary_intent: IntentType
    confidence: float
    context_keywords: List[str]
    domain: str
    urgency_level: float  # 0.0-1.0
    specificity_level: float  # 0.0-1.0
    reasoning: str


@dataclass
class GeneratedQuestion:
    """A single generated question with metadata."""
    question: str
    question_type: QuestionType
    category: str
    priority: float  # 0.0-1.0
    context_relevance: float  # 0.0-1.0
    expected_answer_type: str  # 'text', 'choice', 'scale', 'boolean'
    follow_up_potential: float  # 0.0-1.0
    reasoning: str


@dataclass
class QuestionGenerationResult:
    """Result of question generation process."""
    questions: List[GeneratedQuestion]
    intent_analysis: IntentAnalysis
    conversation_context: Dict[str, Any]
    generation_confidence: float
    recommended_next_questions: List[str]


class AIQuestionGenerator:
    """AI-powered question generation system using Gemini API."""
    
    def __init__(self, gemini_client: Optional[genai.Client] = None, model_name: str = "gemini-2.5-flash", settings: Optional[Any] = None):
        """
        Initialize the AI question generator.
        
        Args:
            gemini_client: Configured Gemini client for AI analysis
            model_name: Name of the Gemini model to use for generation
            settings: Configuration settings for question generation
        """
        self.logger = logging.getLogger(__name__)
        self.gemini_client = gemini_client
        self.model_name = model_name
        
        # Load settings if provided
        if settings and hasattr(settings, 'ai_question_generation'):
            ai_settings = settings.ai_question_generation
            self.max_tokens = ai_settings.max_tokens
            self.temperature = ai_settings.temperature
            self.top_p = ai_settings.top_p
        else:
            # Default settings for highly engaging, creative questions
            self.max_tokens = 4000  # Increased for more detailed responses
            self.temperature = 0.9  # Higher temperature for more creativity
            self.top_p = 0.95  # Even more diverse vocabulary
        
        # Generation settings
        self.max_questions_per_request = 5
        self.min_question_priority = 0.3
        self.api_retry_attempts = 3
        self.api_retry_delay = 1.0
        
        # Cache for frequently used prompts and responses
        self._prompt_cache: Dict[str, str] = {}
        self._response_cache: Dict[str, Any] = {}
        self._cache_ttl = 300  # 5 minutes
        self._cache_timestamps: Dict[str, float] = {}
    
    async def generate_questions(
        self, 
        conversation_state: ConversationState,
        max_questions: int = 3,
        focus_areas: Optional[List[str]] = None
    ) -> QuestionGenerationResult:
        """
        Generate contextually relevant questions based on conversation state.
        
        Args:
            conversation_state: Current conversation state
            max_questions: Maximum number of questions to generate
            focus_areas: Specific areas to focus question generation on
            
        Returns:
            QuestionGenerationResult with generated questions and analysis
        """
        try:
            self.logger.debug(f"Generating questions for session: {conversation_state.session_id}")
            
            # Analyze user intent first
            intent_analysis = await self._analyze_user_intent(
                conversation_state.user_query,
                conversation_state.user_profile
            )
            
            # Generate questions based on intent and context
            questions = await self._generate_contextual_questions(
                conversation_state,
                intent_analysis,
                max_questions,
                focus_areas
            )
            
            # Score and prioritize questions
            prioritized_questions = self._prioritize_questions(
                questions, 
                conversation_state,
                intent_analysis
            )
            
            # Select best questions
            selected_questions = prioritized_questions[:max_questions]
            
            # Generate recommended follow-ups
            follow_ups = self._generate_follow_up_recommendations(
                selected_questions,
                conversation_state
            )
            
            # Calculate generation confidence
            confidence = self._calculate_generation_confidence(
                selected_questions,
                intent_analysis,
                conversation_state
            )
            
            result = QuestionGenerationResult(
                questions=selected_questions,
                intent_analysis=intent_analysis,
                conversation_context=self._extract_context_summary(conversation_state),
                generation_confidence=confidence,
                recommended_next_questions=follow_ups
            )
            
            self.logger.info(f"Generated {len(selected_questions)} questions with {confidence:.2f} confidence")
            return result
            
        except Exception as e:
            self.logger.error(f"Error generating questions: {e}")
            return self._create_fallback_questions(conversation_state)
    
    async def analyze_intent(self, user_query: str, context: Dict[str, Any] = None) -> IntentAnalysis:
        """
        Analyze user intent from query and context.
        
        Args:
            user_query: User's initial query
            context: Additional context information
            
        Returns:
            IntentAnalysis with detected intent and metadata
        """
        return await self._analyze_user_intent(user_query, context or {})
    
    def generate_single_question(
        self,
        category: str,
        context: Dict[str, Any],
        question_type: QuestionType = QuestionType.OPEN_ENDED
    ) -> GeneratedQuestion:
        """
        Generate a single question for a specific category.
        
        Args:
            category: Question category (e.g., 'budget', 'timeline')
            context: Context for question generation
            question_type: Type of question to generate
            
        Returns:
            GeneratedQuestion for the specified category
        """
        # Use rule-based generation for single questions
        return self._generate_rule_based_question(category, context, question_type)
    
    async def _analyze_user_intent(self, user_query: str, context: Dict[str, Any]) -> IntentAnalysis:
        """Analyze user intent using AI."""
        try:
            if not self.gemini_client:
                return self._analyze_intent_rule_based(user_query, context)
            
            # Check cache first
            cache_key = f"intent_{hash(user_query)}"
            if self._is_cache_valid(cache_key):
                return self._response_cache[cache_key]
            
            # Create intent analysis prompt
            prompt = self._create_intent_analysis_prompt(user_query, context)
            
            # Query Gemini with retry logic
            response = await self._query_gemini_with_retry(prompt)
            
            # Parse intent analysis
            intent_analysis = self._parse_intent_response(response.text)
            
            # Cache the result
            self._cache_response(cache_key, intent_analysis)
            
            return intent_analysis
            
        except Exception as e:
            self.logger.warning(f"AI intent analysis failed, using fallback: {e}")
            return self._analyze_intent_rule_based(user_query, context)
    
    async def _generate_contextual_questions(
        self,
        conversation_state: ConversationState,
        intent_analysis: IntentAnalysis,
        max_questions: int,
        focus_areas: Optional[List[str]]
    ) -> List[GeneratedQuestion]:
        """Generate questions using AI based on context."""
        try:
            if not self.gemini_client:
                return self._generate_questions_rule_based(
                    conversation_state, intent_analysis, max_questions
                )
            
            # Create question generation prompt
            prompt = self._create_question_generation_prompt(
                conversation_state,
                intent_analysis,
                max_questions,
                focus_areas
            )
            
            # Query Gemini
            response = await self._query_gemini_with_retry(prompt)
            
            # Parse generated questions
            questions = self._parse_questions_response(response.text)
            
            return questions
            
        except Exception as e:
            self.logger.warning(f"AI question generation failed, using fallback: {e}")
            return self._generate_questions_rule_based(
                conversation_state, intent_analysis, max_questions
            )
    
    def _prioritize_questions(
        self,
        questions: List[GeneratedQuestion],
        conversation_state: ConversationState,
        intent_analysis: IntentAnalysis
    ) -> List[GeneratedQuestion]:
        """Prioritize questions based on relevance and context."""
        # Score questions based on multiple factors
        for question in questions:
            # Calculate composite priority score
            priority_factors = {
                'base_priority': question.priority,
                'context_relevance': question.context_relevance,
                'intent_alignment': self._calculate_intent_alignment(question, intent_analysis),
                'conversation_flow': self._calculate_flow_score(question, conversation_state),
                'information_gap': self._calculate_gap_score(question, conversation_state)
            }
            
            # Weighted combination
            final_priority = (
                priority_factors['base_priority'] * 0.25 +
                priority_factors['context_relevance'] * 0.25 +
                priority_factors['intent_alignment'] * 0.20 +
                priority_factors['conversation_flow'] * 0.15 +
                priority_factors['information_gap'] * 0.15
            )
            
            question.priority = final_priority
        
        # Sort by priority (highest first)
        return sorted(questions, key=lambda q: q.priority, reverse=True)
    
    def _calculate_generation_confidence(
        self,
        questions: List[GeneratedQuestion],
        intent_analysis: IntentAnalysis,
        conversation_state: ConversationState
    ) -> float:
        """Calculate confidence in the generated questions."""
        if not questions:
            return 0.0
        
        # Factors affecting confidence
        avg_question_priority = sum(q.priority for q in questions) / len(questions)
        intent_confidence = intent_analysis.confidence
        context_richness = min(1.0, len(conversation_state.user_profile) / 5)
        
        # Weighted combination
        confidence = (
            avg_question_priority * 0.4 +
            intent_confidence * 0.3 +
            context_richness * 0.3
        )
        
        return min(1.0, max(0.0, confidence))
    
    async def _query_gemini_with_retry(self, prompt: str) -> Any:
        """Query Gemini with retry logic."""
        for attempt in range(self.api_retry_attempts):
            try:
                # Create generation config with maximum creative freedom
                generation_config = {
                    'max_output_tokens': self.max_tokens,
                    'temperature': self.temperature,
                    'top_p': self.top_p,
                    'candidate_count': 1,  # Single response but highly creative
                    'stop_sequences': None,  # No stop sequences to limit creativity
                }
                
                # Use the new google-genai client API
                if hasattr(self.gemini_client, 'aio'):
                    # Async call
                    response = await self.gemini_client.aio.models.generate_content(
                        model=self.model_name,
                        contents=prompt,
                        config=types.GenerateContentConfig(**generation_config)
                    )
                else:
                    # Sync call wrapped in async
                    response = self.gemini_client.models.generate_content(
                        model=self.model_name,
                        contents=prompt,
                        config=types.GenerateContentConfig(**generation_config)
                    )
                return response
                
            except Exception as e:
                self.logger.warning(f"Gemini API attempt {attempt + 1} failed: {e}")
                if attempt < self.api_retry_attempts - 1:
                    await asyncio.sleep(self.api_retry_delay * (attempt + 1))
                else:
                    raise
    
    def _create_intent_analysis_prompt(self, user_query: str, context: Dict[str, Any]) -> str:
        """Create prompt for intent analysis."""
        context_str = json.dumps(context, indent=2) if context else "None"
        
        return f"""Analyze the user's intent and context from their query:

USER QUERY: {user_query}
EXISTING CONTEXT: {context_str}

Analyze and respond with JSON containing:
1. primary_intent: one of [research, purchase, learning, comparison, troubleshooting, recommendation, exploration]
2. confidence: 0.0-1.0 confidence in intent classification
3. context_keywords: list of key terms that indicate intent
4. domain: the subject domain (e.g., "technology", "health", "finance")
5. urgency_level: 0.0-1.0 how urgent the request seems
6. specificity_level: 0.0-1.0 how specific vs. general the request is
7. reasoning: brief explanation of the analysis

Example response:
{{
  "primary_intent": "purchase",
  "confidence": 0.85,
  "context_keywords": ["best", "laptop", "programming", "budget"],
  "domain": "technology",
  "urgency_level": 0.3,
  "specificity_level": 0.7,
  "reasoning": "User is looking to purchase a laptop with specific requirements for programming"
}}"""
    
    def _create_question_generation_prompt(
        self,
        conversation_state: ConversationState,
        intent_analysis: IntentAnalysis,
        max_questions: int,
        focus_areas: Optional[List[str]]
    ) -> str:
        """Create prompt for question generation."""
        context_summary = self._extract_context_summary(conversation_state)
        focus_str = ", ".join(focus_areas) if focus_areas else "understanding their unique situation"
        
        return f"""You are an exceptionally skilled conversation expert who specializes in creating deeply engaging, thought-provoking questions. You're like that friend who asks the most interesting questions at dinner parties - the ones that make people light up and share stories they've never told before.

CONVERSATION CONTEXT:
- User's Original Question: "{conversation_state.user_query}"
- Their Intent: {intent_analysis.primary_intent.value} ({intent_analysis.confidence:.0%} confidence)
- Subject Domain: {intent_analysis.domain}
- What We Already Know: {json.dumps(context_summary, indent=2) if context_summary.get('user_profile') else "This is our first exchange"}
- Current Focus: {focus_str}

YOUR MISSION:
Create {max_questions} absolutely captivating questions that feel like genuine curiosity from someone who truly cares about helping them. These should be the kind of questions that make people think "Wow, that's exactly what I needed to consider!" or "I never thought about it that way before!"

CONVERSATION STYLE TO EMULATE:
Think of yourself as a master consultant who:
- Asks questions that reveal hidden insights and overlooked angles
- Shows genuine fascination with their unique situation  
- Helps people discover things about themselves they didn't know
- Makes complex decisions feel manageable and exciting
- Uses storytelling prompts to unlock rich details
- Connects emotional and practical considerations naturally

QUESTION CRAFTING PRINCIPLES:
✨ **Be Genuinely Curious**: Ask like you're truly fascinated by their story
✨ **Invite Storytelling**: Frame questions to elicit vivid, detailed responses
✨ **Connect Past & Future**: Link their experiences to their aspirations
✨ **Reveal Hidden Factors**: Uncover considerations they might not have thought of
✨ **Make It Personal**: Reference their specific situation, not generic scenarios
✨ **Show Insight**: Demonstrate you understand the deeper implications
✨ **Create Aha Moments**: Ask questions that spark new realizations

EXAMPLES OF ENGAGING VS. BORING:
❌ Boring: "What's your budget?"
✅ Engaging: "I'm curious about the investment side of this - what feels like the sweet spot where you'd be excited about the value you're getting without any buyer's remorse keeping you up at night?"

❌ Boring: "What features do you need?"
✅ Engaging: "Paint me a picture of your ideal experience with this - walk me through what a perfect day using it would look like, from the moment you first interact with it."

❌ Boring: "When do you need this?"
✅ Engaging: "What's the story behind your timing? Is there a particular moment or event that's driving this decision, or is it more of a 'the stars are finally aligning' situation?"

RESPONSE FORMAT:
Generate questions as a JSON array with rich, conversational questions (aim for 25-60 words each to allow for context and nuance):

[
  {{
    "question": "Your beautifully crafted, engaging question here that feels conversational and insightful",
    "question_type": "open_ended",
    "category": "motivation/timeline/preferences/constraints/experience/goals/context/etc",
    "priority": 0.0-1.0,
    "context_relevance": 0.0-1.0,
    "expected_answer_type": "text",
    "follow_up_potential": 0.0-1.0,
    "reasoning": "Why this question creates engagement and reveals important insights"
  }}
]

INSPIRING QUESTION STARTERS TO CONSIDER:
- "I'm really curious about..."
- "What's the story behind..."
- "Paint me a picture of..."
- "I'd love to understand..."
- "What would it feel like if..."
- "Take me back to when..."
- "Imagine if you could..."
- "What's been on your mind about..."
- "If you could wave a magic wand..."
- "What would surprise people to know about..."

Now create {max_questions} questions that will make this person excited to share their story and feel truly understood!"""
    
    def _parse_intent_response(self, response_text: str) -> IntentAnalysis:
        """Parse AI response into IntentAnalysis object."""
        try:
            # Extract JSON from response
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            
            if start == -1 or end == 0:
                raise ValueError("No JSON found in response")
            
            json_text = response_text[start:end]
            data = json.loads(json_text)
            
            return IntentAnalysis(
                primary_intent=IntentType(data.get('primary_intent', 'exploration')),
                confidence=data.get('confidence', 0.5),
                context_keywords=data.get('context_keywords', []),
                domain=data.get('domain', 'general'),
                urgency_level=data.get('urgency_level', 0.5),
                specificity_level=data.get('specificity_level', 0.5),
                reasoning=data.get('reasoning', 'Default intent analysis')
            )
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            self.logger.warning(f"Failed to parse intent response: {e}")
            return self._create_fallback_intent()
    
    def _parse_questions_response(self, response_text: str) -> List[GeneratedQuestion]:
        """Parse AI response into GeneratedQuestion objects."""
        try:
            # Extract JSON array from response
            start = response_text.find('[')
            end = response_text.rfind(']') + 1
            
            if start == -1 or end == 0:
                raise ValueError("No JSON array found in response")
            
            json_text = response_text[start:end]
            questions_data = json.loads(json_text)
            
            questions = []
            for q_data in questions_data:
                question = GeneratedQuestion(
                    question=q_data.get('question', ''),
                    question_type=QuestionType(q_data.get('question_type', 'open_ended')),
                    category=q_data.get('category', 'general'),
                    priority=q_data.get('priority', 0.5),
                    context_relevance=q_data.get('context_relevance', 0.5),
                    expected_answer_type=q_data.get('expected_answer_type', 'text'),
                    follow_up_potential=q_data.get('follow_up_potential', 0.5),
                    reasoning=q_data.get('reasoning', 'Generated question')
                )
                questions.append(question)
            
            return questions
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            self.logger.warning(f"Failed to parse questions response: {e}")
            return []
    
    def _analyze_intent_rule_based(self, user_query: str, context: Dict[str, Any]) -> IntentAnalysis:
        """Fallback rule-based intent analysis."""
        query_lower = user_query.lower()
        
        # Intent classification rules (order matters - more specific first)
        if any(word in query_lower for word in ['research', 'study', 'analyze', 'investigate']):
            intent = IntentType.RESEARCH
            confidence = 0.6
        elif any(word in query_lower for word in ['buy', 'purchase', 'get', 'need']):
            intent = IntentType.PURCHASE
            confidence = 0.7
        elif any(word in query_lower for word in ['learn', 'understand', 'how to', 'explain']):
            intent = IntentType.LEARNING
            confidence = 0.7
        elif any(word in query_lower for word in ['compare', 'vs', 'versus', 'difference']):
            intent = IntentType.COMPARISON
            confidence = 0.8
        elif any(word in query_lower for word in ['recommend', 'suggest', 'best', 'should']):
            intent = IntentType.RECOMMENDATION
            confidence = 0.7
        elif any(word in query_lower for word in ['problem', 'issue', 'fix', 'broken', "won't", "doesn't", "error", "trouble"]):
            intent = IntentType.TROUBLESHOOTING
            confidence = 0.7
        else:
            intent = IntentType.EXPLORATION
            confidence = 0.5
        
        # Extract keywords
        keywords = [word for word in query_lower.split() if len(word) > 3][:5]
        
        # Determine domain
        domain = self._classify_domain(query_lower)
        
        # Calculate urgency and specificity
        urgency = 0.8 if any(word in query_lower for word in ['urgent', 'asap', 'quickly', 'soon']) else 0.3
        specificity = 0.8 if len(keywords) > 3 else 0.4
        
        return IntentAnalysis(
            primary_intent=intent,
            confidence=confidence,
            context_keywords=keywords,
            domain=domain,
            urgency_level=urgency,
            specificity_level=specificity,
            reasoning=f"Rule-based classification as {intent.value}"
        )
    
    def _generate_questions_rule_based(
        self,
        conversation_state: ConversationState,
        intent_analysis: IntentAnalysis,
        max_questions: int
    ) -> List[GeneratedQuestion]:
        """Fallback rule-based question generation."""
        questions = []
        user_profile = conversation_state.user_profile
        
        # Common question templates based on intent
        question_templates = {
            IntentType.PURCHASE: [
                ("What's your budget range?", "budget", 0.9),
                ("When do you need this?", "timeline", 0.8),
                ("What features are most important to you?", "preferences", 0.8),
                ("Are there any constraints or limitations?", "constraints", 0.7),
            ],
            IntentType.LEARNING: [
                ("What's your current experience level?", "expertise", 0.9),
                ("What specific aspects interest you most?", "preferences", 0.8),
                ("How much time can you dedicate to learning?", "timeline", 0.7),
                ("Do you prefer hands-on or theoretical learning?", "learning_style", 0.6),
            ],
            IntentType.RECOMMENDATION: [
                ("What criteria are most important for your decision?", "preferences", 0.9),
                ("What's your experience with similar options?", "expertise", 0.8),
                ("Are there any deal-breakers to avoid?", "constraints", 0.8),
                ("What's your timeline for making this decision?", "timeline", 0.7),
            ]
        }
        
        # Get appropriate templates
        templates = question_templates.get(intent_analysis.primary_intent, question_templates[IntentType.RECOMMENDATION])
        
        # Generate questions from templates
        for question_text, category, priority in templates[:max_questions]:
            # Skip if we already have this information
            if category in user_profile:
                continue
                
            question = GeneratedQuestion(
                question=question_text,
                question_type=QuestionType.OPEN_ENDED,
                category=category,
                priority=priority,
                context_relevance=0.8,
                expected_answer_type="text",
                follow_up_potential=0.6,
                reasoning=f"Rule-based question for {category}"
            )
            questions.append(question)
        
        return questions
    
    def _generate_rule_based_question(
        self,
        category: str,
        context: Dict[str, Any],
        question_type: QuestionType
    ) -> GeneratedQuestion:
        """Generate a single rule-based question."""
        # Question templates by category
        templates = {
            'budget': "What's your budget range for this?",
            'timeline': "What's your timeline for this decision?",
            'expertise': "What's your experience level with this topic?",
            'preferences': "What features or qualities are most important to you?",
            'constraints': "Are there any limitations or requirements we should consider?",
            'goals': "What are you hoping to achieve?",
            'context': "Can you tell me more about how you plan to use this?",
            'background': "What's your background or situation with this topic?"
        }
        
        question_text = templates.get(category, f"Can you tell me more about your {category}?")
        
        return GeneratedQuestion(
            question=question_text,
            question_type=question_type,
            category=category,
            priority=0.7,
            context_relevance=0.8,
            expected_answer_type="text",
            follow_up_potential=0.6,
            reasoning=f"Rule-based question for {category} category"
        )
    
    def _classify_domain(self, query: str) -> str:
        """Classify the domain of the query."""
        import re
        
        domain_keywords = {
            'technology': ['computer', 'software', 'app', 'tech', 'digital', 'programming', 'code', 'laptop'],
            'health': ['health', 'medical', 'doctor', 'medicine', 'fitness', 'diet', 'wellness'],
            'finance': ['money', 'investment', 'bank', 'financial', 'budget', 'cost', 'price'],
            'education': ['learn', 'study', 'course', 'school', 'education', 'training'],
            'travel': ['travel', 'trip', 'vacation', 'flight', 'hotel', 'destination'],
            'home': ['home', 'house', 'furniture', 'appliance', 'garden', 'kitchen', 'room']
        }
        
        # Check each domain with word boundaries for more precise matching
        for domain, keywords in domain_keywords.items():
            for keyword in keywords:
                # Use word boundaries to avoid partial matches like "app" in "appliance"
                if re.search(r'\b' + re.escape(keyword) + r'\b', query, re.IGNORECASE):
                    return domain
        
        return 'general'
    
    def _extract_context_summary(self, conversation_state: ConversationState) -> Dict[str, Any]:
        """Extract a summary of conversation context."""
        return {
            'user_profile': conversation_state.user_profile,
            'information_gaps': conversation_state.information_gaps,
            'priority_factors': conversation_state.priority_factors,
            'conversation_mode': conversation_state.conversation_mode.value,
            'question_count': len(conversation_state.question_history)
        }
    
    def _generate_follow_up_recommendations(
        self,
        questions: List[GeneratedQuestion],
        conversation_state: ConversationState
    ) -> List[str]:
        """Generate recommended follow-up question categories."""
        current_categories = {q.category for q in questions}
        missing_categories = []
        
        # Important categories to consider
        important_categories = [
            'budget', 'timeline', 'preferences', 'constraints', 
            'expertise', 'goals', 'context'
        ]
        
        for category in important_categories:
            if (category not in current_categories and 
                category not in conversation_state.user_profile):
                missing_categories.append(category)
        
        return missing_categories[:3]  # Return top 3 recommendations
    
    def _calculate_intent_alignment(self, question: GeneratedQuestion, intent: IntentAnalysis) -> float:
        """Calculate how well a question aligns with user intent."""
        # Simple alignment based on category relevance to intent
        intent_category_mapping = {
            IntentType.PURCHASE: ['budget', 'timeline', 'preferences', 'constraints'],
            IntentType.LEARNING: ['expertise', 'preferences', 'timeline', 'goals'],
            IntentType.RECOMMENDATION: ['preferences', 'constraints', 'expertise', 'goals'],
            IntentType.COMPARISON: ['preferences', 'constraints', 'priorities'],
            IntentType.RESEARCH: ['goals', 'timeline', 'expertise', 'context'],
            IntentType.TROUBLESHOOTING: ['context', 'constraints', 'timeline'],
            IntentType.EXPLORATION: ['preferences', 'goals', 'context']
        }
        
        relevant_categories = intent_category_mapping.get(intent.primary_intent, [])
        
        if question.category in relevant_categories:
            return 0.9
        elif question.category in ['preferences', 'context']:  # Always somewhat relevant
            return 0.6
        else:
            return 0.3
    
    def _calculate_flow_score(self, question: GeneratedQuestion, conversation_state: ConversationState) -> float:
        """Calculate how well a question fits the conversation flow."""
        # Higher score for questions that build on existing information
        if len(conversation_state.question_history) == 0:
            return 0.8  # First question, moderate score
        
        # Check if question builds on previous context
        if question.category in conversation_state.user_profile:
            return 0.3  # Lower score for redundant information
        
        # Higher score for logical follow-ups
        recent_categories = [qa.category for qa in conversation_state.question_history[-2:]]
        if any(cat in ['budget', 'timeline'] for cat in recent_categories):
            if question.category in ['preferences', 'constraints']:
                return 0.9  # Good follow-up
        
        return 0.6  # Default flow score
    
    def _calculate_gap_score(self, question: GeneratedQuestion, conversation_state: ConversationState) -> float:
        """Calculate how well a question addresses information gaps."""
        if question.category in conversation_state.information_gaps:
            return 0.9
        
        # Check if question relates to missing priority factors
        if question.category in conversation_state.priority_factors:
            return 0.7
        
        return 0.5
    
    def _create_fallback_intent(self) -> IntentAnalysis:
        """Create fallback intent analysis."""
        return IntentAnalysis(
            primary_intent=IntentType.EXPLORATION,
            confidence=0.5,
            context_keywords=[],
            domain='general',
            urgency_level=0.5,
            specificity_level=0.5,
            reasoning="Fallback intent analysis due to processing error"
        )
    
    def _create_fallback_questions(self, conversation_state: ConversationState) -> QuestionGenerationResult:
        """Create diverse, context-aware fallback questions when AI generation fails."""
        
        # Create context-aware fallback questions based on query content
        query_lower = conversation_state.user_query.lower()
        question_count = len(conversation_state.question_history)
        
        # Determine question type based on conversation progress and context
        if question_count == 0:
            # Opening questions - more engaging and conversational
            if any(word in query_lower for word in ['best', 'top', 'recommend']):
                question_text = "I'd love to understand what's most important to you in this decision - what factors should I prioritize?"
            elif any(word in query_lower for word in ['how', 'way', 'method']):
                question_text = "What's your background with this - are you starting fresh or building on some experience?"
            elif any(word in query_lower for word in ['buy', 'purchase', 'get']):
                question_text = "Tell me about what's driving this purchase - is there a particular situation or need you're addressing?"
            else:
                question_text = "What would success look like for you in this situation?"
        elif question_count < 3:
            # Early conversation - build rapport and understanding
            fallback_options = [
                "What constraints or must-haves should I keep in mind while helping you?",
                "I'm curious about how you plan to use this - can you paint me a picture of a typical scenario?",
                "What's your timeline looking like, and is there any urgency I should be aware of?",
                "Are there any past experiences with similar decisions that might inform this one?"
            ]
            question_text = fallback_options[question_count % len(fallback_options)]
        else:
            # Later conversation - deeper insights
            fallback_options = [
                "What other aspects of this decision would be helpful for me to understand?",
                "Are there any deal-breakers or absolute no-goes I should be aware of?",
                "What questions are on your mind about the different options available?",
                "How much flexibility do you have in your approach - are you open to creative solutions?"
            ]
            question_text = fallback_options[question_count % len(fallback_options)]
        
        fallback_questions = [
            GeneratedQuestion(
                question=question_text,
                question_type=QuestionType.OPEN_ENDED,
                category="context",
                priority=0.8,
                context_relevance=0.8,
                expected_answer_type="text",
                follow_up_potential=0.8,
                reasoning=f"Context-aware fallback for query: {conversation_state.user_query}"
            )
        ]
        
        return QuestionGenerationResult(
            questions=fallback_questions,
            intent_analysis=self._create_fallback_intent(),
            conversation_context=self._extract_context_summary(conversation_state),
            generation_confidence=0.3,
            recommended_next_questions=['budget', 'timeline']
        )
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached response is still valid."""
        if cache_key not in self._cache_timestamps:
            return False
        
        return (time.time() - self._cache_timestamps[cache_key]) < self._cache_ttl
    
    def _cache_response(self, cache_key: str, response: Any) -> None:
        """Cache a response with timestamp."""
        self._response_cache[cache_key] = response
        self._cache_timestamps[cache_key] = time.time()
    
    def clear_cache(self) -> None:
        """Clear the response cache."""
        self._response_cache.clear()
        self._cache_timestamps.clear()
        self.logger.debug("Response cache cleared")
