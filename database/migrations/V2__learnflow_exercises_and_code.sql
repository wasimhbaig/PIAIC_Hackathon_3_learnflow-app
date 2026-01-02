-- V2: LearnFlow Exercises and Code Execution
-- Creates exercises, code submissions, and test results tables

-- Exercises table
CREATE TABLE IF NOT EXISTS exercises (
    id SERIAL PRIMARY KEY,
    topic_id INTEGER REFERENCES topics(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    difficulty VARCHAR(20) NOT NULL,
    starter_code TEXT,
    solution_code TEXT,
    test_cases JSONB NOT NULL,
    hints TEXT[],
    time_limit_seconds INTEGER DEFAULT 5,
    memory_limit_mb INTEGER DEFAULT 50,
    points INTEGER DEFAULT 10,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT check_difficulty CHECK (difficulty IN ('easy', 'medium', 'hard')),
    CONSTRAINT check_time_limit CHECK (time_limit_seconds > 0 AND time_limit_seconds <= 30),
    CONSTRAINT check_memory_limit CHECK (memory_limit_mb > 0 AND memory_limit_mb <= 512)
);

CREATE INDEX idx_exercises_topic_id ON exercises(topic_id);
CREATE INDEX idx_exercises_difficulty ON exercises(difficulty);

-- Code submissions table
CREATE TABLE IF NOT EXISTS code_submissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID REFERENCES students(id) ON DELETE CASCADE,
    exercise_id INTEGER REFERENCES exercises(id) ON DELETE SET NULL,
    code TEXT NOT NULL,
    language VARCHAR(20) DEFAULT 'python',
    status VARCHAR(20) NOT NULL,
    execution_time_ms INTEGER,
    memory_used_mb FLOAT,
    stdout TEXT,
    stderr TEXT,
    score INTEGER,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT check_status CHECK (status IN ('passed', 'failed', 'error', 'timeout', 'running')),
    CONSTRAINT check_score CHECK (score IS NULL OR (score >= 0 AND score <= 100))
);

CREATE INDEX idx_code_submissions_student_id ON code_submissions(student_id);
CREATE INDEX idx_code_submissions_exercise_id ON code_submissions(exercise_id);
CREATE INDEX idx_code_submissions_submitted_at ON code_submissions(submitted_at DESC);
CREATE INDEX idx_code_submissions_status ON code_submissions(status);

-- Test results table
CREATE TABLE IF NOT EXISTS test_results (
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
CREATE INDEX idx_test_results_passed ON test_results(passed);
