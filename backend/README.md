# AI 科研文献分析平台后端

Sprint 1 后端基于 FastAPI、SQLAlchemy 和 SQLite。配置 `ECNU_API_KEY` 时可调用成员 B 的 AI/RAG service；未配置、调用失败或向量库不可用时自动降级为 mock，接口结构保持不变。

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

本地 Vue 开发服务器的 `http://localhost:5173` 和 `http://127.0.0.1:5173` 已加入 CORS 白名单。

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
