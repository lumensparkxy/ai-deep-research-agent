Implement the core Research Engine module for the Deep Research Agent with the following 6-stage iterative process:

**Stage 1: Information Gathering**
- Broad exploration of the topic using Gemini 2.5 Pro with grounding
- Extract research areas, key factors, and evidence types needed
- Build initial knowledge base

**Stage 2: Validation & Fact-Checking**
- Verify initial findings for accuracy and reliability
- Identify knowledge gaps and inconsistencies
- Assess source reliability and determine follow-up needs

**Stage 3: Clarification & Follow-up**
- Fill identified knowledge gaps through targeted research
- Gather additional facts, figures, and expert opinions
- Refine understanding of the topic

**Stage 4: Comparative Analysis**
- Systematic comparison of options/alternatives
- Create comparison matrices with pros/cons
- Quantitative analysis where applicable

**Stage 5: Synthesis & Integration**
- Combine findings from all previous stages
- Identify key insights and patterns
- Create executive summary of research

**Stage 6: Final Conclusions**
- Generate evidence-based recommendations
- Assign confidence scores based on research quality
- Create implementation plans and risk assessments

**Key Implementation Details:**
- Each stage should build upon previous stages' findings
- Store stage results in structured format for report generation
- Include progress feedback to user during research
- Handle API failures gracefully with informative error messages
- Calculate overall confidence score based on research completeness
- Support both general and personalized research paths

**Source Reliability Assessment:**
- The system will use an AI-based assessment to determine the reliability of each source.
- The Gemini model will be prompted to evaluate the source's content, author credentials, citations, and potential biases to generate a reliability score (0.0 to 1.0).

**Data Structure for Research Session:**
```json
{
  "query": "user's research question",
  "context": {...},
  "stages": [
    {
      "stage": 1,
      "name": "Information Gathering",
      "findings": {
        "summary": "A brief, natural-language summary of the key findings from this stage.",
        "evidence": [
          {
            "source_url": "http://example.com/source1",
            "source_name": "Example News",
            "reliability_score": 0.8,
            "extracted_text": "A relevant quote or data point from the source.",
            "relevance_score": 0.9
          }
        ],
        "gaps_identified": [
          "What is the long-term impact?",
          "Are there alternative solutions?"
        ]
      },
      "timestamp": "ISO timestamp"
    }
  ],
  "knowledge_base": {
    "entities": [],
    "relationships": [],
    "key_facts": []
  },
  "final_conclusions": {...},
  "confidence_score": 0.85
}
```

**Gemini Integration:**
- Use appropriate prompts for each research stage
- Leverage grounding/search for evidence-based findings
- Structure responses to extract actionable insights
- Implement proper rate limiting and error handling

**Stage-Specific Prompting Strategy:**
- **Stage 1**: "Research the following query using reliable sources and provide evidence-based information..."
- **Stage 2**: "Validate and fact-check the following initial findings..."
- **Stage 3**: "Fill the following knowledge gaps through targeted research..."
- **Stage 4**: "Conduct systematic comparison of the following options..."
- **Stage 5**: "Synthesize all research findings into coherent insights..."
- **Stage 6**: "Generate final conclusions with evidence-based recommendations..."

**Error Handling & Fallbacks:**
- Implement mock responses for when AI services are unavailable
- Graceful degradation with reduced functionality
- Clear user communication about service limitations
- Retry mechanisms for transient failures

The engine should be modular, allowing individual stages to be modified or extended while maintaining the overall research flow.