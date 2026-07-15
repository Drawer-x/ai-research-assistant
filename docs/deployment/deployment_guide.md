# 部署指南 - AI Research Assistant

> **项目名称**：AI Research Assistant  
> **版本**：v0.1  
---

## 1. 概述

### 1.1 文档目的
本文档旨在提供 AI Research Assistant 项目的完整部署指南，包括开发环境搭建、生产环境部署、配置说明和常见问题解决。

### 1.2 适用人员
- 开发人员（本地开发环境搭建）
- 运维人员（生产环境部署）
- 测试人员（测试环境搭建）

### 1.3 技术架构

| 组件 | 技术选型 | 说明 |
|------|---------|------|
| 前端 | React + Vite | 单页应用 |
| 后端 | Python + FastAPI | RESTful API |
| 数据库 | SQLite（开发）/ PostgreSQL（生产） | 数据存储 |
| AI 服务 | OpenAI API / 本地 LLM | 智能分析 |
| 部署 | Docker / 传统部署 | 运行环境 |

---

## 2. 环境要求

### 2.1 开发环境

| 组件 | 版本要求 | 下载地址 |
|------|---------|---------|
| Python | 3.10 或更高 | https://python.org |
| Node.js | 18.x 或更高 | https://nodejs.org |
| Git | 最新版 | https://git-scm.com |
| SQLite | 3.x | Python 内置 |

### 2.2 生产环境

| 组件 | 版本要求 | 说明 |
|------|---------|------|
| Python | 3.10 | 建议使用 pyenv 管理版本 |
| Node.js | 18.x LTS | 建议使用 nvm 管理版本 |
| PostgreSQL | 14.x 或更高 | 生产数据库 |
| Nginx | 最新版 | 反向代理和静态文件服务 |
| Redis（可选） | 7.x | 缓存和会话管理 |
| Docker（可选） | 20.x | 容器化部署 |

### 2.3 系统要求

| 项目 | 最低配置 | 推荐配置 |
|------|---------|---------|
| CPU | 2 核 | 4 核以上 |
| 内存 | 4 GB | 8 GB 以上 |
| 硬盘 | 20 GB | 50 GB 以上 |
| 操作系统 | Ubuntu 20.04 / Windows Server | Ubuntu 22.04 LTS |

---

## 3. 部署方式选择

| 部署方式 | 适用场景 | 复杂度 |
|---------|---------|--------|
| **本地开发部署** | 开发、调试、测试 | 简单 |
| **传统部署** | 小型生产环境、演示 | 中等 |
| **Docker 部署** | 标准化生产环境 | 较复杂 |
| **云平台部署** | 弹性扩展、高可用 | 复杂 |

---

## 4. 本地开发部署（一键启动）

### 4.1 克隆代码

```bash
# 克隆仓库
git clone https://github.com/your-repo/ai-research-assistant.git
cd ai-research-assistant

# 切换到开发分支
git checkout develop
```

### 4.2 后端部署
#### Step 1：创建虚拟环境
```
cd backend

# 使用 venv
python -m venv venv

# 激活虚拟环境
# Windows (Git Bash)
source venv/Scripts/activate
# Windows (PowerShell)
.\venv\Scripts\Activate.ps1
# Linux / Mac
source venv/bin/activate
```
#### Step 2：安装依赖
```
# 配置国内镜像源（加速）
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 安装依赖
pip install -r requirements.txt

# 如果 requirements.txt 不存在，手动安装核心依赖
pip install fastapi uvicorn[standard] sqlalchemy python-dotenv \
    python-multipart passlib python-jose[cryptography] bcrypt \
    aiofiles pytest
```
#### Step 3：配置环境变量
```
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件
# Windows
notepad .env
# Linux / Mac
nano .env
```
.env 配置示例：
```
# ===== 数据库配置 =====
# 开发环境使用 SQLite
DATABASE_URL=sqlite:///./app.db

# 生产环境使用 PostgreSQL（取消注释并修改）
# DATABASE_URL=postgresql://user:password@localhost:5432/ai_research

# ===== 安全配置 =====
SECRET_KEY=your-super-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# ===== 文件上传配置 =====
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=10485760  # 10MB
ALLOWED_EXTENSIONS=.pdf

# ===== AI 服务配置 =====
# OpenAI
# AI_API_URL=https://api.openai.com/v1/chat/completions
# AI_API_KEY=your-openai-api-key
# AI_MODEL=gpt-3.5-turbo

# 本地 Ollama
AI_API_URL=http://localhost:11434/api/generate
AI_API_KEY=ollama  # 本地服务可以留空
AI_MODEL=llama2

# ===== 前端配置 =====
FRONTEND_URL=http://localhost:5173
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```
#### Step 4：初始化数据库
```
# 方式一：Python 脚本初始化
python -c "
from app.database import engine, Base
from app.models import *
Base.metadata.create_all(bind=engine)
print('数据库表创建成功')
"

# 方式二：如果有初始化脚本
python scripts/init_db.py

# 方式三：启动时自动创建（已在 main.py 中配置）
```
#### Step 5：启动后端
```
# 开发模式（热重载）
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 生产模式
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```
验证：
- 访问 http://localhost:8000/docs 查看 API 文档
- 访问 http://localhost:8000/ 查看健康检查
  
### 4.3 前端部署
#### Step 1：安装 Node.js 依赖
```
cd frontend

# 配置国内镜像源
npm config set registry https://registry.npmmirror.com

# 安装依赖
npm install
```
#### Step 2：配置环境变量
创建 frontend/.env：
```
VITE_API_URL=http://localhost:8000
VITE_APP_TITLE=AI Research Assistant
```
#### Step 3：启动前端开发服务器
```
npm run dev
```
验证：访问 http://localhost:5173

## 5. 常见问题解决
### 问题 1：后端启动失败
现象：
```
ModuleNotFoundError: No module named 'xxx'
```
解决方案：
```
# 重新安装依赖
pip install -r requirements.txt

# 如果某个包安装失败，单独安装
pip install xxx -i https://pypi.tuna.tsinghua.edu.cn/simple
```
### 问题 2：数据库连接失败
现象：
```
sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) unable to open database file
```
解决方案：
```
# SQLite：检查目录权限
chmod 777 backend/

# PostgreSQL：检查服务状态
sudo systemctl status postgresql
sudo systemctl start postgresql
```
### 问题 3：端口被占用
现象：
```
ERROR: [Errno 98] Address already in use
```
解决方案：
```
# 查找占用端口的进程
# Windows
netstat -ano | findstr :8000

# Linux / Mac
sudo lsof -i :8000

# 终止进程
kill -9 PID
# 或更换端口
uvicorn app.main:app --port 8001
```
### 问题 4：前端构建失败
现象：
```
Error: Cannot find module 'xxx'
```
解决方案：
```
# 清理缓存
rm -rf node_modules package-lock.json
npm cache clean --force

# 重新安装
npm install --registry=https://registry.npmmirror.com

# 重新构建
npm run build
```
### 问题 5：CORS 跨域错误
```
Access to fetch at 'http://localhost:8000/api/...' from origin 'http://localhost:5173' has been blocked by CORS policy
```
解决方案：
```
在 .env 中配置：

CORS_ORIGINS=http://localhost:5173,http://localhost:3000,https://your-domain.com
```
### 问题 6：AI 服务连接失败
现象：
```
Error: AI API connection timeout
```
解决方案：
```
# 1. 检查 AI_API_URL 是否正确
# 2. 检查 API Key 是否有效
# 3. 检查网络是否通畅
curl http://localhost:11434/api/generate

# 4. 如果使用 OpenAI，检查余额
```