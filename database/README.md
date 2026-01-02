# LearnFlow Database Migrations

This directory contains SQL migration files for the LearnFlow database schema.

## Migration Files

The migrations are numbered sequentially and should be applied in order:

1. **V1__learnflow_core_tables.sql** - Core entities (students, teachers, classes, curriculum)
2. **V2__learnflow_exercises_and_code.sql** - Exercises and code execution
3. **V3__learnflow_quizzes.sql** - Quiz system
4. **V4__learnflow_mastery_and_tracking.sql** - Mastery scores, progress tracking, struggle detection
5. **V5__learnflow_views_and_functions.sql** - Reporting views and helper functions

## Prerequisites

- PostgreSQL 15+ database running
- The base `users` table from the learning platform schema (see skills-library/postgres-k8s-setup)
- Database: `learning_platform` (or configured name)

## Running Migrations

### Option 1: Using the skills-library migration tool

The migrations can be run using the PostgreSQL migration tool from the skills-library:

```bash
# Copy migrations to skills-library postgres migrations directory
cp database/migrations/*.sql ../skills-library/postgres-k8s-setup/migrations/

# Run the migration script
cd ../skills-library/postgres-k8s-setup
./scripts/run-migrations.sh
```

### Option 2: Manual execution with psql

```bash
# Set connection details
export PGHOST=localhost  # or your postgres service
export PGPORT=5432
export PGDATABASE=learning_platform
export PGUSER=postgres
export PGPASSWORD=your_password

# Run migrations in order
psql -f database/migrations/V1__learnflow_core_tables.sql
psql -f database/migrations/V2__learnflow_exercises_and_code.sql
psql -f database/migrations/V3__learnflow_quizzes.sql
psql -f database/migrations/V4__learnflow_mastery_and_tracking.sql
psql -f database/migrations/V5__learnflow_views_and_functions.sql
```

### Option 3: Using kubectl (for Kubernetes deployment)

```bash
# Get the database password
PGPASSWORD=$(kubectl get secret -n postgres postgres-postgresql -o jsonpath='{.data.postgres-password}' | base64 -d)

# Run each migration
for migration in database/migrations/V*.sql; do
  echo "Applying $(basename $migration)..."
  cat "$migration" | kubectl exec -i -n postgres postgres-postgresql-primary-0 -- \
    env PGPASSWORD="$PGPASSWORD" psql -U postgres -d learning_platform
done
```

## Verification

After running migrations, verify the schema:

```sql
-- Check tables
SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename;

-- Check views
SELECT viewname FROM pg_views WHERE schemaname = 'public' ORDER BY viewname;

-- Check functions
SELECT routine_name, routine_type
FROM information_schema.routines
WHERE routine_schema = 'public'
ORDER BY routine_name;

-- Verify modules are seeded
SELECT number, name FROM modules ORDER BY number;
```

Expected output should include:
- **15+ tables**: students, teachers, classes, enrollments, modules, topics, exercises, etc.
- **5 views**: v_student_progress, v_class_performance, v_topic_mastery_distribution, etc.
- **4+ functions**: calculate_mastery_level, update_overall_mastery_score, get_student_learning_path, etc.
- **8 modules**: Basics, Control Flow, Data Structures, Functions, OOP, Files, Errors, Libraries

## Schema Overview

### Core Tables
- `students` - Student profiles and preferences
- `teachers` - Teacher profiles
- `classes` - Class management
- `enrollments` - Student-class relationships
- `modules` - Python curriculum (8 modules)
- `topics` - Individual learning topics

### Assessment Tables
- `exercises` - Coding exercises with test cases
- `code_submissions` - Student code attempts
- `test_results` - Individual test case results
- `quiz_questions` - Quiz question bank
- `quiz_attempts` - Quiz session results
- `quiz_answers` - Individual quiz answers

### Tracking Tables
- `mastery_scores` - Topic-level mastery tracking
- `progress_events` - Activity timeline
- `struggle_alerts` - Automated struggle detection
- `chat_sessions` - AI tutor conversations
- `chat_messages` - Chat history

### Views
- `v_student_progress` - Comprehensive student metrics
- `v_class_performance` - Class-level analytics
- `v_topic_mastery_distribution` - Topic difficulty analysis
- `v_exercise_performance` - Exercise success rates
- `v_recent_activity` - Activity feed

## Data Seeding

### Modules (Pre-seeded in V1)

The 8 Python curriculum modules are automatically seeded:

1. Basics (8 hours)
2. Control Flow (10 hours)
3. Data Structures (12 hours)
4. Functions (10 hours)
5. OOP (15 hours)
6. Files (8 hours)
7. Errors (8 hours)
8. Libraries (10 hours)

### Topics

Topics should be seeded by the application during initialization. See `src/services/curriculum_service.py` for topic seeding.

### Sample Exercises

Sample exercises can be loaded using the exercise generation system. See `src/agents/exercise_agent.py`.

## Rollback

To rollback migrations (use with caution):

```sql
-- Rollback V5 (views and functions)
DROP VIEW IF EXISTS v_recent_activity CASCADE;
DROP VIEW IF EXISTS v_exercise_performance CASCADE;
DROP VIEW IF EXISTS v_topic_mastery_distribution CASCADE;
DROP VIEW IF EXISTS v_class_performance CASCADE;
DROP VIEW IF EXISTS v_student_progress CASCADE;
DROP FUNCTION IF EXISTS calculate_exercise_completion_rate(UUID, INTEGER);
DROP FUNCTION IF EXISTS detect_struggle_patterns(UUID, INTEGER);
DROP FUNCTION IF EXISTS get_student_learning_path(UUID);
DROP FUNCTION IF EXISTS calculate_mastery_level(FLOAT);
DROP FUNCTION IF EXISTS update_overall_mastery_score();

-- Rollback V4 (mastery and tracking)
DROP TABLE IF EXISTS chat_messages CASCADE;
DROP TABLE IF EXISTS chat_sessions CASCADE;
DROP TABLE IF EXISTS struggle_alerts CASCADE;
DROP TABLE IF EXISTS progress_events CASCADE;
DROP TABLE IF EXISTS mastery_scores CASCADE;

-- Rollback V3 (quizzes)
DROP TABLE IF EXISTS quiz_answers CASCADE;
DROP TABLE IF EXISTS quiz_attempts CASCADE;
DROP TABLE IF EXISTS quiz_questions CASCADE;

-- Rollback V2 (exercises)
DROP TABLE IF EXISTS test_results CASCADE;
DROP TABLE IF EXISTS code_submissions CASCADE;
DROP TABLE IF EXISTS exercises CASCADE;

-- Rollback V1 (core)
DROP TABLE IF EXISTS topics CASCADE;
DROP TABLE IF EXISTS modules CASCADE;
DROP TABLE IF EXISTS enrollments CASCADE;
DROP TABLE IF EXISTS classes CASCADE;
DROP TABLE IF EXISTS teachers CASCADE;
DROP TABLE IF EXISTS students CASCADE;
DROP FUNCTION IF EXISTS update_learnflow_updated_at();
DROP EXTENSION IF EXISTS pgcrypto;
```

## Performance Considerations

### Indexes

All migrations include appropriate indexes for:
- Foreign key relationships
- Common query patterns (student_id, topic_id, etc.)
- Time-based queries (created_at, submitted_at, etc.)
- Status filters (is_active, is_resolved, status, etc.)

### Partitioning (Future)

For high-volume tables, consider partitioning:
- `code_submissions` by submitted_at (monthly partitions)
- `chat_messages` by created_at (weekly partitions)
- `progress_events` by created_at (monthly partitions)

### Archival

Implement archival strategy for:
- Chat messages older than 90 days
- Code submissions older than 1 year (keep metadata)
- Progress events older than 1 year

## Troubleshooting

### Common Issues

**Error: relation "users" does not exist**
- Ensure base learning platform schema is created first
- Run skills-library postgres migrations before LearnFlow migrations

**Error: function gen_random_uuid() does not exist**
- The pgcrypto extension wasn't created
- Manually run: `CREATE EXTENSION IF NOT EXISTS pgcrypto;`

**Error: constraint violation**
- Check that you're running migrations in order (V1 → V5)
- Verify no existing data conflicts with new constraints

**Error: permission denied**
- Ensure the database user has CREATE TABLE, CREATE FUNCTION privileges
- May need SUPERUSER for creating extensions

## Testing Migrations

```sql
-- Test data insertion
BEGIN;

-- Create test student
INSERT INTO students (user_id, student_code, current_module)
VALUES (1, 'STU2024001', 1);

-- Check triggers work
SELECT * FROM students WHERE student_code = 'STU2024001';

ROLLBACK;  -- Don't commit test data
```

## Migration History

Track applied migrations in a separate table (optional):

```sql
CREATE TABLE schema_migrations (
    version VARCHAR(255) PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Record migrations as you apply them
INSERT INTO schema_migrations (version) VALUES ('V1__learnflow_core_tables');
INSERT INTO schema_migrations (version) VALUES ('V2__learnflow_exercises_and_code');
-- etc...
```

## Support

For migration issues or questions:
- Check the main documentation: `docs/DATABASE_SCHEMA.md`
- Review the architecture: `docs/ARCHITECTURE.md`
- Open an issue on GitHub
