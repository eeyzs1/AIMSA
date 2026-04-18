# AI Agent 接手指南

> 你是接手这个项目的新 Agent。读这个文件就够了。

## 一句话

智能文档问答平台（RAG）：上传文档 → 提问 → 基于文档内容回答。

## 技术栈

FastAPI + Streamlit + PostgreSQL + MongoDB + Redis + Celery + ChromaDB + Qwen2.5-0.5B

## 架构

```
Streamlit → FastAPI → Celery Worker → LLM Service
               ↓            ↓              ↓
          PostgreSQL    ChromaDB      Qwen2.5-0.5B
           MongoDB(日志)  Redis(队列)
```

## 关键文件（按优先级读）

1. `PROJECT.md` — 完整项目文档（架构/技能覆盖/数据库设计/使用方式）
2. `docs/requirements.md` — 原始需求和需求演进历史
3. `evolution/log.md` — 系统演进历史（代码修复+需求变化）
4. `backend/app/main.py` — 后端入口
5. `backend/app/services/rag_service.py` — RAG核心逻辑
6. `backend/app/tasks/` — Celery异步任务
7. `llm_service/server.py` — LLM推理微服务
8. `frontend/app.py` — Streamlit前端
9. `k8s/` — Kubernetes部署清单
10. `scripts/` — 运维脚本（验证/ETL/灰度/压测）

## 约束

- 所有API端点有输入验证
- 外部服务故障不崩溃，返回503
- Celery任务用显式事件循环（不用asyncio.run）
- 文本分块必须处理无段落分隔的长文本
- 代码遵循PEP8，不写注释除非被要求

## 验证

每次改动后运行：
```bash
bash scripts/verify.sh
```
42项检查，必须全部通过。

## 数据库变更

改模型后需要：
1. 更新 `backend/app/models/document.py`
2. 确保索引定义在 `__table_args__` 中
3. 运行验证

## 需求变更

需求变更记录在 `docs/requirements.md`。如果需求变了：
1. 在 `docs/requirements.md` 添加变更记录
2. 在 `evolution/log.md` 添加演进记录
3. 评估影响范围，修改代码
4. 运行验证
