#!/usr/bin/env bash
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info()  { echo -e "${GREEN}[INFO]${NC} $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }

check_port() {
    ss -tlnp 2>/dev/null | grep -q ":$1 " && echo "1" || true
}

wait_for_http() {
    local url="$1" name="$2" max="$3" n=0
    while [ $n -lt $max ]; do
        if curl -sf "$url" >/dev/null 2>&1; then
            log_info "$name is ready"
            return 0
        fi
        n=$((n + 1))
        sleep 2
    done
    log_error "$name did not become ready in $((max * 2))s"
    return 1
}

if [ ! -f .env ]; then
    log_warn ".env not found, copying from .env.example"
    cp .env.example .env
fi

set -a; source .env; set +a

mkdir -p "${UPLOAD_DIR:-/tmp/aimsa_uploads}" "${CHROMA_PERSIST_DIR:-/tmp/aimsa_chroma}"

ACTION="${1:-start}"

case "$ACTION" in
    start)
        echo ""
        echo "========================================="
        echo "  AIMSA - Starting All Services"
        echo "========================================="
        echo ""

        log_info "Starting database services (PostgreSQL, MongoDB, Redis)..."
        docker compose up -d postgres mongodb redis
        sleep 5

        log_info "Waiting for databases to be healthy..."
        n=0; while [ $n -lt 30 ]; do
            healthy=$(docker inspect --format='{{.State.Health.Status}}' aimsa-postgres-1 2>/dev/null || echo "missing")
            if [ "$healthy" = "healthy" ]; then break; fi
            n=$((n + 1)); sleep 2
        done
        log_info "PostgreSQL is $healthy"

        n=0; while [ $n -lt 30 ]; do
            healthy=$(docker inspect --format='{{.State.Health.Status}}' aimsa-mongodb-1 2>/dev/null || echo "missing")
            if [ "$healthy" = "healthy" ]; then break; fi
            n=$((n + 1)); sleep 2
        done
        log_info "MongoDB is $healthy"

        n=0; while [ $n -lt 30 ]; do
            healthy=$(docker inspect --format='{{.State.Health.Status}}' aimsa-redis-1 2>/dev/null || echo "missing")
            if [ "$healthy" = "healthy" ]; then break; fi
            n=$((n + 1)); sleep 2
        done
        log_info "Redis is $healthy"

        if [ "$(check_port 8001)" ]; then
            log_warn "LLM service already running on port 8001"
        else
            log_info "Starting LLM service..."
            cd llm_service
            HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
                setsid python -m uvicorn server:app --host 0.0.0.0 --port 8001 \
                > /tmp/aimsa_llm.log 2>&1 &
            echo $! > /tmp/aimsa_llm.pid
            cd "$SCRIPT_DIR"
            sleep 5
        fi

        if [ "$(check_port 8000)" ]; then
            log_warn "Backend API already running on port 8000"
        else
            log_info "Starting backend API..."
            cd backend
            setsid python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 \
                > /tmp/aimsa_backend.log 2>&1 &
            echo $! > /tmp/aimsa_backend.pid
            cd "$SCRIPT_DIR"
            sleep 5
        fi

        log_info "Waiting for backend API..."
        wait_for_http "http://localhost:8000/" "Backend API" 20 || true

        if pgrep -f "celery.*celery_app" >/dev/null 2>&1; then
            log_warn "Celery worker already running"
        else
            log_info "Starting Celery worker..."
            cd backend
            setsid python -m celery -A app.tasks.celery_app:celery_app worker \
                --loglevel=info --concurrency=2 \
                > /tmp/aimsa_celery.log 2>&1 &
            echo $! > /tmp/aimsa_celery.pid
            cd "$SCRIPT_DIR"
            sleep 3
        fi

        if [ "$(check_port 8501)" ]; then
            log_warn "Frontend already running on port 8501"
        else
            log_info "Starting frontend..."
            cd frontend
            API_BASE="${API_BASE:-http://localhost:8000/api/v1}" \
                STREAMLIT_SERVER_HEADLESS=true \
                STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
                setsid streamlit run app.py \
                --server.port 8501 --server.address 0.0.0.0 \
                > /tmp/aimsa_frontend.log 2>&1 &
            echo $! > /tmp/aimsa_frontend.pid
            cd "$SCRIPT_DIR"
            sleep 5
        fi

        echo ""
        echo "========================================="
        echo "  AIMSA Services Started!"
        echo "========================================="
        echo ""
        echo "  Frontend:    http://localhost:8501"
        echo "  Backend API: http://localhost:8000"
        echo "  LLM Service: http://localhost:8001"
        echo "  API Docs:    http://localhost:8000/docs"
        echo ""
        echo "  Logs: /tmp/aimsa_*.log"
        echo "  PIDs: /tmp/aimsa_*.pid"
        echo ""
        ;;

    stop)
        echo ""
        log_info "Stopping AIMSA services..."

        for pid_file in /tmp/aimsa_frontend.pid /tmp/aimsa_celery.pid /tmp/aimsa_backend.pid /tmp/aimsa_llm.pid; do
            if [ -f "$pid_file" ]; then
                pid=$(cat "$pid_file")
                if kill -0 "$pid" 2>/dev/null; then
                    kill "$pid" 2>/dev/null
                    log_info "Stopped PID $pid"
                fi
                rm -f "$pid_file"
            fi
        done

        pkill -f "celery.*celery_app" 2>/dev/null || true
        fuser -k 8000/tcp 2>/dev/null || true
        fuser -k 8001/tcp 2>/dev/null || true
        fuser -k 8501/tcp 2>/dev/null || true

        sleep 2

        log_info "Stopping database containers..."
        docker compose stop postgres mongodb redis 2>/dev/null

        log_info "All services stopped"
        ;;

    status)
        echo ""
        echo "=== AIMSA Service Status ==="
        echo ""

        for port_name in "8000:Backend API" "8001:LLM Service" "8501:Frontend"; do
            port="${port_name%%:*}"
            name="${port_name##*:}"
            if [ "$(check_port "$port")" ]; then
                echo -e "  ${GREEN}✅${NC} $name (port $port) - running"
            else
                echo -e "  ${RED}❌${NC} $name (port $port) - stopped"
            fi
        done

        if pgrep -f "celery.*celery_app" >/dev/null 2>&1; then
            echo -e "  ${GREEN}✅${NC} Celery Worker - running"
        else
            echo -e "  ${RED}❌${NC} Celery Worker - stopped"
        fi

        echo ""
        docker compose ps postgres mongodb redis 2>/dev/null | tail -n +2 | while read -r line; do
            if echo "$line" | grep -q "Up\|healthy"; then
                echo -e "  ${GREEN}✅${NC} $line"
            else
                echo -e "  ${RED}❌${NC} $line"
            fi
        done
        echo ""
        ;;

    logs)
        svc="${2:-backend}"
        tail -f "/tmp/aimsa_${svc}.log" 2>/dev/null || log_error "No log for $svc"
        ;;

    *)
        echo "Usage: $0 {start|stop|status|logs [service]}"
        echo ""
        echo "  start  - Start all services"
        echo "  stop   - Stop all services"
        echo "  status - Check service status"
        echo "  logs   - Tail logs (backend|llm|celery|frontend)"
        exit 1
        ;;
esac
