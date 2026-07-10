# Git 协作规范

## 1. 分支说明

| 分支 | 作用 |
|---|---|
| main | 最终稳定展示版本 |
| develop | 日常开发主分支 |
| feature/backend | 后端功能开发 |
| feature/ai | AI 与 PDF 解析开发 |
| feature/frontend | 前端页面开发 |
| feature/test-deploy | 测试与部署文档 |

## 2. 开发流程

1. 从 develop 拉取最新代码
2. 创建或切换到自己的 feature 分支
3. 完成功能后提交 commit
4. push 到远程仓库
5. 创建 Pull Request
6. 由组长 Review 后合并到 develop
7. 每轮 Sprint 结束后合并稳定代码到 main 并打 tag

## 3. Commit 规范

- feat: 新功能
- fix: 修复 bug
- docs: 文档
- test: 测试
- style: 样式
- refactor: 重构
- chore: 配置

## 4. Issue 规范

每个任务都应该对应一个 Issue。
Issue 需要包含：
- 任务描述
- 负责人
- 标签
- Milestone
- 验收标准

## 5. Tag 规划

- v0.1-sprint0
- v0.2-sprint1
- v0.3-sprint2
- v0.4-sprint3
- v1.0-final