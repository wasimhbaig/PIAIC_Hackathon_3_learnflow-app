-- V5: LearnFlow Views and Helper Functions
-- Creates reporting views and utility functions

-- View: Student Progress Summary
CREATE OR REPLACE VIEW v_student_progress AS
SELECT
    s.id as student_id,
    s.student_code,
    u.full_name as student_name,
    s.current_module,
    s.learning_pace,
    COUNT(DISTINCT ms.topic_id) as topics_started,
    COUNT(DISTINCT CASE WHEN ms.mastery_level IN ('proficient', 'mastered') THEN ms.topic_id END) as topics_mastered,
    AVG(ms.overall_score) as avg_mastery_score,
    MAX(ms.current_streak_days) as longest_streak,
    COUNT(DISTINCT cs.id) as total_code_submissions,
    COUNT(DISTINCT cs.id) FILTER (WHERE cs.status = 'passed') as successful_submissions,
    COUNT(DISTINCT qa.id) as total_quiz_attempts,
    AVG(qa.score_percentage) as avg_quiz_score,
    MAX(ms.last_activity_at) as last_active,
    COUNT(DISTINCT CASE WHEN sa.is_resolved = false THEN sa.id END) as active_struggles
FROM students s
JOIN users u ON s.user_id = u.id
LEFT JOIN mastery_scores ms ON s.id = ms.student_id
LEFT JOIN code_submissions cs ON s.id = cs.student_id
LEFT JOIN quiz_attempts qa ON s.id = qa.student_id
LEFT JOIN struggle_alerts sa ON s.id = sa.student_id
GROUP BY s.id, s.student_code, u.full_name, s.current_module, s.learning_pace;

-- View: Class Performance Dashboard
CREATE OR REPLACE VIEW v_class_performance AS
SELECT
    c.id as class_id,
    c.name as class_name,
    t.teacher_code,
    u.full_name as teacher_name,
    c.start_date,
    c.end_date,
    c.is_active,
    COUNT(DISTINCT e.student_id) as total_students,
    COUNT(DISTINCT CASE WHEN vsp.last_active > CURRENT_TIMESTAMP - INTERVAL '7 days' THEN e.student_id END) as active_students,
    AVG(vsp.avg_mastery_score) as class_avg_mastery,
    AVG(vsp.avg_quiz_score) as class_avg_quiz_score,
    SUM(vsp.total_code_submissions) as total_submissions,
    COUNT(DISTINCT sa.id) FILTER (WHERE sa.is_resolved = false) as active_struggle_alerts,
    COUNT(DISTINCT sa.id) FILTER (WHERE sa.severity = 'high' AND sa.is_resolved = false) as high_priority_alerts
FROM classes c
JOIN teachers t ON c.teacher_id = t.id
JOIN users u ON t.user_id = u.id
LEFT JOIN enrollments e ON c.id = e.class_id AND e.status = 'active'
LEFT JOIN v_student_progress vsp ON e.student_id = vsp.student_id
LEFT JOIN struggle_alerts sa ON e.student_id = sa.student_id
WHERE c.is_active = true
GROUP BY c.id, c.name, t.teacher_code, u.full_name, c.start_date, c.end_date, c.is_active;

-- View: Topic Mastery Distribution
CREATE OR REPLACE VIEW v_topic_mastery_distribution AS
SELECT
    t.id as topic_id,
    t.name as topic_name,
    m.name as module_name,
    t.difficulty,
    COUNT(DISTINCT ms.student_id) as total_students,
    COUNT(DISTINCT CASE WHEN ms.mastery_level = 'beginner' THEN ms.student_id END) as beginners,
    COUNT(DISTINCT CASE WHEN ms.mastery_level = 'learning' THEN ms.student_id END) as learning,
    COUNT(DISTINCT CASE WHEN ms.mastery_level = 'proficient' THEN ms.student_id END) as proficient,
    COUNT(DISTINCT CASE WHEN ms.mastery_level = 'mastered' THEN ms.student_id END) as mastered,
    AVG(ms.overall_score) as avg_score,
    AVG(ms.quiz_score) as avg_quiz_score,
    AVG(ms.code_quality_score) as avg_code_quality
FROM topics t
JOIN modules m ON t.module_id = m.id
LEFT JOIN mastery_scores ms ON t.id = ms.topic_id
GROUP BY t.id, t.name, m.name, t.difficulty;

-- View: Exercise Performance Stats
CREATE OR REPLACE VIEW v_exercise_performance AS
SELECT
    e.id as exercise_id,
    e.title,
    t.name as topic_name,
    e.difficulty,
    e.points,
    COUNT(DISTINCT cs.student_id) as attempted_by,
    COUNT(cs.id) as total_attempts,
    COUNT(cs.id) FILTER (WHERE cs.status = 'passed') as successful_attempts,
    ROUND(100.0 * COUNT(cs.id) FILTER (WHERE cs.status = 'passed') / NULLIF(COUNT(cs.id), 0), 2) as success_rate,
    AVG(cs.execution_time_ms) as avg_execution_time,
    AVG(cs.score) as avg_score,
    MIN(cs.submitted_at) as first_attempt,
    MAX(cs.submitted_at) as last_attempt
FROM exercises e
JOIN topics t ON e.topic_id = t.id
LEFT JOIN code_submissions cs ON e.id = cs.exercise_id
GROUP BY e.id, e.title, t.name, e.difficulty, e.points;

-- View: Recent Activity Timeline
CREATE OR REPLACE VIEW v_recent_activity AS
SELECT
    pe.id,
    pe.student_id,
    s.student_code,
    u.full_name as student_name,
    pe.event_type,
    pe.event_data,
    pe.created_at
FROM progress_events pe
JOIN students s ON pe.student_id = s.id
JOIN users u ON s.user_id = u.id
ORDER BY pe.created_at DESC;

-- Function: Get student's current learning path
CREATE OR REPLACE FUNCTION get_student_learning_path(p_student_id UUID)
RETURNS TABLE (
    module_number INTEGER,
    module_name VARCHAR(100),
    topic_id INTEGER,
    topic_name VARCHAR(255),
    mastery_level VARCHAR(20),
    overall_score FLOAT,
    recommended_next BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        m.number,
        m.name,
        t.id,
        t.name,
        COALESCE(ms.mastery_level, 'beginner'),
        COALESCE(ms.overall_score, 0.0),
        (ms.mastery_level IS NULL OR ms.mastery_level = 'beginner') AND
        t.order_index = (
            SELECT MIN(t2.order_index)
            FROM topics t2
            LEFT JOIN mastery_scores ms2 ON t2.id = ms2.topic_id AND ms2.student_id = p_student_id
            WHERE t2.module_id = m.id
            AND (ms2.mastery_level IS NULL OR ms2.mastery_level IN ('beginner', 'learning'))
        ) as recommended_next
    FROM modules m
    JOIN topics t ON m.id = t.module_id
    LEFT JOIN mastery_scores ms ON t.id = ms.topic_id AND ms.student_id = p_student_id
    ORDER BY m.order_index, t.order_index;
END;
$$ LANGUAGE plpgsql;

-- Function: Detect struggle patterns
CREATE OR REPLACE FUNCTION detect_struggle_patterns(p_student_id UUID, p_topic_id INTEGER)
RETURNS TABLE (
    pattern VARCHAR(50),
    severity VARCHAR(20),
    description TEXT,
    evidence JSONB
) AS $$
DECLARE
    repeated_errors INTEGER;
    low_quiz_attempts INTEGER;
    failed_submissions INTEGER;
    time_on_exercise INTEGER;
BEGIN
    -- Check for repeated errors (same error 3+ times)
    SELECT COUNT(DISTINCT cs.id)
    INTO repeated_errors
    FROM code_submissions cs
    WHERE cs.student_id = p_student_id
    AND cs.exercise_id IN (SELECT id FROM exercises WHERE topic_id = p_topic_id)
    AND cs.status = 'error'
    AND cs.submitted_at > CURRENT_TIMESTAMP - INTERVAL '24 hours';

    IF repeated_errors >= 3 THEN
        pattern := 'repeated_error';
        severity := 'medium';
        description := format('Student encountered %s errors in the last 24 hours', repeated_errors);
        evidence := jsonb_build_object('error_count', repeated_errors);
        RETURN NEXT;
    END IF;

    -- Check for low quiz scores
    SELECT COUNT(*)
    INTO low_quiz_attempts
    FROM quiz_attempts qa
    WHERE qa.student_id = p_student_id
    AND qa.topic_id = p_topic_id
    AND qa.score_percentage < 50
    AND qa.completed_at > CURRENT_TIMESTAMP - INTERVAL '7 days';

    IF low_quiz_attempts >= 2 THEN
        pattern := 'low_quiz_score';
        severity := 'high';
        description := format('Student scored below 50%% on %s recent quizzes', low_quiz_attempts);
        evidence := jsonb_build_object('low_score_count', low_quiz_attempts);
        RETURN NEXT;
    END IF;

    -- Check for multiple failed submissions
    SELECT COUNT(*)
    INTO failed_submissions
    FROM code_submissions cs
    WHERE cs.student_id = p_student_id
    AND cs.exercise_id IN (SELECT id FROM exercises WHERE topic_id = p_topic_id)
    AND cs.status IN ('failed', 'error')
    AND cs.submitted_at > CURRENT_TIMESTAMP - INTERVAL '1 hour';

    IF failed_submissions >= 5 THEN
        pattern := 'multiple_failures';
        severity := 'high';
        description := format('Student had %s failed code submissions in the last hour', failed_submissions);
        evidence := jsonb_build_object('failure_count', failed_submissions);
        RETURN NEXT;
    END IF;

    RETURN;
END;
$$ LANGUAGE plpgsql;

-- Function: Calculate exercise completion rate
CREATE OR REPLACE FUNCTION calculate_exercise_completion_rate(p_student_id UUID, p_topic_id INTEGER)
RETURNS FLOAT AS $$
DECLARE
    total_exercises INTEGER;
    completed_exercises INTEGER;
BEGIN
    SELECT COUNT(*) INTO total_exercises
    FROM exercises
    WHERE topic_id = p_topic_id;

    SELECT COUNT(DISTINCT exercise_id) INTO completed_exercises
    FROM code_submissions
    WHERE student_id = p_student_id
    AND status = 'passed'
    AND exercise_id IN (SELECT id FROM exercises WHERE topic_id = p_topic_id);

    IF total_exercises = 0 THEN
        RETURN 0;
    END IF;

    RETURN (completed_exercises::FLOAT / total_exercises::FLOAT) * 100;
END;
$$ LANGUAGE plpgsql;
