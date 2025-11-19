"""
End-to-End Flow Test for Deep Research Agent.

This test simulates a complete research session by mocking the AI responses
but executing the full logic of the ResearchEngine and ReportGenerator.
It verifies that data flows correctly through all 6 stages and produces a report.
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from config.settings import Settings
from core.research_engine import ResearchEngine
from core.report_generator import ReportGenerator
from utils.session_manager import SessionManager

@pytest.mark.asyncio
class TestEndToEndFlow:
    """End-to-end flow tests with mocked AI."""

    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace."""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            (workspace / "sessions").mkdir()
            (workspace / "reports").mkdir()
            yield workspace

    @pytest.fixture
    def settings(self, temp_workspace):
        """Configure settings for testing."""
        with patch.dict('os.environ', {
            'GEMINI_API_KEY': 'test_key',
            'SESSION_STORAGE_PATH': str(temp_workspace / "sessions"),
            'REPORT_OUTPUT_PATH': str(temp_workspace / "reports"),
            'LOG_LEVEL': 'DEBUG'
        }):
            yield Settings()

    def test_complete_research_flow(self, settings, temp_workspace):
        """
        Test the full research flow from query to report generation.
        
        This test mocks the Gemini API calls but runs the actual ResearchEngine logic,
        verifying that:
        1. All 6 stages are executed in order.
        2. Data is passed correctly between stages.
        3. Session state is updated.
        4. Final report is generated.
        """
        
        # Define mock responses for each stage
        stage_responses = [
            # Stage 1: Information Gathering
            json.dumps({
                "summary": "Initial gathering on Python vs Rust.",
                "key_facts": ["Python is interpreted", "Rust is compiled"],
                "evidence": [{"source_description": "Tech docs", "reliability_score": 0.9, "extracted_text": "Rust is memory safe", "relevance_score": 0.95}],
                "gaps_identified": ["Performance benchmarks", "Learning curve"],
                "research_areas": ["Memory safety", "Ecosystem"]
            }),
            # Stage 2: Validation
            json.dumps({
                "summary": "Validated facts.",
                "validated_facts": ["Python is slower than Rust"],
                "questionable_information": [],
                "additional_gaps": ["Specific web framework comparisons"],
                "reliability_assessment": {"overall_confidence": 0.9}
            }),
            # Stage 3: Clarification
            json.dumps({
                "summary": "Clarified performance gaps.",
                "gap_responses": [{"gap": "Performance benchmarks", "findings": "Rust is 10x faster", "confidence": 0.9}],
                "additional_evidence": [],
                "remaining_gaps": []
            }),
            # Stage 4: Comparative Analysis
            json.dumps({
                "summary": "Comparison completed.",
                "options_identified": [
                    {"option": "Python", "description": "Easy to learn", "pros": ["Huge ecosystem"], "cons": ["Slow"], "score": 0.8},
                    {"option": "Rust", "description": "High performance", "pros": ["Fast", "Safe"], "cons": ["Hard to learn"], "score": 0.85}
                ],
                "comparison_criteria": ["Speed", "Ease of use"],
                "comparison_matrix": {"Python": {"Speed": 3, "Ease of use": 9}, "Rust": {"Speed": 10, "Ease of use": 5}},
                "standout_recommendations": ["Use Rust for systems programming"]
            }),
            # Stage 5: Synthesis
            json.dumps({
                "summary": "Synthesized findings.",
                "key_insights": ["Trade-off between dev speed and execution speed"],
                "patterns_identified": ["Rust adoption is growing"],
                "confidence_assessment": {"overall_confidence": 0.9},
                "decision_factors": []
            }),
            # Stage 6: Final Conclusions
            json.dumps({
                "summary": "Final verdict: It depends on the use case.",
                "primary_recommendation": "Use Python for scripting, Rust for performance.",
                "recommendations": [
                    {"recommendation": "Learn Rust for long term", "reasoning": "Career growth", "priority": "high", "confidence": 0.9}
                ],
                "implementation_plan": [{"step": "Start with Python", "timeline": "Week 1"}],
                "risk_assessment": [],
                "success_metrics": ["Code quality"],
                "confidence_factors": ["Strong community consensus"]
            })
        ]

        # Mock the Gemini client
        with patch('google.genai.Client') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            # Mock the generate_content method to return our stage responses sequentially
            mock_response = Mock()
            mock_response.text = "" # Placeholder
            
            # We need a side_effect that returns a mock object with the .text attribute set to the next response
            def side_effect(*args, **kwargs):
                resp = Mock()
                if stage_responses:
                    resp.text = stage_responses.pop(0)
                else:
                    resp.text = "{}" # Fallback
                return resp
            
            mock_client.models.generate_content.side_effect = side_effect

            # Initialize components
            session_manager = SessionManager(settings)
            research_engine = ResearchEngine(settings)
            report_generator = ReportGenerator(settings)

            # Define test query and context
            query = "Compare Python and Rust for backend development"
            context = {
                "personalize": True,
                "user_info": {"role": "CTO"},
                "constraints": {"timeline": "immediate"}
            }

            # --- Step 1: Run Research ---
            print("\n🚀 Starting Research Engine...")
            results = research_engine.conduct_research(query, context, "test_session_id")

            # Verify Research Results
            assert results is not None
            assert "stages" in results
            assert len(results["stages"]) == 6
            assert results["stages"][0]["name"] == "Information Gathering"
            assert results["stages"][5]["name"] == "Final Conclusions"
            assert results["confidence_score"] > 0.0
            
            # Verify specific data flow (e.g., Stage 4 comparison data)
            stage_4 = results["stages"][3]
            assert stage_4["name"] == "Comparative Analysis"
            assert len(stage_4["findings"]["options_identified"]) == 2
            assert stage_4["findings"]["options_identified"][0]["option"] == "Python"

            # Verify Session Data was saved
            sessions = session_manager.list_sessions()
            assert len(sessions) == 1
            session_data = sessions[0]
            assert session_data["query"] == query
            assert session_data["status"] == "completed"

            # --- Step 2: Generate Report ---
            print("\n📝 Generating Report...")
            report_path = report_generator.generate_report(session_data, results, "detailed")

            # Verify Report Generation
            assert report_path is not None
            assert Path(report_path).exists()
            
            # Read report content
            with open(report_path, 'r') as f:
                content = f.read()
            
            # Verify Report Content
            assert "# 📊 Deep Research Report" in content
            assert f"**Query**: {query}" in content
            assert "## 🔬 Research Methodology" in content # Detailed section
            assert "Python" in content
            assert "Rust" in content
            assert "Use Python for scripting, Rust for performance" in content # Primary recommendation

            print(f"\n✅ End-to-End Test Passed! Report generated at: {report_path}")
