#!/usr/bin/env bash
set -uo pipefail

PASS=0
FAIL=0

check() {
    local label="$1"
    shift
    if "$@" &>/dev/null; then
        echo "  ✅ $label"
        ((PASS++)) || true
    else
        echo "  ❌ $label"
        ((FAIL++)) || true
    fi
}

echo "=== AIMSA Verification ==="

echo "[1/7] Python syntax check..."
for f in backend/app/main.py backend/app/config.py backend/app/db/postgres.py backend/app/db/mongo.py backend/app/db/vector.py backend/app/models/document.py backend/app/services/document_service.py backend/app/services/rag_service.py backend/app/tasks/celery_app.py backend/app/tasks/document_tasks.py backend/app/tasks/inference_tasks.py backend/app/api/documents.py backend/app/api/questions.py backend/app/api/monitoring.py llm_service/server.py; do
    check "$f" python -m py_compile "$f"
done

echo "[2/7] Module import check..."
check "app.config" python -c "import sys; sys.path.insert(0,'backend'); from app.config import settings"
check "app.db.postgres" python -c "import sys; sys.path.insert(0,'backend'); from app.db.postgres import Base"
check "app.db.mongo" python -c "import sys; sys.path.insert(0,'backend'); from app.db.mongo import mongo_db"
check "app.db.vector" python -c "import sys; sys.path.insert(0,'backend'); from app.db.vector import get_chroma"
check "app.models" python -c "import sys; sys.path.insert(0,'backend'); from app.models import Document, Question"
check "app.main" python -c "import sys; sys.path.insert(0,'backend'); from app.main import app"

echo "[3/7] API routing check..."
check "13 routes" python -c "import sys; sys.path.insert(0,'backend'); from app.main import app; assert len(app.routes) == 13"
check "root 200" python -c "import sys; sys.path.insert(0,'backend'); from fastapi.testclient import TestClient; from app.main import app; c=TestClient(app); assert c.get('/').status_code==200"
check "health 200" python -c "import sys; sys.path.insert(0,'backend'); from fastapi.testclient import TestClient; from app.main import app; c=TestClient(app); assert c.get('/api/v1/monitoring/health').status_code==200"
check "degraded 503" python -c "import sys; sys.path.insert(0,'backend'); from fastapi.testclient import TestClient; from app.main import app; c=TestClient(app,raise_server_exceptions=False); assert c.get('/api/v1/documents/').status_code==503"
check "validation 400" python -c "import sys; sys.path.insert(0,'backend'); from fastapi.testclient import TestClient; from app.main import app; c=TestClient(app,raise_server_exceptions=False); assert c.post('/api/v1/questions/',json={'document_id':'bad','question':'x'}).status_code==400"

echo "[4/7] Business logic check..."
check "text chunking" python -c "import sys; sys.path.insert(0,'backend'); from app.tasks.document_tasks import _chunk_text; assert len(_chunk_text('test '*200, chunk_size=200, overlap=50)) > 1"
check "empty text" python -c "import sys; sys.path.insert(0,'backend'); from app.tasks.document_tasks import _chunk_text; assert _chunk_text('') == []"

echo "[5/7] Infrastructure files check..."
for f in docker-compose.yml backend/Dockerfile llm_service/Dockerfile frontend/Dockerfile backend/requirements.txt llm_service/requirements.txt frontend/requirements.txt .env.example .github/workflows/ci.yml frontend/.streamlit/secrets.toml; do
    check "$f" test -f "$f"
done

echo "[6/7] Test files check..."
for f in backend/tests/conftest.py backend/tests/test_api/test_documents.py backend/tests/test_services/test_rag_service.py; do
    check "$f" test -f "$f"
done

echo "[7/7] OpenAPI schema check..."
check "OpenAPI valid" python -c "import sys; sys.path.insert(0,'backend'); from app.main import app; s=app.openapi(); assert s['info']['title']=='AIMSA - AI Model Service Accelerator'"

echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="
if [ $FAIL -gt 0 ]; then
    exit 1
fi
