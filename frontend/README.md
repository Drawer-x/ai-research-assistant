# 前端运行说明

要求 Node.js 20.19+ 或 22.12+。

```bash
cd frontend
npm install
npm run dev
```

默认通过 Vite 将 `/api` 代理到 `http://127.0.0.1:8000`。如需直连其他后端，可设置 `VITE_API_BASE_URL`。

登录成功后 JWT 保存在浏览器 `localStorage.token`，请求封装会自动添加 `Authorization: Bearer <token>`。PDF 上传使用 `multipart/form-data`，字段名为 `file`。
