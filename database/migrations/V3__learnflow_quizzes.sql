-- V3: LearnFlow Quizzes and Assessments
-- Creates quiz questions, attempts, and answers tables

-- Quiz questions table
CREATE TABLE IF NOT EXISTS quiz_questions (
    id SERIAL PRIMARY KEY,
    topic_id INTEGER REFERENCES topics(id) ON DELETE CASCADE,
    question_type VARCHAR(20) NOT NULL,
    question_text TEXT NOT NULL,
    options JSONB,
    correct_answer TEXT NOT NULL,
    explanation TEXT,
    difficulty VARCHAR(20) NOT NULL,
    points INTEGER DEFAULT 10,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT check_question_type CHECK (question_type IN ('multiple_choice', 'coding', 'true_false')),
    CONSTRAINT check_difficulty CHECK (difficulty IN ('easy', 'medium', 'hard')),
    CONSTRAINT check_points CHECK (points > 0)
);

CREATE INDEX idx_quiz_questions_topic_id ON quiz_questions(topic_id);
CREATE INDEX idx_quiz_questions_type ON quiz_questions(question_type);
CREATE INDEX idx_quiz_questions_difficulty ON quiz_questions(difficulty);

-- Quiz attempts table
CREATE TABLE IF NOT EXISTS quiz_attempts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID REFERENCES students(id) ON DELETE CASCADE,
    topic_id INTEGER REFERENCES topics(id) ON DELETE CASCADE,
    total_questions INTEGER NOT NULL,
    correct_answers INTEGER NOT NULL,
    score_percentage FLOAT NOT NULL,
    time_taken_seconds INTEGER,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT check_total_questions CHECK (total_questions > 0),
    CONSTRAINT check_correct_answers CHECK (correct_answers >= 0 AND correct_answers <= total_questions),
    CONSTRAINT check_score CHECK (score_percentage >= 0 AND score_percentage <= 100)
);

CREATE INDEX idx_quiz_attempts_student_id ON quiz_attempts(student_id);
CREATE INDEX idx_quiz_attempts_topic_id ON quiz_attempts(topic_id);
CREATE INDEX idx_quiz_attempts_completed_at ON quiz_attempts(completed_at DESC);
CREATE INDEX idx_quiz_attempts_score ON quiz_attempts(score_percentage);

-- Quiz answers table
CREATE TABLE IF NOT EXISTS quiz_answers (
    id SERIAL PRIMARY KEY,
    attempt_id UUID REFERENCES quiz_attempts(id) ON DELETE CASCADE,
    question_id INTEGER REFERENCES quiz_questions(id) ON DELETE CASCADE,
    student_answer TEXT,
    is_correct BOOLEAN NOT NULL,
    time_taken_seconds INTEGER,
    CONSTRAINT check_time_taken CHECK (time_taken_seconds IS NULL OR time_taken_seconds >= 0)
);

CREATE INDEX idx_quiz_answers_attempt_id ON quiz_answers(attempt_id);
CREATE INDEX idx_quiz_answers_question_id ON quiz_answers(question_id);
CREATE INDEX idx_quiz_answers_correct ON quiz_answers(is_correct);
