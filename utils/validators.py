"""
Input Validation and Sanitization for Deep Research Agent
Ensures data quality and security for all user inputs.
"""

import re
import logging
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import os


class ValidationError(Exception):
    """Raised when input validation fails."""
    pass


class InputValidator:
    """Handles validation and sanitization of user inputs."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Common patterns for validation
        self.patterns = {
            # Allow DRA_YYYYMMDD_HHMMSS or with optional microseconds suffix
            'session_id': re.compile(r'^DRA_\d{8}_\d{6}(?:_\d{6})?$'),
            'file_path': re.compile(r'^[a-zA-Z0-9._/\-\s]+$'),
            'query': re.compile(r'^.{5,500}$'),  # 5-500 characters
            'email': re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'),
            'number': re.compile(r'^-?\d+\.?\d*$')
        }
        self.sql_blacklist = re.compile(r'\b(ALTER|CREATE|DELETE|DROP|EXEC|INSERT|MERGE|SELECT|UPDATE|UNION)\b', re.IGNORECASE)
        self.xss_blacklist = re.compile(r'(<script.*?>|</script>|onerror=|onload=|javascript:|<iframe>|<svg>|<body>)', re.IGNORECASE)
        self.command_blacklist = re.compile(r'(rm -rf|wget|curl|del C:|format C:)', re.IGNORECASE)
        self.ldap_blacklist = re.compile(r'[\*\(\)\\]', re.IGNORECASE)
        self.control_chars_blacklist = re.compile(r'[\x00-\x1f\x7f]')

    def sanitize_string(self, text: str, max_length: int = 1000) -> str:
        """
        Sanitize string input by removing dangerous characters and limiting length.
        
        Args:
            text: Input string to sanitize
            max_length: Maximum allowed length
            
        Returns:
            Sanitized string
        """
        if not isinstance(text, str):
            text = str(text)

        # Remove control characters
        text = self.control_chars_blacklist.sub('', text)

        # Remove potentially dangerous characters and patterns
        text = self.sql_blacklist.sub('', text)
        text = self.xss_blacklist.sub('', text)
        text = self.command_blacklist.sub('', text)
        text = self.ldap_blacklist.sub('', text)
        
        dangerous_chars = ['<', '>', '\"''', "'", '&', '`', '$', '\\', ';', '|', '--']
        for char in dangerous_chars:
            text = text.replace(char, '')

        # Limit length
        text = text[:max_length]
        
        # Strip whitespace
        text = text.strip()
        
        return text
    
    def validate_query(self, query: str) -> str:
        """
        Validate and sanitize a research query.
        
        Args:
            query: User's research question
            
        Returns:
            Validated and sanitized query
            
        Raises:
            ValidationError: If query is invalid
        """
        if not query or not isinstance(query, str):
            raise ValidationError("Query must be a non-empty string")
        
        # Sanitize
        query = self.sanitize_string(query, max_length=500)
        
        # Validate length
        if len(query) < 5:
            raise ValidationError("Query must be at least 5 characters long")
        
        if len(query) > 500:
            raise ValidationError("Query must be less than 500 characters")
        
        # Check for meaningful content
        if not re.search(r'[a-zA-Z]', query):
            raise ValidationError("Query must contain alphabetic characters")
        
        return query
    
    def validate_session_id(self, session_id: str) -> str:
        """
        Validate session ID format.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Validated session ID
            
        Raises:
            ValidationError: If session ID is invalid
        """
        if not session_id or not isinstance(session_id, str):
            raise ValidationError("Session ID must be a non-empty string")

        sanitized_id = self.sanitize_string(session_id)
        if sanitized_id != session_id:
            raise ValidationError("Session ID contains invalid characters.")

        if not self.patterns['session_id'].match(sanitized_id):
            raise ValidationError("Session ID must follow format: DRA_YYYYMMDD_HHMMSS")

        return sanitized_id

    def validate_file_path(self, file_path: str, project_root: Path, must_exist: bool = False) -> str:
        """
        Validate file path for security and format.

        Args:
            file_path: Path to validate
            project_root: The root directory of the project for validation context.
            must_exist: Whether file must already exist

        Returns:
            Validated file path

        Raises:
            ValidationError: If path is invalid
        """
        if not file_path or not isinstance(file_path, str):
            raise ValidationError("File path must be a non-empty string")

        # Prevent directory traversal attacks
        if '..' in file_path or '\\' in file_path:
            raise ValidationError("File path cannot contain '..' or '\\'.")

        # Prevent absolute paths and other schemes
        if os.path.isabs(file_path) or ':' in file_path or file_path.startswith('~'):
            raise ValidationError("File path cannot be absolute or contain schemes.")

        # Convert to Path object for validation
        try:
            # Create a safe, absolute path by joining the project root and the relative file path
            safe_path = project_root.joinpath(file_path).resolve()

            # Check if the resolved path is within the project directory
            if not str(safe_path).startswith(str(project_root.resolve())):
                raise ValidationError("File path must be within project directory")

            if must_exist and not safe_path.exists():
                raise ValidationError(f"File does not exist: {file_path}")

        except (OSError, ValueError) as e:
            raise ValidationError(f"Invalid file path: {e}")

        return str(file_path)

    def validate_personalization_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate personalization data from user.
        
        Args:
            data: Dictionary of personalization information
            
        Returns:
            Validated and sanitized data
            
        Raises:
            ValidationError: If data is invalid
        """
        if not isinstance(data, dict):
            raise ValidationError("Personalization data must be a dictionary")

        if len(data) > 100:  # Limit number of keys
            raise ValidationError("Personalization data cannot have more than 100 keys.")

        validated_data = {}

        for key, value in data.items():
            if key.lower() in ('__proto__', 'constructor', 'prototype') or '.' in key:
                raise ValidationError(f"Invalid key in personalization data: {key}")

            # Sanitize key
            clean_key = self.sanitize_string(key, max_length=50)
            if not clean_key:
                continue
            
            # Handle different value types
            if isinstance(value, str):
                clean_value = self.sanitize_string(value, max_length=200)
            elif isinstance(value, (int, float)):
                clean_value = value
            elif isinstance(value, bool):
                clean_value = value
            elif isinstance(value, dict):
                clean_value = self.validate_personalization_data(value)
            elif isinstance(value, list):
                if len(value) > 50: # Limit list size
                    raise ValidationError(f"List in personalization data for key '{clean_key}' is too long.")
                clean_value = [self.sanitize_string(str(item), max_length=100)
                              for item in value if item][:10]  # Limit list size
            else:
                # Convert to string and sanitize
                clean_value = self.sanitize_string(str(value), max_length=200)
            
            if clean_value != '' and clean_value is not None:
                validated_data[clean_key] = clean_value
        
        return validated_data
    
    def validate_report_depth(self, depth: str) -> str:
        """
        Validate report depth setting.
        
        Args:
            depth: Report depth level
            
        Returns:
            Validated depth
            
        Raises:
            ValidationError: If depth is invalid
        """
        valid_depths = ['quick', 'standard', 'detailed']
        
        if not depth or not isinstance(depth, str):
            raise ValidationError("Report depth must be a non-empty string")
        
        depth = depth.lower().strip()
        
        if depth not in valid_depths:
            raise ValidationError(f"Report depth must be one of: {', '.join(valid_depths)}")
        
        return depth
    
    def validate_context_data(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate context data structure.
        
        Args:
            context: Context dictionary
            
        Returns:
            Validated context data
        """
        if not isinstance(context, dict):
            return {}
        
        validated_context = {}
        
        # Validate boolean flags
        if 'personalize' in context:
            validated_context['personalize'] = bool(context['personalize'])
        
        # Validate user info
        if 'user_info' in context and isinstance(context['user_info'], dict):
            validated_context['user_info'] = self.validate_personalization_data(
                context['user_info']
            )
        
        # Validate constraints
        if 'constraints' in context and isinstance(context['constraints'], dict):
            validated_context['constraints'] = self.validate_personalization_data(
                context['constraints']
            )
        
        # Validate preferences
        if 'preferences' in context and isinstance(context['preferences'], dict):
            validated_context['preferences'] = self.validate_personalization_data(
                context['preferences']
            )
        
        return validated_context
    
    def validate_confidence_score(self, score: Union[int, float]) -> float:
        """
        Validate confidence score.
        
        Args:
            score: Confidence score between 0 and 1
            
        Returns:
            Validated score
            
        Raises:
            ValidationError: If score is invalid
        """
        try:
            score = float(score)
        except (TypeError, ValueError):
            raise ValidationError("Confidence score must be a number")
        
        if not 0.0 <= score <= 1.0:
            raise ValidationError("Confidence score must be between 0.0 and 1.0")
        
        return score
    
    def validate_research_stage(self, stage: int, max_stages: int = 6) -> int:
        """
        Validate research stage number.
        
        Args:
            stage: Stage number
            max_stages: Maximum allowed stage number
            
        Returns:
            Validated stage number
            
        Raises:
            ValidationError: If stage is invalid
        """
        try:
            stage = int(stage)
        except (TypeError, ValueError):
            raise ValidationError("Stage must be an integer")
        
        if not 1 <= stage <= max_stages:
            raise ValidationError(f"Stage must be between 1 and {max_stages}")
        
        return stage
