# Neo4j 使用说明

## 当前角色

Neo4j 现在已经正式接入：

- 多智能体主链
- FastAPI
- Vue 正式前端

但 Neo4j 仍然只是“知识查询后端”，不会替代规则引擎、剂量检查、风险汇总或 SafetyGuard。

## 推荐配置

```env
KG_BACKEND=auto
NEO4J_URI=bolt://127.0.0.1:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=你的密码
NEO4J_DATABASE=neo4j
```

推荐默认：

```text
KG_BACKEND=auto
```

这意味着：

- Neo4j 可用时优先使用 Neo4j
- Neo4j 不可用时自动回退 CSV

## 后端状态接口

前端和后端都会使用：

```http
GET /api/v1/kg/backend-status
```

返回会包含：

- `configured_backend`
- `active_backend`
- `configured_knowledge_backend`
- `active_knowledge_backend`
- `knowledge_backend`
- `fallback_used`
- `fallback_reason`
- `neo4j_connected`
- `neo4j_version`

## 前端展示

正式 Vue 前端会显示：

- 当前实际知识图谱后端
- 是否发生 CSV 回退
- 回退原因
- Neo4j 是否已连接

设置弹窗中还可以选择：

- 自动
- CSV
- Neo4j

## 调试方式

连接测试：

```bash
python scripts/test_neo4j_connection.py
```

查询脚本：

```bash
python scripts/query_neo4j_drug.py --drug 布洛芬
python scripts/query_neo4j_drug.py --drug 布洛芬 --pair 硝苯地平
```

多智能体联调：

```bash
python scripts/run_multi_agent_case.py
```

## 真实集成测试

默认 `python -m pytest` 不依赖真实 Neo4j。

真实连接联调建议手动运行，不影响普通本地测试或 CI。
