Create a comprehensive AI-powered Deep Research Agent that provides universal decision support through multi-stage iterative research and evidence-based recommendations. This system MUST help users make informed decisions about ANY topic through thorough analysis.

**Core Architecture:**
- **Conversational Interface**: Natural language interaction (CLI, web, or chat interface)
- **Modular Design**: Independent core modules that can be extended or replaced
- **Configuration-Driven**: Environment variables and config files for all settings
- **Session-Based**: Each research session stored with unique identifiers
- **Multi-Stage Research**: 6-stage iterative validation process
- **Report Generation**: Professional markdown reports with customizable depth

**Key Features:**
1. **Universal Decision Support** - Handle any decision type (health, finance, technology, lifestyle, etc.)
2. **AI-Powered Research** - Use Gemini 2.5 Pro for comprehensive analysis with grounding/search
3. **Evidence-Based Approach** - Prioritize reliable sources and factual information
4. **Personalized Recommendations** - Tailored to user's specific context and constraints
5. **Comprehensive Reports** - Detailed markdown reports with Quick/Standard/Detailed options
6. **Session Management** - Store and retrieve research sessions for future reference

**Research Methodology (6-Stage Iterative Process):**
1. **Information Gathering** - Broad exploration and initial research
2. **Validation & Fact-Checking** - Verify findings and identify knowledge gaps
3. **Clarification & Follow-up** - Fill gaps and address ambiguities
4. **Comparative Analysis** - Systematic comparison of options/alternatives
5. **Synthesis & Integration** - Combine all findings into coherent insights
6. **Final Conclusions** - Evidence-based recommendations with confidence scores

**Technical Requirements:**
- **AI Integration**: Gemini 2.5 Pro API with grounding/search capabilities
- **Data Storage**: Local files (JSON for sessions, Markdown for reports)
- **Configuration**: Environment variables + YAML/JSON config files
- **Error Handling**: Graceful degradation and user-friendly error messages
- **Modularity**: Core components MUST be independent and extensible
- **Progress Feedback**: Real-time updates during multi-stage research process
- **Input Validation**: Sanitize and validate all user inputs for security
- **Confidence Scoring**: Calculate and display research confidence levels using a hybrid model that considers source quality, evidence consistency, and AI self-assessment.

**User Experience Flow:**
1. User provides initial query/decision need
2. System asks clarifying questions and gathers context
3. Optional personalization (demographics, constraints, preferences)
4. Multi-stage research process with progress updates
5. Report generation with customizable depth
6. Session storage for future reference

**Core Modules to Implement:**
- **Conversation Handler**: Manages user interaction and context gathering
- **Research Engine**: Conducts the 6-stage iterative research process
- **Report Generator**: Creates professional markdown reports
- **Session Manager**: Handles data persistence and retrieval
- **Configuration Manager**: Manages settings and environment variables
- **Input Validator**: Ensures data quality and security

**Implementation Guidelines:**
- Design for extensibility - new research stages or data sources SHOULD be easy to add
- Implement comprehensive logging for debugging and monitoring
- Use structured data formats (JSON) for internal data exchange
- Create clear separation between interface logic and core functionality
- Build with deployment flexibility in mind (local, cloud, containerized)
- Ensure graceful handling of API rate limits and network issues

Create a production-ready system that can be easily deployed, extended, and maintained. Focus on clean architecture, proper error handling, and excellent user experience.