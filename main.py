#!/usr/bin/env python3
"""
Deep Research Agent - Main Entry Point
AI-powered decision support through multi-stage iterative research.
"""

import sys
import logging
import argparse
import signal
import json
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.settings import Settings, ConfigurationError
from core.conversation import ConversationHandler
from utils.session_manager import SessionManager

# Import version from package
try:
    from __init__ import __version__
except ImportError:
    # Fallback if import fails
    __version__ = "unknown"

# Global variables for signal handling
_current_session_manager = None
_current_session_id = None


def signal_handler(signum, frame):
    """Handle SIGINT and SIGTERM by marking current session as interrupted."""
    global _current_session_manager, _current_session_id
    
    signal_name = "SIGINT" if signum == signal.SIGINT else "SIGTERM"
    print(f"\n\n⚠️  Received {signal_name}. Gracefully shutting down...")
    
    # Mark current session as interrupted if one exists
    if _current_session_manager and _current_session_id:
        try:
            # Load session directly from file to avoid validator issues
            session_file = _current_session_manager.session_dir / f"{_current_session_id}.json"
            if session_file.exists():
                with open(session_file, 'r') as f:
                    session_data = json.load(f)
                
                if session_data.get("status") not in ["completed", "interrupted"]:
                    session_data["status"] = "interrupted"
                    
                    # Save directly to file
                    with open(session_file, 'w') as f:
                        json.dump(session_data, f, indent=2)
                    
                    print(f"✅ Session {_current_session_id} marked as interrupted")
        except Exception as e:
            print(f"⚠️  Could not mark session as interrupted: {e}")
    
    print("👋 Research session interrupted. Goodbye!")
    sys.exit(0)


def setup_signal_handlers():
    """Setup signal handlers for graceful shutdown."""
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


def set_current_session(session_manager, session_id):
    """Set the current active session for signal handling."""
    global _current_session_manager, _current_session_id
    _current_session_manager = session_manager
    _current_session_id = session_id


def clear_current_session():
    """Clear the current active session."""
    global _current_session_manager, _current_session_id
    _current_session_manager = None
    _current_session_id = None


def setup_logging(settings: Settings) -> None:
    """Configure logging for the application."""
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
        ]
    )
    
    # Reduce noise from external libraries
    logging.getLogger('google').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)


def print_banner(settings: Settings) -> None:
    """Print application banner."""
    banner_width = settings.banner_width
    print("=" * banner_width)
    print(f"🤖 {settings.app_name} v{settings.app_version}")
    print("Universal Decision Support through AI-Powered Research")
    print("=" * banner_width)
    print()


def main() -> int:
    """Main application entry point."""
    parser = argparse.ArgumentParser(
        description="Deep Research Agent - AI-powered decision support"
    )
    parser.add_argument(
        "--version", 
        action="version",
        version=f"%(prog)s {__version__}"
    )
    parser.add_argument(
        "--config", 
        help="Path to configuration file"
    )
    parser.add_argument(
        "--env", 
        help="Path to environment file"
    )
    parser.add_argument(
        "--debug", 
        action="store_true",
        help="Enable debug mode"
    )
    parser.add_argument(
        "--list-sessions", 
        action="store_true",
        help="List recent research sessions"
    )
    parser.add_argument(
        "--cleanup", 
        type=int,
        metavar="DAYS",
        help="Clean up sessions older than specified days"
    )
    
    args = parser.parse_args()
    
    try:
        # Setup signal handlers for graceful shutdown
        setup_signal_handlers()
        
        # Initialize configuration
        settings = Settings(config_path=args.config, env_path=args.env)
        
        # Override debug mode if specified
        if args.debug:
            settings.config['app']['debug'] = True
        
        # Setup logging
        setup_logging(settings)
        logger = logging.getLogger(__name__)
        
        logger.info(f"Starting {settings.app_name} v{settings.app_version}")
        
        # Initialize session manager for cleanup and signal handling
        session_manager = SessionManager(settings)
        
        # Clean up any truly incomplete sessions on startup
        session_manager.cleanup_incomplete_sessions()
        # Handle utility commands
        if args.list_sessions:
            sessions = session_manager.list_sessions()
            
            if not sessions:
                print("No research sessions found.")
                return 0
            
            print(f"Recent Research Sessions ({len(sessions)}):")
            print("-" * settings.separator_width)
            
            for session in sessions:
                status = session['status']
                # Add visual indicator for interrupted sessions
                status_display = f"❌ {status}" if status == "interrupted" else status
                
                print(f"ID: {session['session_id']}")
                print(f"Created: {session['created_at']}")
                print(f"Query: {session['query']}")
                print(f"Status: {status_display}")
                print(f"Confidence: {session['confidence_score']:.{settings.confidence_decimal_places}f}")
                print("-" * settings.separator_width)
            
            return 0
        
        if args.cleanup is not None:
            deleted_count = session_manager.cleanup_old_sessions(args.cleanup)
            print(f"Cleaned up {deleted_count} sessions older than {args.cleanup} days.")
            return 0
        
        # Start main application
        print_banner(settings)
        
        # Initialize conversation handler
        conversation = ConversationHandler(settings)
        
        # Start interactive session
        conversation.start_interactive_session()
        
        return 0
        
    except ConfigurationError as e:
        print(f"❌ Configuration Error: {e}", file=sys.stderr)
        print("\nPlease check your .env file and configuration.", file=sys.stderr)
        return 1
        
    except KeyboardInterrupt:
        print("\n\n👋 Research session interrupted. Goodbye!")
        return 0
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        if args.debug:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
