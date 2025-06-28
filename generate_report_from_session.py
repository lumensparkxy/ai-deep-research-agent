#!/usr/bin/env python3
"""
Generate Report from Existing Session
Utility script to create reports from previously completed research sessions.
"""

import sys
import json
import logging
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.settings import Settings
from core.report_generator import ReportGenerator
from utils.session_manager import SessionManager


def main():
    """Generate report from the most recent session."""
    
    # Initialize configuration
    settings = Settings()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    # Initialize components
    session_manager = SessionManager(settings)
    report_generator = ReportGenerator(settings)
    
    # Get the most recent session
    sessions = session_manager.list_sessions(limit=1)
    if not sessions:
        print("❌ No sessions found.")
        return 1
    
    most_recent_session = sessions[0]
    session_id = most_recent_session['session_id']
    
    print(f"📄 Generating report for session: {session_id}")
    print(f"   Query: {most_recent_session['query']}")
    print(f"   Created: {most_recent_session['created_at']}")
    
    # Load full session data
    session_data = session_manager.load_session(session_id)
    
    if 'research_results' not in session_data:
        print("❌ Session does not contain research results.")
        return 1
    
    # Ask for report depth
    print("\n📊 Choose your report depth:")
    print("   1. Quick (2-3 pages) - Key findings and top recommendations")
    print("   2. Standard (5-7 pages) - Balanced detail with actionable insights")
    print("   3. Detailed (10+ pages) - Comprehensive analysis with methodology")
    
    while True:
        choice = input("\nReport depth (1/2/3 or quick/standard/detailed): ").strip().lower()
        
        if choice in ['1', 'quick']:
            depth = 'quick'
            break
        elif choice in ['2', 'standard']:
            depth = 'standard'
            break
        elif choice in ['3', 'detailed']:
            depth = 'detailed'
            break
        else:
            print("❌ Invalid choice. Please enter 1, 2, 3, or the depth name.")
    
    # Generate report
    try:
        report_path = report_generator.generate_report(
            session_data=session_data,
            research_results=session_data['research_results'],
            depth=depth
        )
        
        # Update session with report path
        session_manager.update_session_report_path(session_id, report_path)
        
        print(f"\n✅ Report generated successfully!")
        print(f"📁 Report location: {report_path}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Failed to generate report: {e}")
        print(f"❌ Error generating report: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
