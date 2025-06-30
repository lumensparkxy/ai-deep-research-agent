"""
Tests for AI-first Intent Analyzer

Tests the fluid, intelligence-driven intent analysis without rigid classifications.
"""

import pytest
from unittest.mock import Mock, MagicMock
import json

from core.intent_analyzer import IntentAnalyzer, IntentInsights


class TestIntentInsights:
    """Test the IntentInsights data structure"""
    
    def test_intent_insights_creation(self):
        """Test creating IntentInsights"""
        insights = IntentInsights(
            raw_analysis="Sample analysis",
            key_insights={"core_intent": "purchase decision"},
            conversation_strategy="consultative",
            question_focus_areas=["budget", "preferences"],
            estimated_complexity="moderate",
            confidence_level=0.8,
            contextual_notes="Test notes"
        )
        
        assert insights.raw_analysis == "Sample analysis"
        assert insights.get_insight("core_intent") == "purchase decision"
        assert insights.confidence_level == 0.8
    
    def test_get_insight_with_default(self):
        """Test getting insight with default fallback"""
        insights = IntentInsights(
            raw_analysis="Test",
            key_insights={"existing_key": "value"},
            conversation_strategy="standard",
            question_focus_areas=[],
            estimated_complexity="simple",
            confidence_level=0.5,
            contextual_notes=""
        )
        
        assert insights.get_insight("existing_key") == "value"
        assert insights.get_insight("nonexistent_key", "default") == "default"
        assert insights.get_insight("nonexistent_key") is None
    
    def test_to_dict_serialization(self):
        """Test converting insights to dictionary"""
        insights = IntentInsights(
            raw_analysis="Analysis text",
            key_insights={"intent": "research"},
            conversation_strategy="standard",
            question_focus_areas=["area1", "area2"],
            estimated_complexity="moderate",
            confidence_level=0.7,
            contextual_notes="Notes"
        )
        
        result = insights.to_dict()
        
        assert isinstance(result, dict)
        assert result["raw_analysis"] == "Analysis text"
        assert result["key_insights"]["intent"] == "research"
        assert result["confidence_level"] == 0.7


class TestIntentAnalyzer:
    """Test the AI-first Intent Analyzer"""
    
    @pytest.fixture
    def mock_gemini_client(self):
        """Create mock Gemini client"""
        client = Mock()
        
        # Create a callable that returns different responses based on call count
        def generate_content_side_effect(prompt):
            if "USER QUERY:" in prompt:
                # First call - analysis response
                response = Mock()
                response.text = """
                This user is looking for a smartphone with photography capabilities. 
                
                CORE INTENT: They want to capture better photos, likely for personal/family use.
                
                DECISION CONTEXT: This appears to be a purchase decision with moderate complexity.
                
                EMOTIONAL UNDERTONES: Moderate urgency, seeking quality improvement.
                
                CONVERSATION STRATEGY: Take a consultative approach, focus on usage patterns and specific photo needs.
                
                The user likely values image quality but may also have budget considerations.
                """
                return response
            else:
                # Second call - JSON extraction response
                response = Mock()
                response.text = """{
            "key_insights": {
                "core_intent": "better photography capabilities",
                "decision_context": "smartphone purchase",
                "emotional_undertones": "moderate urgency",
                "stakeholder_implications": "personal/family use"
            },
            "conversation_strategy": "consultative",
            "question_focus_areas": ["photography needs", "budget", "current frustrations"],
            "estimated_complexity": "moderate",
            "confidence_level": 0.8,
            "contextual_notes": "Focus on image quality and usage patterns"
        }"""
                return response
        
        client.generate_content.side_effect = generate_content_side_effect
        return client
    
    @pytest.fixture
    def intent_analyzer(self, mock_gemini_client):
        """Create IntentAnalyzer with mocked client"""
        return IntentAnalyzer(mock_gemini_client)
    
    def test_analyze_user_intent_success(self, intent_analyzer):
        """Test successful intent analysis"""
        query = "best smartphone for photography"
        
        insights = intent_analyzer.analyze_user_intent(query)
        
        assert isinstance(insights, IntentInsights)
        assert insights.confidence_level > 0.5
        assert "photography" in insights.raw_analysis.lower()
        assert insights.get_insight("core_intent") == "better photography capabilities"
        assert "consultative" in insights.conversation_strategy
    
    def test_analyze_with_context(self):
        """Test intent analysis with additional context"""
        # Create fresh mock for this test
        mock_client = Mock()
        
        def generate_content_side_effect(prompt):
            if "USER QUERY:" in prompt and "laptop for work" in prompt:
                # Verify context is included
                assert "developer" in prompt
                assert "budget_range" in prompt
                response = Mock()
                response.text = "Analysis for laptop query with developer context"
                return response
            else:
                response = Mock()
                response.text = """{
            "key_insights": {"core_intent": "development machine"},
            "conversation_strategy": "technical",
            "question_focus_areas": ["performance"],
            "estimated_complexity": "moderate",
            "confidence_level": 0.8,
            "contextual_notes": "Developer context"
        }"""
                return response
        
        mock_client.generate_content.side_effect = generate_content_side_effect
        analyzer = IntentAnalyzer(mock_client)
        
        query = "laptop for work"
        context = {"user_role": "developer", "budget_range": "high"}
        
        insights = analyzer.analyze_user_intent(query, context)
        
        assert isinstance(insights, IntentInsights)
        assert insights.get_insight("core_intent") == "development machine"
    
    def test_analyze_intent_with_failure(self, mock_gemini_client):
        """Test graceful handling of analysis failure"""
        # Make Gemini client raise an exception
        mock_gemini_client.generate_content.side_effect = Exception("API Error")
        
        analyzer = IntentAnalyzer(mock_gemini_client)
        insights = analyzer.analyze_user_intent("test query")
        
        # Should return fallback insights
        assert isinstance(insights, IntentInsights)
        assert insights.confidence_level < 0.5  # Low confidence for fallback
        assert "fallback" in insights.contextual_notes.lower()
    
    def test_generate_conversation_opener(self, intent_analyzer):
        """Test generating conversation opener from insights"""
        insights = IntentInsights(
            raw_analysis="User wants photography smartphone",
            key_insights={"core_intent": "better photos"},
            conversation_strategy="consultative",
            question_focus_areas=["usage", "budget"],
            estimated_complexity="moderate",
            confidence_level=0.8,
            contextual_notes="Focus on image quality"
        )
        
        # Mock the opener generation response
        opener_response = Mock()
        opener_response.text = "I can see you're looking to improve your photography experience. Let me understand your specific needs better."
        intent_analyzer.gemini_client.generate_content.return_value = opener_response
        
        opener = intent_analyzer.generate_conversation_opener(insights)
        
        assert isinstance(opener, str)
        assert len(opener) > 0
        assert "photography" in opener.lower()
    
    def test_update_insights_with_response(self, intent_analyzer):
        """Test updating insights based on user response"""
        original_insights = IntentInsights(
            raw_analysis="Initial analysis",
            key_insights={"core_intent": "smartphone purchase"},
            conversation_strategy="standard",
            question_focus_areas=["general"],
            estimated_complexity="moderate",
            confidence_level=0.6,
            contextual_notes="Initial understanding"
        )
        
        # Mock updated analysis
        updated_response = Mock()
        updated_response.text = "Updated analysis with new information about portrait photography needs"
        
        json_response = Mock()
        json_response.text = """```json
        {
            "key_insights": {
                "core_intent": "portrait photography smartphone",
                "specific_use": "family photos"
            },
            "conversation_strategy": "family-focused",
            "question_focus_areas": ["indoor lighting", "ease of use"],
            "estimated_complexity": "moderate",
            "confidence_level": 0.9,
            "contextual_notes": "Family photography context"
        }
        ```"""
        
        intent_analyzer.gemini_client.generate_content.side_effect = [updated_response, json_response]
        
        updated_insights = intent_analyzer.update_insights_with_response(
            original_insights,
            "What type of photography interests you?",
            "Portrait photography of my kids"
        )
        
        assert isinstance(updated_insights, IntentInsights)
        assert updated_insights.confidence_level > original_insights.confidence_level
        assert "portrait" in updated_insights.get_insight("core_intent", "").lower()
    
    def test_create_intent_analysis_prompt(self, intent_analyzer):
        """Test prompt creation for intent analysis"""
        query = "best laptop for programming"
        context = {"experience": "beginner", "budget": "1500"}
        
        prompt = intent_analyzer._create_intent_analysis_prompt(query, context)
        
        assert isinstance(prompt, str)
        assert query in prompt
        assert "beginner" in prompt
        assert "1500" in prompt
        assert "CORE INTENT" in prompt
        assert "CONVERSATION STRATEGY" in prompt
    
    def test_extract_insights_json_parsing(self):
        """Test extracting insights from analysis text"""
        # Create fresh mock for this test
        mock_client = Mock()
        analyzer = IntentAnalyzer(mock_client)
        
        analysis = "The user wants a smartphone for photography with good low-light performance."
        
        # Mock JSON extraction response
        json_response = Mock()
        json_response.text = """{
            "key_insights": {
                "core_intent": "photography smartphone",
                "priority": "low-light performance"
            },
            "conversation_strategy": "technical",
            "question_focus_areas": ["camera specs", "budget"],
            "estimated_complexity": "moderate",
            "confidence_level": 0.85,
            "contextual_notes": "Technical photography focus"
        }"""
        
        mock_client.generate_content.return_value = json_response
        
        insights = analyzer._extract_insights_from_analysis(analysis)
        
        assert isinstance(insights, dict)
        assert insights["key_insights"]["core_intent"] == "photography smartphone"
        assert insights["confidence_level"] == 0.85
    
    def test_create_fallback_insights(self, intent_analyzer):
        """Test creating fallback insights"""
        query = "test query"
        
        fallback = intent_analyzer._create_fallback_insights(query)
        
        assert isinstance(fallback, IntentInsights)
        assert fallback.confidence_level < 0.5
        assert "fallback" in fallback.contextual_notes.lower()
        assert query in fallback.raw_analysis


class TestIntentAnalyzerIntegration:
    """Integration tests for complete intent analysis flow"""
    
    def test_complete_analysis_flow(self):
        """Test complete intent analysis workflow"""
        # Mock client with realistic responses
        mock_client = Mock()
        
        # Analysis response
        analysis_response = Mock()
        analysis_response.text = """
        This user is seeking a laptop for programming work. 
        
        CORE INTENT: They need a reliable development machine.
        DECISION CONTEXT: Professional tool purchase, likely replacing current setup.
        EMOTIONAL UNDERTONES: Practical decision with performance focus.
        CONVERSATION STRATEGY: Technical but accessible approach.
        
        Focus on development requirements, performance needs, and workflow optimization.
        """
        
        # JSON extraction response
        json_response = Mock()
        json_response.text = """{
            "key_insights": {
                "core_intent": "development machine",
                "decision_context": "professional tool purchase"
            },
            "conversation_strategy": "technical-accessible",
            "question_focus_areas": ["development type", "performance needs", "portability"],
            "estimated_complexity": "moderate",
            "confidence_level": 0.8,
            "contextual_notes": "Focus on development workflow"
        }"""
        
        mock_client.generate_content.side_effect = [analysis_response, json_response]
        
        analyzer = IntentAnalyzer(mock_client)
        insights = analyzer.analyze_user_intent("best laptop for programming")
        
        # Verify complete analysis
        assert insights.get_insight("core_intent") == "development machine"
        assert insights.conversation_strategy == "technical-accessible"
        assert "development type" in insights.question_focus_areas
        assert insights.confidence_level == 0.8
