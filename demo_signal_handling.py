#!/usr/bin/env python3
"""
Demo script to show the signal handling functionality working.
"""

import sys
import signal
import json
import time
import tempfile
from pathlib import Path
from unittest.mock import Mock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from main import setup_signal_handlers, set_current_session, signal_handler
from utils.session_manager import SessionManager


def create_mock_settings(temp_dir):
    """Create mock settings for testing."""
    mock_settings = Mock()
    mock_settings.session_storage_path = str(temp_dir / "sessions")
    mock_settings.session_file_permissions = "0600"
    mock_settings.default_session_limit = 10
    mock_settings.query_max_length = 1000
    mock_settings.query_truncate_length = 100
    mock_settings.separator_width = 60
    mock_settings.confidence_decimal_places = 2
    return mock_settings


def demo_signal_handling():
    """Demonstrate the signal handling functionality."""
    print("🔬 Signal Handling Demo for Research Session Interruption")
    print("=" * 60)
    
    # Create temporary directory for demo
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        mock_settings = create_mock_settings(temp_path)
        
        # Create session manager
        session_manager = SessionManager(mock_settings)
        session_manager.session_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a test session
        session_data = {
            "session_id": "DRA_20250629_DEMO_001",
            "created_at": "2025-06-29T12:00:00",
            "query": "Best smartphone for photography under $500",
            "status": "stage_1",
            "context": {"personalize": True}
        }
        
        session_file = session_manager.session_dir / f"{session_data['session_id']}.json"
        with open(session_file, 'w') as f:
            json.dump(session_data, f, indent=2)
        
        print(f"✅ Created demo session: {session_data['session_id']}")
        print(f"   Status: {session_data['status']}")
        print(f"   Query: {session_data['query']}")
        
        # Set current session for signal handling
        set_current_session(session_manager, session_data['session_id'])
        print("✅ Set current session for signal handling")
        
        # Simulate signal interruption
        print("\n🚨 Simulating SIGINT (Ctrl+C) interruption...")
        try:
            # Mock sys.exit to prevent actual exit
            import main
            original_exit = main.sys.exit
            main.sys.exit = lambda x: None
            
            # Call signal handler
            signal_handler(signal.SIGINT, None)
            
            # Restore original exit
            main.sys.exit = original_exit
            
        except SystemExit:
            pass
        
        # Check if session was marked as interrupted
        with open(session_file, 'r') as f:
            updated_session = json.load(f)
        
        print(f"\n✅ Session status after interruption: {updated_session['status']}")
        
        if updated_session['status'] == 'interrupted':
            print("🎉 SUCCESS: Session was properly marked as interrupted!")
        else:
            print("❌ FAILED: Session was not marked as interrupted")
            return False
        
        # Test cleanup functionality
        print("\n🧹 Testing cleanup of incomplete sessions...")
        
        # Create some test sessions for cleanup
        test_sessions = [
            {
                "session_id": "DRA_20250628_OLD_001",
                "created_at": "2025-06-28T12:00:00",  # 1 day ago
                "query": "Old query",
                "status": "created"  # Should be cleaned up as stale
            },
            {
                "session_id": "DRA_CORRUPTED",
                # Missing required fields - should be cleaned up
            }
        ]
        
        # Create old session (will be cleaned as stale)
        old_session_file = session_manager.session_dir / "DRA_20250628_OLD_001.json"
        with open(old_session_file, 'w') as f:
            json.dump(test_sessions[0], f)
        
        # Create corrupted session file
        corrupted_file = session_manager.session_dir / "DRA_CORRUPTED.json"
        corrupted_file.write_text('{ "incomplete": "json"')
        
        print(f"✅ Created test sessions for cleanup demo")
        
        # Run cleanup
        deleted_count = session_manager.cleanup_incomplete_sessions()
        print(f"✅ Cleanup completed: {deleted_count} sessions removed")
        
        # Verify cleanup results
        remaining_sessions = list(session_manager.session_dir.glob("*.json"))
        print(f"✅ Remaining sessions: {len(remaining_sessions)}")
        
        for session_file in remaining_sessions:
            with open(session_file, 'r') as f:
                session = json.load(f)
            print(f"   - {session['session_id']}: {session['status']}")
        
        print("\n🎉 Demo completed successfully!")
        print("\nKey features demonstrated:")
        print("  ✅ Signal handling for graceful interruption")
        print("  ✅ Session status marking as 'interrupted'")
        print("  ✅ Cleanup of incomplete/corrupted sessions")
        print("  ✅ Preservation of valid interrupted sessions")
        
        return True


if __name__ == "__main__":
    success = demo_signal_handling()
    sys.exit(0 if success else 1)