# AIMSA — 智能文档问答平台（RAG）

> AI Model Service Accelerator — 让训练好的模型5分钟内变成生产级推理服务

[English version](README_EN.md)

## 产品定位

面向AI全栈工程师的Portfolio项目，核心场景：**上传文档 → 提问 → 基于文档内容回答**。

选择这个产品的原因：LLM推理的异步性天然串联了前端/后端/消息队列/数据库/AI推理/质量保障全部技能点。

---

## 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                           用户浏览器                             │
│                      http://localhost:8501                       │
└───────────────────────────┬─────────────────────────────────────┘
                            │ HTTP
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│               Frontend (Streamlit)  端口 8501                    │
│  作用：Web UI，提供文档上传、智能问答、监控面板三个界面              │
│  当前使用：用户交互入口，通过 HTTP 调用 Backend API               │
└───────────────────────────┬─────────────────────────────────────┘
                            │ HTTP REST API
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│              Backend API (FastAPI)  端口 8000                    │
│  作用：核心业务逻辑，REST API 网关                                │
│  当前使用：                                                       │
│    - 文档上传/列表/删除 (POST/GET/DELETE /api/v1/documents/)     │
│    - 问题提交/查询 (POST/GET /api/v1/questions/)                │
│    - 健康检查/监控 (/api/v1/monitoring/health, /stats)          │
│    - 异步任务分发（提交到 Celery）                                │
└──────┬──────────┬──────────┬──────────┬─────────────────────────┘
       │          │          │          │
       ▼          ▼          ▼          ▼
┌──────────┐ ┌────────┐ ┌────────┐ ┌──────────────────────────┐
│PostgreSQL│ │MongoDB │ │ChromaDB│ │  Celery Worker            │
│ 端口5432 │ │端口27017│ │(内存)  │ │  (异步任务执行器)          │
│          │ │        │ │        │ │                            │
│ 存储：    │ │ 存储：  │ │ 存储：  │ │  处理两类异步任务：         │
│ ·文档元数据│ │·推理日志│ │·文档向量│ │  1.文档处理(分块+向量化)   │
│ ·问题记录 │ │·性能指标│ │        │ │  2.推理任务(检索+生成)     │
│ ·用户数据 │ │        │ │        │ │                            │
└──────────┘ └────────┘ └────────┘ └──────┬──────────┬──────────┘
                                            │          │
                                            ▼          ▼
                                     ┌────────┐  ┌──────────────┐
                                     │ Redis  │  │ LLM Service  │
                                     │端口6379│  │  端口 8001    │
                                     │        │  │              │
                                     │ 存储：  │  │ 作用：大模型   │
                                     │·任务队列│  │   推理服务     │
                                     │·任务结果│  │ 当前模型：     │
                                     │·速率限制│  │  Qwen2.5-    │
                                     │        │  │  0.5B-Instruct│
                                     └────────┘  └──────────────┘
```

### 组件详解

| 组件 | 技术栈 | 作用 | 当前使用方式 |
|------|--------|------|-------------|
| **Frontend** | Streamlit + httpx | Web 用户界面 | 用户通过浏览器访问，提供文档上传、问答、监控三个标签页 |
| **Backend API** | FastAPI + SQLAlchemy + Motor | 业务逻辑核心 | 接收前端请求，同步操作返回结果，异步任务分发到 Celery |
| **PostgreSQL** | PostgreSQL 16 | 关系型主数据库 | 存储文档元数据（Document 表）和问题记录（Question 表），支持事务和复杂查询 |
| **MongoDB** | MongoDB 7 | 文档型日志数据库 | 存储推理日志（inference_logs）和性能指标（metrics），写入快、Schema 灵活 |
| **Redis** | Redis 8 | 缓存 + 消息队列 | 作为 Celery 的 broker（任务队列）和 backend（任务结果存储），也用于速率限制 |
| **ChromaDB** | ChromaDB 1.5.x | 向量数据库 | 存储文档分块的向量嵌入，支持余弦相似度检索（RAG 的"检索"部分） |
| **Celery Worker** | Celery 5.x | 异步任务执行器 | 执行两类后台任务：①文档处理（分块+向量化入库）②推理任务（向量检索→LLM 生成） |
| **LLM Service** | FastAPI + Transformers | 大模型推理服务 | 加载 Qwen2.5-0.5B-Instruct 模型，接收 prompt 返回生成文本（RAG 的"生成"部分） |

### 核心数据流

**文档上传流程：**

```
用户上传 → Backend API → 保存文件到磁盘 → 写 PostgreSQL(Document, status=uploaded) →
分发 Celery 任务 → Worker 读取文件 → 分块(500字/块, 100字重叠) → ChromaDB 存向量 →
更新 PostgreSQL(Document.status=ready, chunk_count=N)
```

**问答流程：**

```
用户提问 → Backend API → 写 PostgreSQL(Question, status=pending) →
分发 Celery 任务 → Worker 从 ChromaDB 检索 top-k 相关分块 →
构造 prompt(检索内容 + 问题) → 调用 LLM Service /generate 生成回答 →
写 MongoDB(推理日志: 延迟/状态/token数) → 更新 PostgreSQL(Question.answer, status=completed)
```

**监控数据流：**

```
前端请求 /api/v1/monitoring/stats → Backend API →
  → MongoDB 聚合查询 inference_logs:
      · total_inferences: 总推理次数
      · avg_latency: 平均延迟
      · failure_count: 失败次数
      · recent_inferences_1h: 最近1小时推理次数
      · max_latency: 最大延迟
  → 返回聚合结果给前端展示

前端请求 /api/v1/monitoring/health → Backend API →
  → 检查 PostgreSQL / MongoDB / Redis / LLM Service 连接状态
  → 返回各组件健康状态
```

---

## 项目结构

```
AIMSA/
├── backend/                    # FastAPI 后端
│   ├── app/
│   │   ├── main.py            # 应用入口，全局异常处理
│   │   ├── config.py          # 配置管理（pydantic-settings）
│   │   ├── api/               # API路由层
│   │   │   ├── documents.py   # 文档上传/列表/查询
│   │   │   ├── questions.py   # 提问/回答/历史
│   │   │   └── monitoring.py  # 健康检查/统计指标
│   │   ├── models/
│   │   │   └── document.py    # SQLAlchemy模型（6个索引）
│   │   ├── services/
│   │   │   ├── document_service.py  # 文档/问题CRUD
│   │   │   └── rag_service.py       # RAG核心：检索+生成
│   │   ├── tasks/
│   │   │   ├── celery_app.py        # Celery配置
│   │   │   ├── document_tasks.py    # 文档分块+向量化
│   │   │   └── inference_tasks.py   # 异步推理任务
│   │   └── db/
│   │       ├── postgres.py    # PostgreSQL异步连接
│   │       ├── mongo.py       # MongoDB日志存储
│   │       └── vector.py      # ChromaDB向量存储
│   ├── tests/                 # 测试
│   ├── Dockerfile
│   └── requirements.txt
│
├── llm_service/               # LLM推理微服务（独立部署）
│   ├── server.py              # FastAPI + Qwen2.5-0.5B
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/                  # Streamlit 前端
│   ├── app.py                 # 三Tab界面
│   ├── .streamlit/
│   │   └── secrets.toml       # Docker内网配置
│   ├── Dockerfile
│   └── requirements.txt
│
├── k8s/                       # Kubernetes部署清单
│   ├── 00-namespace-config.yaml  # 命名空间 + ConfigMap + Secret
│   ├── 01-postgres.yaml          # PG StatefulSet + PVC + Service
│   ├── 02-mongodb.yaml           # MongoDB StatefulSet + PVC + Service
│   ├── 03-redis.yaml             # Redis Deployment + Service
│   ├── 04-backend.yaml           # 后端 Deployment(2副本) + Service
│   ├── 05-celery-worker.yaml     # Celery Worker(2副本)
│   ├── 06-llm-service.yaml       # LLM CPU版
│   ├── 07-llm-service-gpu.yaml   # LLM GPU版(nvidia.com/gpu)
│   ├── 08-frontend.yaml          # 前端 NodePort
│   └── 09-canary.yaml            # 灰度发布 Ingress
│
├── scripts/                   # 运维脚本
│   ├── verify.sh              # 42项自动化验证
│   ├── etl_inference_logs.py  # ETL: MongoDB → PostgreSQL
│   ├── canary_deploy.py       # 灰度发布脚本
│   └── benchmark.py           # 性能压测
│
├── .github/workflows/
│   └── ci.yml                 # CI: lint → test → build
│
├── docker-compose.yml         # 一键启动7个服务
├── start.sh                   # 一键启动脚本
└── .env.example               # 环境变量模板
```

---

## 快速开始

### 前置条件

- Docker + Docker Compose
- Python 3.11+ （本地开发需要）
- （LLM 服务需要 HuggingFace 缓存或网络访问来下载模型）

### 方式一：一键启动脚本（推荐本地开发）

```bash
# 1. 复制环境变量
cp .env.example .env

# 2. 一键启动（数据库用 Docker，应用用本地进程）
./start.sh start

# 3. 访问
#    前端：    http://localhost:8501
#    后端API： http://localhost:8000/docs
#    LLM服务： http://localhost:8001/health

# 其他命令
./start.sh status   # 查看服务状态
./start.sh stop     # 停止所有服务
./start.sh logs backend  # 查看某个服务的日志
```

> **说明**：`start.sh` 用 Docker Compose 启动数据库（PostgreSQL、MongoDB、Redis），
> 用本地 Python 进程启动应用服务（Backend、LLM、Celery、Frontend）。
> 这样做的好处是：应用代码修改后无需重新构建镜像，调试更方便；
> LLM 服务设置 `HF_HUB_OFFLINE=1` 避免网络问题。

### 方式二：Docker Compose 全容器启动

```bash
# 1. 复制环境变量
cp .env.example .env

# 2. 构建并启动所有服务
docker compose up --build -d

# 3. 访问
#    前端：    http://localhost:8501
#    后端API： http://localhost:8000/docs
#    LLM服务： http://localhost:8001/health
#    健康检查： http://localhost:8000/api/v1/monitoring/health
```

> **注意**：
> - LLM 服务使用本地 HuggingFace 缓存（挂载 `~/.cache/huggingface`），
>   需要预先下载模型或确保缓存目录中有 `Qwen/Qwen2.5-0.5B-Instruct`。
> - LLM 服务设置了 `HF_HUB_OFFLINE=1` 和 `TRANSFORMERS_OFFLINE=1`，
>   模型会在第一次推理请求时懒加载（启动时加载可能失败，不影响使用）。
> - 所有配置通过环境变量注入，优先级：环境变量 > .env 文件 > 代码默认值。

### 方式三：手动本地开发

```bash
# 1. 安装依赖
pip install -r backend/requirements.txt
pip install -r llm_service/requirements.txt
pip install -r frontend/requirements.txt

# 2. 启动数据库（Docker）
docker compose up -d postgres mongodb redis

# 3. 启动 LLM 推理服务（需要 HuggingFace 缓存或网络）
cd llm_service
HF_HUB_OFFLINE=1 uvicorn server:app --host 0.0.0.0 --port 8001

# 4. 启动后端 API（另一个终端）
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 5. 启动 Celery Worker（另一个终端）
cd backend
celery -A app.tasks.celery_app:celery_app worker --loglevel=info --concurrency=2

# 6. 启动前端（另一个终端）
cd frontend
API_BASE=http://localhost:8000/api/v1 streamlit run app.py \
    --server.port 8501 --server.address 0.0.0.0 --server.headless true
```

> **注意**：
> - LLM 服务需要 `HF_HUB_OFFLINE=1` 环境变量（如果 HuggingFace 不可达）
> - 前端需要 `API_BASE` 环境变量或 `.streamlit/secrets.toml` 配置
> - 前端需要 `--server.headless true` 跳过 Streamlit 欢迎提示
> - 所有服务的配置统一从项目根目录 `.env` 文件读取

### 方式四：Kubernetes 部署（minikube 本地测试）

```bash
# 1. 启动 minikube
minikube start --cpus=2 --memory=4096

# 2. 构建镜像并加载到 minikube
docker compose build
minikube image load aimsa-backend:latest aimsa-llm-service:latest aimsa-frontend:latest \
    postgres:16-alpine mongo:7 redis:8-alpine

# 3. 部署所有资源
kubectl apply -f k8s/

# 4. 查看状态
kubectl get pods -n aimsa

# 5. 访问前端
minikube service frontend-service -n aimsa

# 6. 清理
kubectl delete namespace aimsa
minikube stop
```

> **注意**：
> - K8s 清单已设置 `imagePullPolicy: Never`，适用于 minikube 本地测试。
> - 生产环境需推送镜像到仓库，并移除 `imagePullPolicy: Never`。
> - LLM 服务需要预缓存模型或挂载 HuggingFace 缓存 PVC。
> - 镜像名已更新：`aimsa-llm` → `aimsa-llm-service`，Redis 版本 `7-alpine` → `8-alpine`。

---

## 使用流程

### 1. 上传文档

在前端"文档管理"Tab上传 txt/md/pdf 文件。后端收到文件后：
- 保存到 `UPLOAD_DIR`
- Celery异步任务：读取 → 分块 → 向量化 → 存入ChromaDB
- 文档状态变为 `ready`

### 2. 提问

在"智能问答"Tab选择已就绪的文档，输入问题：
- 后端创建Question记录（状态 `pending`）
- Celery异步任务：向量检索top-k片段 → 拼接prompt → LLM生成回答
- 前端轮询结果，展示回答

### 3. 监控

在"监控面板"Tab查看：
- 总推理次数 / 最近1小时推理次数
- 平均延迟 / 最大延迟
- 失败次数

---

## 数据库设计

### PostgreSQL — 结构化数据

**documents 表：**
| 列 | 类型 | 索引 | 说明 |
|---|---|---|---|
| id | UUID | PK | 文档ID |
| filename | VARCHAR(255) | INDEX | 文件名 |
| content_type | VARCHAR(100) | | MIME类型 |
| file_path | TEXT | | 存储路径 |
| file_size | INTEGER | | 文件大小 |
| status | ENUM | INDEX | uploaded/processing/ready/failed |
| chunk_count | INTEGER | | 分块数量 |
| processing_error | TEXT | | 处理错误信息 |
| created_at | DATETIME | INDEX | 创建时间 |
| updated_at | DATETIME | | 更新时间 |

**复合索引：** `(status, created_at)` — 按状态过滤并按时间排序

**questions 表：**
| 列 | 类型 | 索引 | 说明 |
|---|---|---|---|
| id | UUID | PK | 问题ID |
| document_id | UUID | INDEX + FK(CASCADE) | 关联文档 |
| question | TEXT | | 问题内容 |
| answer | TEXT | | 回答内容 |
| sources | JSONB | | 检索来源（JSON） |
| status | ENUM | INDEX | pending/processing/completed/failed |
| latency_ms | INTEGER | | 推理延迟 |
| token_count | INTEGER | | 生成token数 |
| created_at | DATETIME | INDEX | 创建时间 |
| completed_at | DATETIME | | 完成时间 |

**复合索引：** `(document_id, status)` — 按文档查问题并按状态过滤

### MongoDB — 非结构化日志

**inference_logs 集合：**
```json
{
  "task_id": "uuid",
  "latency": 1.23,
  "status": "completed",
  "chunk_count": 5
}
```

**metrics 集合：**
```json
{
  "service": "llm_inference",
  "latency": 0.8,
  "tokens": 128
}
```

### ChromaDB — 向量存储

- 集合名：`documents`
- 距离函数：cosine
- 元数据：`document_id`, `chunk_index`

---

## 运维脚本

### 自动化验证

```bash
bash scripts/verify.sh
# 42项检查：语法 → 导入 → API路由 → 业务逻辑 → 基础设施 → 测试 → OpenAPI
```

### ETL（MongoDB → PostgreSQL）

```bash
# 导出最近24小时的推理日志到PG分析表
python scripts/etl_inference_logs.py --since-hours 24

# 预览模式（不写入）
python scripts/etl_inference_logs.py --dry-run
```

### 灰度发布

```bash
# 部署新版本LLM，10%流量灰度
python scripts/canary_deploy.py --image aimsa-llm:v2 --weight 10

# 全量发布（逐步5%→10%→25%→50%→100%）
python scripts/canary_deploy.py --image aimsa-llm:v2 --weight 100
```

### 性能压测

```bash
python scripts/benchmark.py --base-url http://localhost:8000 --requests 100
# 输出：RPS / P50 / P95 / P99 / 错误率
```

---

## CI/CD

GitHub Actions 流水线（`.github/workflows/ci.yml`）：

```
push/PR → lint(ruff) → test(pytest + PG + Redis) → build(Docker镜像)
```

---

## 技术栈总览

| 层 | 技术 | 为什么选它 |
|---|---|---|
| 前端 | Streamlit | Python全栈，快速验证 |
| 后端 | FastAPI | 异步高性能，自动API文档 |
| 任务队列 | Celery + Redis | 成熟的异步任务方案 |
| 关系数据库 | PostgreSQL | 索引/事务/JSONB |
| 文档数据库 | MongoDB | 灵活schema存日志 |
| 向量数据库 | ChromaDB | 轻量级本地向量检索 |
| LLM | Qwen2.5-0.5B-Instruct | 小模型快速验证全链路 |
| 容器化 | Docker Compose | 开发阶段轻量编排 |
| 编排 | Kubernetes | 生产级部署+GPU调度 |
| CI/CD | GitHub Actions | 自动lint/test/build |

---

## 自我演进记录

项目在构建过程中经历了4次自我修复（记录在 `evolution/log.md`）：

1. **DB崩溃** → 添加全局异常处理器，503优雅降级
2. **asyncio.run()** → 改用显式事件循环管理
3. **长段落不分块** → 添加强制分割逻辑
4. **Streamlit配置缺失** → 添加secrets.toml

最终验证：**42/42 自动化检查全部通过**。
