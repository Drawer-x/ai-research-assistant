# Sprint 1 后端 API 契约

本文档定义 AI 驱动科研文献分析平台 Sprint 1 的联调接口。服务基址默认为 `http://127.0.0.1:8000`，交互文档位于 `/docs`。AI 总结、论文问答和 Agent 科研规划可调用成员 B 的 service；未配置 `ECNU_API_KEY`、远端调用失败或 RAG 数据不可用时自动降级为 mock。关系图边仅使用数据库已有关系。

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
| POST | `/api/papers/{paper_id}/summary` | 是 | 生成并保存 mock 总结 |
| POST | `/api/papers/{paper_id}/qa` | 是 | mock 论文问答 |
| GET | `/api/graph/papers` | 是 | ECharts Graph 节点和关系边 |
| POST | `/api/agent/research-plan` | 是 | 生成并保存 mock 科研规划 |

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

- `generate_paper_summary` 优先调用可用的 AI service，失败时返回固定结构化占位内容；两种结果都会写入 `ai_summaries` 并通过 `is_mock` 区分。
- `answer_question_about_paper` 优先使用向量检索与 AI 回答；缺少 Key、索引或依赖异常时返回固定回答和空证据。
- 关系图节点来自数据库；关系边仅来自已有 `paper_relations`，Sprint 1 不自动推断关系。
- `generate_research_plan` 优先调用 AI service，失败时按周数生成占位计划，并写入 `research_plans`。
- PDF 文本通过 PyMuPDF 尝试提取；标题和摘要自动识别仍是占位能力。
