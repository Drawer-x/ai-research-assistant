# AI 科研文献分析平台后端

Sprint 1 后端基于 FastAPI、SQLAlchemy 和 SQLite，AI 总结、问答、关系图及科研规划当前为 mock 实现。

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

## 快速联调

先调用 `POST /api/auth/register` 和 `POST /api/auth/login`，复制返回的 token。在 Swagger 右上角 Authorize 中输入 token（无需手动添加 `Bearer`），然后调用文献、标签和 mock API。
