# AIMSA — 智能文档问答平台（RAG）

> AI Model Service Accelerator — 让训练好的模型5分钟内变成生产级推理服务

## 产品定位

面向AI全栈工程师的Portfolio项目，核心场景：**上传文档 → 提问 → 基于文档内容回答**。

选择这个产品的原因：LLM推理的异步性天然串联了前端/后端/消息队列/数据库/AI推理/质量保障全部技能点。

---

## 架构

```
用户 → Streamlit(8501) → FastAPI(8000) → Celery Worker → LLM Service(8001)
                                ↓                ↓              ↓
                          PostgreSQL       ChromaDB        Qwen2.5-0.5B
                         (元数据/索引)    (向量检索)        (生成回答)
                                ↓
                           MongoDB
                        (推理日志/指标)
                                ↑
                           Redis (任务队列)
```

---

## 岗位技能覆盖

### 工作职责

| # | 要求 | 项目体现 | 关键文件 |
|---|------|---------|---------|
| 1 | 前端：Python Streamlit | 三Tab界面：文档管理/智能问答/监控面板 | `frontend/app.py` |
| 2 | 后端：RESTful API + 消息队列 + 任务调度 | FastAPI 13个API端点 + Celery异步任务 + Redis消息队列 | `backend/app/main.py`, `backend/app/tasks/` |
| 3 | 数据层：PG + Mongo + 表设计 + 调优 + ETL | PostgreSQL 6个索引 + JSONB + 外键CASCADE + MongoDB日志 + ETL脚本 | `backend/app/models/document.py`, `scripts/etl_inference_logs.py` |
| 4 | AI协同：模型封装 + Docker + K8s + GPU | 独立LLM推理微服务 + 9个K8s清单 + GPU部署清单 + 灰度发布 | `llm_service/server.py`, `k8s/` |
| 5 | 质量保障：测试 + CI/CD + 灰度发布 + 压测 | pytest + GitHub Actions CI + 灰度发布脚本 + 压测脚本 | `backend/tests/`, `.github/workflows/ci.yml`, `scripts/` |

### 任职资格

| # | 要求 | 体现 |
|---|------|------|
| 1 | 3年+ 全栈经验，独立交付 | 单人完成前端+后端+数据层+AI推理+部署全链路 |
| 2 | 熟练 Python + Web框架 | FastAPI + Streamlit + Celery |
| 3 | 精通 PG 设计优化，索引/事务 | 6个索引 + JSONB + CASCADE + 复合索引 + ETL |
| 4 | 熟悉 Linux/Git/Docker/DevOps | Docker Compose + K8s + CI/CD + Shell脚本 |
| 5 | 编码规范 + 单元测试 | PEP8 + pytest + 42项自动化验证 |

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
└── .env.example               # 环境变量模板
```

---

## 快速开始

### 前置条件

- Docker + Docker Compose
- （可选）Python 3.11+ 用于本地开发

### 方式一：Docker Compose 一键启动

```bash
# 1. 复制环境变量
cp .env.example .env

# 2. 构建并启动所有服务
docker compose up --build

# 3. 访问
#    前端：    http://localhost:8501
#    后端API： http://localhost:8000/docs
#    LLM服务： http://localhost:8001/health
```

### 方式二：本地开发（需要本地 PostgreSQL/MongoDB/Redis）

```bash
# 1. 安装依赖
pip install -r backend/requirements.txt
pip install -r llm_service/requirements.txt
pip install -r frontend/requirements.txt

# 2. 启动基础设施（只需Redis即可验证核心链路）
docker compose up -d redis

# 3. 启动后端
cd backend
REDIS_HOST=localhost uvicorn app.main:app --port 8000

# 4. 启动LLM推理服务（另一个终端）
cd llm_service
uvicorn server:app --port 8001

# 5. 启动前端（另一个终端）
cd frontend
streamlit run app.py --server.port 8501
```

### 方式三：Kubernetes 部署

```bash
# 1. 构建并推送镜像
docker compose build
docker tag aimsa-backend your-registry/aimsa-backend:latest
docker tag aimsa-llm your-registry/aimsa-llm:latest
docker tag aimsa-frontend your-registry/aimsa-frontend:latest
docker push your-registry/aimsa-backend:latest
docker push your-registry/aimsa-llm:latest
docker push your-registry/aimsa-frontend:latest

# 2. 更新 k8s 清单中的镜像名
# 编辑 k8s/04-backend.yaml, k8s/06-llm-service.yaml, k8s/08-frontend.yaml

# 3. 部署
kubectl apply -f k8s/

# 4. 查看状态
kubectl get pods -n aimsa
```

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

## 核心数据流

```
上传文档:
  POST /api/v1/documents/ → 保存文件 → Celery: 分块+向量化 → ChromaDB
                                                         → PG: status=ready

提问:
  POST /api/v1/questions/ → PG: status=pending → Celery: RAG pipeline
    → ChromaDB: 向量检索top-k
    → LLM Service: /generate → 生成回答
    → MongoDB: 记录推理日志(延迟/状态)
    → PG: status=completed, answer=...
```

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
