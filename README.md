# 社区药店药物交互检查 Agent

这是一个面向社区药店、基层医生和药师的本地药物安全辅助系统。项目包含 FastAPI 后端、Vue 前端、多智能体用药安全检查、症状问诊辅助、候选药协作评估、CSV / Neo4j 知识图谱查询、剂量检查、证据引用和 LLM 报告润色。

系统仅用于用药安全辅助参考，不构成诊断、处方或最终用药建议。

## 环境要求

- Python 3.10+
- Node.js 18+
- npm
- 可选：Neo4j Desktop 或 Neo4j Server
- 可选：OpenAI-compatible 或 Anthropic-compatible LLM API Key

## 克隆后安装

```bash
git clone <你的 Gitee 仓库地址>
cd medical_drug_agent
```

安装 Python 依赖：

```bash
python -m pip install -r requirements.txt
```

安装前端依赖：

```bash
cd frontend
npm install
cd ..
```

## 配置 .env

复制示例配置：

```bash
copy .env.example .env
```

Linux / macOS 可使用：

```bash
cp .env.example .env
```

然后编辑 `.env`，填写自己的配置：

```env
LLM_PROVIDER=auto
LLM_API_KEY=your_api_key_here
LLM_BASE_URL=https://your-openai-compatible-base-url/v1
LLM_MODEL=your_model_name_here

KG_BACKEND=auto
NEO4J_URI=bolt://127.0.0.1:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_neo4j_password_here
NEO4J_DATABASE=neo4j
```

说明：

- `.env` 是本地私密配置，不要提交到 Gitee。
- `.env.example` 可以提交，用于给其他人参考。
- `NEO4J_URI=bolt://127.0.0.1:7687` 表示 FastAPI 后端访问本机 Neo4j，浏览器不会直接连接 Neo4j。
- 前端默认通过 Vite proxy 调用后端，通常不需要填写 `VITE_API_BASE_URL`。

## 启动 Neo4j 和导入数据

如果只想使用 CSV 后端，可以在 `.env` 中设置：

```env
KG_BACKEND=csv
```

如果要启用 Neo4j：

1. 启动 Neo4j，确认 Bolt 端口为 `7687`。
2. 在 `.env` 中填写 `NEO4J_PASSWORD`。
3. 设置 `KG_BACKEND=auto` 或 `KG_BACKEND=neo4j`。
4. 按项目现有 Neo4j 文档导入数据。

更多说明见：

- [docs/neo4j_usage.md](docs/neo4j_usage.md)

## 启动项目

推荐从项目根目录运行：

```bash
python scripts/run_all.py
```

默认不会自动打开浏览器，只打印访问地址：

```text
[后端] FastAPI: http://0.0.0.0:8000
[后端] 文档地址: http://127.0.0.1:8000/docs
[前端] Vue: http://0.0.0.0:5173
[系统] 本机访问:
  - http://localhost:5173/drug-safety
[系统] 局域网访问:
  - http://192.168.x.x:5173/drug-safety
```

本机访问：

```text
http://localhost:5173/drug-safety
```

局域网访问：

```text
http://本机局域网IP:5173/drug-safety
```

如果想启动后自动打开一次浏览器：

```bash
python scripts/run_all.py --open
```

## 启动顺序

`run_all.py` 会先启动 FastAPI 后端，并循环检测：

```text
http://127.0.0.1:8000/health
```

只有后端健康检查返回 200 后，才会启动 Vue/Vite 前端。这样可以避免前端代理过早请求后端导致：

```text
ECONNREFUSED 127.0.0.1:8000
```

如果后端 30 秒内没有就绪，脚本会停止继续启动前端。

## 分别启动

后端：

```bash
python scripts/run_api.py
```

前端：

```bash
cd frontend
npm run dev
```

后端监听 `0.0.0.0:8000`，支持局域网访问。前端 Vite 监听 `0.0.0.0:5173`。

## 前端请求后端的方式

前端代码默认请求相对路径：

```text
/api/v1/...
/health
```

开发环境由 `frontend/vite.config.js` 代理到：

```text
http://127.0.0.1:8000
```

这样局域网用户访问 `http://本机局域网IP:5173` 时，请求会先到运行项目这台电脑的 Vite 服务，再由 Vite 转发给本机 FastAPI，避免浏览器错误请求访问者自己的 `localhost`。

如需让前端直接请求某个远端后端，可以设置：

```env
VITE_API_BASE_URL=http://后端IP:8000
```

设置后需要重启前端。

## 局域网访问失败排查

如果本机可以打开：

```text
http://192.168.xxx.xxx:5173/drug-safety
```

但同一局域网其他设备打不开，通常不是后端业务代码问题，可以按下面顺序检查。

### 1. Windows 防火墙拦截

需要放行：

```text
TCP 5173
TCP 8000
Node.js
Python
```

如果前端通过 Vite proxy 调用后端，其他设备主要访问 `5173`，但为了调试方便也建议放行 `8000`。

### 2. 当前网络是手机热点

部分手机热点会限制设备之间互相访问，也就是客户端隔离。建议使用普通 WiFi、路由器或实验室局域网测试。

### 3. Windows 网络类型是公用网络

如果 Windows 把当前 WiFi 识别为“公用网络”，入站访问可能被拦截。建议切换为“专用网络”，或者在防火墙里允许专用网络访问。

### 4. 使用了错误的 IP

如果启动时显示多个 Network 地址，优先使用：

```text
192.168.x.x
```

不要优先使用 WSL、Docker、VMware、Hyper-V、VPN 等虚拟网卡地址。

### 5. 检测方式

在本机先测试：

```text
http://192.168.xxx.xxx:5173/drug-safety
```

另一台 Windows 电脑可以测试：

```powershell
Test-NetConnection 192.168.xxx.xxx -Port 5173
```

如果失败，说明网络或防火墙不通。

## 常见问题

### 前端能打开，但接口请求失败

优先确认后端是否启动：

```text
http://运行项目电脑IP:8000/docs
```

开发环境也可以通过前端代理检查：

```text
http://运行项目电脑IP:5173/health
```

### 药物搜索框没有数据

确认药物选项接口可访问：

```text
http://运行项目电脑IP:5173/api/v1/drugs/options
```

### Neo4j 不可用

如果 `KG_BACKEND=auto`，系统会自动回退 CSV。可以在系统调试页查看实际使用的是 `neo4j` 还是 `csv`。

### LLM 润色失败

系统会自动回退模板报告，并保留风险发现、证据引用和规则结果不变。请检查 `.env` 中的 `LLM_API_KEY`、`LLM_BASE_URL` 和 `LLM_MODEL`。

## 验证

```bash
python -m py_compile scripts/run_all.py scripts/run_api.py
```

```bash
cd frontend
npm run build
```
