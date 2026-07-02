# Vue 前端

这是社区药店药物交互检查 Agent 的正式前端，基于 `Vue 3 + Vite + Element Plus + Axios`。

## 安装依赖

```bash
cd frontend
npm install
```

## 推荐启动方式

从项目根目录一键启动前后端：

```bash
python scripts/run_all.py
```

本机访问：

```text
http://localhost:5173/drug-safety
```

局域网访问：

```text
http://你的局域网IP:5173/drug-safety
```

## 单独启动前端

```bash
cd frontend
npm run dev
```

Vite 已配置：

- `host: "0.0.0.0"`，支持局域网访问。
- `/api` 代理到 `http://127.0.0.1:8000`。
- `/health` 代理到 `http://127.0.0.1:8000`。

前端默认使用相对路径调用后端，不会把 `127.0.0.1:8000` 写死到浏览器请求中。

## 可选 API 地址覆盖

默认留空即可。如果需要直接请求远端 FastAPI，可在项目根目录 `.env` 中设置：

```env
VITE_API_BASE_URL=http://后端IP:8000
```

设置后需要重启前端。
