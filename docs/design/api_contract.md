# Sprint 1–3 后端 API 契约

本文档定义 AI 驱动科研文献分析平台 Sprint 1–3 的联调接口。服务基址默认为 `http://127.0.0.1:8000`，交互文档位于 `/docs`。AI 总结、论文问答、多论文对比、关系生成和 Agent 科研规划通过 adapter 调用对应 service；未配置 `ECNU_API_KEY`、远端调用失败、结构化返回非法或 RAG 数据不可用时自动降级为稳定 fallback。生成的关系、AI 历史与计划均持久化并按用户隔离。

## 统一响应

成功：

```json
{"code": 200, "message": "success", "data": {}}
```

失败（HTTP 状态码与 `code` 一致）：

```json
{"code": 400, "message": "具体错误原因", "data": null}
```

## 认证

除健康检查、注册、登录外均需请求头：

```http
Authorization: Bearer <JWT token>
```

登录请求及响应：

```http
POST /api/auth/login
Content-Type: application/json

{"username":"test","password":"123456"}
```

```json
{"code":200,"message":"success","data":{"token":"xxx","token_type":"bearer","user":{"id":1,"username":"test","email":"test@example.com"}}}
```

## 接口清单

| 方法 | 路径 | 认证 | 用途 |
|---|---|---:|---|
| GET | `/api/health` | 否 | 健康检查 |
| POST | `/api/auth/register` | 否 | 用户注册 |
| POST | `/api/auth/login` | 否 | 用户登录 |
| GET | `/api/auth/me` | 是 | 当前用户 |
| POST | `/api/papers/upload` | 是 | 上传 PDF，表单字段 `file` |
| GET | `/api/papers` | 是 | 文献列表；支持 `q`、`read_status`、`tag` |
| GET | `/api/papers/{paper_id}` | 是 | 文献详情 |
| PUT | `/api/papers/{paper_id}` | 是 | 修改文献元数据 |
| DELETE | `/api/papers/{paper_id}` | 是 | 删除文献记录 |
| PUT | `/api/papers/{paper_id}/status` | 是 | 更新阅读状态 |
| POST | `/api/tags` | 是 | 创建标签 |
| GET | `/api/tags` | 是 | 标签列表 |
| POST | `/api/papers/{paper_id}/tags` | 是 | 添加或自动创建标签 |
| DELETE | `/api/papers/{paper_id}/tags/{tag_id}` | 是 | 移除论文标签 |
| POST | `/api/papers/{paper_id}/summary` | 是 | 生成并保存结构化总结（AI 或 fallback） |
| POST | `/api/papers/{paper_id}/qa` | 是 | 真实 AI 或 fallback 论文问答 |
| GET | `/api/graph/papers` | 是 | ECharts Graph 节点和关系边 |
| POST | `/api/agent/research-plan` | 是 | 生成并保存真实 AI 或 fallback 科研规划 |
| GET | `/api/papers/{paper_id}/summaries` | 是 | 查询当前用户论文的总结历史 |
| GET | `/api/papers/{paper_id}/qa-records` | 是 | 查询当前用户论文的问答历史 |
| POST | `/api/papers/compare` | 是 | 对比至少两篇当前用户的论文 |
| GET | `/api/papers/comparisons` | 是 | 查询当前用户的对比历史 |
| POST | `/api/graph/generate` | 是 | 为当前用户至少两篇论文生成并保存关系 |
| GET | `/api/graph/relations` | 是 | 查询当前用户论文之间的关系 |
| GET | `/api/agent/research-plans` | 是 | 查询当前用户计划历史 |
| GET | `/api/agent/research-plans/{plan_id}` | 是 | 查询当前用户单条计划 |

## 请求与返回示例

注册：

```json
{"username":"test","email":"test@example.com","password":"123456"}
```

上传使用 `multipart/form-data`，字段名固定为 `file`。上传成功后 `data` 包含 `paper_id`、元数据、标签、解析状态和 PDF 相对路径。即使解析失败也会成功创建记录，此时 `parse_status` 为 `failed`。

更新文献（字段均可选）：

```json
{"title":"Attention Is All You Need","authors":"Vaswani et al.","year":2017,"venue":"NeurIPS","abstract":"..."}
```

阅读状态：

```json
{"read_status":"rough_read"}
```

可用值为 `unread`、`rough_read`、`intensive_read`、`to_reproduce`、`for_review`、`archived`。

标签：

```json
{"name":"Transformer"}
```

为论文添加标签：

```json
{"tag_name":"Transformer"}
```

AI 总结响应的 `data`：

```json
{"paper_id":1,"summary":{"background":"这里是论文研究背景，占位数据","problem":"这里是论文要解决的问题，占位数据","method":"这里是论文核心方法，占位数据","experiment":"这里是实验设置，占位数据","result":"这里是主要结果，占位数据","innovation":"这里是创新点，占位数据","limitation":"这里是局限性，占位数据"},"is_mock":true}
```

论文问答请求与 `data`：

```json
{"question":"这篇论文解决了什么问题？"}
```

```json
{"answer":"这是基于论文内容生成的占位回答。","evidence":[],"has_evidence":false,"is_mock":true}
```

关系图 `data`：

```json
{"nodes":[{"id":1,"name":"Attention Is All You Need","year":2017,"category":"paper"}],"edges":[{"source":1,"target":2,"relation_type":"similar_topic","label":"主题相似"}]}
```

无关系记录时仍返回当前用户的论文节点，`edges` 为空数组。

科研规划请求及 `data` 示例：

```json
{"topic":"时间序列预测中的 Transformer 模型","level":"beginner","duration_weeks":4}
```

```json
{"topic":"时间序列预测中的 Transformer 模型","stages":[{"name":"背景学习","tasks":["阅读综述论文","了解基础概念"],"output":"完成研究背景笔记"}],"weekly_plan":[{"week":1,"goal":"了解基础概念","tasks":["阅读 2 篇相关论文","整理研究笔记"]}],"risks":["选题范围较大，建议先聚焦具体任务"],"is_mock":true}
```

## AI 与 Mock 降级边界

ChatECNU 请求由后端统一发送到 `ECNU_API_URL`，模型取自 `ECNU_MODEL`，超时取自 `ECNU_API_TIMEOUT_SECONDS`；请求体为 `messages`、`stream=false` 和 `model`。API Key 只能来自被 Git 忽略的 `backend/.env`，不会传到前端或写入日志。

响应兼容 `choices[0].message.content`、`data.choices[0].message.content`、顶层 `content` 和 `message.content`。HTTP 错误、超时、连接失败、非 JSON、缺少文本或业务 JSON 校验失败均进入 fallback，不向客户端透传上游原始响应。

- adapter 优先调用 `generate_paper_summary_result`，兼容嵌套 `summary/content/data` 后规范化七个字段；失败时返回固定结构化占位内容。两种结果都会写入 `ai_summaries` 并通过 `is_mock` 区分。
- `answer_question_about_paper` 优先从当前用户论文的向量索引检索证据片段，再通过统一 ChatECNU client 基于片段回答；索引或 embedding 不可用但正文非空时使用安全截断的正文片段，正文为空或 ChatECNU 调用/解析失败时才返回 fallback。
- 关系图节点来自数据库；关系边仅来自已有 `paper_relations`，Sprint 1 不自动推断关系。
- `generate_research_plan` 优先调用 AI service，失败时按周数生成占位计划，并写入 `research_plans`。
- PDF 文本通过 PyMuPDF 尝试提取；标题和摘要自动识别仍是占位能力。

## Sprint 2 AI 结果与对比

以上接口均需要 `Authorization: Bearer <token>`，且仅允许访问当前用户的论文和 AI 结果。API 层通过 `ai_adapter_service` 调用成员 B 的 `generate_paper_summary_result`、`answer_question_about_paper` 和 `compare_papers`；函数缺失、异常或返回结构无效时使用稳定 fallback。QA 的字符串、字典或列表 evidence 会规范化为字符串列表。

总结历史：

```http
GET /api/papers/1/summaries
```

```json
{"code":200,"message":"success","data":[{"id":1,"paper_id":1,"summary_type":"structured","content":{"background":"..."},"model_name":"fallback-mock","is_mock":true,"created_at":"2026-07-15T10:00:00"}]}
```

问答请求仍使用 Sprint 1 路径，成功后会写入 `qa_records`：

```http
POST /api/papers/1/qa
Content-Type: application/json

{"question":"这篇论文解决了什么问题？"}
```

问答历史：

```http
GET /api/papers/1/qa-records
```

```json
{"code":200,"message":"success","data":[{"id":1,"paper_id":1,"question":"这篇论文解决了什么问题？","answer":"fallback 回答","evidence":[],"has_evidence":false,"is_mock":true,"created_at":"2026-07-15T10:00:00"}]}
```

多论文对比：

```http
POST /api/papers/compare
Content-Type: application/json

{"paper_ids":[1,2],"compare_dimensions":["problem","method","dataset","result","limitation"]}
```

```json
{"code":200,"message":"success","data":{"comparison_id":1,"paper_ids":[1,2],"compare_dimensions":["problem","method","dataset","result","limitation"],"comparison_table":[{"paper_id":1,"title":"Paper A","problem":"待由 AI 提取或 fallback"}],"summary":"这是多论文对比的 fallback 总结，后续可由成员 B 替换为真实 AI 输出。","is_mock":true}}
```

对比历史：

```http
GET /api/papers/comparisons
```

返回当前用户的 `paper_ids`、对比维度、完整结果、`is_mock` 和创建时间，不返回其他用户数据。成员 B 后续只需提供 `app.services.compare_service.compare_papers(papers, compare_dimensions)`，无需修改 API 路径。

## Sprint 3 关系图

```http
POST /api/graph/generate
Authorization: Bearer <token>
Content-Type: application/json

{"paper_ids":[1,2,3],"relation_types":["citation","topic_similarity","method_similarity"],"force_regenerate":false}
```

`paper_ids` 为空时使用当前用户全部论文。返回 `nodes`、`edges`、`is_mock` 和 `generated_count`。节点包含 `paper_id/title/authors/year/venue/read_status`；边包含 `id/source/target/relation_type/weight/description/is_mock`。查询使用 `GET /api/graph/papers`，只查边使用 `GET /api/graph/relations`。两端论文必须属于当前用户。

成员 B 可提供以下任一名称，adapter 会优先检测：`generate_paper_relations`、`build_paper_relations`、`generate_literature_graph`。推荐契约：

```python
generate_paper_relations(papers: list[dict], relation_types: list[str]) -> dict
```

返回 `{"relations":[{"source":1,"target":2,"relation_type":"topic_similarity","weight":0.8,"description":"...","is_mock":false}],"is_mock":false}`。函数缺失、异常或结构非法时使用确定性 fallback。

## Sprint 3 Agent

旧请求仍有效：`{"topic":"RAG","level":"beginner","duration_weeks":4}`。新请求：

```json
{"research_topic":"RAG","research_goal":"完成原型","duration_weeks":8,"current_level":"undergraduate","paper_ids":[1,2]}
```

生成响应包含 `plan_id/research_topic/research_goal/duration_weeks/current_level/reading_route/stages/weekly_plan/tasks/risks/recommended_papers/is_mock/created_at`。历史按 `created_at DESC, id DESC` 返回；详情和历史均只允许计划所有者访问。

成员 B 推荐实现：

```python
generate_research_plan(research_topic: str, research_goal: str, duration_weeks: int, current_level: str | None = None, papers: list[dict] | None = None) -> dict
```

Adapter 同时兼容当前 Sprint 1 实际签名 `generate_research_plan(topic, level, duration_weeks)`，并兼容名称 `create_research_plan`、`generate_agent_plan`。真实 service 缺失、异常或完全非法时，返回按周数生成的稳定 fallback，`is_mock=true`。
