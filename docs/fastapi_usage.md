# FastAPI 使用说明

## 安装依赖

```bash
python -m pip install -r requirements.txt
```

## 启动 API 服务

```bash
python scripts/run_api.py
```

后端监听：

```text
http://0.0.0.0:8000
```

本机访问 Swagger：

```text
http://127.0.0.1:8000/docs
```

局域网访问 Swagger：

```text
http://你的局域网IP:8000/docs
```

## 健康检查

```http
GET /health
```

响应示例：

```json
{
  "status": "ok",
  "service": "medical-drug-agent",
  "engine_version": "local-csv-mvp-v1"
}
```

## 版本接口

```http
GET /api/v1/version
```

响应示例：

```json
{
  "service": "medical-drug-agent",
  "api_version": "v1",
  "engine_version": "local-csv-mvp-v1",
  "mode": "local-csv-mvp"
}
```

## 药物安全检查

```http
POST /api/v1/drug-safety/check
Content-Type: application/json
```

请求示例：

```json
{
  "current_drugs": ["硝苯地平"],
  "new_drug": "布洛芬",
  "age": 68,
  "diseases": ["高血压"],
  "patient_factors": [],
  "dose": null
}
```

## 前端代理

Vue 开发服务器默认把以下路径代理到 FastAPI：

```text
/api -> http://127.0.0.1:8000
/health -> http://127.0.0.1:8000
```

浏览器请求保持同源相对路径，因此局域网用户访问前端时不会请求自己电脑上的 `localhost`。
