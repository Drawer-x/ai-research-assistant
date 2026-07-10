# 数据库设计

## 1. users 用户表

| 字段 | 类型 | 说明 |
|---|---|---|
| id | integer | 用户 ID |
| username | varchar | 用户名 |
| email | varchar | 邮箱 |
| password_hash | varchar | 密码哈希 |
| role | varchar | 用户角色 |
| created_at | datetime | 创建时间 |

## 2. papers 文献表

| 字段 | 类型 | 说明 |
|---|---|---|
| id | integer | 文献 ID |
| user_id | integer | 所属用户 |
| title | varchar | 论文标题 |
| authors | text | 作者 |
| year | integer | 年份 |
| venue | varchar | 会议或期刊 |
| abstract | text | 摘要 |
| pdf_path | varchar | PDF 文件路径 |
| read_status | varchar | 阅读状态 |
| created_at | datetime | 上传时间 |

## 3. tags 标签表

| 字段 | 类型 | 说明 |
|---|---|---|
| id | integer | 标签 ID |
| user_id | integer | 用户 ID |
| name | varchar | 标签名称 |

## 4. paper_tags 文献标签关联表

| 字段 | 类型 | 说明 |
|---|---|---|
| id | integer | ID |
| paper_id | integer | 文献 ID |
| tag_id | integer | 标签 ID |

## 5. ai_summaries AI 总结表

| 字段 | 类型 | 说明 |
|---|---|---|
| id | integer | 总结 ID |
| paper_id | integer | 文献 ID |
| summary_type | varchar | 总结类型 |
| content | text | 总结内容 |
| model_name | varchar | 模型名称 |
| created_at | datetime | 创建时间 |

## 6. paper_relations 文献关系表

| 字段 | 类型 | 说明 |
|---|---|---|
| id | integer | 关系 ID |
| source_paper_id | integer | 起点论文 |
| target_paper_id | integer | 终点论文 |
| relation_type | varchar | 关系类型 |
| relation_reason | text | 关系说明 |
| confidence | float | 置信度 |

## 7. research_plans 科研计划表

| 字段 | 类型 | 说明 |
|---|---|---|
| id | integer | 计划 ID |
| user_id | integer | 用户 ID |
| topic | varchar | 研究主题 |
| goal | text | 研究目标 |
| plan_content | text | 计划内容 |
| created_at | datetime | 创建时间 |