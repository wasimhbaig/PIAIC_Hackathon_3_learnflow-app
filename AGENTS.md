# LearnFlow Multi-Agent System

## Overview

LearnFlow uses a specialized multi-agent architecture where each AI agent has expertise in a specific aspect of Python tutoring. All agents are powered by Claude (Anthropic) and communicate via Dapr service invocation.

## Agent Architecture

```
Student Query
     ↓
┌────────────────┐
│ Triage Agent   │ ← Routes to specialist
└────────┬───────┘
         │
    ┌────┴────┬────────┬──────────┬────────────┐
    ↓         ↓        ↓          ↓            ↓
┌─────────┐ ┌────┐ ┌──────┐ ┌─────────┐ ┌──────────┐
│Concepts │ │Code│ │Debug │ │Exercise │ │Progress  │
│ Agent   │ │Rev │ │Agent │ │ Agent   │ │Agent     │
└─────────┘ └────┘ └──────┘ └─────────┘ └──────────┘
     │         │       │          │           │
     └─────────┴───────┴──────────┴───────────┘
                      ↓
               Student Response
```

## Agents

### 1. Triage Agent

**Purpose**: Route student queries to the appropriate specialist agent

**Model**: Claude Sonnet 4.5

**Responsibilities**:
- Analyze student queries using keyword matching and AI classification
- Route to specialist agents based on query type
- Maintain high routing accuracy (>90% confidence)
- Handle ambiguous queries with intelligent fallbacks

**Routing Rules**:
- **Concepts Agent**: "explain", "what is", "how does", "teach me"
- **Debug Agent**: "error", "bug", "not working", "broken"
- **Code Review Agent**: "review", "check", "feedback", "improve"
- **Exercise Agent**: "practice", "exercise", "challenge", "quiz"
- **Progress Agent**: "progress", "score", "how am I doing"

**Example**:
```
Input: "How do for loops work in Python?"
→ Routes to Concepts Agent (confidence: 0.95)
```

### 2. Concepts Agent

**Purpose**: Explain Python concepts with adaptive teaching

**Model**: Claude Sonnet 4.5

**Responsibilities**:
- Explain Python concepts clearly and effectively
- Adapt explanations to student level (beginner/learning/proficient/mastered)
- Provide code examples with line-by-line breakdowns
- Use analogies and visual representations
- Ask follow-up questions to check understanding
- Match student's preferred learning style (theory/examples/visual/mixed)

**Teaching Approach**:
1. Clear, concise explanation (2-3 sentences)
2. Simple code example with comments
3. Line-by-line breakdown
4. Practical use case demonstration
5. Follow-up question or practice suggestion

**Example Response**:
```
For loops let you repeat code for each item in a sequence.

```python
for i in range(5):
    print(i)  # Prints 0, 1, 2, 3, 4
```

This loop runs 5 times, with i taking values 0 through 4...

Would you like to try writing a for loop yourself?
```

### 3. Code Review Agent

**Purpose**: Analyze code for correctness, style, efficiency, and readability

**Model**: Claude Sonnet 4.5

**Responsibilities**:
- Review code across 4 dimensions (correctness, style, efficiency, readability)
- Provide specific, actionable feedback
- Score each dimension 0-100
- Calculate weighted overall score
- Identify bugs, logic errors, and edge cases
- Check PEP 8 compliance
- Analyze time/space complexity
- Suggest optimizations

**Review Framework**:
- **Correctness** (40%): Logic, edge cases, bugs
- **Style** (20%): PEP 8, naming, whitespace
- **Efficiency** (20%): Time/space complexity, optimizations
- **Readability** (20%): Variable names, comments, structure

**Example Output**:
```
✅ **Correctness**: 85/100
Your logic is sound for basic cases, but consider edge case when list is empty.

⚠️ **Style**: 70/100
Line 5: Use snake_case for variable names (change myList to my_list)

**Overall Score**: 78/100 (Proficient)
```

### 4. Debug Agent

**Purpose**: Help students fix errors through guided discovery

**Model**: Claude Sonnet 4.5

**Responsibilities**:
- Parse error messages and tracebacks
- Identify root causes of errors
- Provide progressive hints (NOT full solutions)
- Teach debugging strategies
- Adapt hint strength based on attempts
- Guide students to discover solutions themselves
- Build debugging confidence

**Hint Progression**:
1. **Gentle** (Attempts 0-1): Direction to look
2. **Specific** (Attempts 2-3): Narrow down location
3. **Strong** (Attempts 4+): Almost the answer, student applies it

**Example**:
```
🔍 **Error Analysis**
NameError means Python can't find a variable you're trying to use.

💡 **Hints**:
1. Look at line 5 where the error occurred
2. Check if you spelled the variable name correctly
3. Did you define 'count' before using it?

**Try This**: Add a print statement before line 5 to see what variables are defined
```

### 5. Exercise Agent

**Purpose**: Generate and auto-grade coding challenges

**Model**: Claude Sonnet 4.5

**Responsibilities**:
- Generate topic-specific exercises
- Adapt difficulty to student level
- Create comprehensive test cases
- Provide progressive hints
- Auto-grade submissions
- Give detailed feedback on failures
- Track exercise completion

**Exercise Components**:
- Title and clear description
- Difficulty level (easy/medium/hard)
- Starter code (optional)
- Test cases (visible and hidden)
- Progressive hints
- Reference solution

**Grading Process**:
1. Run code against test cases
2. Check correctness of outputs
3. Evaluate code quality
4. Provide specific feedback on failures
5. Calculate score (0-100)

### 6. Progress Agent

**Purpose**: Track and report student mastery and learning progress

**Model**: Claude Haiku 4 (faster, cost-effective for analytics)

**Responsibilities**:
- Calculate mastery scores using weighted formula
- Track learning velocity and streaks
- Identify strengths and weaknesses
- Provide motivational feedback
- Suggest next learning steps
- Generate progress reports

**Mastery Calculation**:
```
Overall Score =
  Exercise Completion × 40% +
  Quiz Scores × 30% +
  Code Quality × 20% +
  Consistency (Streak) × 10%
```

**Mastery Levels**:
- 0-40%: Beginner 🔴
- 41-70%: Learning 🟡
- 71-90%: Proficient 🟢
- 91-100%: Mastered 🔵

**Example Report**:
```
📊 **Your Learning Progress**

**Module 2: Control Flow - 68% (Learning)**
- For Loops: 85% (Proficient) ✅
- While Loops: 60% (Learning) 📚

**Streak**: 5 days 🔥

**Strengths**: 💪
- Excellent grasp of for loops
- Consistent practice habits

**Next Steps**:
1. Practice while loops with simpler exercises
2. Review loop termination conditions
```

## Agent Orchestrator

**Service**: `learnflow-agents` (Port 8001)

**Responsibilities**:
- Host all 6 AI agents
- Handle Dapr service invocation
- Route requests to agents
- Manage agent lifecycle
- Provide health checks
- Subscribe to Kafka events
- Log agent performance metrics

**Endpoints**:
- `POST /invoke` - Invoke agent (auto-routes via Triage)
- `POST /agents/{agent_name}` - Direct agent invocation
- `GET /agents` - List all agents
- `GET /health` - Orchestrator health check

**Dapr Integration**:
- App ID: `learnflow-agents`
- Subscribes to: `struggle-alerts`, `student-activity`
- Publishes to: `mastery-updates`

## Inter-Agent Communication

Agents communicate through the orchestrator using Dapr service invocation:

```
API Gateway
    ↓ (Dapr invoke)
Triage Agent
    ↓ (routing decision)
Specialist Agent
    ↓ (response)
API Gateway
    ↓ (WebSocket)
Student
```

## Agent Context

All agents receive contextual information:
- `student_id`: Student UUID
- `student_level`: beginner|learning|proficient|mastered
- `student_preferences`: theory|examples|visual|mixed
- `topic`: Current topic name
- `mastery_score`: Current mastery percentage
- `code`: Student's code (if applicable)
- `error`: Error message (if applicable)
- `previous_attempts`: Number of attempts (for debugging)

## MCP Integration

The MCP (Model Context Protocol) server provides agents with rich context:

**Available Tools**:
- `get_student_progress` - Comprehensive progress data
- `analyze_code_submission` - Detailed submission analysis
- `get_curriculum_topics` - Module/topic structure
- `detect_struggle_patterns` - Struggle analysis
- `suggest_exercises` - Personalized recommendations
- `get_common_errors` - Common error patterns by topic

This enables agents to:
- Make informed decisions based on student history
- Provide personalized feedback
- Detect patterns across submissions
- Recommend targeted interventions

## Performance Metrics

Agents are monitored via Prometheus:
- `learnflow_agent_response_time_seconds` - Agent response latency
- `learnflow_agent_invocations_total` - Total invocations by agent
- `learnflow_agent_errors_total` - Agent error rate
- `learnflow_triage_routing_confidence` - Triage accuracy

## Scaling Strategy

- **API Gateway**: 3 replicas (horizontal scaling)
- **Agent Orchestrator**: 2 replicas (handles high AI load)
- **Load Balancing**: Dapr service mesh distributes requests
- **Caching**: Future: Cache common concept explanations

## Error Handling

1. Agent failures return helpful error messages
2. Triage fallback: Routes to Concepts Agent if uncertain
3. Retry logic with exponential backoff
4. Circuit breaker for Claude API failures
5. Graceful degradation with cached responses

## Future Enhancements

1. **Agent Learning**: Fine-tune agents based on student feedback
2. **Collaborative Agents**: Multiple agents collaborate on complex queries
3. **Proactive Agents**: Agents initiate conversations when struggles detected
4. **Multilingual Support**: Agents teach in multiple languages
5. **Voice Integration**: Voice-based tutoring with speech-to-text

## Development

### Testing Agents Locally

```bash
# Start orchestrator
cd src/agents
python orchestrator.py

# Test agent directly
curl -X POST http://localhost:8001/agents/concepts \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "test-123",
    "message": "How do for loops work?",
    "context": {"student_level": "beginner"}
  }'
```

### Agent Health Checks

```bash
# Check all agents
curl http://localhost:8001/health

# Check specific agent
curl http://localhost:8001/agents/concepts/health
```

## References

- **Anthropic Claude API**: https://docs.anthropic.com/
- **Dapr Service Invocation**: https://docs.dapr.io/developing-applications/building-blocks/service-invocation/
- **MCP Protocol**: https://modelcontextprotocol.io/
