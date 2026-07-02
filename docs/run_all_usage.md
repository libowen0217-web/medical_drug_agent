# 一键启动与局域网访问

## 推荐启动

在项目根目录运行：

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

如果希望启动后自动打开一次浏览器：

```bash
python scripts/run_all.py --open
```

如果 `5173` 端口已被占用，脚本只提示前端可能已经启动，不会再自动打开新页面。

## 启动顺序

`run_all.py` 会按下面顺序启动：

1. 启动 FastAPI 后端。
2. 循环检测 `http://127.0.0.1:8000/health`。
3. 只有 `/health` 返回 200 后，才启动 Vue/Vite 前端。
4. 打印本机访问地址和局域网访问地址。

如果后端 30 秒内没有通过健康检查，脚本会停止继续启动前端，避免 Vite 代理出现 `ECONNREFUSED 127.0.0.1:8000`。

## 第一次启动前端

如果 `frontend/node_modules` 不存在，请先运行：

```bash
cd frontend
npm install
cd ..
```

## 局域网访问

本机访问：

```text
http://localhost:5173/drug-safety
```

同一局域网其他设备访问：

```text
http://本机局域网IP:5173/drug-safety
```

如果脚本检测到多个局域网地址，请优先尝试 `192.168` 开头的地址。

## 局域网访问失败排查

如果本机可以打开：

```text
http://192.168.xxx.xxx:5173/drug-safety
```

但同一局域网其他设备打不开，通常不是后端业务代码问题，可以按下面顺序检查。

### 1. Windows 防火墙拦截

建议放行：

```text
TCP 5173
TCP 8000
Node.js
Python
```

前端通过 Vite proxy 调用后端时，其他设备主要访问 `5173`，但为了调试方便也建议放行 `8000`。

### 2. 手机热点限制设备互访

部分手机热点会启用客户端隔离。即使设备连接同一个热点，也可能无法互相访问。

建议使用普通 WiFi、路由器或实验室局域网测试。

### 3. Windows 网络类型是公用网络

如果 Windows 把当前 WiFi 识别为“公用网络”，入站访问可能被拦截。

建议切换为“专用网络”，或者在防火墙里允许专用网络访问。

### 4. 使用了错误的 IP

如果启动时显示多个地址，优先使用：

```text
192.168.x.x
```

不要优先使用 WSL、Docker、VMware、Hyper-V、VPN 等虚拟网卡地址。

### 5. 端口连通性检测

在本机先测试：

```text
http://192.168.xxx.xxx:5173/drug-safety
```

另一台 Windows 电脑可以测试：

```powershell
Test-NetConnection 192.168.xxx.xxx -Port 5173
```

如果失败，说明网络或防火墙不通。

## 停止服务

在运行 `run_all.py` 的终端按：

```text
Ctrl+C
```

脚本会关闭由它启动的后端和前端子进程。
