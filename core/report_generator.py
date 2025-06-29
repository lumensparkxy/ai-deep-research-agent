"""
Report Generator for Deep Research Agent
Creates professional markdown reports from research results with multiple depth levels.
"""

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from config.settings import Settings


class ReportGenerator:
    """Professional report generation system with multiple depth levels."""
    
    def __init__(self, settings: Settings):
        """Initialize report generator."""
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        
        # Ensure report directory exists
        self.report_dir = Path(self.settings.report_output_path)
        self.report_dir.mkdir(parents=True, exist_ok=True)
        
        # Report depth configurations
        self.depth_configs = {
            "quick": {
                "max_pages": 3,
                "sections": ["executive_summary", "key_recommendations", "sources"],
                "max_evidence": 5,
                "max_recommendations": 3
            },
            "standard": {
                "max_pages": 7,
                "sections": ["executive_summary", "research_overview", "detailed_analysis", 
                           "recommendations", "implementation", "sources"],
                "max_evidence": 15,
                "max_recommendations": 8
            },
            "detailed": {
                "max_pages": 15,
                "sections": ["executive_summary", "methodology", "stage_analysis", 
                           "detailed_findings", "comparative_analysis", "recommendations", 
                           "implementation", "risk_assessment", "success_metrics", "sources"],
                "max_evidence": 30,
                "max_recommendations": 15
            }
        }
        
        # Override with settings if available
        config_depths = self.settings.report_depths
        for depth_name, config in config_depths.items():
            if depth_name in self.depth_configs:
                # Update with values from settings
                self.depth_configs[depth_name].update({
                    "max_evidence": config.get("max_evidence", self.depth_configs[depth_name]["max_evidence"]),
                    "max_recommendations": config.get("max_recommendations", self.depth_configs[depth_name]["max_recommendations"]),
                    "max_facts_per_stage": config.get("max_facts_per_stage", 5),
                    "max_insights_per_section": config.get("max_insights_per_section", 10)
                })
    
    def generate_report(self, session_data: Dict[str, Any], 
                       research_results: Dict[str, Any], depth: str) -> str:
        """
        Generate comprehensive report from research results.
        
        Args:
            session_data: Complete session information
            research_results: Research findings from all stages
            depth: Report depth level (quick/standard/detailed)
            
        Returns:
            Path to generated report file
        """
        try:
            # Validate inputs
            if depth not in self.depth_configs:
                depth = "standard"
                self.logger.warning(f"Invalid depth provided, using standard")
            
            # Generate filename
            filename = self._generate_filename(session_data)
            report_path = self.report_dir / filename
            
            # Build report content
            report_content = self._build_report_content(
                session_data, research_results, depth
            )
            
            # Save report
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            self.logger.info(f"Generated {depth} report: {report_path}")
            return str(report_path)
            
        except Exception as e:
            self.logger.error(f"Failed to generate report: {e}")
            # Generate minimal fallback report
            return self._generate_fallback_report(session_data, research_results, depth)
    
    def _generate_filename(self, session_data: Dict[str, Any]) -> str:
        """Generate descriptive filename for report."""
        session_id = session_data.get("session_id", "unknown")
        query = session_data.get("query", "research")
        
        # Create query slug (safe filename)
        query_slug = re.sub(r'[^\w\s-]', '', query)
        query_slug = re.sub(r'[-\s]+', '_', query_slug)
        query_slug = query_slug[:self.settings.filename_query_max_length]  # Limit length
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{session_id}_{query_slug}.md"
    
    def _build_report_content(self, session_data: Dict[str, Any], 
                            research_results: Dict[str, Any], depth: str) -> str:
        """Build complete report content based on depth level."""
        config = self.depth_configs[depth]
        sections = config["sections"]
        
        # Extract data
        query = session_data.get("query", "Research Query")
        session_id = session_data.get("session_id", "Unknown")
        context = session_data.get("context", {})
        stages = research_results.get("stages", [])
        conclusions = research_results.get("final_conclusions", {})
        confidence = research_results.get("confidence_score", 0.0)
        
        # Start building report
        content_parts = []
        
        # Header
        content_parts.append(self._build_header(query, session_id, confidence, depth))
        
        # Build sections based on depth configuration
        if "executive_summary" in sections:
            content_parts.append(self._build_executive_summary(conclusions, context, config))
        
        if "methodology" in sections:
            content_parts.append(self._build_methodology_section(stages))
        
        if "research_overview" in sections:
            content_parts.append(self._build_research_overview(stages, config))
        
        if "stage_analysis" in sections:
            content_parts.append(self._build_stage_analysis(stages, config))
        
        if "detailed_analysis" in sections:
            content_parts.append(self._build_detailed_analysis(stages, config))
        
        if "detailed_findings" in sections:
            content_parts.append(self._build_detailed_findings(stages, config))
        
        if "comparative_analysis" in sections:
            content_parts.append(self._build_comparative_analysis(stages, config))
        
        if "recommendations" in sections:
            content_parts.append(self._build_recommendations(conclusions, config))
        
        if "key_recommendations" in sections:
            content_parts.append(self._build_key_recommendations(conclusions, config))
        
        if "implementation" in sections:
            content_parts.append(self._build_implementation_plan(conclusions, config))
        
        if "risk_assessment" in sections:
            content_parts.append(self._build_risk_assessment(conclusions, config))
        
        if "success_metrics" in sections:
            content_parts.append(self._build_success_metrics(conclusions, config))
        
        if "sources" in sections:
            content_parts.append(self._build_sources_section(stages, config))
        
        # Footer
        content_parts.append(self._build_footer(session_data, research_results))
        
        return "\n\n".join(content_parts)
    
    def _build_header(self, query: str, session_id: str, confidence: float, depth: str) -> str:
        """Build report header."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return f"""# 📊 Deep Research Report

**Query**: {query}  
**Generated**: {timestamp}  
**Session ID**: {session_id}  
**Confidence Score**: {confidence:.1%}  
**Report Depth**: {depth.title()}

---"""
    
    def _build_executive_summary(self, conclusions: Dict[str, Any], 
                               context: Dict[str, Any], config: Dict[str, Any]) -> str:
        """Build executive summary section."""
        summary = conclusions.get("summary", "Research completed successfully.")
        primary_rec = conclusions.get("primary_recommendation", "")
        
        content = f"""## 📋 Executive Summary

{summary}"""
        
        if primary_rec:
            content += f"""

### 🎯 Primary Recommendation
{primary_rec}"""
        
        # Add personalization context if available
        if context.get("personalize") and context.get("user_info"):
            content += f"""

### 👤 Personalized For
- **Profile**: {self._format_user_context(context)}"""
        
        return content
    
    def _build_methodology_section(self, stages: List[Dict[str, Any]]) -> str:
        """Build methodology section for detailed reports."""
        return f"""## 🔬 Research Methodology

This report was generated using a comprehensive 6-stage iterative research process:

1. **Information Gathering** - Initial broad exploration and evidence collection
2. **Validation & Fact-Checking** - Verification of findings and gap identification  
3. **Clarification & Follow-up** - Targeted research to fill knowledge gaps
4. **Comparative Analysis** - Systematic comparison of options and alternatives
5. **Synthesis & Integration** - Integration of all findings into coherent insights
6. **Final Conclusions** - Evidence-based recommendations and implementation guidance

**Stages Completed**: {len(stages)}/6  
**Research Quality**: Each finding includes source reliability scores and relevance assessments"""
    
    def _clean_response_text(self, text: str) -> str:
        """
        Clean malformed JSON responses or raw text for display in reports.
        
        Args:
            text: Raw text that might contain malformed JSON
            
        Returns:
            Cleaned text suitable for display
        """
        if not text:
            return "No summary available"
            
        # Check if text starts with JSON markdown
        if text.startswith("```json"):
            # Try to extract the JSON content and parse it
            try:
                # Remove markdown formatting
                json_text = text.replace("```json\n", "").replace("```", "")
                
                # Try to parse as JSON
                import json
                parsed = json.loads(json_text)
                
                # Extract summary if it exists
                if isinstance(parsed, dict) and "summary" in parsed:
                    return parsed["summary"]
                
            except (json.JSONDecodeError, ValueError):
                # If JSON parsing fails, try to extract summary manually
                if '"summary":' in text:
                    try:
                        # Find the summary value
                        start = text.find('"summary": "') + 12
                        end = text.find('",', start)
                        if end == -1:
                            end = text.find('"', start)
                        if start > 11 and end > start:
                            summary = text[start:end]
                            # Clean up escape characters
                            return summary.replace('\\"', '"').replace('\\n', ' ')
                    except:
                        pass
                
                # Fallback: return first line without markdown
                first_line = text.split('\n')[0]
                if first_line.startswith("```"):
                    return "Stage analysis completed"
                return first_line
        
        return text

    def _build_research_overview(self, stages: List[Dict[str, Any]], config: Dict[str, Any]) -> str:
        """Build research process overview."""
        content = """## 🔍 Research Process Overview

### Research Stages Completed"""
        
        for i, stage in enumerate(stages[:6], 1):
            stage_name = stage.get("name", f"Stage {i}")
            findings = stage.get("findings", {})
            raw_summary = findings.get("summary", "Stage completed")
            
            # Clean the summary text
            summary = self._clean_response_text(raw_summary)
            
            content += f"""

**Stage {i}: {stage_name}**  
{summary}"""
        
        return content
    
    def _build_stage_analysis(self, stages: List[Dict[str, Any]], config: Dict[str, Any]) -> str:
        """Build detailed stage-by-stage analysis."""
        content = """## 📊 Stage-by-Stage Analysis"""
        
        for i, stage in enumerate(stages, 1):
            stage_name = stage.get("name", f"Stage {i}")
            findings = stage.get("findings", {})
            raw_summary = findings.get("summary", "No summary available")
            
            # Clean the summary text
            summary = self._clean_response_text(raw_summary)
            
            content += f"""

### Stage {i}: {stage_name}

**Summary**: {summary}"""
            
            # Add key findings
            if "key_facts" in findings:
                facts = findings["key_facts"][:self.settings.facts_display_limit]  # Limit for readability
                if facts:
                    content += "\n\n**Key Findings**:"
                    for fact in facts:
                        content += f"\n- {fact}"
            
            # Add evidence count
            evidence = findings.get("evidence", [])
            if evidence:
                avg_reliability = sum(e.get("reliability_score", 0) for e in evidence) / len(evidence)
                content += f"\n\n**Evidence**: {len(evidence)} sources (avg. reliability: {avg_reliability:.1%})"
        
        return content
    
    def _build_detailed_analysis(self, stages: List[Dict[str, Any]], config: Dict[str, Any]) -> str:
        """Build detailed analysis section."""
        content = """## 📈 Detailed Analysis"""
        
        # Aggregate insights across stages
        all_insights = []
        all_evidence = []
        
        for stage in stages:
            findings = stage.get("findings", {})
            
            # Collect insights
            if "key_insights" in findings:
                all_insights.extend(findings["key_insights"])
            if "patterns_identified" in findings:
                all_insights.extend(findings["patterns_identified"])
            if "key_facts" in findings:
                all_insights.extend(findings["key_facts"][:3])  # Top facts only
            
            # Collect evidence
            if "evidence" in findings:
                all_evidence.extend(findings["evidence"])
        
        # Key insights
        if all_insights:
            content += "\n\n### 🧠 Key Insights"
            max_insights = config.get("max_insights_per_section", self.settings.evidence_display_limit)
            for insight in all_insights[:max_insights]:
                content += f"\n- {insight}"
        
        # Evidence quality analysis
        if all_evidence:
            high_quality = [e for e in all_evidence if e.get("reliability_score", 0) >= 0.8]
            content += f"""

### 📊 Evidence Quality
- **Total Sources**: {len(all_evidence)}
- **High-Quality Sources** (≥80% reliability): {len(high_quality)}
- **Average Reliability**: {sum(e.get("reliability_score", 0) for e in all_evidence) / len(all_evidence):.1%}"""
        
        return content
    
    def _build_detailed_findings(self, stages: List[Dict[str, Any]], config: Dict[str, Any]) -> str:
        """Build comprehensive findings section."""
        content = """## 🔎 Detailed Findings"""
        
        # Group findings by category
        findings_by_category = {
            "Facts & Evidence": [],
            "Patterns & Insights": [],
            "Gaps & Limitations": []
        }
        
        for stage in stages:
            findings = stage.get("findings", {})
            
            # Facts and evidence
            if "key_facts" in findings:
                findings_by_category["Facts & Evidence"].extend(findings["key_facts"])
            if "validated_facts" in findings:
                findings_by_category["Facts & Evidence"].extend(findings["validated_facts"])
            
            # Patterns and insights
            if "key_insights" in findings:
                findings_by_category["Patterns & Insights"].extend(findings["key_insights"])
            if "patterns_identified" in findings:
                findings_by_category["Patterns & Insights"].extend(findings["patterns_identified"])
            
            # Gaps and limitations
            if "gaps_identified" in findings:
                findings_by_category["Gaps & Limitations"].extend(findings["gaps_identified"])
            if "remaining_gaps" in findings:
                findings_by_category["Gaps & Limitations"].extend(findings["remaining_gaps"])
        
        # Build sections
        for category, items in findings_by_category.items():
            if items:
                content += f"\n\n### {category}"
                max_items = self.settings.content_limits.get("category_items_limit", 10)
                for item in items[:max_items]:  # Limit items per category
                    content += f"\n- {item}"
        
        return content
    
    def _build_comparative_analysis(self, stages: List[Dict[str, Any]], config: Dict[str, Any]) -> str:
        """Build comparative analysis section."""
        content = """## ⚖️ Comparative Analysis"""
        
        # Find comparative analysis stage
        comp_stage = None
        for stage in stages:
            if stage.get("name") == "Comparative Analysis":
                comp_stage = stage
                break
        
        if comp_stage:
            findings = comp_stage.get("findings", {})
            
            # Options comparison
            options = findings.get("options_identified", [])
            if options:
                content += "\n\n### Options Evaluated"
                max_options = self.settings.content_limits.get("options_comparison_limit", 5)
                for i, option in enumerate(options[:max_options], 1):
                    content += f"""

**Option {i}: {option.get("option", "Unknown")}**
- **Description**: {option.get("description", "No description")}
- **Score**: {option.get("score", 0):.1%}"""
                    
                    pros = option.get("pros", [])
                    cons = option.get("cons", [])
                    
                    pros_limit = self.settings.content_limits.get("pros_cons_display_limit", 3)
                    cons_limit = self.settings.content_limits.get("pros_cons_display_limit", 3)
                    
                    if pros:
                        content += "\n- **Pros**: " + "; ".join(pros[:pros_limit])
                    if cons:
                        content += "\n- **Cons**: " + "; ".join(cons[:cons_limit])
            
            # Standout recommendations
            standouts = findings.get("standout_recommendations", [])
            if standouts:
                content += "\n\n### Standout Options"
                max_standouts = self.settings.content_limits.get("standout_recommendations_limit", 3)
                for rec in standouts[:max_standouts]:
                    content += f"\n- {rec}"
        else:
            content += "\n\nComparative analysis was not completed in this research session."
        
        return content
    
    def _build_recommendations(self, conclusions: Dict[str, Any], config: Dict[str, Any]) -> str:
        """Build comprehensive recommendations section."""
        content = """## 🎯 Recommendations"""
        
        recommendations = conclusions.get("recommendations", [])
        
        if recommendations:
            # Group by priority
            high_priority = [r for r in recommendations if r.get("priority") == "high"]
            medium_priority = [r for r in recommendations if r.get("priority") == "medium"]
            low_priority = [r for r in recommendations if r.get("priority") == "low"]
            other = [r for r in recommendations if r.get("priority") not in ["high", "medium", "low"]]
            
            for priority_group, title in [
                (high_priority, "🔴 High Priority"),
                (medium_priority, "🟡 Medium Priority"), 
                (low_priority, "🟢 Low Priority"),
                (other, "📌 Additional Recommendations")
            ]:
                if priority_group:
                    content += f"\n\n### {title}"
                    max_recs = min(config["max_recommendations"], 
                                 self.settings.content_limits.get("priority_items_limit", 3) 
                                 if priority_group == high_priority else config["max_recommendations"])
                    for rec in priority_group[:max_recs]:
                        rec_text = rec.get("recommendation", "No recommendation text")
                        reasoning = rec.get("reasoning", "")
                        confidence = rec.get("confidence", 0)
                        
                        content += f"""

**{rec_text}**
- **Reasoning**: {reasoning}
- **Confidence**: {confidence:.1%}"""
        else:
            content += "\n\nNo specific recommendations were generated."
        
        return content
    
    def _build_key_recommendations(self, conclusions: Dict[str, Any], config: Dict[str, Any]) -> str:
        """Build key recommendations section for quick reports."""
        content = """## 🎯 Key Recommendations"""
        
        primary_rec = conclusions.get("primary_recommendation", "")
        if primary_rec:
            content += f"\n\n### Primary Recommendation\n{primary_rec}"
        
        recommendations = conclusions.get("recommendations", [])[:config["max_recommendations"]]
        
        if recommendations:
            content += "\n\n### Top Recommendations"
            for i, rec in enumerate(recommendations, 1):
                rec_text = rec.get("recommendation", "No recommendation")
                confidence = rec.get("confidence", 0)
                content += f"\n{i}. **{rec_text}** (Confidence: {confidence:.1%})"
        
        return content
    
    def _build_implementation_plan(self, conclusions: Dict[str, Any], config: Dict[str, Any]) -> str:
        """Build implementation plan section."""
        content = """## 🚀 Implementation Plan"""
        
        plan = conclusions.get("implementation_plan", [])
        
        if plan:
            content += "\n\n### Action Steps"
            for i, step in enumerate(plan, 1):
                step_desc = step.get("description", step.get("step", "Action step"))
                timeline = step.get("timeline", "TBD")
                content += f"\n{i}. **{step_desc}**"
                if timeline != "TBD":
                    content += f" (Timeline: {timeline})"
        else:
            content += "\n\nImplementation guidance was not provided in this research."
        
        return content
    
    def _build_risk_assessment(self, conclusions: Dict[str, Any], config: Dict[str, Any]) -> str:
        """Build risk assessment section."""
        content = """## ⚠️ Risk Assessment"""
        
        risks = conclusions.get("risk_assessment", [])
        
        if risks:
            content += "\n\n### Identified Risks"
            for risk in risks:
                risk_desc = risk.get("risk", "Unspecified risk")
                likelihood = risk.get("likelihood", "unknown")
                impact = risk.get("impact", "unknown")
                mitigation = risk.get("mitigation", "No mitigation provided")
                
                content += f"""

**{risk_desc}**
- **Likelihood**: {likelihood.title()}
- **Impact**: {impact.title()}
- **Mitigation**: {mitigation}"""
        else:
            content += "\n\nNo specific risks were identified in this research."
        
        return content
    
    def _build_success_metrics(self, conclusions: Dict[str, Any], config: Dict[str, Any]) -> str:
        """Build success metrics section."""
        content = """## 📈 Success Metrics"""
        
        metrics = conclusions.get("success_metrics", [])
        
        if metrics:
            content += "\n\n### Key Performance Indicators"
            for metric in metrics:
                content += f"\n- {metric}"
        else:
            content += "\n\nSuccess metrics were not defined in this research."
        
        return content
    
    def _build_sources_section(self, stages: List[Dict[str, Any]], config: Dict[str, Any]) -> str:
        """Build sources and references section."""
        content = """## 📚 Sources & References"""
        
        # Collect all evidence sources
        all_sources = []
        for stage in stages:
            evidence = stage.get("findings", {}).get("evidence", [])
            all_sources.extend(evidence)
        
        if all_sources:
            # Sort by reliability score (highest first)
            all_sources.sort(key=lambda x: x.get("reliability_score", 0), reverse=True)
            
            content += f"\n\n**Total Sources**: {len(all_sources)}"
            content += f"  \n**Average Reliability**: {sum(s.get('reliability_score', 0) for s in all_sources) / len(all_sources):.1%}"
            
            content += "\n\n### Source Details"
            
            for i, source in enumerate(all_sources[:config["max_evidence"]], 1):
                source_name = source.get("source_description", source.get("source_name", f"Source {i}"))
                reliability = source.get("reliability_score", 0)
                relevance = source.get("relevance_score", 0)
                extract = source.get("extracted_text", "")
                
                content += f"""

**{i}. {source_name}**
- **Reliability**: {reliability:.1%}
- **Relevance**: {relevance:.1%}"""
                
                if extract:
                    extract_length = self.settings.source_extract_preview_length
                    content += f"\n- **Extract**: \"{extract[:extract_length]}{'...' if len(extract) > extract_length else ''}\""""
        else:
            content += "\n\nNo sources were documented in this research."
        
        return content
    
    def _build_footer(self, session_data: Dict[str, Any], research_results: Dict[str, Any]) -> str:
        """Build report footer."""
        return f"""---

## 📄 Report Information

**System**: Deep Research Agent v{session_data.get('version', '1.0.0')}  
**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Session ID**: {session_data.get('session_id', 'Unknown')}  
**Research Confidence**: {research_results.get('confidence_score', 0):.1%}

*This report was generated using AI-powered research with evidence-based analysis. All sources include reliability scores for quality assessment.*"""
    
    def _format_user_context(self, context: Dict[str, Any]) -> str:
        """Format user context for display."""
        parts = []
        
        user_info = context.get("user_info", {})
        constraints = context.get("constraints", {})
        preferences = context.get("preferences", {})
        
        if user_info:
            info_parts = [f"{k}: {v}" for k, v in user_info.items()]
            parts.append("; ".join(info_parts))
        
        if constraints:
            const_parts = [f"{k}: {v}" for k, v in constraints.items()]
            parts.append("Constraints: " + "; ".join(const_parts))
        
        if preferences:
            pref_parts = [f"{k}: {v}" for k, v in preferences.items()]
            parts.append("Preferences: " + "; ".join(pref_parts))
        
        return " | ".join(parts) if parts else "General research"
    
    def _generate_fallback_report(self, session_data: Dict[str, Any], 
                                research_results: Dict[str, Any], depth: str) -> str:
        """Generate minimal fallback report if main generation fails."""
        try:
            filename = self._generate_filename(session_data)
            report_path = self.report_dir / f"fallback_{filename}"
            
            fallback_content = f"""# Deep Research Report (Fallback)

**Query**: {session_data.get('query', 'Unknown')}
**Session ID**: {session_data.get('session_id', 'Unknown')}
**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary

A research session was completed but the full report could not be generated due to a technical issue.

## Available Data

- **Stages Completed**: {len(research_results.get('stages', []))}
- **Confidence Score**: {research_results.get('confidence_score', 0):.1%}

## Raw Results

{research_results.get('final_conclusions', {}).get('summary', 'No summary available')}

---

*This is a fallback report. Please check the session data file for complete research results.*"""
            
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(fallback_content)
            
            self.logger.warning(f"Generated fallback report: {report_path}")
            return str(report_path)
            
        except Exception as e:
            self.logger.error(f"Failed to generate fallback report: {e}")
            return "report_generation_failed.md"
