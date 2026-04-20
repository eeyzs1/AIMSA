# AIMSA — Intelligent Document Q&A Platform (RAG)

> AI Model Service Accelerator — Turn trained models into production-grade inference services in 5 minutes

[中文版本](README.md)

## Product Positioning

A portfolio project for AI full-stack engineers. Core scenario: **Upload document → Ask question → Get answer based on document content**.

Why this product: The asynchronous nature of LLM inference naturally connects all skill points — frontend, backend, message queues, databases, AI inference, and quality assurance.

---

## System Architecture

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
│ ·Doc     │ │·Infer. │ │·Doc    │ │  1.Document processing    │
│   meta   │ │  logs  │ │  vectors│ │    (chunk + vectorize)    │
│ ·Q&A     │ │·Metrics│ │        │ │  2.Inference task         │
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

---

## Project Structure

```
AIMSA/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── main.py            # App entry, global exception handling
│   │   ├── config.py          # Config management (pydantic-settings)
│   │   ├── api/               # API route layer
│   │   │   ├── documents.py   # Document upload/list/query
│   │   │   ├── questions.py   # Question/answer/history
│   │   │   └── monitoring.py  # Health check/stats
│   │   ├── models/
│   │   │   └── document.py    # SQLAlchemy models (6 indexes)
│   │   ├── services/
│   │   │   ├── document_service.py  # Document/question CRUD
│   │   │   └── rag_service.py       # RAG core: retrieve + generate
│   │   ├── tasks/
│   │   │   ├── celery_app.py        # Celery config
│   │   │   ├── document_tasks.py    # Document chunking + vectorization
│   │   │   └── inference_tasks.py   # Async inference tasks
│   │   └── db/
│   │       ├── postgres.py    # PostgreSQL async connection
│   │       ├── mongo.py       # MongoDB log storage
│   │       └── vector.py      # ChromaDB vector storage
│   ├── tests/                 # Tests
│   ├── Dockerfile
│   └── requirements.txt
│
├── llm_service/               # LLM inference microservice (independently deployed)
│   ├── server.py              # FastAPI + Qwen2.5-0.5B
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/                  # Streamlit frontend
│   ├── app.py                 # Three-tab UI
│   ├── .streamlit/
│   │   └── secrets.toml       # Docker internal network config
│   ├── Dockerfile
│   └── requirements.txt
│
├── k8s/                       # Kubernetes deployment manifests
│   ├── 00-namespace-config.yaml  # Namespace + ConfigMap + Secret
│   ├── 01-postgres.yaml          # PG StatefulSet + PVC + Service
│   ├── 02-mongodb.yaml           # MongoDB StatefulSet + PVC + Service
│   ├── 03-redis.yaml             # Redis Deployment + Service
│   ├── 04-backend.yaml           # Backend Deployment(2 replicas) + Service
│   ├── 05-celery-worker.yaml     # Celery Worker(2 replicas)
│   ├── 06-llm-service.yaml       # LLM CPU version
│   ├── 07-llm-service-gpu.yaml   # LLM GPU version (nvidia.com/gpu)
│   ├── 08-frontend.yaml          # Frontend NodePort
│   └── 09-canary.yaml            # Canary deployment Ingress
│
├── scripts/                   # Ops scripts
│   ├── verify.sh              # 42-item automated verification
│   ├── etl_inference_logs.py  # ETL: MongoDB → PostgreSQL
│   ├── canary_deploy.py       # Canary deployment script
│   └── benchmark.py           # Performance benchmarking
│
├── .github/workflows/
│   └── ci.yml                 # CI: lint → test → build
│
├── docker-compose.yml         # One-click start 7 services
├── start.sh                   # One-click startup script
└── .env.example               # Environment variable template
```

---

## Quick Start

### Prerequisites

- Docker + Docker Compose
- Python 3.11+ (for local development)
- HuggingFace cache with `Qwen/Qwen2.5-0.5B-Instruct` model (or network access to download)

### Method 1: One-Click Script (Recommended for Local Dev)

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

### Method 2: Docker Compose (All Containers)

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

### Method 3: Manual Local Development

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
> - LLM service needs `HF_HUB_OFFLINE=1` env var if HuggingFace is unreachable
> - Frontend needs `API_BASE` env var or `.streamlit/secrets.toml` config
> - Frontend needs `--server.headless true` to skip Streamlit welcome prompt
> - All services read config from the project root `.env` file

### Method 4: Kubernetes (minikube Local Test)

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

---

## Usage Flow

### 1. Upload Document

Upload txt/md/pdf files in the "Document Management" tab. After receiving the file, the backend:
- Saves to `UPLOAD_DIR`
- Celery async task: read → chunk → vectorize → store in ChromaDB
- Document status becomes `ready`

### 2. Ask Question

Select a ready document in the "Q&A" tab and enter a question:
- Backend creates a Question record (status `pending`)
- Celery async task: vector retrieval top-k chunks → construct prompt → LLM generates answer
- Frontend polls for result and displays the answer

### 3. Monitor

View in the "Monitoring" tab:
- Total inferences / inferences in last 1 hour
- Average latency / maximum latency
- Failure count

---

## Database Design

### PostgreSQL — Structured Data

**documents table:**
| Column | Type | Index | Description |
|---|---|---|---|
| id | UUID | PK | Document ID |
| filename | VARCHAR(255) | INDEX | File name |
| content_type | VARCHAR(100) | | MIME type |
| file_path | TEXT | | Storage path |
| file_size | INTEGER | | File size |
| status | ENUM | INDEX | uploaded/processing/ready/failed |
| chunk_count | INTEGER | | Chunk count |
| processing_error | TEXT | | Processing error message |
| created_at | DATETIME | INDEX | Creation time |
| updated_at | DATETIME | | Update time |

**Composite index:** `(status, created_at)` — filter by status and sort by time

**questions table:**
| Column | Type | Index | Description |
|---|---|---|---|
| id | UUID | PK | Question ID |
| document_id | UUID | INDEX + FK(CASCADE) | Associated document |
| question | TEXT | | Question content |
| answer | TEXT | | Answer content |
| sources | JSONB | | Retrieval sources (JSON) |
| status | ENUM | INDEX | pending/processing/completed/failed |
| latency_ms | INTEGER | | Inference latency |
| token_count | INTEGER | | Generated token count |
| created_at | DATETIME | INDEX | Creation time |
| completed_at | DATETIME | | Completion time |

**Composite index:** `(document_id, status)` — query questions by document and filter by status

### MongoDB — Unstructured Logs

**inference_logs collection:**
```json
{
  "task_id": "uuid",
  "latency": 1.23,
  "status": "completed",
  "chunk_count": 5
}
```

**metrics collection:**
```json
{
  "service": "llm_inference",
  "latency": 0.8,
  "tokens": 128
}
```

### ChromaDB — Vector Storage

- Collection name: `documents`
- Distance function: cosine
- Metadata: `document_id`, `chunk_index`

---

## Ops Scripts

### Automated Verification

```bash
bash scripts/verify.sh
# 42 checks: syntax → imports → API routes → business logic → infrastructure → tests → OpenAPI
```

### ETL (MongoDB → PostgreSQL)

```bash
# Export last 24 hours of inference logs to PG analysis table
python scripts/etl_inference_logs.py --since-hours 24

# Preview mode (no write)
python scripts/etl_inference_logs.py --dry-run
```

### Canary Deployment

```bash
# Deploy new LLM version, 10% canary traffic
python scripts/canary_deploy.py --image aimsa-llm:v2 --weight 10

# Full rollout (gradual 5%→10%→25%→50%→100%)
python scripts/canary_deploy.py --image aimsa-llm:v2 --weight 100
```

### Performance Benchmarking

```bash
python scripts/benchmark.py --base-url http://localhost:8000 --requests 100
# Output: RPS / P50 / P95 / P99 / Error rate
```

---

## CI/CD

GitHub Actions pipeline (`.github/workflows/ci.yml`):

```
push/PR → lint(ruff) → test(pytest + PG + Redis) → build(Docker images)
```

---

## Tech Stack Overview

| Layer | Technology | Why |
|---|---|---|
| Frontend | Streamlit | Python full-stack, rapid prototyping |
| Backend | FastAPI | Async high performance, auto API docs |
| Task Queue | Celery + Redis | Mature async task solution |
| Relational DB | PostgreSQL | Indexes/transactions/JSONB |
| Document DB | MongoDB | Flexible schema for logs |
| Vector DB | ChromaDB | Lightweight local vector retrieval |
| LLM | Qwen2.5-0.5B-Instruct | Small model for full pipeline validation |
| Containerization | Docker Compose | Lightweight orchestration for dev |
| Orchestration | Kubernetes | Production deployment + GPU scheduling |
| CI/CD | GitHub Actions | Auto lint/test/build |

---

## Self-Evolution Record

The project underwent 4 self-healing cycles during development (recorded in `evolution/log.md`):

1. **DB crash** → Added global exception handler, 503 graceful degradation
2. **asyncio.run()** → Switched to explicit event loop management
3. **Long paragraphs not chunked** → Added forced splitting logic
4. **Streamlit config missing** → Added secrets.toml

Final verification: **42/42 automated checks passed**.
