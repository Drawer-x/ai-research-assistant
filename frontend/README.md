# 前端运行说明

要求 Node.js 20.19+ 或 22.12+。

```bash
cd frontend
npm install
npm run dev
```

默认通过 Vite 将 `/api` 代理到 `http://127.0.0.1:8000`。如需直连其他后端，可设置 `VITE_API_BASE_URL`。

登录成功后 JWT 保存在浏览器 `localStorage.token`，请求封装会自动添加 `Authorization: Bearer <token>`。PDF 上传使用 `multipart/form-data`，字段名为 `file`。

论文详情页通过后端生成并加载结构化总结、QA 与证据；综述辅助页通过 `/api/papers/compare` 生成对比，并通过 `/api/papers/comparisons` 恢复最近一次历史结果。页面不会直接调用外部 AI，也不会保存 AI Key。`is_mock=true` 时会显示 Fallback/模拟结果提示。

生产构建：

```bash
npm run build
```
