"""
Pytest configuration and shared fixtures for Deep Research Agent tests.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch
import json
from datetime import datetime

# Add project root to path for imports
import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import Settings


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_settings(temp_dir):
    """Create mock settings for testing."""
    settings = Mock(spec=Settings)
    settings.app_name = "Deep Research Agent"
    settings.app_version = "1.0.0"
    settings.log_level = "INFO"
    settings.session_storage_path = str(temp_dir / "sessions")
    settings.report_storage_path = str(temp_dir / "reports")
    settings.research_stages = [
        "Initial Analysis",
        "Source Research", 
        "Comparative Analysis",
        "Expert Validation",
        "Risk Assessment",
        "Final Synthesis"
    ]
    
    # Validation settings - provide actual integer values instead of Mock objects
    settings.string_max_length = 1000
    settings.query_max_length = 500
    settings.query_min_length = 5
    settings.personalization_max_keys = 100
    settings.personalization_key_max_length = 50
    settings.personalization_value_max_length = 200
    settings.personalization_list_item_max_length = 100
    settings.personalization_list_max_size = 10
    settings.personalization_nested_list_max_size = 50
    settings.stage_count = 6
    settings.fallback_max_retries = 3
    settings.max_retries = 3
    settings.session_file_permissions = "600"
    settings.default_session_limit = 50
    settings.query_display_length = 100
    
    # Add base_path property for session manager tests
    settings.base_path = temp_dir
    
    # Add properties needed for research engine tests
    settings.gemini_api_key = "test_key"
    settings.ai_model = "gemini-2.0-flash-exp"
    settings.ai_max_tokens = 4000
    settings.ai_temperature = 0.7
    settings.ai_safety_settings = {}
    
    return settings


@pytest.fixture
def sample_session_data():
    """Sample session data for testing."""
    return {
        "session_id": "DRA_20250628_120000",
        "created_at": "2025-06-28T12:00:00",
        "version": "1.0.0",
        "query": "Best smartphone under $500 for photography",
        "context": {
            "personalize": True,
            "user_info": {
                "budget": "500",
                "priority": "photography"
            },
            "constraints": {
                "timeline": "1 month"
            }
        },
        "research_results": {
            "stages": [],
            "final_conclusions": {},
            "confidence_score": 0.0
        },
        "report_path": None,
        "status": "created"
    }


@pytest.fixture
def sample_stage_data():
    """Sample stage data for testing."""
    return {
        "stage": 1,
        "stage_name": "Initial Analysis",
        "findings": {
            "key_factors": ["price", "camera quality", "brand reputation"],
            "initial_research": "Preliminary findings about smartphone market"
        },
        "sources": [
            "https://example.com/smartphone-reviews",
            "https://example.com/camera-tests"
        ],
        "confidence": 0.7
    }


@pytest.fixture
def invalid_session_ids():
    """List of invalid session IDs for testing."""
    return [
        "",
        "invalid_format",
        "DRA_20250628",  # Missing time
        "DRA_2025628_120000",  # Wrong date format
        "DRA_20250628_1200",  # Wrong time format
        "PREFIX_20250628_120000",  # Wrong prefix
        None,
        123,
        []
    ]


@pytest.fixture
def valid_session_ids():
    """List of valid session IDs for testing."""
    return [
        "DRA_20250628_120000",
        "DRA_20241231_235959",
        "DRA_20250101_000000"
    ]


@pytest.fixture
def sample_queries():
    """Sample queries for testing validation."""
    return {
        "valid": [
            "Best smartphone under $500 for photography",
            "What are the healthiest breakfast options?",
            "Should I invest in cryptocurrency in 2025?",
            "Best programming language to learn for data science"
        ],
        "invalid": [
            "",  # Empty
            "Hi",  # Too short
            "a" * 501,  # Too long
            None,  # None
            123,  # Not string
            "<script>alert('test')</script>",  # Contains dangerous chars
        ]
    }


@pytest.fixture
def mock_datetime():
    """Mock datetime for consistent testing."""
    with patch('utils.session_manager.datetime') as mock_dt:
        mock_datetime_obj = Mock()
        mock_datetime_obj.isoformat.return_value = "2025-06-28T12:00:00"
        mock_dt.now.return_value = mock_datetime_obj
        mock_dt.now().strftime.return_value = "20250628_120000"
        yield mock_dt


@pytest.fixture
def sample_complex_context():
    """Sample complex context data for testing."""
    return {
        "personalize": True,
        "user_info": {
            "age": 30,
            "location": "San Francisco",
            "income": "75000",
            "preferences": ["quality", "sustainability", "value"]
        },
        "constraints": {
            "budget": {"min": 100, "max": 500},
            "timeline": "urgent",
            "requirements": ["waterproof", "good camera"],
            "location": "USA"
        },
        "preferences": {
            "brands": ["Apple", "Samsung", "Google"],
            "features": {
                "camera": "high_priority",
                "battery": "medium_priority",
                "storage": "low_priority"
            },
            "style": "minimalist"
        }
    }


@pytest.fixture
def extended_sample_queries():
    """Extended sample queries for comprehensive testing."""
    return {
        "valid": [
            "Best smartphone under $500 for photography enthusiasts",
            "What are the healthiest breakfast options for athletes?",
            "Should I invest in cryptocurrency or traditional stocks in 2025?",
            "Best programming language to learn for data science careers",
            "How to choose the right health insurance plan for a family",
            "Compare electric vehicles under $40,000 for daily commuting"
        ],
        "invalid": [
            "",  # Empty
            "Hi",  # Too short
            "How",  # Too short
            "a" * 501,  # Too long (501 characters)
            None,  # None
            123,  # Not string
            [],  # List
            {},  # Dictionary
            "<script>alert('test')</script>",  # Contains dangerous chars
            "12345!@#$%",  # No alphabetic characters
        ],
        "edge_cases": [
            "Valid query with numbers 123",  # Mixed alphanumeric
            "Query with special chars: - _ . ()",  # Safe special chars
            "a" * 5,  # Minimum length
            "a" * 500,  # Maximum length
        ]
    }


@pytest.fixture
def sample_personalization_responses():
    """Sample personalization responses for testing."""
    return {
        "health": {
            "age": "30",
            "weight": "70kg",
            "fitness_goal": "weight loss",
            "dietary_restrictions": "vegetarian"
        },
        "finance": {
            "income": "75000",
            "risk_tolerance": "moderate",
            "investment_timeline": "long term",
            "financial_goals": "retirement"
        },
        "technology": {
            "budget": "500",
            "usage": "professional",
            "brand_preference": "Apple",
            "features": "camera quality"
        },
        "lifestyle": {
            "interests": "outdoor activities",
            "location": "San Francisco",
            "lifestyle": "active",
            "preferences": "eco-friendly"
        }
    }
