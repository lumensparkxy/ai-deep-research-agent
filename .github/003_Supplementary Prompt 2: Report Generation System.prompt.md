Create a comprehensive Report Generator that produces professional markdown reports from research results with three depth levels:

**Report Depth Options:**
1. **Quick (2-3 pages)** - Key findings and top recommendations only
2. **Standard (5-7 pages)** - Balanced detail with actionable insights
3. **Detailed (10+ pages)** - Comprehensive analysis with methodology

**Standard Report Structure:**
- **Header**: Query, timestamp, session ID, confidence score
- **Executive Summary**: Key findings and primary recommendation
- **Research Process Overview**: Brief methodology explanation
- **Detailed Analysis**: Stage-by-stage findings (for detailed reports)
- **Recommendations**: Prioritized, actionable suggestions with pros/cons
- **Implementation Plan**: Step-by-step guidance
- **Risk Assessment**: Potential challenges and mitigation strategies
- **Success Metrics**: How to measure outcomes
- **Sources & References**: Research sources with confidence indicators
- **Confidence Assessment**: Overall reliability scoring

**Content Extraction Methods:**
- Parse research stage results to extract relevant information
- Format findings with proper markdown structure
- Include confidence scores and source attribution
- Generate actionable recommendations with priority levels
- Create comparison tables for alternative options

**File Management:**
- Generate unique filenames with session ID and query slug
- Save reports to designated output directory
- Support both regular and iterative research formats
- Include metadata for future reference

**Formatting Requirements:**
- Professional markdown with proper headers and sections
- Consistent styling across all report types
- Include emojis and visual elements for readability
- Proper code blocks for structured data
- Clear section separation and logical flow

**Sample Report Header:**
```markdown
# Deep Research Report

**Query**: [User's question]  
**Generated**: [Timestamp]  
**Session ID**: [Unique identifier]  
**Confidence Score**: [XX.X%]

---

## 📋 Executive Summary
[Key findings and primary recommendation]

## 🔍 Research Analysis
[Methodology and findings overview]
```

**Content Extraction Helpers:**
- Extract key insights from final conclusions
- Parse confidence scores and risk assessments
- Format comparison tables for alternatives
- Generate action items from implementation plans
- Create source attribution with reliability indicators

**Reliability Indicators:**
- Each source cited in the report will be accompanied by its raw numeric reliability score (e.g., "Reliability: 0.85").
- The score, ranging from 0.0 to 1.0, is derived from the AI-based assessment defined in the Research Engine module.

The report generator should produce publication-ready documents that users can share, reference, or use for decision-making.