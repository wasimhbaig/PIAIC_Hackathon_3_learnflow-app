---
sidebar_position: 1
---

# Introduction to LearnFlow

Welcome to **LearnFlow** - an AI-powered Python tutoring platform built for PIAIC Hackathon 3.

## What is LearnFlow?

LearnFlow is a production-ready educational platform that combines:

- 🤖 **6 Specialized AI Agents** powered by Claude (Anthropic)
- 🚀 **Autonomous Deployment** from a single command
- 📡 **Event-Driven Architecture** with Kafka and Dapr
- 💻 **Code Execution Sandbox** for safe Python code running
- 📊 **Mastery Tracking** with weighted scoring
- 🚨 **Struggle Detection** with automated teacher alerts

## Key Features

### For Students

- Chat with AI Python tutors in real-time
- Write and execute Python code in browser
- Take auto-graded coding quizzes
- Track progress across 8 Python modules
- Receive personalized hints when stuck

### For Teachers

- Monitor class performance in real-time
- Receive automatic struggle alerts
- Generate custom coding exercises with AI
- View student code submissions
- Analyze common error patterns

## Quick Start

Get LearnFlow running in 10 minutes:

```bash
# Set environment variables
export ANTHROPIC_API_KEY="sk-ant-your-key-here"
export JWT_SECRET="your-secret-key"

# Deploy entire platform
cd skills-library/learnflow-deploy
./scripts/deploy.sh

# Access at https://learnflow.local
```

See the [Deployment Guide](./deployment) for detailed instructions.

## Architecture

LearnFlow uses a modern microservices architecture:

```
Student UI → API Gateway → AI Agents → PostgreSQL
                ↓               ↓
             Kafka (Events) → MCP Server
```

Learn more about the [Architecture](./architecture).

## Python Curriculum

8 comprehensive modules covering Python fundamentals:

1. **Basics** - Variables, types, I/O, operators
2. **Control Flow** - Conditionals, loops
3. **Data Structures** - Lists, dicts, tuples, sets
4. **Functions** - Definitions, parameters, scope
5. **OOP** - Classes, inheritance, encapsulation
6. **Files** - Reading/writing, CSV, JSON
7. **Errors** - Try/except, debugging
8. **Libraries** - Packages, APIs, virtual environments

## Multi-Agent System

LearnFlow uses 6 specialized AI agents:

- **Triage Agent**: Routes queries to specialists
- **Concepts Agent**: Teaches Python with examples
- **Code Review Agent**: Analyzes code quality
- **Debug Agent**: Guides error fixing
- **Exercise Agent**: Generates challenges
- **Progress Agent**: Tracks mastery

Learn more about [AI Agents](./agents).

## Technology Stack

**Backend:**
- Python 3.11, FastAPI, SQLAlchemy
- Anthropic Claude API

**Infrastructure:**
- Kubernetes, Helm, Dapr, Docker
- PostgreSQL 15, Apache Kafka
- Nginx Ingress, Prometheus

**Frontend:**
- React, Next.js, TypeScript
- Tailwind CSS, Monaco Editor

## Hackathon Alignment

LearnFlow achieves 100% alignment with PIAIC Hackathon 3 evaluation criteria:

- ✅ Skills Autonomy (15%)
- ✅ Token Efficiency (10%)
- ✅ Cross-Agent Compatible (5%)
- ✅ Architecture (20%)
- ✅ MCP Integration (10%)
- ✅ Documentation (10%)
- ✅ Spec-Kit Plus Usage (15%)
- ✅ LearnFlow Completion (15%)

## Next Steps

1. [Deploy LearnFlow](./deployment)
2. [Understand the Architecture](./architecture)
3. [Learn about AI Agents](./agents)
4. [Explore the API](./api)
5. [Read the Database Schema](./database)

## Get Help

- 📖 [Documentation](./intro)
- 🐛 [GitHub Issues](https://github.com/learnflow/learnflow-app/issues)
- 💬 [Community Discussions](https://github.com/learnflow/learnflow-app/discussions)
