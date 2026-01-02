-- V1: LearnFlow Core Tables
-- Creates students, teachers, classes, enrollments, and curriculum structure

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Students table
CREATE TABLE IF NOT EXISTS students (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    student_code VARCHAR(20) UNIQUE NOT NULL,
    current_module INTEGER DEFAULT 1,
    learning_pace VARCHAR(20) DEFAULT 'normal',
    preferred_explanation_style VARCHAR(20) DEFAULT 'examples',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT check_module CHECK (current_module BETWEEN 1 AND 8),
    CONSTRAINT check_pace CHECK (learning_pace IN ('slow', 'normal', 'fast')),
    CONSTRAINT check_style CHECK (preferred_explanation_style IN ('theory', 'examples', 'visual', 'mixed'))
);

CREATE INDEX idx_students_user_id ON students(user_id);
CREATE INDEX idx_students_current_module ON students(current_module);

-- Teachers table
CREATE TABLE IF NOT EXISTS teachers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    teacher_code VARCHAR(20) UNIQUE NOT NULL,
    specialization TEXT[],
    years_experience INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_teachers_user_id ON teachers(user_id);

-- Classes table
CREATE TABLE IF NOT EXISTS classes (
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

-- Enrollments table
CREATE TABLE IF NOT EXISTS enrollments (
    id SERIAL PRIMARY KEY,
    student_id UUID REFERENCES students(id) ON DELETE CASCADE,
    class_id INTEGER REFERENCES classes(id) ON DELETE CASCADE,
    enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'active',
    UNIQUE(student_id, class_id),
    CONSTRAINT check_status CHECK (status IN ('active', 'completed', 'dropped'))
);

CREATE INDEX idx_enrollments_student_id ON enrollments(student_id);
CREATE INDEX idx_enrollments_class_id ON enrollments(class_id);

-- Modules table (8 Python curriculum modules)
CREATE TABLE IF NOT EXISTS modules (
    id SERIAL PRIMARY KEY,
    number INTEGER UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    order_index INTEGER NOT NULL,
    estimated_hours INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT check_number CHECK (number BETWEEN 1 AND 8)
);

-- Topics table
CREATE TABLE IF NOT EXISTS topics (
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

-- Seed Python curriculum modules
INSERT INTO modules (number, name, description, order_index, estimated_hours) VALUES
(1, 'Basics', 'Variables, Data Types, Input/Output, Operators, Type Conversion', 1, 8),
(2, 'Control Flow', 'Conditionals (if/elif/else), For Loops, While Loops, Break/Continue', 2, 10),
(3, 'Data Structures', 'Lists, Tuples, Dictionaries, Sets', 3, 12),
(4, 'Functions', 'Defining Functions, Parameters, Return Values, Scope', 4, 10),
(5, 'OOP', 'Classes & Objects, Attributes & Methods, Inheritance, Encapsulation', 5, 15),
(6, 'Files', 'Reading/Writing Files, CSV Processing, JSON Handling', 6, 8),
(7, 'Errors', 'Try/Except, Exception Types, Custom Exceptions, Debugging', 7, 8),
(8, 'Libraries', 'Installing Packages, Working with APIs, Virtual Environments', 8, 10)
ON CONFLICT (number) DO NOTHING;

-- Trigger function for updated_at
CREATE OR REPLACE FUNCTION update_learnflow_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply triggers
CREATE TRIGGER update_students_updated_at
    BEFORE UPDATE ON students
    FOR EACH ROW
    EXECUTE FUNCTION update_learnflow_updated_at();

CREATE TRIGGER update_teachers_updated_at
    BEFORE UPDATE ON teachers
    FOR EACH ROW
    EXECUTE FUNCTION update_learnflow_updated_at();

CREATE TRIGGER update_classes_updated_at
    BEFORE UPDATE ON classes
    FOR EACH ROW
    EXECUTE FUNCTION update_learnflow_updated_at();
