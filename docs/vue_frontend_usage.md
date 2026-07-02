# Vue 正式前端使用说明

## 访问入口

推荐直接一键启动：

```bash
python scripts/run_all.py
```

访问：

```text
http://localhost:5173/drug-safety
```

也可以分别启动：

```bash
python scripts/run_api.py
cd frontend
npm run dev
```

## 当前前端主线

正式前端现在围绕这条项目主线展示：

```text
药物输入
→ 多智能体协作
→ Neo4j / CSV 知识图谱查询
→ 规则引擎与剂量检查
→ Evidence 证据引用
→ LLM 报告润色
→ SafetyGuard 安全过滤
→ 药师版 / 患者版报告
```

## 页面导航

左侧保留四个模块：

- 用药安全检查
- 症状问诊辅助
- 候选药协作评估
- 系统调试与审计

默认进入：

```text
/drug-safety
```

## 顶部系统能力状态

页面顶部会显示：

- 后端状态：已连接 / 未连接
- 知识图谱后端：Neo4j / 本地 CSV / 自动回退状态
- LLM 润色：已启用 / 已使用 / 已回退模板 / 未启用
- 审计日志：已启用 / 未启用

依赖接口：

```http
GET /health
GET /api/v1/kg/backend-status
```

## 设置弹窗

右上角“设置”支持：

- API 地址
- 知识图谱后端：`auto / csv / neo4j`
- 启用 LLM 报告润色
- 启用审计日志
- 显示完整 JSON
- 显示 Agent 执行链路

推荐默认：

```text
knowledge_backend=auto
```

如果 Neo4j 不可用，系统会自动回退 CSV，前端会显示回退原因。

## 用药安全检查页

结果区重点展示：

- 综合风险等级
- 知识图谱后端状态
- LLM 润色状态
- 多智能体执行链路
- 风险发现列表
- 证据引用列表
- 药师版报告
- 患者版报告
- 完整 JSON

说明：

- 前端只调用 FastAPI
- 前端不直接读取 CSV
- 前端不直接连接 Neo4j
- 所有用户可见状态尽量中文化

## 症状问诊辅助页

会展示：

- 红旗症状筛查
- OTC 候选药生成
- 候选药安全检查
- 候选药协作辩论摘要
- 问诊辅助报告

如果红旗症状触发，页面会明确提示阻断 OTC 和候选药协作评估。

## 候选药协作评估页

该页面读取最近一次症状问诊结果。

如果还没有问诊结果，会显示提示先去完成一次症状分析。

候选药排序采用安全表达，不会显示：

- 推荐药物
- 最适合
- 最安全

## 系统调试与审计页

可查看：

- API 地址
- 后端健康状态
- 知识图谱后端状态
- Neo4j 连接状态
- LLM 状态
- 最近一次药物安全检查 JSON
- 最近一次症状问诊 JSON

## LLM 默认行为

- 当前默认启用 `LLMReportAgent`
- LLM 只润色 `pharmacist_report` 和 `patient_report`
- LLM 不修改风险等级、风险发现、证据项和剂量结果
- 如果调用失败，会自动回退模板报告

## Neo4j 与 CSV

- 前端设置中可以切换 `auto / csv / neo4j`
- 推荐默认 `auto`
- 如果 Neo4j 不可用，系统自动回退 CSV
- 页面会显示当前实际后端与回退原因
