# 需求文档

## 原始需求（2026-04-16）

### 来源

用户提供的AI全栈工程师岗位描述，目标是构建一个Portfolio项目覆盖所有技能点。

### 原始岗位要求

**工作职责：**
1. 前端：用 Python（Django/FastAPI/Streamlit）或 Java（Spring Boot + Thymeleaf/前后端分离）快速开发可交付的Web应用
2. 后端：负责RESTful API、微服务、消息队列、任务调度，保障高并发、高可用
3. 数据层：MySQL/PostgreSQL/MongoDB 表设计、调优、备份、迁移，必要时编写ETL脚本
4. AI 协同：与算法团队对接，把模型（PyTorch/TensorFlow）封装成在线推理服务（Docker + K8s + GPU），持续监控效果
5. 质量保障：单元/集成测试、CI/CD、灰度发布、性能压测、故障复盘

**任职资格：**
1. 3 年及以上 Web 全栈开发经验，可独立交付完整项目
2. 熟练使用 Python 或 Java 之一，熟悉常用Web框架
3. 精通关系型数据库（MySQL/PostgreSQL）设计与优化，熟悉索引、事务、分库分表
4. 熟悉 Linux、Git、Docker，了解 DevOps 流程
5. 良好的编码规范（PEP8/Google Java Style）和单元测试习惯

### 需求推导过程

1. **动机确认**：用户确认目标是"展示技能的Portfolio项目"，产品是手段
2. **产品选型**：选择"智能文档问答（RAG）"而非"模型服务平台"，因为：
   - 一看就懂，不需要解释"为什么需要"
   - LLM推理的异步性天然串联全部技能点
   - 前端和数据层都能自然覆盖
3. **技术选型**：FastAPI + Streamlit + PostgreSQL + MongoDB + Redis + Celery + ChromaDB + Qwen2.5-0.5B
4. **验证模型**：0.5B小模型做快速验证，验证目标是"管道通，不是答案好"

---

## 需求演进历史

### Rev 0 → Rev 1（2026-04-16）

**触发**：用户指出"你做的东西怎么体现了这些？我连你打包的容器都没看到"

**变化**：
- 新增：数据库索引设计（6个索引 + 复合索引 + JSONB）
- 新增：ETL脚本（MongoDB → PostgreSQL）
- 新增：K8s部署清单（9个YAML，含GPU版）
- 新增：灰度发布机制（K8s Ingress canary + 脚本）
- 新增：性能压测脚本
- 新增：Docker容器实际运行验证

**原因**：原始实现只覆盖了"能跑"的层面，缺少岗位要求中明确提到的索引调优、ETL、K8s、GPU、灰度、压测等深度技能展示。

### Rev 1 → Rev 2（2026-04-16）

**触发**：用户指出"如果让一个ai agent接手这个项目，我该给他看哪个文件？另外你在哪里记录的原始需求？"

**变化**：
- 新增：`docs/onboarding.md` 作为AI Agent接手入口文件
- 新增：`docs/requirements.md` 记录原始需求和演进历史
- 升级：`evolution/log.md` 同时记录需求演进和系统演进

**原因**：项目缺少"接手入口"和"需求溯源"，AI Agent无法独立理解项目全貌和决策背景。

### Rev 2 → Rev 3（2026-04-18）

**触发**：CI流水线首次运行失败（ruff check 7个错误）

**变化**：
- 修复：监控API补全 metrics 集合查询（原只查 inference_logs，metrics 数据被忽略）
- 修复：文档分块参数 CHUNK_SIZE/CHUNK_OVERLAP 从硬编码改为 settings 配置项
- 修复：删除 rag_service.py 中复制残留的 select 和 Question 导入
- 修复：删除 test_documents.py 中复制残留的 _chunk_text 导入
- 修复：删除 conftest.py 中多余的 pytest 导入
- 新增：ruff.toml 配置文件（target-version py314, line-length 120）
- 更新：CI Python 版本从 3.11 改为 3.14

**原因**：CI lint 失败的根因不是"代码有多余行"，而是两个功能缺失——监控面板没用到 metrics 数据，分块参数不可配置。其余是复制残留。从根因修复而非打补丁。

### Rev 3 → Rev 4（2026-04-18）

**触发**：AI Agent自我进化（proactive），识别出安全/可靠性/运维层面的改进空间

**变化**：
- 新增：深化健康检查 — /monitoring/health 探测 PG/Mongo/Redis/ChromaDB/LLM 连通性
- 新增：LLM调用指数退避重试 — 3次重试，1s/2s/4s延迟
- 新增：CORS可配置 + 速率限制中间件（默认60 req/min）
- 新增：文档删除API — DELETE /api/v1/documents/{doc_id}，级联清理文件/向量/记录
- 新增：MongoDB连接池显式配置（maxPoolSize=20, minPoolSize=5, timeout等）
- 新增：K8s HPA自动扩缩容清单（10-hpa.yaml）
- 新增：数据库备份脚本（scripts/backup.sh）

**原因**：项目功能完整但缺少生产化安全/可靠性/运维能力。健康检查不检查依赖、LLM调用无重试、CORS全开放、无速率限制、无删除功能、MongoDB连接池未优化、K8s无HPA、无备份机制。这些是生产环境的基本要求。

---

## 当前需求状态（Rev 4）

### 功能需求

| # | 需求 | 状态 | 对应技能 |
|---|------|------|---------|
| F1 | 上传文档（txt/md/pdf） | ✅ 已实现 | 前端+后端 |
| F2 | 文档分块+向量化 | ✅ 已实现 | AI协同 |
| F3 | 基于文档提问 | ✅ 已实现 | AI协同+后端 |
| F4 | 异步推理（Celery+Redis） | ✅ 已实现 | 消息队列+任务调度 |
| F5 | 推理监控面板 | ✅ 已实现 | 前端+MongoDB |
| F6 | Docker Compose一键部署 | ✅ 已实现 | Docker |
| F7 | K8s生产部署 | ✅ 已实现 | K8s+GPU |
| F8 | 灰度发布 | ✅ 已实现 | 灰度发布 |
| F9 | ETL数据管道 | ✅ 已实现 | ETL |
| F10 | 性能压测 | ✅ 已实现 | 性能压测 |
| F11 | 文档删除（级联清理） | ✅ 已实现 | 后端+数据一致性 |

### 非功能需求

| # | 需求 | 状态 | 对应技能 |
|---|------|------|---------|
| NF1 | DB不可用时优雅降级 | ✅ 已实现 | 高可用 |
| NF2 | 输入验证 | ✅ 已实现 | 安全 |
| NF3 | 数据库索引优化 | ✅ 已实现 | 索引/调优 |
| NF4 | CI/CD流水线 | ✅ 已实现 | DevOps |
| NF5 | 42项自动化验证 | ✅ 已实现 | 质量保障 |
| NF6 | PEP8编码规范 | ✅ 已实现 | 编码规范 |
| NF7 | 深化健康检查（依赖探测） | ✅ 已实现 | 分布式监控 |
| NF8 | LLM调用重试（指数退避） | ✅ 已实现 | 高可用 |
| NF9 | CORS可配置 + 速率限制 | ✅ 已实现 | 安全 |
| NF10 | MongoDB连接池优化 | ✅ 已实现 | 数据库调优 |
| NF11 | HPA自动扩缩容 | ✅ 已实现 | K8s运维 |
| NF12 | 数据库备份/恢复 | ✅ 已实现 | 运维 |

### 未实现（可演进）

| # | 需求 | 优先级 | 说明 |
|---|------|--------|------|
| P1 | 用户认证系统 | 中 | 当前无认证 |
| P2 | 分库分表 | 低 | 数据量小时不需要 |
| P3 | 故障复盘模板 | 低 | 可在scripts/添加 |
