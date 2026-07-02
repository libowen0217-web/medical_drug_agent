# Audit Log Usage

## 1. 为什么医疗安全检查需要审计日志

审计日志有助于记录每次检查请求、查看返回结果、复现历史场景，并为后续演示、调试和合规说明提供基础证据。

## 2. 当前审计日志记录什么

- 请求摘要：当前药物、新增药物、年龄、疾病、患者因素、是否提供剂量
- 统一响应摘要：状态、错误码、综合风险等级、风险条目数量、安全警告数量
- 完整统一响应结构
- request_id、audit_id、timestamp、engine_version

## 3. 当前审计日志不记录什么

- 不记录姓名
- 不记录手机号
- 不记录身份证号
- 不记录其他敏感身份信息

## 4. 如何启动 FastAPI 并产生审计日志

```bash
python scripts/run_api.py
```

然后调用：

```http
POST /api/v1/drug-safety/check
```

FastAPI 路由默认开启审计。

## 5. 如何查看最近日志

```bash
python scripts/show_audit_logs.py --limit 5
```

## 6. 如何根据 audit_id 回放请求

```bash
python scripts/replay_audit_case.py --audit-id <audit_id>
```

也可以：

```bash
python scripts/replay_audit_case.py --request-id <request_id>
```

## 7. 当前限制

- 本地 JSONL 文件，不是正式数据库
- 未做用户身份系统
- 未做日志加密
- 不适合作为生产医疗合规系统

## 8. 后续可升级

- SQLite / PostgreSQL 审计表
- 日志加密
- 用户权限
- 操作员 ID
- 完整证据链版本号

