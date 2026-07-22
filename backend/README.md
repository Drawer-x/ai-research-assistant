# AI 科研文献分析平台后端

后端基于 FastAPI、SQLAlchemy 和 SQLite。Sprint 2 的 adapter 接入成员 B 的 `generate_paper_summary_result`、`answer_question_about_paper` 和 `compare_papers`；配置 `ECNU_API_KEY` 时可调用 ECNU OpenAI-compatible 服务，未配置、调用失败、返回非法或 RAG 向量库不可用时自动降级为稳定 fallback，接口仍返回 `code/message/data`。

## 启动

```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
pip install -r requirements.txt
# Windows
copy .env.example .env
# macOS/Linux: cp .env.example .env
uvicorn app.main:app --reload
```

Swagger: http://127.0.0.1:8000/docs

数据库默认创建为 `backend/ai_research_assistant.db`，上传文件保存到 `backend/uploads/{user_id}/`；两者均被根目录 `.gitignore` 忽略。

本地 Vue 开发服务器的 5173 与 5174 端口（`localhost` 和 `127.0.0.1`）已加入 CORS 白名单。

## 快速联调

先调用 `POST /api/auth/register` 和 `POST /api/auth/login`，复制返回的 token。在 Swagger 右上角 Authorize 中输入 token（无需手动添加 `Bearer`），然后调用文献、标签和 mock API。

## Sprint 2 冒烟测试

先启动后端，然后在另一个终端运行：

```bash
cd backend
python scripts/sprint2_smoke_test.py
```

测试其他地址：

```bash
python scripts/sprint2_smoke_test.py --base-url http://127.0.0.1:8767
```

脚本会自动注册唯一用户、上传两份临时 PDF，并验证总结/问答落库、多论文对比和历史查询。测试不依赖真实 AI；未配置 `ECNU_API_KEY` 时使用 fallback。

运行全部后端自动化测试（需从 `backend` 目录执行）：

```bash
.venv\Scripts\python.exe -m unittest discover -s tests -v
```

## ChatECNU 配置

Chat completion 统一由 `app/services/llm_client.py` 调用，前端不会接触 ChatECNU 或 API Key。复制 `.env.example` 为 `backend/.env`，只在该文件配置：

```dotenv
ECNU_API_KEY=
ECNU_API_URL=https://chat.ecnu.edu.cn/open/api/v1/chat/completions
ECNU_MODEL=ecnu-plus
ECNU_API_TIMEOUT_SECONDS=60
```

`backend/.env` 已被 Git 忽略，不得提交或把 Key 写入前端。聊天请求固定使用 `stream=false`。`ECNU_BASE_URL`、`ECNU_EMBEDDING_MODEL` 等旧变量继续用于现有 embedding/RAG 链路。

未配置 Key、连接或超时失败、HTTP 非成功、非 JSON、响应缺少文本、模型结构化 JSON 非法时，summary、QA、compare 会自动 fallback。接口中的 `is_mock=false` 表示真实 AI service 成功；`is_mock=true` 表示 fallback。

mock 单元测试不访问互联网：

```bash
python -m unittest discover -s tests -v
```

连通性脚本默认不发送请求；仅以下命令会显式访问真实 ChatECNU：

```bash
python scripts/test_ecnu_api.py --live
```

诊断 summary、QA、compare 三条真实业务链路（默认同样不联网）：

```bash
python scripts/test_ecnu_business_flow.py
python scripts/test_ecnu_business_flow.py --live
```

脚本只输出配置状态、`is_mock`、字段名、文本字符数和安全错误摘要。QA 优先使用用户论文的向量检索；索引或 embedding 暂不可用但论文正文非空时，会改用受限正文片段调用 ChatECNU，避免把可用真实模型错误降级为 Mock。

## Sprint 3 Graph 与 Agent

新增关系生成 `POST /api/graph/generate`、关系列表 `GET /api/graph/relations`，并保留 `GET /api/graph/papers`。生成结果写入既有 `paper_relations`；关系两端统一为较小 ID 到较大 ID，相同端点和类型不会重复保存。`is_mock` 与 description 编码在既有 `relation_reason` JSON 中，兼容旧纯文本记录，无需修改旧 SQLite 表。

Agent 保留 `POST /api/agent/research-plan`，同时兼容 Sprint 1 的 `topic/level` 和 Sprint 3 的 `research_topic/current_level/research_goal/paper_ids`。新增：

- `GET /api/agent/research-plans`
- `GET /api/agent/research-plans/{plan_id}`

计划完整结构写入既有 `research_plans.plan_content` JSON。所有接口要求 JWT，并验证论文、关系和计划归属。

Sprint 3 冒烟测试：

```bash
python scripts/sprint3_smoke_test.py
python scripts/sprint3_smoke_test.py --base-url http://127.0.0.1:8767
python scripts/sprint3_smoke_test.py --base-url http://127.0.0.1:8769 --request-timeout 120
```

脚本默认读取统一配置，将 read timeout 设为 `max(120, ECNU_API_TIMEOUT_SECONDS + 30)`，连接超时为 10 秒。真实 Agent 调用使用 `(10, ECNU_API_TIMEOUT_SECONDS)` 的连接/读取超时；模型超时、连接失败或返回非法时，后端会在有界等待后保存并返回完整 fallback 计划。

最终全链路测试覆盖认证、三篇临时 PDF、文献 CRUD、标签、总结/QA/对比历史、Graph、Agent 与双用户隔离：

```bash
python scripts/final_integration_test.py --base-url http://127.0.0.1:8769 --request-timeout 120
```

测试成功输出 `FINAL_INTEGRATION_TEST_OK`；脚本不打印 token、Key、完整正文或 Prompt，并会清理其上传的临时论文。
