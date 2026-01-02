-- V4: LearnFlow Mastery Tracking and Analytics
-- Creates mastery scores, progress events, struggle alerts, and chat tables

-- Mastery scores table
CREATE TABLE IF NOT EXISTS mastery_scores (
    id SERIAL PRIMARY KEY,
    student_id UUID REFERENCES students(id) ON DELETE CASCADE,
    topic_id INTEGER REFERENCES topics(id) ON DELETE CASCADE,

    -- Component scores (0-100)
    exercise_completion_score FLOAT DEFAULT 0,
    quiz_score FLOAT DEFAULT 0,
    code_quality_score FLOAT DEFAULT 0,
    consistency_score FLOAT DEFAULT 0,

    -- Overall mastery (weighted average: 40% + 30% + 20% + 10%)
    overall_score FLOAT DEFAULT 0,
    mastery_level VARCHAR(20) DEFAULT 'beginner',

    -- Tracking metrics
    exercises_completed INTEGER DEFAULT 0,
    exercises_total INTEGER DEFAULT 0,
    quizzes_taken INTEGER DEFAULT 0,
    current_streak_days INTEGER DEFAULT 0,
    last_activity_at TIMESTAMP,

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(student_id, topic_id),
    CONSTRAINT check_exercise_completion_score CHECK (exercise_completion_score >= 0 AND exercise_completion_score <= 100),
    CONSTRAINT check_quiz_score CHECK (quiz_score >= 0 AND quiz_score <= 100),
    CONSTRAINT check_code_quality_score CHECK (code_quality_score >= 0 AND code_quality_score <= 100),
    CONSTRAINT check_consistency_score CHECK (consistency_score >= 0 AND consistency_score <= 100),
    CONSTRAINT check_overall_score CHECK (overall_score >= 0 AND overall_score <= 100),
    CONSTRAINT check_level CHECK (mastery_level IN ('beginner', 'learning', 'proficient', 'mastered')),
    CONSTRAINT check_exercises CHECK (exercises_completed >= 0 AND exercises_completed <= exercises_total),
    CONSTRAINT check_streak CHECK (current_streak_days >= 0)
);

CREATE INDEX idx_mastery_scores_student_id ON mastery_scores(student_id);
CREATE INDEX idx_mastery_scores_topic_id ON mastery_scores(topic_id);
CREATE INDEX idx_mastery_scores_level ON mastery_scores(mastery_level);
CREATE INDEX idx_mastery_scores_overall ON mastery_scores(overall_score DESC);

-- Progress events table
CREATE TABLE IF NOT EXISTS progress_events (
    id SERIAL PRIMARY KEY,
    student_id UUID REFERENCES students(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,
    event_data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT check_event_type CHECK (event_type IN (
        'code_submitted', 'quiz_completed', 'exercise_completed',
        'topic_started', 'topic_completed', 'module_completed',
        'mastery_level_up', 'streak_milestone', 'struggle_detected'
    ))
);

CREATE INDEX idx_progress_events_student_id ON progress_events(student_id);
CREATE INDEX idx_progress_events_type ON progress_events(event_type);
CREATE INDEX idx_progress_events_created_at ON progress_events(created_at DESC);

-- Struggle alerts table
CREATE TABLE IF NOT EXISTS struggle_alerts (
    id SERIAL PRIMARY KEY,
    student_id UUID REFERENCES students(id) ON DELETE CASCADE,
    topic_id INTEGER REFERENCES topics(id) ON DELETE CASCADE,
    trigger_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    description TEXT NOT NULL,
    suggested_action TEXT,
    context_data JSONB,
    is_resolved BOOLEAN DEFAULT false,
    resolved_at TIMESTAMP,
    resolved_by UUID,
    resolution_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT check_trigger CHECK (trigger_type IN (
        'repeated_error', 'stuck_on_exercise', 'low_quiz_score',
        'confused_signal', 'multiple_failures', 'excessive_time'
    )),
    CONSTRAINT check_severity CHECK (severity IN ('low', 'medium', 'high'))
);

CREATE INDEX idx_struggle_alerts_student_id ON struggle_alerts(student_id);
CREATE INDEX idx_struggle_alerts_topic_id ON struggle_alerts(topic_id);
CREATE INDEX idx_struggle_alerts_unresolved ON struggle_alerts(is_resolved) WHERE is_resolved = false;
CREATE INDEX idx_struggle_alerts_severity ON struggle_alerts(severity);
CREATE INDEX idx_struggle_alerts_created_at ON struggle_alerts(created_at DESC);

-- Chat sessions table
CREATE TABLE IF NOT EXISTS chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID REFERENCES students(id) ON DELETE CASCADE,
    topic_id INTEGER REFERENCES topics(id) ON DELETE SET NULL,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    message_count INTEGER DEFAULT 0,
    satisfaction_rating INTEGER,
    feedback_text TEXT,
    CONSTRAINT check_rating CHECK (satisfaction_rating IS NULL OR (satisfaction_rating >= 1 AND satisfaction_rating <= 5)),
    CONSTRAINT check_message_count CHECK (message_count >= 0)
);

CREATE INDEX idx_chat_sessions_student_id ON chat_sessions(student_id);
CREATE INDEX idx_chat_sessions_topic_id ON chat_sessions(topic_id);
CREATE INDEX idx_chat_sessions_started_at ON chat_sessions(started_at DESC);

-- Chat messages table
CREATE TABLE IF NOT EXISTS chat_messages (
    id SERIAL PRIMARY KEY,
    session_id UUID REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    agent_metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT check_role CHECK (role IN ('student', 'triage', 'concepts', 'debug', 'review', 'exercise', 'progress'))
);

CREATE INDEX idx_chat_messages_session_id ON chat_messages(session_id);
CREATE INDEX idx_chat_messages_role ON chat_messages(role);
CREATE INDEX idx_chat_messages_created_at ON chat_messages(created_at DESC);

-- Trigger for mastery scores updated_at
CREATE TRIGGER update_mastery_scores_updated_at
    BEFORE UPDATE ON mastery_scores
    FOR EACH ROW
    EXECUTE FUNCTION update_learnflow_updated_at();

-- Function to calculate mastery level based on score
CREATE OR REPLACE FUNCTION calculate_mastery_level(score FLOAT)
RETURNS VARCHAR(20) AS $$
BEGIN
    RETURN CASE
        WHEN score < 41 THEN 'beginner'
        WHEN score < 71 THEN 'learning'
        WHEN score < 91 THEN 'proficient'
        ELSE 'mastered'
    END;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Function to update overall mastery score
CREATE OR REPLACE FUNCTION update_overall_mastery_score()
RETURNS TRIGGER AS $$
BEGIN
    -- Weighted average: Exercise 40%, Quiz 30%, Code Quality 20%, Consistency 10%
    NEW.overall_score := (
        NEW.exercise_completion_score * 0.40 +
        NEW.quiz_score * 0.30 +
        NEW.code_quality_score * 0.20 +
        NEW.consistency_score * 0.10
    );

    -- Update mastery level based on overall score
    NEW.mastery_level := calculate_mastery_level(NEW.overall_score);

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-calculate overall score
CREATE TRIGGER calculate_overall_mastery
    BEFORE INSERT OR UPDATE OF exercise_completion_score, quiz_score, code_quality_score, consistency_score
    ON mastery_scores
    FOR EACH ROW
    EXECUTE FUNCTION update_overall_mastery_score();
