# AI Research Assistant

AI 驱动的科研文献分析平台。Sprint 1 支持用户认证、PDF 文献管理、标签与阅读状态、AI 总结与问答、文献关系图和 Agent 科研规划。

## 启动后端

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
# Windows: copy .env.example .env
# macOS/Linux: cp .env.example .env
uvicorn app.main:app --reload
```

Swagger：http://127.0.0.1:8000/docs

`ECNU_API_KEY` 在 Sprint 1 中是可选配置。未配置或 AI/RAG 服务不可用时，后端自动返回结构稳定的 mock 数据。

## 启动前端

前端使用 Vite 8，建议 Node.js 20.19+ 或 22.12+。

```bash
cd frontend
npm install
npm run dev
```

打开终端显示的地址（默认 http://localhost:5173）。开发服务器默认把 `/api` 代理到 `http://127.0.0.1:8000`；联调 8769 后端时可先设置 `VITE_PROXY_TARGET=http://127.0.0.1:8769`。后端 CORS 同时允许本地 5173 和 5174。

## 联调顺序

1. 启动后端并访问 Swagger/健康检查。
2. 启动前端，注册并登录。
3. 上传 PDF，在文献库进入详情。
4. 修改元数据和阅读状态，添加或移除标签。
5. 生成 AI 总结并提交论文问题。
6. 打开关系图和 Agent 科研规划页面。

接口契约见 `docs/design/api_contract.md`，目录说明见 `docs/design/project_structure.md`。

完整自动化联调（后端启动后执行）：

```bash
cd backend
.venv\Scripts\python.exe scripts\final_integration_test.py --base-url http://127.0.0.1:8769 --request-timeout 120
```
