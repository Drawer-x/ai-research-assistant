# 前端运行说明

要求 Node.js 20.19+ 或 22.12+。

```bash
cd frontend
npm install
npm run dev
```

默认通过 Vite 将 `/api` 代理到 `http://127.0.0.1:8769`。联调其他后端时可设置 `VITE_PROXY_TARGET`；生产构建需要浏览器直连其他后端时设置 `VITE_API_BASE_URL`。论文上传与其他 Axios 请求使用同一 API 基址。

登录成功后 JWT 保存在浏览器 `localStorage.token`，请求封装会自动添加 `Authorization: Bearer <token>`。PDF 上传使用 `multipart/form-data`，字段名为 `file`。

论文详情页通过后端生成并加载结构化总结、QA 与证据；综述辅助页通过 `/api/papers/compare` 生成对比，并通过 `/api/papers/comparisons` 恢复最近一次历史结果。页面不会直接调用外部 AI，也不会保存 AI Key。`is_mock=true` 时会显示 Fallback/模拟结果提示。

前端不会在 API 失败时注入固定论文 ID、伪造问答或对比内容；失败会保留空状态并显示后端 `message`。

## Playwright E2E

Graph E2E 默认通过 Playwright 的 `msedge` channel 使用系统安装的 Edge，不依赖仓库中的本机绝对路径：

```bash
npm run test:e2e
```

如需指定其他兼容浏览器，可设置 `PLAYWRIGHT_EXECUTABLE_PATH`：

```powershell
$env:PLAYWRIGHT_EXECUTABLE_PATH="C:\path\to\browser.exe"
npm.cmd run test:e2e
```

也可以安装 Playwright Chromium：

```bash
npx playwright install chromium
```

生产构建：

```bash
npm run build
```

前端单元与组件契约测试：

```bash
npm run test:unit
```

测试覆盖论文删除、结构化总结映射、当前用户恢复、ECharts 图数据映射及 Agent 关联论文 `paper_ids` 请求。
