# Deep Research Agent

A comprehensive AI-powered decision support system that provides universal decision support through multi-stage iterative research and evidence-based recommendations.

## 🌟 Overview

The Deep Research Agent helps users make informed decisions about ANY topic through thorough analysis, using a 6-stage iterative research process powered by Google Gemini 2.5 Pro AI.

### Key Features

- **Universal Decision Support** - Handle any decision type (health, finance, technology, lifestyle, etc.)
- **AI-Powered Research** - Comprehensive analysis with grounding and search capabilities
- **Evidence-Based Approach** - Prioritize reliable sources and factual information
- **Personalized Recommendations** - Tailored to user's specific context and constraints
- **Comprehensive Reports** - Detailed markdown reports with Quick/Standard/Detailed options
- **Session Management** - Store and retrieve research sessions for future reference

## 🏗️ Architecture

### Core Components

1. **Configuration Management** (`config/`)
   - Environment-driven settings with YAML configuration
   - Validation of required settings
   - Multi-environment support

2. **Session Management** (`utils/session_manager.py`)
   - Unique session IDs with timestamp format: `DRA_YYYYMMDD_HHMMSS`
   - JSON persistence of complete research data
   - Session retrieval and cleanup utilities

3. **Input Validation** (`utils/validators.py`)
   - Comprehensive input sanitization
   - Security-focused validation for all user inputs
   - Query and context validation

4. **Conversational Interface** (`core/conversation.py`)
   - Natural language interaction
   - Intelligent context gathering based on query classification
   - Progress feedback during research

5. **Research Engine** (`core/research_engine.py`) *[In Development]*
   - 6-stage iterative research process
   - Gemini AI integration with grounding/search
   - Confidence scoring and evidence assessment

6. **Report Generation** (`core/report_generator.py`) *[In Development]*
   - Professional markdown reports
   - Three depth levels: Quick, Standard, Detailed
   - Source attribution and confidence indicators

## 🚀 Installation

### Prerequisites

- Python 3.9 or higher
- Google Gemini API key

### Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd deep-research-agent
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env and add your GEMINI_API_KEY
   ```

## 🎯 Usage

### Interactive Research Session

Start an interactive research session:

```bash
python main.py
```

The system will guide you through:
1. **Query Collection** - What decision do you need help with?
2. **Personalization** - Optional context gathering for tailored recommendations
3. **Research Process** - Live progress through 6-stage research
4. **Report Generation** - Choose report depth and receive comprehensive analysis

### Command Line Options

```bash
# Show help
python main.py --help

# List recent sessions
python main.py --list-sessions

# Clean up old sessions (older than 30 days)
python main.py --cleanup 30

# Enable debug mode
python main.py --debug

# Use custom configuration
python main.py --config custom_settings.yaml --env custom.env
```

## 📁 Project Structure

```
deep-research-agent/
├── main.py                     # Entry point
├── requirements.txt            # Dependencies
├── .env.example               # Environment template
├── README.md                  # This file
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

## ⚙️ Configuration

### Environment Variables (.env)

```bash
# Required
GEMINI_API_KEY=your_api_key_here

# Optional (with defaults)
RESEARCH_DEPTH=standard
MAX_RESEARCH_SOURCES=10
SESSION_STORAGE_PATH=./data/sessions
REPORT_OUTPUT_PATH=./data/reports
LOG_LEVEL=INFO
```

### YAML Configuration (config/settings.yaml)

The YAML file contains structured configuration for:
- Application settings
- Research parameters
- AI model configuration
- Output formatting options
- Personalization categories

## 🔬 Research Methodology

The Deep Research Agent uses a 6-stage iterative process:

1. **Information Gathering** - Broad exploration and initial research
2. **Validation & Fact-Checking** - Verify findings and identify knowledge gaps
3. **Clarification & Follow-up** - Fill gaps and address ambiguities
4. **Comparative Analysis** - Systematic comparison of options/alternatives
5. **Synthesis & Integration** - Combine all findings into coherent insights
6. **Final Conclusions** - Evidence-based recommendations with confidence scores

## 📊 Report Types

### Quick (2-3 pages)
- Executive summary
- Key recommendations
- Top sources

### Standard (5-7 pages)
- Executive summary
- Research overview
- Detailed analysis
- Recommendations
- Implementation guidance
- Sources

### Detailed (10+ pages)
- Complete methodology
- Stage-by-stage analysis
- Comparative analysis
- Risk assessment
- Success metrics
- Comprehensive sources

## 🔐 Security & Privacy

- **Local Storage**: All data stored locally on your machine
- **Input Sanitization**: Comprehensive validation prevents injection attacks
- **API Key Protection**: Never logged or exposed in output
- **File System Security**: Path validation prevents directory traversal

## 🛠️ Development Status

### ✅ Completed (Foundation - Stage 1)
- Configuration management system
- Session persistence and management
- Input validation and sanitization
- Conversational user interface
- Project architecture and structure
- Error handling and logging

### 🚧 In Development
- **Stage 2**: Full Research Engine with Gemini AI integration
- **Stage 3**: Comprehensive Report Generation system
- **Stage 4**: Enhanced personalization features
- **Stage 5**: Advanced user interface improvements
- **Stage 6**: Production deployment optimization

## 🤝 Contributing

This project follows a structured implementation approach:

1. Each stage builds upon the previous foundation
2. Modular design allows independent component development
3. Comprehensive testing and validation at each stage
4. Production-ready code with proper error handling

## 📄 License

[License information to be added]

## 🔗 Links

- [API Documentation](docs/api.md) *[Coming soon]*
- [Development Guide](docs/development.md) *[Coming soon]*
- [Deployment Guide](docs/deployment.md) *[Coming soon]*

---

**Current Version**: 1.0.0 (Foundation)  
**Last Updated**: June 28, 2025

For questions, issues, or contributions, please refer to the project's issue tracker and contribution guidelines.
