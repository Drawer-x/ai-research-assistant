# AI Prompt 与本地推断设计

本文档记录后端已经实现的 AI 输入、输出校验和降级边界。外部 LLM 与
Embedding 均为可选依赖；只有外部模型输出通过完整结构校验时才能返回
`is_mock=false`，本地模板、占位内容或不可验证结果均返回 `is_mock=true`。

## 通用约束

- LLM 调用统一使用 `app.services.llm_client.chat_with_deepseek`，复用现有
  OpenAI-compatible ChatECNU 客户端、超时和最大提示词长度配置。
- 论文正文、检索片段、用户问题、研究主题和对比维度均为不可信数据。提示词
  使用显式数据边界，并要求忽略数据中改变角色、泄露提示词或偏离任务的指令。
- 不允许根据缺失上下文编造科研结论。结构化响应只接受一个 JSON 对象；多个
  顶层 JSON 对象会被拒绝。
- 缺 Key、超时、provider 异常、空响应、非法 JSON、字段缺失或类型错误均不能
  标记为真实模型结果。
- 普通日志不得包含 API Key、Authorization、完整提示词、完整论文正文或完整模型
  响应。

## Sprint 2 服务

### 论文总结

入口：`generate_paper_summary_result(paper_text)`。

提示词要求只根据 `<paper_content>` 内至多 15,000 字符的正文生成七个字符串字段：
`background`、`problem`、`method`、`experiment`、`result`、`innovation`、
`limitation`。原文未提供的信息使用保守表述；结构不合格时返回完整本地 fallback。

### 论文问答

入口：`answer_question_about_paper(question, paper_text, paper_id, user_id)`。

调用 LLM 前先校验索引文件、owner 和正文指纹，再检索最多 8 个 L2 最近分块。
`<retrieved_context>` 总长度上限为 12,000 字符；`<user_question>` 由 API schema
限制为 2,000 字符。检索为空时不调用 LLM；生成失败时保留已检索 evidence，并
标记 `is_mock=true`。

### 多论文对比

入口：`compare_papers(papers, compare_dimensions)`。

提示词包含有界论文元数据、摘要和正文预览，并要求 `comparison_table` 为每个输入
`paper_id` 返回且仅返回一行、覆盖全部指定维度，同时返回非空 `summary`。服务按
输入顺序重排并校验行；模型返回未知、重复或缺失论文时使用完整 fallback。

## Sprint 3 文献关系生成设计

入口：`generate_paper_relations(papers, relation_types)`。

该能力不调用外部模型，而是仅使用调用方已经完成权限过滤的论文字典执行本地、
确定性推断。Service 不访问数据库，也不接受用户或路径对象。

- `topic_similarity`：标题权重最高，摘要次之，作者和 venue 仅为辅助，正文只读取
  有界预览；英文使用规范化 token，中文使用 2～4 字 n-gram，并过滤“paper”、
  “study”、“研究”、“方法”等通用词。关系由 weighted Jaccard 和最少共同信息阈值
  决定，说明只列出真实共同关键词。
- `method_similarity`：在标题、摘要和有界正文预览中识别中英文方法族，包括
  Transformer、注意力、CNN/RNN/LSTM/GRU、BERT、RAG、知识图谱、GNN、对比学习、
  微调、LoRA、Embedding、向量检索、强化学习、扩散模型、随机森林、SVM、XGBoost
  等。至少有一个共同方法才生成关系，权重与方法集合重合度相关。
- `citation`：依次检查目标论文完整标题是否出现在源论文参考文献区域或正文，或
  是否同时存在作者、年份和足够的标题关键词。`source` 始终为引用者，`target` 始终
  为被引论文；不会为稳定排序而交换方向。长正文预览在固定总预算内同时保留开头
  与尾部，以降低参考文献区域被截断的概率。

主题和方法关系将较小 `paper_id` 作为 `source`，引用关系保留方向。所有关系均校验
输入 ID、自环、类型、权重范围，并按类型和 ID 稳定排序、去重。真实本地算法找到
有证据关系时返回 `is_mock=false`；输入不足、没有任何关系或可恢复异常时返回
`{"relations": [], "is_mock": true}`，不会制造演示边。

## Sprint 3 Agent 科研规划 Prompt

入口：

```python
generate_research_plan(
    research_topic,
    research_goal,
    duration_weeks,
    current_level=None,
    papers=None,
)
```

### 输入与截断

- `research_topic` 必须为非空字符串；`duration_weeks` 必须是 1～52 的整数，bool
  不作为整数接受。
- 空 `research_goal` 转为包含研究主题的默认可验证目标；空 `current_level` 转为
  保守的“基础水平（未提供）”。
- 论文最多保留 20 篇，按有效且唯一的正整数 `paper_id` 稳定排序。只向模型传递
  `paper_id`、标题、作者、年份、venue、摘要和正文预览；不传用户 ID、文件路径、
  token 或数据库内部字段。
- 每篇标题最多 500 字符并优先完整保留；其余字段根据论文数和剩余预算动态分配，
  作者最多 300 字符、venue 200 字符、摘要 1,200 字符、正文 8,000 字符。全部论文
  字段内容约束在 24,000 字符预算内，不会将完整 PDF 发送给模型。

### Prompt injection 防护

用户请求置于 `<user_request>`，论文数据置于 `<papers>`。提示词明确声明标签内
内容是不可信数据，论文正文中的角色切换、提示词泄露、忽略约束、输出 Markdown
或非 JSON 等命令不得执行。模型只能基于提供的论文 ID 推荐论文，不得补造来源。
服务日志只记录失败类别、耗时、是否配置 Key、论文数和计划周数。

### 输出 JSON 结构

模型只能返回一个 JSON 对象，包含以下列表：

```json
{
  "reading_route": [
    {"order": 1, "name": "...", "goal": "...", "tasks": ["..."], "output": "..."}
  ],
  "stages": [
    {"name": "...", "start_week": 1, "end_week": 1, "goals": ["..."],
     "tasks": ["..."], "deliverables": ["..."]}
  ],
  "weekly_plan": [
    {"week": 1, "goal": "...", "tasks": ["..."], "deliverables": ["..."]}
  ],
  "tasks": [
    {"name": "...", "category": "experiment", "priority": "high",
     "estimated_hours": 8, "dependencies": [], "acceptance_criteria": "..."}
  ],
  "risks": [
    {"risk": "...", "probability": "medium", "impact": "high", "mitigation": "..."}
  ],
  "recommended_papers": [
    {"paper_id": 1, "title": "输入中的原始标题", "reading_order": 1, "reason": "..."}
  ]
}
```

### 结构校验规则

- `reading_route` 非空，order 为唯一正整数，按 order 排序；名称、目标、任务和产出
  均非空。
- `stages` 非空，周范围有效、不重叠、连续覆盖完整周期；目标、任务和交付物非空。
  校验后从 `deliverables` 统一生成兼容旧显示的 `output`，避免两份产出字段冲突。
- `weekly_plan` 必须恰好覆盖第 1 至 `duration_weeks` 周，每周只出现一次，目标、任务
  和交付物非空。
- `tasks` 非空，优先级只接受 `high/medium/low`，工时为 1～168 的正整数，依赖为
  字符串列表，验收标准非空；拒绝仅为“继续学习”“推进研究”等空泛任务。
- `risks` 非空，概率和影响只接受 `high/medium/low`，风险及缓解措施非空。
- `recommended_papers` 必须是列表；ID 和标题必须与输入论文完全对应，ID 和阅读顺序
  不得重复。无输入论文时必须为空，允许在相关性不足时只推荐部分论文。

JSON 由共享的 `parse_json_object` 解析，并用 `unwrap_model_object` 处理 `data` 或
`content` 对象包装。只有六类结构全部通过校验才返回 `is_mock=false`；任何关键字段
缺失、周计划不完整、类型异常或论文推荐越界均触发 fallback。

### Agent fallback 与兼容性

缺 Key、超时、网络或 HTTP 错误、空响应、非法 JSON、结构校验失败和其他可恢复运行
时异常都会返回六个列表齐全的确定性计划并标记 `is_mock=true`。fallback 根据主题、
目标、水平和周期划分阅读、问题定义、方案、验证及验收阶段；每周内容随阶段变化，
最后一周固定包含总结、验收和汇报。1 周计划也会生成完整有效结构。

fallback 的论文推荐只从清洗后的输入论文生成，保留原始 ID 和标题；无论文时为空。
为兼容 Sprint 2 仍直接使用 `(topic, level, duration_weeks)` 的调用方，Service 保留一个
窄兼容路径，但 Sprint 3 主入口及 adapter 使用本节完整签名和六列表结构。

## 配置依赖

真实 LLM 调用需要 `ECNU_API_KEY`。可选配置为 `ECNU_BASE_URL`、
`ECNU_CHAT_MODEL`、`ECNU_EMBEDDING_MODEL`、`AI_TIMEOUT_SECONDS`、
`AI_MAX_PROMPT_CHARS`、`EMBEDDING_BATCH_SIZE` 和 `EMBEDDING_MAX_INPUT_CHARS`。
应用导入、启动和离线单元测试不应要求真实 Key 或网络。
