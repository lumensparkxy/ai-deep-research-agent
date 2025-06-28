# Copilot Instructions for Deep Research Agent Implementation

## Project Overview
You are helping implement a comprehensive AI-powered Deep Research Agent that provides universal decision support through multi-stage iterative research and evidence-based recommendations.

## Implementation Sequence
Execute the prompts in this exact order:
1. `001_Main System Prompt.md` - Foundation and architecture
2. `002_Supplementary Prompt 1: Research Engine Implementation.md` - Core research logic
3. `003_Supplementary Prompt 2: Report Generation System.md` - Report creation system
4. `004_Supplementary Prompt 3: Configuration & Session Management.md` - Settings and data persistence
5. `005_Supplementary Prompt 4: User Interface & Interaction Design.md` - User interaction flow
6. `006_Supplementary Prompt 5: Deployment & Production.md` - Production deployment setup

## Key Implementation Guidelines

### Code Quality Standards
- Follow Python PEP 8 style guidelines
- Use type hints for all function parameters and return values
- Implement comprehensive error handling with informative messages
- Add docstrings to all classes and methods
- Use structured logging instead of print statements

### Architecture Principles
- **Modular Design**: Each core module MUST be independent and extensible
- **Configuration-Driven**: All settings via environment variables and config files
- **Session-Based**: Every research session MUST have unique identifiers and be persistable
- **Error Resilience**: Graceful degradation when external services fail
- **Progressive Enhancement**: Core functionality works even with minimal configuration

### File Structure Requirements
```
project/
├── main.py                     # Entry point
├── requirements.txt            # Dependencies
├── .env.example               # Environment template
├── config/
│   ├── __init__.py
│   ├── settings.py            # Configuration management
│   └── settings.yaml          # Default settings
├── core/
│   ├── __init__.py
│   ├── research_engine.py     # 6-stage research process
│   ├── report_generator.py    # Markdown report creation
│   └── conversation.py        # User interaction handling
├── utils/
│   ├── __init__.py
│   ├── session_manager.py     # Session persistence
│   └── validators.py          # Input validation
└── data/
    ├── sessions/              # JSON session files
    └── reports/               # Generated markdown reports
```

### Critical Implementation Details

#### Research Engine (Stage 2)
- Implement exactly 6 stages: Information Gathering → Validation → Clarification → Comparative Analysis → Synthesis → Final Conclusions
- Each stage MUST build upon previous findings
- Store all stage results in structured JSON format
- Calculate confidence scores based on source reliability and evidence consistency
- Handle API rate limiting and network failures gracefully

#### Session Management (Stage 4)
- Session IDs format: `DRA_YYYYMMDD_HHMMSS`
- Store complete research data as JSON files in `data/sessions/`
- Include query, context, all stage results, and report paths
- Implement session retrieval for future reference

#### Report Generation (Stage 3)
- Three depth levels: Quick (2-3 pages), Standard (5-7 pages), Detailed (10+ pages)
- Professional markdown with proper headers, emojis, and formatting
- Include confidence scores and source attribution
- Save to `data/reports/` with descriptive filenames

#### Configuration System (Stage 4)
- Load from `.env` file and `config/settings.yaml`
- Validate all required settings on startup
- Provide sensible defaults for optional configurations
- Support multiple environments (dev, staging, production)

### API Integration Requirements
- Use Google Gemini 2.5 Pro with grounding/search capabilities
- Implement proper error handling for API failures
- Respect rate limits with exponential backoff
- Structure prompts for each research stage appropriately
- Extract structured data from AI responses

### User Experience Requirements
- Conversational CLI interface with clear progress indicators
- Intelligent context gathering based on query classification
- Real-time updates during multi-stage research process
- Input validation and sanitization for security
- Graceful error recovery with helpful messages

### Testing & Quality Assurance
- Include error handling tests for API failures
- Validate configuration loading and environment setup
- Test session persistence and retrieval
- Verify report generation for all depth levels
- Check input validation and sanitization

### Security Considerations
- Never log or expose API keys
- Sanitize all user inputs to prevent injection attacks
- Implement proper file system permissions
- Validate file paths to prevent directory traversal

### Performance Guidelines
- Keep API calls efficient with targeted prompts
- Implement progress feedback for long-running operations
- Use appropriate data structures for research findings
- Handle large research datasets efficiently

## Development Workflow
1. Start with configuration and environment setup
2. Implement core modules in dependency order
3. Test each module independently before integration
4. Build user interface layer last
5. Add comprehensive error handling throughout
6. Validate entire workflow with sample queries

## Common Pitfalls to Avoid
- DO NOT implement caching or async processing in MVP (deferred features)
- DO NOT skip input validation and sanitization
- DO NOT hardcode file paths or API endpoints
- DO NOT ignore rate limiting and error handling
- DO NOT create circular dependencies between modules

## Success Criteria
The implementation is complete when:
- A user can input any research query
- The system conducts 6-stage iterative research
- Professional reports are generated in all depth levels
- Sessions are properly stored and retrievable
- The system handles errors gracefully
- Configuration is environment-driven and flexible

## MVP Focus
The initial release SHOULD focus on core functionality:
- Basic CLI interface
- Complete 6-stage research process
- Report generation (all depths)
- Session management
- Configuration system
- Essential error handling

Advanced features (caching, async processing, web interface) are deferred to future releases.
