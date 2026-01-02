# LearnFlow Architecture

## System Overview

LearnFlow is an AI-powered Python tutoring platform built on a microservices architecture with event-driven communication.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        Student/Teacher UI                        │
│                         (React/Next.js)                          │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTP/WebSocket
┌──────────────────────────┴──────────────────────────────────────┐
│                      API Gateway (FastAPI)                       │
│  - Authentication & Authorization                                │
│  - Request Routing                                               │
│  - WebSocket Management                                          │
└────┬─────────────────────┬─────────────────────┬────────────────┘
     │                     │                     │
     │ REST/WS             │ Events              │ Queries
     │                     │                     │
┌────┴──────────┐   ┌──────┴─────────┐   ┌──────┴────────┐
│  AI Agent     │   │  Event Bus     │   │  Database     │
│  Orchestrator │   │  (Kafka)       │   │  (PostgreSQL) │
└────┬──────────┘   └────────────────┘   └───────────────┘
     │
     ├─── Triage Agent (Router)
     │
     ├─── Concepts Agent (Teaching)
     │
     ├─── Code Review Agent (Analysis)
     │
     ├─── Debug Agent (Error Help)
     │
     ├─── Exercise Agent (Practice)
     │
     └─── Progress Agent (Tracking)
```

## Core Components

### 1. API Layer (`src/api/`)
- **Framework**: FastAPI
- **Responsibilities**:
  - HTTP REST endpoints for CRUD operations
  - WebSocket connections for real-time chat
  - Authentication/authorization (JWT)
  - Request validation (Pydantic)
  - Rate limiting

### 2. Agent System (`src/agents/`)
Multi-agent architecture powered by Claude (Anthropic):

#### Triage Agent
- **Purpose**: Routes student queries to appropriate specialists
- **Logic**:
  - "explain", "what is", "how does" → Concepts Agent
  - "error", "bug", "not working" → Debug Agent
  - "review my code" → Code Review Agent
  - "practice", "exercise" → Exercise Agent
  - "progress", "how am I doing" → Progress Agent

#### Concepts Agent
- **Purpose**: Explains Python concepts with examples
- **Capabilities**:
  - Adaptive explanations based on student level
  - Code examples for each concept
  - Analogies and visualizations
  - Follow-up questions for understanding

#### Code Review Agent
- **Purpose**: Analyzes student code
- **Checks**:
  - Correctness (logic errors, edge cases)
  - Style (PEP 8 compliance)
  - Efficiency (time/space complexity)
  - Readability (naming, comments)

#### Debug Agent
- **Purpose**: Helps students fix errors
- **Process**:
  1. Parse error message and traceback
  2. Identify root cause
  3. Provide hints (not full solutions)
  4. Guide student to discovery

#### Exercise Agent
- **Purpose**: Generates and grades coding challenges
- **Features**:
  - Topic-specific exercises
  - Difficulty adaptation
  - Auto-grading with test cases
  - Hints system

#### Progress Agent
- **Purpose**: Tracks and reports student mastery
- **Metrics**:
  - Module completion rates
  - Mastery scores per topic
  - Streak tracking
  - Learning velocity

### 3. Code Execution Sandbox (`src/sandbox/`)
- **Technology**: Docker containers with RestrictedPython
- **Safety Constraints**:
  - 5-second timeout per execution
  - 50MB memory limit
  - No file system access (except temp)
  - No network access
  - Standard library only (MVP scope)
- **Process**:
  1. Receive code from API
  2. Spin up isolated container
  3. Execute with resource limits
  4. Capture stdout/stderr
  5. Destroy container
  6. Return results

### 4. Data Models (`src/models/`)
SQLAlchemy ORM models for:
- Users (students, teachers)
- Curriculum (modules, topics)
- Exercises & Quizzes
- Code Submissions
- Mastery Scores
- Progress Tracking

### 5. Business Logic (`src/services/`)
- **MasteryService**: Calculates topic mastery scores
- **StruggleDetectionService**: Identifies struggling students
- **ExerciseGenerationService**: Creates coding challenges
- **ProgressTrackingService**: Monitors learning progress
- **EventPublisher**: Publishes events to Kafka

## Data Flow

### Student Code Submission Flow
```
1. Student writes code in UI
2. API receives code + context
3. Code sent to Sandbox for execution
4. Results returned to API
5. If review requested:
   - Send to Code Review Agent
   - Get feedback
6. Update mastery score
7. Publish event to Kafka (code-submitted)
8. Return feedback to student
```

### Quiz Taking Flow
```
1. Student requests quiz for topic
2. Exercise Agent generates questions
3. Student submits answers
4. Auto-grader evaluates
5. Update mastery score
6. Check for struggle triggers
7. Publish event (quiz-completed)
8. Return results + explanations
```

### Teacher Monitoring Flow
```
1. Teacher views class dashboard
2. API queries aggregated metrics
3. Subscribe to real-time updates (WebSocket)
4. Struggle alerts pushed when triggered
5. Generate custom exercises on demand
```

## Technology Stack

### Backend
- **Language**: Python 3.11+
- **Framework**: FastAPI
- **ORM**: SQLAlchemy
- **Migration**: Alembic
- **Validation**: Pydantic
- **AI**: Anthropic Claude API

### Data Layer
- **Database**: PostgreSQL 15
- **Caching**: Redis (future)
- **Message Queue**: Apache Kafka
- **Object Storage**: MinIO (for code artifacts)

### Infrastructure
- **Orchestration**: Kubernetes
- **Container Runtime**: Docker
- **CI/CD**: GitHub Actions
- **Monitoring**: Prometheus + Grafana

## Database Schema

See `database/migrations/` for detailed schema.

Key tables:
- `students` - Student profiles & authentication
- `teachers` - Teacher profiles & class assignments
- `modules` - Python curriculum modules (8 total)
- `topics` - Individual topics within modules
- `exercises` - Coding challenges
- `quiz_questions` - Multiple choice & coding questions
- `code_submissions` - Student code attempts
- `quiz_attempts` - Quiz responses & scores
- `mastery_scores` - Per-topic mastery tracking
- `progress_events` - Activity timeline
- `struggle_alerts` - Teacher notifications

## Event Schema (Kafka Topics)

### student-activity
```json
{
  "event_type": "code_submitted|quiz_taken|concept_viewed",
  "student_id": "uuid",
  "timestamp": "iso8601",
  "metadata": { ... }
}
```

### mastery-updates
```json
{
  "student_id": "uuid",
  "topic_id": "integer",
  "old_score": "float",
  "new_score": "float",
  "level": "beginner|learning|proficient|mastered"
}
```

### struggle-alerts
```json
{
  "student_id": "uuid",
  "trigger_type": "repeated_error|stuck_on_exercise|low_quiz_score",
  "details": { ... },
  "suggested_action": "string"
}
```

## Security Considerations

1. **Authentication**: JWT tokens with refresh mechanism
2. **Authorization**: Role-based access control (Student/Teacher)
3. **Code Execution**: Sandboxed containers, no network/file access
4. **Input Validation**: All inputs validated with Pydantic
5. **Rate Limiting**: Prevent API abuse
6. **SQL Injection**: ORM prevents direct SQL
7. **XSS**: API doesn't render HTML

## Scalability Strategy

1. **Horizontal Scaling**: Stateless API pods behind load balancer
2. **Agent Pool**: Multiple agent instances for parallel processing
3. **Sandbox Pool**: Pre-warmed containers for fast execution
4. **Database**: Read replicas for query load
5. **Caching**: Redis for frequently accessed data
6. **Event Processing**: Kafka consumers scale independently

## Monitoring & Observability

1. **Metrics**:
   - API response times
   - Code execution times
   - Agent response times
   - Error rates
   - Mastery score distributions

2. **Logging**:
   - Structured JSON logs
   - Correlation IDs for request tracing
   - Student interaction logs

3. **Alerting**:
   - High error rates
   - Slow responses
   - Sandbox failures
   - Database connection issues

## Future Enhancements

1. **Advanced Features**:
   - Collaborative coding sessions
   - Peer code review
   - AI pair programming
   - Video explanations

2. **ML Improvements**:
   - Personalized learning paths
   - Predictive struggle detection
   - Adaptive difficulty
   - Learning style optimization

3. **Infrastructure**:
   - Multi-region deployment
   - CDN for static assets
   - GraphQL API option
   - Mobile app support
