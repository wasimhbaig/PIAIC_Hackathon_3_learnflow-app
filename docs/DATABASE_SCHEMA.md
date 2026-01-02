# LearnFlow Database Schema

## Overview

LearnFlow extends the base learning platform schema with Python-specific tutoring features.

## Entity Relationship Diagram

```
┌─────────────┐       ┌──────────────┐       ┌─────────────┐
│  students   │───┬───│    classes   │───────│  teachers   │
└─────────────┘   │   └──────────────┘       └─────────────┘
       │          │
       │          │   ┌──────────────┐
       │          └───│ enrollments  │
       │              └──────────────┘
       │
       ├──────────┬──────────┬──────────┬──────────────┐
       │          │          │          │              │
┌──────▼────┐ ┌──▼────────┐ ┌▼────────┐ ┌▼───────────┐ ┌▼──────────┐
│code_      │ │quiz_      │ │mastery_ │ │progress_   │ │struggle_  │
│submissions│ │attempts   │ │scores   │ │events      │ │alerts     │
└───────────┘ └───────────┘ └─────────┘ └────────────┘ └───────────┘
     │              │
┌────▼────┐    ┌───▼────┐
│test_    │    │quiz_   │
│results  │    │answers │
└─────────┘    └────────┘

┌─────────────┐       ┌──────────────┐       ┌─────────────┐
│   modules   │───────│    topics    │───────│  exercises  │
└─────────────┘       └──────────────┘       └─────────────┘
                            │
                            │
                      ┌─────▼──────┐
                      │quiz_       │
                      │questions   │
                      └────────────┘
```

## Table Definitions

### Students
```sql
CREATE TABLE students (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    student_code VARCHAR(20) UNIQUE NOT NULL,  -- e.g., "STU2024001"
    current_module INTEGER DEFAULT 1,
    learning_pace VARCHAR(20) DEFAULT 'normal',  -- slow, normal, fast
    preferred_explanation_style VARCHAR(20) DEFAULT 'examples',  -- theory, examples, visual
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT check_module CHECK (current_module BETWEEN 1 AND 8),
    CONSTRAINT check_pace CHECK (learning_pace IN ('slow', 'normal', 'fast')),
    CONSTRAINT check_style CHECK (preferred_explanation_style IN ('theory', 'examples', 'visual', 'mixed'))
);

CREATE INDEX idx_students_user_id ON students(user_id);
CREATE INDEX idx_students_current_module ON students(current_module);
```

### Teachers
```sql
CREATE TABLE teachers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    teacher_code VARCHAR(20) UNIQUE NOT NULL,  -- e.g., "TCH2024001"
    specialization TEXT[],  -- e.g., ['basics', 'oop', 'data_structures']
    years_experience INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_teachers_user_id ON teachers(user_id);
```

### Classes
```sql
CREATE TABLE classes (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    teacher_id UUID REFERENCES teachers(id) ON DELETE CASCADE,
    start_date DATE NOT NULL,
    end_date DATE,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_classes_teacher_id ON classes(teacher_id);
CREATE INDEX idx_classes_active ON classes(is_active);
```

### Enrollments
```sql
CREATE TABLE enrollments (
    id SERIAL PRIMARY KEY,
    student_id UUID REFERENCES students(id) ON DELETE CASCADE,
    class_id INTEGER REFERENCES classes(id) ON DELETE CASCADE,
    enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'active',  -- active, completed, dropped
    UNIQUE(student_id, class_id),
    CONSTRAINT check_status CHECK (status IN ('active', 'completed', 'dropped'))
);

CREATE INDEX idx_enrollments_student_id ON enrollments(student_id);
CREATE INDEX idx_enrollments_class_id ON enrollments(class_id);
```

### Modules
```sql
CREATE TABLE modules (
    id SERIAL PRIMARY KEY,
    number INTEGER UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    order_index INTEGER NOT NULL,
    estimated_hours INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT check_number CHECK (number BETWEEN 1 AND 8)
);

-- Seed data for 8 Python modules
INSERT INTO modules (number, name, description, order_index, estimated_hours) VALUES
(1, 'Basics', 'Variables, Data Types, Input/Output, Operators, Type Conversion', 1, 8),
(2, 'Control Flow', 'Conditionals (if/elif/else), For Loops, While Loops, Break/Continue', 2, 10),
(3, 'Data Structures', 'Lists, Tuples, Dictionaries, Sets', 3, 12),
(4, 'Functions', 'Defining Functions, Parameters, Return Values, Scope', 4, 10),
(5, 'OOP', 'Classes & Objects, Attributes & Methods, Inheritance, Encapsulation', 5, 15),
(6, 'Files', 'Reading/Writing Files, CSV Processing, JSON Handling', 6, 8),
(7, 'Errors', 'Try/Except, Exception Types, Custom Exceptions, Debugging', 7, 8),
(8, 'Libraries', 'Installing Packages, Working with APIs, Virtual Environments', 8, 10);
```

### Topics
```sql
CREATE TABLE topics (
    id SERIAL PRIMARY KEY,
    module_id INTEGER REFERENCES modules(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    order_index INTEGER NOT NULL,
    difficulty VARCHAR(20) DEFAULT 'beginner',
    example_code TEXT,
    key_concepts TEXT[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT check_difficulty CHECK (difficulty IN ('beginner', 'intermediate', 'advanced'))
);

CREATE INDEX idx_topics_module_id ON topics(module_id);
CREATE INDEX idx_topics_difficulty ON topics(difficulty);
```

### Exercises
```sql
CREATE TABLE exercises (
    id SERIAL PRIMARY KEY,
    topic_id INTEGER REFERENCES topics(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    difficulty VARCHAR(20) NOT NULL,
    starter_code TEXT,
    solution_code TEXT,
    test_cases JSONB NOT NULL,  -- [{"input": ..., "expected": ..., "hidden": bool}]
    hints TEXT[],
    time_limit_seconds INTEGER DEFAULT 5,
    memory_limit_mb INTEGER DEFAULT 50,
    points INTEGER DEFAULT 10,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT check_difficulty CHECK (difficulty IN ('easy', 'medium', 'hard'))
);

CREATE INDEX idx_exercises_topic_id ON exercises(topic_id);
CREATE INDEX idx_exercises_difficulty ON exercises(difficulty);
```

### Code Submissions
```sql
CREATE TABLE code_submissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID REFERENCES students(id) ON DELETE CASCADE,
    exercise_id INTEGER REFERENCES exercises(id) ON DELETE SET NULL,
    code TEXT NOT NULL,
    language VARCHAR(20) DEFAULT 'python',
    status VARCHAR(20) NOT NULL,  -- passed, failed, error, timeout
    execution_time_ms INTEGER,
    memory_used_mb FLOAT,
    stdout TEXT,
    stderr TEXT,
    score INTEGER,  -- 0-100
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT check_status CHECK (status IN ('passed', 'failed', 'error', 'timeout', 'running'))
);

CREATE INDEX idx_code_submissions_student_id ON code_submissions(student_id);
CREATE INDEX idx_code_submissions_exercise_id ON code_submissions(exercise_id);
CREATE INDEX idx_code_submissions_submitted_at ON code_submissions(submitted_at DESC);
```

### Test Results
```sql
CREATE TABLE test_results (
    id SERIAL PRIMARY KEY,
    submission_id UUID REFERENCES code_submissions(id) ON DELETE CASCADE,
    test_case_index INTEGER NOT NULL,
    passed BOOLEAN NOT NULL,
    input_data TEXT,
    expected_output TEXT,
    actual_output TEXT,
    error_message TEXT,
    execution_time_ms INTEGER
);

CREATE INDEX idx_test_results_submission_id ON test_results(submission_id);
```

### Quiz Questions
```sql
CREATE TABLE quiz_questions (
    id SERIAL PRIMARY KEY,
    topic_id INTEGER REFERENCES topics(id) ON DELETE CASCADE,
    question_type VARCHAR(20) NOT NULL,  -- multiple_choice, coding, true_false
    question_text TEXT NOT NULL,
    options JSONB,  -- For multiple choice: ["option1", "option2", ...]
    correct_answer TEXT NOT NULL,
    explanation TEXT,
    difficulty VARCHAR(20) NOT NULL,
    points INTEGER DEFAULT 10,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT check_question_type CHECK (question_type IN ('multiple_choice', 'coding', 'true_false')),
    CONSTRAINT check_difficulty CHECK (difficulty IN ('easy', 'medium', 'hard'))
);

CREATE INDEX idx_quiz_questions_topic_id ON quiz_questions(topic_id);
CREATE INDEX idx_quiz_questions_difficulty ON quiz_questions(difficulty);
```

### Quiz Attempts
```sql
CREATE TABLE quiz_attempts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID REFERENCES students(id) ON DELETE CASCADE,
    topic_id INTEGER REFERENCES topics(id) ON DELETE CASCADE,
    total_questions INTEGER NOT NULL,
    correct_answers INTEGER NOT NULL,
    score_percentage FLOAT NOT NULL,
    time_taken_seconds INTEGER,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT check_score CHECK (score_percentage BETWEEN 0 AND 100)
);

CREATE INDEX idx_quiz_attempts_student_id ON quiz_attempts(student_id);
CREATE INDEX idx_quiz_attempts_topic_id ON quiz_attempts(topic_id);
CREATE INDEX idx_quiz_attempts_completed_at ON quiz_attempts(completed_at DESC);
```

### Quiz Answers
```sql
CREATE TABLE quiz_answers (
    id SERIAL PRIMARY KEY,
    attempt_id UUID REFERENCES quiz_attempts(id) ON DELETE CASCADE,
    question_id INTEGER REFERENCES quiz_questions(id) ON DELETE CASCADE,
    student_answer TEXT,
    is_correct BOOLEAN NOT NULL,
    time_taken_seconds INTEGER
);

CREATE INDEX idx_quiz_answers_attempt_id ON quiz_answers(attempt_id);
```

### Mastery Scores
```sql
CREATE TABLE mastery_scores (
    id SERIAL PRIMARY KEY,
    student_id UUID REFERENCES students(id) ON DELETE CASCADE,
    topic_id INTEGER REFERENCES topics(id) ON DELETE CASCADE,

    -- Component scores (0-100)
    exercise_completion_score FLOAT DEFAULT 0,
    quiz_score FLOAT DEFAULT 0,
    code_quality_score FLOAT DEFAULT 0,
    consistency_score FLOAT DEFAULT 0,

    -- Overall mastery (weighted average)
    overall_score FLOAT DEFAULT 0,
    mastery_level VARCHAR(20) DEFAULT 'beginner',

    -- Tracking
    exercises_completed INTEGER DEFAULT 0,
    quizzes_taken INTEGER DEFAULT 0,
    current_streak_days INTEGER DEFAULT 0,
    last_activity_at TIMESTAMP,

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(student_id, topic_id),
    CONSTRAINT check_scores CHECK (
        exercise_completion_score BETWEEN 0 AND 100 AND
        quiz_score BETWEEN 0 AND 100 AND
        code_quality_score BETWEEN 0 AND 100 AND
        consistency_score BETWEEN 0 AND 100 AND
        overall_score BETWEEN 0 AND 100
    ),
    CONSTRAINT check_level CHECK (mastery_level IN ('beginner', 'learning', 'proficient', 'mastered'))
);

CREATE INDEX idx_mastery_scores_student_id ON mastery_scores(student_id);
CREATE INDEX idx_mastery_scores_topic_id ON mastery_scores(topic_id);
CREATE INDEX idx_mastery_scores_level ON mastery_scores(mastery_level);
```

### Progress Events
```sql
CREATE TABLE progress_events (
    id SERIAL PRIMARY KEY,
    student_id UUID REFERENCES students(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,
    event_data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_progress_events_student_id ON progress_events(student_id);
CREATE INDEX idx_progress_events_type ON progress_events(event_type);
CREATE INDEX idx_progress_events_created_at ON progress_events(created_at DESC);
```

### Struggle Alerts
```sql
CREATE TABLE struggle_alerts (
    id SERIAL PRIMARY KEY,
    student_id UUID REFERENCES students(id) ON DELETE CASCADE,
    topic_id INTEGER REFERENCES topics(id) ON DELETE CASCADE,
    trigger_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,  -- low, medium, high
    description TEXT NOT NULL,
    suggested_action TEXT,
    is_resolved BOOLEAN DEFAULT false,
    resolved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT check_trigger CHECK (trigger_type IN (
        'repeated_error', 'stuck_on_exercise', 'low_quiz_score',
        'confused_signal', 'multiple_failures', 'time_spent'
    )),
    CONSTRAINT check_severity CHECK (severity IN ('low', 'medium', 'high'))
);

CREATE INDEX idx_struggle_alerts_student_id ON struggle_alerts(student_id);
CREATE INDEX idx_struggle_alerts_unresolved ON struggle_alerts(is_resolved) WHERE is_resolved = false;
CREATE INDEX idx_struggle_alerts_created_at ON struggle_alerts(created_at DESC);
```

### Chat Sessions
```sql
CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID REFERENCES students(id) ON DELETE CASCADE,
    topic_id INTEGER REFERENCES topics(id) ON DELETE SET NULL,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    message_count INTEGER DEFAULT 0,
    satisfaction_rating INTEGER,  -- 1-5 stars
    CONSTRAINT check_rating CHECK (satisfaction_rating IS NULL OR satisfaction_rating BETWEEN 1 AND 5)
);

CREATE INDEX idx_chat_sessions_student_id ON chat_sessions(student_id);
CREATE INDEX idx_chat_sessions_started_at ON chat_sessions(started_at DESC);
```

### Chat Messages
```sql
CREATE TABLE chat_messages (
    id SERIAL PRIMARY KEY,
    session_id UUID REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,  -- student, triage, concepts, debug, review, exercise, progress
    content TEXT NOT NULL,
    agent_metadata JSONB,  -- Agent-specific data (reasoning, citations, etc.)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT check_role CHECK (role IN ('student', 'triage', 'concepts', 'debug', 'review', 'exercise', 'progress'))
);

CREATE INDEX idx_chat_messages_session_id ON chat_messages(session_id);
CREATE INDEX idx_chat_messages_created_at ON chat_messages(created_at DESC);
```

## Views for Reporting

### Student Progress Summary
```sql
CREATE VIEW v_student_progress AS
SELECT
    s.id as student_id,
    s.student_code,
    s.current_module,
    COUNT(DISTINCT ms.topic_id) as topics_started,
    COUNT(DISTINCT CASE WHEN ms.mastery_level IN ('proficient', 'mastered') THEN ms.topic_id END) as topics_mastered,
    AVG(ms.overall_score) as avg_mastery_score,
    MAX(ms.current_streak_days) as longest_streak,
    COUNT(DISTINCT cs.id) as total_code_submissions,
    COUNT(DISTINCT qa.id) as total_quiz_attempts
FROM students s
LEFT JOIN mastery_scores ms ON s.id = ms.student_id
LEFT JOIN code_submissions cs ON s.id = cs.student_id
LEFT JOIN quiz_attempts qa ON s.id = qa.student_id
GROUP BY s.id, s.student_code, s.current_module;
```

### Class Performance Dashboard
```sql
CREATE VIEW v_class_performance AS
SELECT
    c.id as class_id,
    c.name as class_name,
    t.user_id as teacher_id,
    COUNT(DISTINCT e.student_id) as total_students,
    AVG(vsp.avg_mastery_score) as class_avg_mastery,
    COUNT(DISTINCT sa.id) as active_struggle_alerts
FROM classes c
JOIN teachers t ON c.teacher_id = t.id
JOIN enrollments e ON c.id = e.class_id
LEFT JOIN v_student_progress vsp ON e.student_id = vsp.student_id
LEFT JOIN struggle_alerts sa ON e.student_id = sa.student_id AND sa.is_resolved = false
WHERE c.is_active = true
GROUP BY c.id, c.name, t.user_id;
```

## Mastery Calculation Formula

```sql
-- Weighted average:
overall_score = (
    exercise_completion_score * 0.40 +
    quiz_score * 0.30 +
    code_quality_score * 0.20 +
    consistency_score * 0.10
)

-- Mastery level mapping:
CASE
    WHEN overall_score < 41 THEN 'beginner'
    WHEN overall_score < 71 THEN 'learning'
    WHEN overall_score < 91 THEN 'proficient'
    ELSE 'mastered'
END
```

## Data Retention Policy

- **Chat Messages**: Retain for 90 days
- **Code Submissions**: Retain indefinitely (anonymized after 1 year)
- **Quiz Attempts**: Retain indefinitely
- **Progress Events**: Retain for 1 year
- **Struggle Alerts**: Retain for 6 months after resolution
