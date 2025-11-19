"""
Custom exceptions for Deep Research Agent.
"""

class DeepResearchError(Exception):
    """Base exception for Deep Research Agent."""
    pass

class ConfigurationError(DeepResearchError):
    """Raised when configuration is invalid."""
    pass

class ValidationError(DeepResearchError):
    """Raised when input validation fails."""
    pass

class GeminiAPIError(DeepResearchError):
    """Raised when Gemini API calls fail."""
    pass

class ResearchStageError(DeepResearchError):
    """Raised when a research stage fails."""
    def __init__(self, stage_num: int, stage_name: str, message: str, original_error: Exception = None):
        self.stage_num = stage_num
        self.stage_name = stage_name
        self.original_error = original_error
        super().__init__(f"Stage {stage_num} ({stage_name}) failed: {message}")

class PromptGenerationError(DeepResearchError):
    """Raised when prompt generation fails."""
    pass
