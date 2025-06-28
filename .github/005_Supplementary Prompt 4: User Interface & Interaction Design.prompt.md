Design an intuitive user interaction system for the Deep Research Agent that guides users through the research process:

**Conversation Flow:**
1. **Welcome & Query Collection**: Friendly introduction and initial question gathering
2. **Personalization Choice**: Ask user if they want personalized recommendations
3. **Context Gathering**: Intelligent questioning based on query type
4. **Research Process**: Live progress updates during multi-stage research
5. **Report Generation**: User choice of report depth and format
6. **Session Completion**: Summary and file location information

**Intelligent Context Gathering:**
- **Query Analysis**: The system will use an LLM-based classification approach. The Gemini model will be prompted to classify the user's query into one of the following predefined categories: Health, Finance, Technology, Lifestyle, or Other. This classification will determine the set of relevant follow-up questions.
- **Adaptive Questions**: Ask relevant demographic/contextual information
- **Constraint Collection**: Budget, timeline, location, other limitations
- **Preference Mapping**: Priorities, deal-breakers, success criteria
- **Validation**: Ensure input quality and completeness

**Context Gathering Examples:**
- **Health queries**: Age, weight, fitness level, health conditions
- **Financial queries**: Income range, risk tolerance, timeline
- **Location queries**: Current location, preferred regions, mobility constraints
- **Purchase decisions**: Budget range, must-have features, deal-breakers

**Sample Interaction Flow:**
```
🤖 Welcome to Deep Research Agent!
What decision do you need help with today?
> I want to improve my cardio stamina

Should I personalize recommendations based on your profile? (y/n)
> y

📋 Let me gather some information to personalize recommendations:
Age (optional): 30
Weight (optional): 75kg
Current fitness level: beginner
```

**Progress Communication:**
- **Stage Indicators**: Clear progress through 6-stage research process
- **Real-time Updates**: "Analyzing...", "Gathering evidence...", "Synthesizing..."
- **Time Estimates**: Approximate completion times for user planning
- **Error Recovery**: Graceful handling of API issues or timeouts

**Sample Progress Messages:**
```
🔬 Starting Iterative Research Process for: 'your query'
======================================================

📊 STAGE 1: Initial Information Gathering
   ✅ Gathered 1,234 characters of initial information

🔍 STAGE 2: Validation & Fact-Checking
   ✅ Validated findings and identified knowledge gaps

❓ STAGE 3: Clarification & Follow-up
   ✅ Filled knowledge gaps with additional research
```

**User Experience Principles:**
- **Natural Language**: Conversational tone throughout interaction
- **Progressive Disclosure**: Reveal complexity gradually as needed
- **Clear Choices**: Simple options with helpful explanations
- **Feedback Loops**: Confirm understanding before proceeding
- **Escape Routes**: Allow users to modify inputs or restart

**Input Validation & Sanitization:**
- **Query Quality**: Ensure meaningful research questions
- **Context Validation**: Verify demographic and preference data
- **Security**: Sanitize inputs to prevent injection attacks
- **Error Messages**: Helpful guidance for correction

**Accessibility Considerations:**
- **Clear Language**: Avoid technical jargon in user-facing text
- **Flexible Input**: Accept various formats for common data types
- **Help Text**: Contextual guidance for complex questions
- **Error Recovery**: Easy ways to correct mistakes

The interface MUST feel like talking to a knowledgeable research assistant who asks smart questions and provides clear guidance throughout the process.