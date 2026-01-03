"""
Agent Orchestrator
Coordinates all AI agents and handles Dapr service invocation
"""
from typing import Dict, Any, Optional
import asyncio
import structlog
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import uvicorn

from src.agents.triage import TriageAgent
from src.agents.concepts import ConceptsAgent
from src.agents.code_review import CodeReviewAgent
from src.agents.debug import DebugAgent
from src.agents.exercise import ExerciseAgent
from src.agents.progress import ProgressAgent
from src.config import settings

logger = structlog.get_logger()

# Initialize all agents
triage_agent = TriageAgent()
concepts_agent = ConceptsAgent()
code_review_agent = CodeReviewAgent()
debug_agent = DebugAgent()
exercise_agent = ExerciseAgent()
progress_agent = ProgressAgent()

# Agent registry
AGENTS = {
    "triage": triage_agent,
    "concepts": concepts_agent,
    "code-review": code_review_agent,
    "debug": debug_agent,
    "exercise": exercise_agent,
    "progress": progress_agent
}

# FastAPI app for Dapr service invocation
app = FastAPI(
    title="LearnFlow Agent Orchestrator",
    description="Multi-agent system for AI-powered Python tutoring",
    version="1.0.0"
)


class AgentRequest(BaseModel):
    """Request to invoke an agent"""
    student_id: str
    message: str
    context: Dict[str, Any] = {}
    agent: Optional[str] = None  # If None, uses triage


class AgentResponse(BaseModel):
    """Response from an agent"""
    agent: str
    content: str
    metadata: Dict[str, Any]


@app.on_event("startup")
async def startup():
    """Initialize agents on startup"""
    logger.info("Agent Orchestrator starting up")

    # Perform health checks on all agents
    health_tasks = [agent.health_check() for agent in AGENTS.values()]
    health_results = await asyncio.gather(*health_tasks)

    for result in health_results:
        logger.info(
            "Agent health check",
            agent=result["agent"],
            status=result["status"]
        )

    logger.info("All agents initialized", total_agents=len(AGENTS))


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "LearnFlow Agent Orchestrator",
        "agents": list(AGENTS.keys()),
        "version": "1.0.0"
    }


@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "healthy",
        "agents": len(AGENTS)
    }


@app.get("/agents")
async def list_agents():
    """List all available agents"""
    return {
        "agents": [
            {
                "name": name,
                "purpose": agent.purpose,
                "model": agent.model
            }
            for name, agent in AGENTS.items()
        ]
    }


@app.post("/invoke", response_model=AgentResponse)
async def invoke_agent(request: AgentRequest):
    """
    Invoke an agent to process a student query

    Flow:
    1. If agent not specified, use Triage to route
    2. Invoke the appropriate specialist agent
    3. Return agent's response
    """
    try:
        logger.info(
            "Agent invocation requested",
            student_id=request.student_id,
            specified_agent=request.agent,
            message_preview=request.message[:50]
        )

        # Determine which agent to use
        if request.agent and request.agent in AGENTS:
            # Direct invocation
            target_agent_name = request.agent
            logger.debug("Direct agent invocation", agent=target_agent_name)

        else:
            # Use triage to route
            logger.debug("Using triage for routing")
            routing_result = await triage_agent.process(
                message=request.message,
                context=request.context
            )

            target_agent_name = routing_result.get("target_agent", "concepts")
            request.context["routing"] = routing_result

            logger.info(
                "Triage routing complete",
                target_agent=target_agent_name,
                confidence=routing_result.get("confidence"),
                method=routing_result.get("method")
            )

        # Invoke the target agent
        target_agent = AGENTS.get(target_agent_name)

        if not target_agent:
            logger.error("Invalid agent", agent=target_agent_name)
            raise HTTPException(status_code=400, detail=f"Invalid agent: {target_agent_name}")

        # Process the message
        result = await target_agent.process(
            message=request.message,
            context=request.context
        )

        logger.info(
            "Agent processing complete",
            agent=target_agent_name,
            response_length=len(result.get("content", "")),
            confidence=result.get("metadata", {}).get("confidence")
        )

        return AgentResponse(
            agent=target_agent_name,
            content=result.get("content", ""),
            metadata=result.get("metadata", {})
        )

    except Exception as e:
        logger.error("Agent invocation failed", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/triage")
async def triage_endpoint(request: AgentRequest):
    """
    Route a query to the appropriate agent (triage only)
    Returns routing decision without processing
    """
    try:
        result = await triage_agent.process(
            message=request.message,
            context=request.context
        )

        return {
            "target_agent": result.get("target_agent"),
            "confidence": result.get("confidence"),
            "reasoning": result.get("reasoning"),
            "method": result.get("method")
        }

    except Exception as e:
        logger.error("Triage failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agents/{agent_name}")
async def invoke_specific_agent(agent_name: str, request: AgentRequest):
    """
    Directly invoke a specific agent (bypassing triage)

    Supported agents:
    - concepts
    - code-review
    - debug
    - exercise
    - progress
    """
    if agent_name not in AGENTS:
        raise HTTPException(
            status_code=404,
            detail=f"Agent '{agent_name}' not found. Available: {list(AGENTS.keys())}"
        )

    try:
        agent = AGENTS[agent_name]
        result = await agent.process(
            message=request.message,
            context=request.context
        )

        return AgentResponse(
            agent=agent_name,
            content=result.get("content", ""),
            metadata=result.get("metadata", {})
        )

    except Exception as e:
        logger.error(f"Agent {agent_name} failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agents/{agent_name}/health")
async def agent_health(agent_name: str):
    """Check health of a specific agent"""
    if agent_name not in AGENTS:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_name}")

    agent = AGENTS[agent_name]
    return await agent.health_check()


# Dapr subscription endpoint for pub/sub
@app.get("/dapr/subscribe")
async def subscribe():
    """
    Dapr pub/sub subscriptions
    Subscribe to events that might trigger agent actions
    """
    return [
        {
            "pubsubname": settings.DAPR_PUBSUB_NAME,
            "topic": "struggle-alerts",
            "route": "/events/struggle-alert"
        },
        {
            "pubsubname": settings.DAPR_PUBSUB_NAME,
            "topic": "student-activity",
            "route": "/events/student-activity"
        }
    ]


@app.post("/events/struggle-alert")
async def handle_struggle_alert(request: Request):
    """
    Handle struggle alert events
    Could trigger proactive agent intervention
    """
    data = await request.json()
    logger.info("Struggle alert received", data=data)

    # In production: Trigger proactive help from appropriate agent
    # e.g., Debug agent could analyze recent errors
    # Exercise agent could generate simpler practice problems

    return {"success": True}


@app.post("/events/student-activity")
async def handle_student_activity(request: Request):
    """
    Handle student activity events
    Track patterns for better agent responses
    """
    data = await request.json()
    logger.debug("Student activity logged", event_type=data.get("data", {}).get("event_type"))

    return {"success": True}


if __name__ == "__main__":
    # Run the orchestrator
    uvicorn.run(
        "src.agents.orchestrator:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
