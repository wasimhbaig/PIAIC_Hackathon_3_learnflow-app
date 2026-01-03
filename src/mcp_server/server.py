"""
MCP Server for LearnFlow
Provides rich context to AI agents for debugging and expansion
"""
import asyncio
import json
from typing import Dict, Any, List
import structlog
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from src.config import settings

logger = structlog.get_logger()

# Create MCP server
mcp = Server("learnflow")


###############################################################################
# MCP Tools - Available to AI Agents
###############################################################################

@mcp.list_tools()
async def list_tools() -> List[Tool]:
    """
    List all available MCP tools
    """
    return [
        Tool(
            name="get_student_progress",
            description="Retrieve comprehensive student progress including mastery scores for all topics",
            inputSchema={
                "type": "object",
                "properties": {
                    "student_id": {
                        "type": "string",
                        "description": "UUID of the student"
                    }
                },
                "required": ["student_id"]
            }
        ),
        Tool(
            name="analyze_code_submission",
            description="Deep analysis of a code submission including test results and quality metrics",
            inputSchema={
                "type": "object",
                "properties": {
                    "submission_id": {
                        "type": "string",
                        "description": "UUID of the code submission"
                    }
                },
                "required": ["submission_id"]
            }
        ),
        Tool(
            name="get_curriculum_topics",
            description="Get all topics for a Python module with descriptions and difficulty",
            inputSchema={
                "type": "object",
                "properties": {
                    "module_id": {
                        "type": "integer",
                        "description": "Module number (1-8)",
                        "minimum": 1,
                        "maximum": 8
                    }
                },
                "required": ["module_id"]
            }
        ),
        Tool(
            name="detect_struggle_patterns",
            description="Analyze student activity to detect struggle patterns and recommend interventions",
            inputSchema={
                "type": "object",
                "properties": {
                    "student_id": {
                        "type": "string",
                        "description": "UUID of the student"
                    },
                    "lookback_days": {
                        "type": "integer",
                        "description": "Number of days to analyze",
                        "default": 7
                    }
                },
                "required": ["student_id"]
            }
        ),
        Tool(
            name="suggest_exercises",
            description="Generate personalized exercise recommendations based on student performance",
            inputSchema={
                "type": "object",
                "properties": {
                    "student_id": {
                        "type": "string",
                        "description": "UUID of the student"
                    },
                    "topic_id": {
                        "type": "integer",
                        "description": "Topic ID to generate exercises for"
                    },
                    "difficulty": {
                        "type": "string",
                        "enum": ["easy", "medium", "hard"],
                        "description": "Desired difficulty level"
                    }
                },
                "required": ["student_id", "topic_id"]
            }
        ),
        Tool(
            name="get_common_errors",
            description="Retrieve most common errors for a topic to help agents provide better debugging guidance",
            inputSchema={
                "type": "object",
                "properties": {
                    "topic_id": {
                        "type": "integer",
                        "description": "Topic ID"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of errors to return",
                        "default": 5
                    }
                },
                "required": ["topic_id"]
            }
        )
    ]


@mcp.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """
    Handle tool calls from AI agents
    """
    logger.info("MCP tool called", tool=name, arguments=arguments)

    try:
        if name == "get_student_progress":
            result = await get_student_progress(arguments["student_id"])

        elif name == "analyze_code_submission":
            result = await analyze_code_submission(arguments["submission_id"])

        elif name == "get_curriculum_topics":
            result = await get_curriculum_topics(arguments["module_id"])

        elif name == "detect_struggle_patterns":
            result = await detect_struggle_patterns(
                arguments["student_id"],
                arguments.get("lookback_days", 7)
            )

        elif name == "suggest_exercises":
            result = await suggest_exercises(
                arguments["student_id"],
                arguments["topic_id"],
                arguments.get("difficulty", "medium")
            )

        elif name == "get_common_errors":
            result = await get_common_errors(
                arguments["topic_id"],
                arguments.get("limit", 5)
            )

        else:
            return [TextContent(
                type="text",
                text=f"Unknown tool: {name}"
            )]

        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]

    except Exception as e:
        logger.error("Tool call failed", tool=name, error=str(e))
        return [TextContent(
            type="text",
            text=f"Error: {str(e)}"
        )]


###############################################################################
# Tool Implementations
###############################################################################

async def get_student_progress(student_id: str) -> Dict[str, Any]:
    """
    Get comprehensive student progress

    In production, this would query the database.
    For MVP, returning mock data.
    """
    # Mock data - In production: query database
    return {
        "student_id": student_id,
        "current_module": 2,
        "overall_mastery": 68.5,
        "topics": [
            {
                "topic_id": 1,
                "topic_name": "Variables and Data Types",
                "module": 1,
                "mastery_score": 95,
                "level": "mastered",
                "exercises_completed": 12,
                "quizzes_taken": 3,
                "avg_quiz_score": 92
            },
            {
                "topic_id": 2,
                "topic_name": "For Loops",
                "module": 2,
                "mastery_score": 85,
                "level": "proficient",
                "exercises_completed": 8,
                "quizzes_taken": 2,
                "avg_quiz_score": 80
            },
            {
                "topic_id": 3,
                "topic_name": "While Loops",
                "module": 2,
                "mastery_score": 60,
                "level": "learning",
                "exercises_completed": 5,
                "quizzes_taken": 1,
                "avg_quiz_score": 65
            }
        ],
        "streak_days": 5,
        "last_activity": "2025-01-02T10:30:00Z"
    }


async def analyze_code_submission(submission_id: str) -> Dict[str, Any]:
    """
    Analyze a code submission

    Provides detailed metrics and test results
    """
    return {
        "submission_id": submission_id,
        "student_id": "student-123",
        "exercise_id": 42,
        "submitted_at": "2025-01-02T10:25:00Z",
        "code_length": 45,
        "execution_time_ms": 23,
        "status": "passed",
        "test_results": {
            "total": 5,
            "passed": 4,
            "failed": 1,
            "details": [
                {"test": "basic_case", "passed": True},
                {"test": "edge_case_empty", "passed": True},
                {"test": "edge_case_negative", "passed": False, "error": "IndexError"},
                {"test": "large_input", "passed": True},
                {"test": "special_characters", "passed": True}
            ]
        },
        "quality_metrics": {
            "correctness": 80,
            "style": 90,
            "efficiency": 85,
            "readability": 75
        },
        "overall_score": 82
    }


async def get_curriculum_topics(module_id: int) -> Dict[str, Any]:
    """
    Get all topics for a module
    """
    modules = {
        1: {
            "number": 1,
            "name": "Basics",
            "topics": [
                {"id": 1, "name": "Variables and Data Types", "difficulty": "beginner"},
                {"id": 2, "name": "Input/Output", "difficulty": "beginner"},
                {"id": 3, "name": "Operators", "difficulty": "beginner"},
                {"id": 4, "name": "Type Conversion", "difficulty": "intermediate"}
            ]
        },
        2: {
            "number": 2,
            "name": "Control Flow",
            "topics": [
                {"id": 5, "name": "If/Elif/Else", "difficulty": "beginner"},
                {"id": 6, "name": "For Loops", "difficulty": "beginner"},
                {"id": 7, "name": "While Loops", "difficulty": "intermediate"},
                {"id": 8, "name": "Break and Continue", "difficulty": "intermediate"}
            ]
        }
    }

    return modules.get(module_id, {
        "number": module_id,
        "name": f"Module {module_id}",
        "topics": []
    })


async def detect_struggle_patterns(student_id: str, lookback_days: int) -> Dict[str, Any]:
    """
    Analyze student activity to detect struggles
    """
    return {
        "student_id": student_id,
        "analysis_period_days": lookback_days,
        "struggles_detected": True,
        "patterns": [
            {
                "type": "repeated_error",
                "topic_id": 3,
                "topic_name": "While Loops",
                "error_type": "infinite_loop",
                "occurrences": 4,
                "severity": "medium",
                "recommendation": "Provide tutorial on loop termination conditions"
            },
            {
                "type": "stuck_on_exercise",
                "exercise_id": 42,
                "time_spent_minutes": 25,
                "attempts": 7,
                "severity": "high",
                "recommendation": "Offer progressive hints or simpler practice problem"
            }
        ],
        "suggested_interventions": [
            "Send Debug Agent proactively",
            "Recommend easier exercises on while loops",
            "Notify teacher via struggle alert"
        ]
    }


async def suggest_exercises(student_id: str, topic_id: int, difficulty: str) -> Dict[str, Any]:
    """
    Generate exercise recommendations
    """
    return {
        "student_id": student_id,
        "topic_id": topic_id,
        "difficulty": difficulty,
        "recommended_exercises": [
            {
                "exercise_id": 101,
                "title": "Simple While Loop Counter",
                "difficulty": "easy",
                "estimated_time_minutes": 10,
                "rationale": "Student struggling with while loops - start easy"
            },
            {
                "exercise_id": 102,
                "title": "User Input While Loop",
                "difficulty": "easy",
                "estimated_time_minutes": 15,
                "rationale": "Builds on previous, adds input handling"
            }
        ]
    }


async def get_common_errors(topic_id: int, limit: int) -> Dict[str, Any]:
    """
    Get most common errors for a topic
    """
    return {
        "topic_id": topic_id,
        "common_errors": [
            {
                "error_type": "NameError",
                "message": "name 'x' is not defined",
                "frequency": 45,
                "typical_cause": "Variable used before assignment",
                "hint_template": "Check if you defined 'x' before using it"
            },
            {
                "error_type": "IndentationError",
                "message": "unexpected indent",
                "frequency": 32,
                "typical_cause": "Inconsistent indentation",
                "hint_template": "Make sure your indentation is consistent (4 spaces)"
            },
            {
                "error_type": "SyntaxError",
                "message": "invalid syntax",
                "frequency": 28,
                "typical_cause": "Missing colon after if/for/while",
                "hint_template": "Did you forget a colon (:) after your statement?"
            }
        ]
    }


###############################################################################
# Server Startup
###############################################################################

async def main():
    """Run the MCP server"""
    logger.info("Starting LearnFlow MCP Server", port=settings.MCP_SERVER_PORT)

    async with stdio_server() as (read_stream, write_stream):
        await mcp.run(
            read_stream,
            write_stream,
            mcp.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
