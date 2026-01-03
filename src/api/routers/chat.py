"""
Chat endpoints
WebSocket-based real-time chat with AI tutoring agents
"""
from typing import Dict, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.orm import Session
import structlog
import json
from datetime import datetime
import uuid

from src.api.dependencies import get_db
from src.config import settings

logger = structlog.get_logger()

router = APIRouter()

# Active WebSocket connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info("WebSocket connected", client_id=client_id, total_connections=len(self.active_connections))

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info("WebSocket disconnected", client_id=client_id, total_connections=len(self.active_connections))

    async def send_message(self, message: dict, client_id: str):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(message)

    async def broadcast(self, message: dict):
        for connection in self.active_connections.values():
            await connection.send_json(message)


manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_chat_endpoint(
    websocket: WebSocket,
    student_id: str = Query(..., description="Student ID for authentication"),
    session_id: str = Query(default=None, description="Optional chat session ID")
):
    """
    WebSocket endpoint for real-time chat with AI tutors

    Flow:
    1. Client connects with student_id
    2. Student sends messages (queries/code/questions)
    3. Server invokes Triage Agent via Dapr
    4. Triage routes to appropriate specialist agent
    5. Agent response sent back to client
    6. Messages logged to database
    7. Events published to Kafka for analytics

    Message Format (Client -> Server):
    {
        "type": "message",
        "content": "How do for loops work?",
        "metadata": {
            "topic_id": 123,
            "code": "optional code snippet"
        }
    }

    Message Format (Server -> Client):
    {
        "type": "agent_response",
        "agent": "concepts",
        "content": "Let me explain for loops...",
        "metadata": {
            "confidence": 0.95,
            "follow_up_suggestions": [...]
        },
        "timestamp": "2025-01-02T10:30:00Z"
    }
    """
    # Generate session ID if not provided
    if not session_id:
        session_id = str(uuid.uuid4())

    client_id = f"{student_id}:{session_id}"

    await manager.connect(websocket, client_id)

    # Send welcome message
    await websocket.send_json({
        "type": "system",
        "content": "Connected to LearnFlow AI Tutoring",
        "session_id": session_id,
        "timestamp": datetime.utcnow().isoformat()
    })

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()

            logger.info(
                "Received chat message",
                student_id=student_id,
                session_id=session_id,
                message_type=data.get("type")
            )

            # Process message
            if data.get("type") == "message":
                content = data.get("content", "")
                metadata = data.get("metadata", {})

                # In production: Save message to database
                # chat_message = ChatMessage(
                #     session_id=session_id,
                #     role="student",
                #     content=content,
                #     created_at=datetime.utcnow()
                # )
                # db.add(chat_message)
                # db.commit()

                # Invoke Triage Agent via Dapr service invocation
                try:
                    # In production: Use Dapr client to invoke agent
                    # from dapr.clients import DaprClient
                    # with DaprClient() as dapr:
                    #     result = dapr.invoke_method(
                    #         app_id="learnflow-agents",
                    #         method_name="triage",
                    #         data=json.dumps({
                    #             "student_id": student_id,
                    #             "message": content,
                    #             "metadata": metadata
                    #         }),
                    #         http_verb="POST"
                    #     )
                    #     agent_response = json.loads(result.data)

                    # Mock agent response for MVP
                    agent_response = await mock_agent_response(content, metadata)

                    # Send agent response to client
                    await websocket.send_json({
                        "type": "agent_response",
                        "agent": agent_response["agent"],
                        "content": agent_response["content"],
                        "metadata": agent_response.get("metadata", {}),
                        "timestamp": datetime.utcnow().isoformat()
                    })

                    # In production: Save agent response to database
                    # agent_msg = ChatMessage(
                    #     session_id=session_id,
                    #     role=agent_response["agent"],
                    #     content=agent_response["content"],
                    #     agent_metadata=agent_response.get("metadata", {}),
                    #     created_at=datetime.utcnow()
                    # )
                    # db.add(agent_msg)
                    # db.commit()

                    # Publish event to Kafka
                    # In production: Use Dapr pub/sub
                    # await publish_student_activity_event(
                    #     student_id=student_id,
                    #     event_type="chat_message",
                    #     metadata={
                    #         "session_id": session_id,
                    #         "agent": agent_response["agent"],
                    #         "message_length": len(content)
                    #     }
                    # )

                    logger.info(
                        "Agent response sent",
                        student_id=student_id,
                        agent=agent_response["agent"]
                    )

                except Exception as e:
                    logger.error("Error processing message", error=str(e), exc_info=True)
                    await websocket.send_json({
                        "type": "error",
                        "content": "Sorry, I encountered an error. Please try again.",
                        "timestamp": datetime.utcnow().isoformat()
                    })

            elif data.get("type") == "ping":
                # Heartbeat
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                })

    except WebSocketDisconnect:
        manager.disconnect(client_id)
        logger.info("Client disconnected", student_id=student_id, session_id=session_id)

    except Exception as e:
        logger.error("WebSocket error", error=str(e), exc_info=True)
        manager.disconnect(client_id)


async def mock_agent_response(message: str, metadata: dict) -> dict:
    """
    Mock agent response for MVP
    In production, this would invoke actual AI agents via Dapr
    """
    message_lower = message.lower()

    # Simple keyword-based routing (mimics Triage Agent)
    if any(keyword in message_lower for keyword in ["how", "what", "explain", "tell me"]):
        agent = "concepts"
        content = """
Let me explain that concept!

For loops in Python allow you to iterate over a sequence (like a list, tuple, or string).

Here's an example:
```python
for i in range(5):
    print(i)
# Output: 0, 1, 2, 3, 4
```

You can also loop through lists:
```python
fruits = ["apple", "banana", "cherry"]
for fruit in fruits:
    print(fruit)
```

Would you like to try writing a for loop yourself?
"""

    elif any(keyword in message_lower for keyword in ["error", "bug", "wrong", "not working"]):
        agent = "debug"
        content = """
Let me help you debug that error!

Looking at your code, I can see the issue might be related to indentation or variable scope.

Here's a hint: Check if your loop variable is defined before you try to use it.

Try fixing it yourself first, and if you're still stuck, I can provide more specific guidance!
"""

    elif any(keyword in message_lower for keyword in ["review", "check", "feedback"]):
        agent = "code-review"
        content = """
Great job on your code! Here's my review:

✅ **Correctness**: Logic looks good
⚠️ **Style**: Consider using more descriptive variable names
✅ **Efficiency**: O(n) time complexity is optimal for this problem
💡 **Readability**: Add a comment explaining the algorithm

Overall Score: 85/100

Would you like specific suggestions for improvement?
"""

    elif any(keyword in message_lower for keyword in ["practice", "exercise", "challenge"]):
        agent = "exercise"
        content = """
Here's a coding challenge for you!

**Exercise: FizzBuzz**
Write a program that prints numbers from 1 to 100.
- For multiples of 3, print "Fizz"
- For multiples of 5, print "Buzz"
- For multiples of both, print "FizzBuzz"

Try solving it, and I'll check your solution!
"""

    elif any(keyword in message_lower for keyword in ["progress", "score", "how am i"]):
        agent = "progress"
        content = """
Here's your learning progress:

**Module 2: Control Flow - 68% (Learning)**
- For Loops: 85% (Proficient) ✅
- While Loops: 60% (Learning) 📚
- Conditionals: 75% (Proficient) ✅

**Overall Mastery: 68%**
You're doing great! Keep practicing while loops to reach proficient level.

Streak: 5 days 🔥
"""

    else:
        agent = "triage"
        content = """
I'm here to help you learn Python! I can:

1. **Explain concepts** - Ask "How do loops work?"
2. **Debug errors** - Share your error message
3. **Review code** - Send me your code for feedback
4. **Generate exercises** - Request practice problems
5. **Track progress** - Check your mastery scores

What would you like to work on?
"""

    return {
        "agent": agent,
        "content": content,
        "metadata": {
            "confidence": 0.92,
            "processing_time_ms": 250
        }
    }


@router.get("/history/{session_id}")
async def get_chat_history(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    Get chat history for a session
    """
    # In production: Fetch from database
    # messages = db.query(ChatMessage).filter(
    #     ChatMessage.session_id == session_id
    # ).order_by(ChatMessage.created_at).all()

    return {
        "session_id": session_id,
        "messages": [
            # Mock data
            {
                "role": "student",
                "content": "How do for loops work?",
                "timestamp": "2025-01-02T10:30:00Z"
            },
            {
                "role": "concepts",
                "content": "For loops allow you to iterate...",
                "timestamp": "2025-01-02T10:30:05Z"
            }
        ]
    }


@router.get("/sessions/{student_id}")
async def get_chat_sessions(
    student_id: str,
    db: Session = Depends(get_db)
):
    """
    Get all chat sessions for a student
    """
    # In production: Fetch from database
    # sessions = db.query(ChatSession).filter(
    #     ChatSession.student_id == student_id
    # ).order_by(ChatSession.started_at.desc()).all()

    return {
        "student_id": student_id,
        "sessions": [
            {
                "session_id": "session-123",
                "started_at": "2025-01-02T10:00:00Z",
                "message_count": 15,
                "topic": "For Loops"
            }
        ]
    }
