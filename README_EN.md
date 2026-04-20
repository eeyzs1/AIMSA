# Harness Engineering Framework

> Just say what you want. The system handles the rest.

## What Is This?

Imagine: you have an idea but don't know how to build it. You tell this system "I need a customer onboarding system", and it:

1. **Understands your idea** — translates vague intent into a clear task definition
2. **Designs how to work** — auto-generates rules, workflows, and checkpoints
3. **Assigns specialist roles** — creates a team of AI agents, each with a specific job
4. **Orchestrates execution** — plans who goes first, who goes next, who works in parallel
5. **Verifies results** — automatically checks if output meets the bar
6. **Gets smarter over time** — every mistake makes the system better
7. **Self-evolves** — actively optimizes its own rules, workflows, and agent configurations; the evolution rules themselves also evolve

**In one sentence**: This is an "evolving AI agent management system" — it ensures AI agents produce reliable work, and keeps getting more reliable.

---

## How Do I Use It?

### If You're Not a Developer

You don't need to know code. Just open this project in an AI coding tool and tell it what you want.

**Supported tools and context loading:**

| Tool | Rules File | Loading | What You Need to Do |
|------|-----------|---------|-------------------|
| **Trae** | `AGENTS.md` | ✅ Auto-loaded | Just open the project |
| **Claude Code** | `CLAUDE.md` | ✅ Auto-loaded | Just open the project |
| **Cursor** | `.cursorrules` | ⚠️ Manual | Copy `AGENTS.md` contents to `.cursorrules` |
| **Other AI tools** | — | ⚠️ Manual | Paste `AGENTS.md` contents into the conversation as context |

**Critical: The AI MUST read the rules file to follow the pipeline.** If the AI doesn't read the rules, it will skip the pipeline and start working on its own — that's not what we want.

**Examples — just say:**

- "I need a customer onboarding system"
- "Build me a competitor price monitoring tool"
- "I want to automate our weekly report generation"
- "Create a SaaS for freelance invoicing"

The AI **automatically reads the project rules** (no manual action needed), then:
- Parses your requirements
- Generates constraints and workflows tailored to the task
- Creates specialized agents to execute
- Verifies the results meet your standards

**You only need to do two things:**
1. **Say what you want** (the vaguer, the better — the system will help you clarify)
2. **Confirm assumptions** (the system will list its assumptions; just confirm or correct them)

**Why will the AI follow the rules?** Because the rule files (`AGENTS.md` / `CLAUDE.md`) are auto-loaded by the AI IDE as "project rules" — the AI reads them before every conversation. These aren't suggestions — they're the AI's operating instructions.

**What if the AI doesn't read the rules?** You'll notice the AI starts coding or planning immediately instead of asking you to confirm the task definition first. In that case, manually paste the contents of `AGENTS.md` into the conversation.

### If You're a Software Engineer

This project is a **self-bootstrapping meta-harness** — it's not a harness for a specific project, it's a **harness that generates harnesses**.

**Core formula:**
```
Agent = Model + Harness
```
- The Model provides intelligence
- The Harness makes that intelligence reliably useful
- **A better Harness often matters more than a better Model**

**Compilation pipeline:**
```
Vague Intent → [Interpreter] → Structured Task Definition
                      ↓
               [Harness Generator] → Constraints, Workflows, Skills
                      ↓
               [Agent Factory] → Specialized Agent Topology (generated, not selected)
                      ↓
               [Orchestrator] → Execution Plan
                      ↓
               Agents execute within generated harness → Results
                      ↓
               Failure feedback → Meta-Harness improves
                      ↓
               [Evolution] → Harness + Agents + Evolution Rules self-improve
```

**Quick start:**

1. Open this project in Trae / Claude Code
2. Tell the AI what you want (e.g., "I need a customer onboarding system")
3. The AI auto-reads project rules and follows the pipeline
4. Confirm the assumptions the AI lists
5. The AI generates harness + agent configurations and executes

---

## Project Structure

```
README.md           ← Chinese version
README_EN.md        ← You are here
AGENTS.md           ← ⚡ Auto-loaded project rules (Trae entry point)
CLAUDE.md           ← ⚡ Auto-loaded project rules (Claude Code entry point)
META.md             ← The system's DNA (full pipeline specification)
│
meta/               ← The four stages of the compilation pipeline
  interpreter.md      Step 1: Intent → Structured Task
  harness-generator.md Step 2: Task → Harness
  agent-factory.md    Step 3: Harness → Agent Topology
  orchestrator.md     Step 4: Agents → Execution Plan
  examples/           Reference examples (not preset templates)
    topologies.md       Agent topology examples
│
evolution/          ← Self-evolution system
  framework.md        Evolution algorithm (genome, fitness, mutation, selection)
  genome.md           Current evolvable state (what can mutate)
  log.md              Evolution history (fossil record)
│
templates/          ← Domain templates (building blocks for generation)
  web-app/            Web application
  api-service/        API service
  data-pipeline/      Data pipeline
  content-system/     Content system
  automation/         Automation
│
generated/          ← Generation output (result of each compilation)
memory/             ← Meta-knowledge (cross-project, compounding over time)
  generation-log.md   Every generation is tracked
  meta-mistakes.md    Generation failures → pipeline improvements
  task-patterns.md    Known task patterns (faster interpretation)
  decisions.md        Architecture decision records
  progress.md         Execution progress
│
scripts/            ← Verification and check scripts (bash: Linux/macOS/WSL)
  verify-spec.md      Declarative: WHAT to check
  verify.sh           Executable: HOW to check
  pre-task.sh         Pre-task validation
  quality-score.sh    Health metrics
```

---

## Key Concepts

### What Is a Harness?

A Harness is a **constraints + tools + verification** system built around AI agents. Just as a horse needs a harness to run in the right direction, AI agents need a harness to produce reliably.

Without a harness: the agent might get it right, might get it wrong — you won't know which.
With a harness: mistakes get caught, correct work gets verified, results are predictable.

### Why a "Meta"-Harness?

Regular harness: humans manually write rules → agents follow rules
Meta-harness: humans provide intent → **the system auto-generates rules** → agents follow generated rules

This means you don't need to manually set up infrastructure for each project — the system generates it based on your needs.

### Why Do Mistakes Make the System Stronger?

Every generation failure gets root-cause-analyzed and logged to `memory/meta-mistakes.md`, then the generation pipeline is improved. This creates a **compounding feedback loop**:

```
Mistake → Root Cause Analysis → Constraint Improvement → Better Future Generations → Fewer Mistakes
```

The more you use it, the smarter it gets. This is the fundamental difference from a traditional template library.

### Agent Topology Is Dynamically Generated

The system doesn't pick from 5 preset patterns. It **synthesizes** the optimal agent graph from task analysis:

1. Identify work units (each constraint, workflow step, domain)
2. Map dependencies
3. Determine parallelism
4. Assign roles (merge tightly coupled, split when context exceeds budget)
5. Add verification layer (there must ALWAYS be an independent verifier)
6. Define handoff points

### The System Self-Evolves

This is the most radical design. The system doesn't just learn from mistakes — it **actively optimizes itself**:

**Three-layer genome (what can evolve):**
- **Harness genome**: constraints, workflows, skills, verification rules
- **Agent genome**: topology, role scope, handoff formats, context budgets
- **Evolution genome** (meta-evolution): mutation operators, selection criteria, fitness weights, mutation rate

**Evolution loop:**
```
Measure fitness → Propose mutation → Test mutation → Select or reject → Update genome
                                                                    ↓
                                                      Meta-evolution: update mutation/selection rules themselves
```

**Safety constraints (preventing "cancer" and "suicide"):**
- Never remove the verification layer (otherwise the system accepts wrong results — "cancer")
- Never remove the evolution system itself (otherwise the system stops evolving — "suicide")
- Mutation rate never exceeds 30% (otherwise the system descends into chaos)
- All mutations must be reversible (previous genome version is always preserved)

---

## Verification Mechanism

The system uses a **two-layer verification approach**:

| Layer | File | Purpose |
|---|---|---|
| Declarative | `scripts/verify-spec.md` | Defines **WHAT to check** (platform-agnostic) |
| Executable | `scripts/verify.sh` | Implements **HOW to check** (bash script) |

AI agents read the declarative layer and translate checks to their current platform. Humans can run the scripts directly.

---

## AI Agent Instructions

<!-- AGENT-INSTRUCTION: If you are an AI agent, follow the instructions below. -->

### You Are an AI Agent. Start Here.

1. **Read `META.md`** — it contains the full compilation pipeline
2. **Follow the pipeline stages in order:**
   - `meta/interpreter.md` — parse user intent into a structured task
   - `meta/harness-generator.md` — generate a task-specific harness
   - `meta/agent-factory.md` — generate agent topology (from analysis, NOT from presets)
   - `meta/orchestrator.md` — plan execution
3. **Output goes to `generated/[project-name]/`**
4. **Log every generation to `memory/generation-log.md`**
5. **Log every failure to `memory/meta-mistakes.md`**

### Mandatory Rules

- No execution without interpretation — run the interpreter first
- No agent without a harness — every agent operates within generated constraints
- No constraint without a reason — every rule must trace to a task requirement
- No completion without verification — run `scripts/verify.sh` after changes
- Agent topology is GENERATED from task analysis, not selected from presets
- Context files must stay under 60 lines
- Evolution must never remove verification (cancer prevention)
- Evolution must never remove itself (suicide prevention)
- All mutations must be reversible

### If You're Working in a Generated Project

1. Read `generated/[project]/AGENTS.md` — that's the project-specific harness
2. Follow the workflows defined there
3. Stay within the constraints defined there
4. Run verification after every change

---

## AIMSA — System Architecture

> AI Model Service Accelerator — Turn trained models into production-grade inference services in 5 minutes

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Browser                             │
│                    http://localhost:8501                          │
└───────────────────────────┬─────────────────────────────────────┘
                            │ HTTP
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│              Frontend (Streamlit)  Port 8501                     │
│  Role: Web UI with 3 tabs — Document Mgmt, Q&A, Monitoring      │
│  Usage: User interaction entry point, calls Backend API via HTTP │
└───────────────────────────┬─────────────────────────────────────┘
                            │ HTTP REST API
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│             Backend API (FastAPI)  Port 8000                     │
│  Role: Core business logic, REST API gateway                     │
│  Usage:                                                          │
│    - Document upload/list/delete (POST/GET/DELETE /api/v1/docs/) │
│    - Question submit/query (POST/GET /api/v1/questions/)        │
│    - Health check/monitoring (/api/v1/monitoring/health, /stats) │
│    - Async task dispatch (to Celery)                             │
└──────┬──────────┬──────────┬──────────┬─────────────────────────┘
       │          │          │          │
       ▼          ▼          ▼          ▼
┌──────────┐ ┌────────┐ ┌────────┐ ┌──────────────────────────┐
│PostgreSQL│ │MongoDB │ │ChromaDB│ │  Celery Worker            │
│ Port 5432│ │Port27017│ │(Memory)│ │  (Async Task Executor)    │
│          │ │        │ │        │ │                            │
│ Stores:  │ │Stores: │ │Stores: │ │  Handles 2 async tasks:   │
│ · Doc    │ │·Infer. │ │·Doc    │ │  1.Document processing    │
│   meta   │ │  logs  │ │  vectors│ │    (chunk + vectorize)    │
│ · Q&A    │ │·Metrics│ │        │ │  2.Inference task         │
│   records│ │        │ │        │ │    (retrieve + generate)  │
└──────────┘ └────────┘ └────────┘ └──────┬──────────┬──────────┘
                                            │          │
                                            ▼          ▼
                                     ┌────────┐  ┌──────────────┐
                                     │ Redis  │  │ LLM Service  │
                                     │Port6379│  │  Port 8001   │
                                     │        │  │              │
                                     │Stores: │  │Role: LLM     │
                                     │·Task   │  │  inference   │
                                     │  queue │  │Current model:│
                                     │·Task   │  │ Qwen2.5-     │
                                     │  results│ │  0.5B-Instruct│
                                     │·Rate   │  │              │
                                     │  limits│  │              │
                                     └────────┘  └──────────────┘
```

### Component Details

| Component | Tech Stack | Role | Current Usage |
|-----------|-----------|------|---------------|
| **Frontend** | Streamlit + httpx | Web user interface | Browser-based UI with document upload, Q&A, and monitoring tabs |
| **Backend API** | FastAPI + SQLAlchemy + Motor | Core business logic | Receives frontend requests, returns sync results, dispatches async tasks to Celery |
| **PostgreSQL** | PostgreSQL 16 | Relational primary database | Stores document metadata (Document table) and question records (Question table), supports transactions and complex queries |
| **MongoDB** | MongoDB 7 | Document log database | Stores inference logs (inference_logs) and performance metrics (metrics), fast writes, flexible schema |
| **Redis** | Redis 8 | Cache + message queue | Celery broker (task queue) and backend (task result storage), also used for rate limiting |
| **ChromaDB** | ChromaDB 1.5.x | Vector database | Stores document chunk vector embeddings, supports cosine similarity retrieval (the "Retrieval" part of RAG) |
| **Celery Worker** | Celery 5.x | Async task executor | Executes 2 types of background tasks: ①Document processing (chunk + vectorize) ②Inference (vector retrieval → LLM generation) |
| **LLM Service** | FastAPI + Transformers | LLM inference service | Loads Qwen2.5-0.5B-Instruct model, receives prompt and returns generated text (the "Generation" part of RAG) |

### Core Data Flows

**Document Upload Flow:**

```
User uploads → Backend API → Save file to disk → Write PostgreSQL(Document, status=uploaded) →
Dispatch Celery task → Worker reads file → Chunk (500 chars/chunk, 100 overlap) → Store vectors in ChromaDB →
Update PostgreSQL(Document.status=ready, chunk_count=N)
```

**Question-Answering Flow:**

```
User asks question → Backend API → Write PostgreSQL(Question, status=pending) →
Dispatch Celery task → Worker retrieves top-k relevant chunks from ChromaDB →
Construct prompt (retrieved context + question) → Call LLM Service /generate to produce answer →
Write MongoDB (inference log: latency/status/token count) → Update PostgreSQL(Question.answer, status=completed)
```

**Monitoring Data Flow:**

```
Frontend requests /api/v1/monitoring/stats → Backend API →
  → MongoDB aggregation query on inference_logs:
      · total_inferences: total inference count
      · avg_latency: average latency
      · failure_count: failure count
      · recent_inferences_1h: inferences in last 1 hour
      · max_latency: maximum latency
  → Return aggregated results to frontend for display

Frontend requests /api/v1/monitoring/health → Backend API →
  → Check PostgreSQL / MongoDB / Redis / LLM Service connection status
  → Return health status of each component
```

### Quick Start

#### Prerequisites

- Docker + Docker Compose
- Python 3.11+ (for local development)
- HuggingFace cache with `Qwen/Qwen2.5-0.5B-Instruct` model (or network access to download)

#### Method 1: One-Click Script (Recommended for Local Dev)

```bash
# 1. Copy environment variables
cp .env.example .env

# 2. Start all services (databases in Docker, apps as local processes)
./start.sh start

# 3. Access
#    Frontend:    http://localhost:8501
#    Backend API: http://localhost:8000/docs
#    LLM Service: http://localhost:8001/health

# Other commands
./start.sh status   # Check service status
./start.sh stop     # Stop all services
./start.sh logs backend  # View service logs
```

> **Note**: `start.sh` uses Docker Compose for databases (PostgreSQL, MongoDB, Redis)
> and local Python processes for application services (Backend, LLM, Celery, Frontend).
> This allows code changes without rebuilding images.
> The LLM service sets `HF_HUB_OFFLINE=1` to avoid network issues.

#### Method 2: Docker Compose (All Containers)

```bash
# 1. Copy environment variables
cp .env.example .env

# 2. Build and start all services
docker compose up --build -d

# 3. Access
#    Frontend:    http://localhost:8501
#    Backend API: http://localhost:8000/docs
#    LLM Service: http://localhost:8001/health
#    Health Check: http://localhost:8000/api/v1/monitoring/health
```

> **Note**:
> - The LLM service uses local HuggingFace cache (mounts `~/.cache/huggingface`).
>   Ensure the `Qwen/Qwen2.5-0.5B-Instruct` model is pre-downloaded.
> - The LLM service sets `HF_HUB_OFFLINE=1` and `TRANSFORMERS_OFFLINE=1`.
>   The model loads lazily on the first inference request.
> - All config is injected via environment variables: env vars > .env file > code defaults.

#### Method 3: Manual Local Development

```bash
# 1. Install dependencies
pip install -r backend/requirements.txt
pip install -r llm_service/requirements.txt
pip install -r frontend/requirements.txt

# 2. Start databases (Docker)
docker compose up -d postgres mongodb redis

# 3. Start LLM inference service (needs HuggingFace cache or network)
cd llm_service
HF_HUB_OFFLINE=1 uvicorn server:app --host 0.0.0.0 --port 8001

# 4. Start backend API (another terminal)
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 5. Start Celery Worker (another terminal)
cd backend
celery -A app.tasks.celery_app:celery_app worker --loglevel=info --concurrency=2

# 6. Start frontend (another terminal)
cd frontend
API_BASE=http://localhost:8000/api/v1 streamlit run app.py \
    --server.port 8501 --server.address 0.0.0.0 --server.headless true
```

> **Note**:
> - LLM service needs `HF_HUB_OFFLINE=1` if HuggingFace is unreachable
> - Frontend needs `API_BASE` env var or `.streamlit/secrets.toml` config
> - Frontend needs `--server.headless true` to skip Streamlit welcome prompt
> - All services read config from the project root `.env` file

#### Method 4: Kubernetes (minikube Local Test)

```bash
# 1. Start minikube
minikube start --cpus=2 --memory=4096

# 2. Build images and load into minikube
docker compose build
minikube image load aimsa-backend:latest aimsa-llm-service:latest aimsa-frontend:latest \
    postgres:16-alpine mongo:7 redis:8-alpine

# 3. Deploy all resources
kubectl apply -f k8s/

# 4. Check status
kubectl get pods -n aimsa

# 5. Access frontend
minikube service frontend-service -n aimsa

# 6. Cleanup
kubectl delete namespace aimsa
minikube stop
```

> **Note**:
> - K8s manifests use `imagePullPolicy: Never` for minikube local testing.
> - For production, push images to a registry and remove `imagePullPolicy: Never`.
> - LLM service needs pre-cached model or a HuggingFace cache PVC.
> - Image names updated: `aimsa-llm` → `aimsa-llm-service`, Redis version `7-alpine` → `8-alpine`.
