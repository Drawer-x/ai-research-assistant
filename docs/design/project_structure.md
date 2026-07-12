# 项目目录结构说明

本项目采用前后端分离结构，后端负责 API、数据库、文件上传、AI service 对接；前端负责页面展示和用户交互；docs 目录用于保存需求、设计、测试、部署和 Sprint 文档。

## 目录结构

```text
ai-research-assistant/
│
├── backend/                    # 后端代码，成员 A 主要负责
│   ├── app/
│   │   ├── api/                # 后端路由接口
│   │   ├── core/               # 配置、安全、统一响应
│   │   ├── models/             # 数据库模型
│   │   ├── schemas/            # 请求/响应数据结构
│   │   ├── services/           # 业务逻辑和 AI service
│   │   ├── database.py
│   │   └── main.py
│   ├── uploads/                # 本地上传文件目录，只保留 .gitkeep
│   ├── requirements.txt
│   ├── .env.example
│   └── README.md
│
├── frontend/                   # 前端代码，成员 C 主要负责
├── docs/                       # 项目文档
│   ├── design/                 # 设计文档、接口文档
│   ├── test/                   # 测试计划和测试结果，成员 D 主要负责
│   ├── deployment/             # 部署文档，成员 D 主要负责
│   ├── sprint/                 # Sprint 计划、Review、Retrospective
│   └── meeting/                # Daily Scrum 会议记录
│
├── demo_assets/                # 演示材料，不提交大体积 PDF
├── scripts/                    # 辅助脚本
├── README.md
└── .gitignore