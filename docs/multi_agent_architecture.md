# 多 Agent 架构说明

## 为什么增加多 Agent 层

当前项目已经具备本地 CSV 查询、规则检查、剂量检查、风险汇总、模板报告、安全过滤、审计、FastAPI、LangGraph 等能力。  
这一步不是重写业务逻辑，而是在这些稳定模块之上增加一个清晰的多 Agent 编排层，让后续对接 FastAPI、前端、LangGraph 或人工复核时，边界更清楚、可观测性更好。

## 当前 Agent 角色

- `DrugNormalizationAgent`
  - 负责药名标准化与患者信息整理
- `KGQueryAgent`
  - 负责本地 CSV/PrimeKG 子集查询
- `RuleCheckAgent`
  - 负责调用本地安全规则引擎
- `DoseCheckAgent`
  - 负责调用本地剂量检查器
- `EvidenceAgent`
  - 负责本地证据摘要检索
  - 当前为非关键 Agent，不阻断主流程
- `RiskAggregationAgent`
  - 负责汇总规则、剂量、KG 结果，输出总体风险
- `ReportAgent`
  - 负责生成药师版与患者版模板报告
- `SafetyGuardAgent`
  - 负责报告安全过滤与免责声明补充
- `AuditAgent`
  - 负责本地审计日志记录
  - 当前为非关键 Agent，不阻断主流程

## SupervisorAgent 编排顺序

主流程如下：

1. `DrugNormalizationAgent`
2. `KGQueryAgent`
3. `RuleCheckAgent`
4. `DoseCheckAgent`
5. `RiskAggregationAgent`
6. `ReportAgent`
7. `SafetyGuardAgent`
8. 构造统一 API-ready 响应
9. `AuditAgent` 可选执行

说明：

- `EvidenceAgent` 已实现，但当前不强依赖主流程结果，因为现有 `RiskAggregator` 内部已经会复用本地 evidence 检索能力。
- 关键 Agent 失败时，`SupervisorAgent` 会返回统一错误协议。
- 非关键 Agent 失败时，会写入 `metadata.multi_agent.warnings`，但不阻断主流程。

## 与单 Service 路径的区别

单 Service 路径：

- 由 `DrugSafetyService` 直接调用 `DrugSafetyWorkflow` 完成整条流程

多 Agent 路径：

- 由 `SupervisorAgent` 显式拆分执行步骤
- 每一步都有独立 `AgentResult`
- `metadata.multi_agent` 会记录执行过哪些 Agent、哪些 Agent 失败

## 这不是“多个大模型互相讨论”

当前多 Agent 全部是确定性工具型 Agent：

- 不接真实 LLM
- 不调用外网
- 不调用 Neo4j
- 不引入新的医疗推理模型

每个 Agent 只是对既有本地模块做职责分层和流程编排。

## 医疗安全边界

- 风险等级来自本地规则、剂量检查与已有风险汇总模块
- 证据来自本地 evidence 数据层
- 报告来自模板生成器
- 安全表达来自安全过滤器
- 系统不替代医生或药师判断

## 如何运行

```bash
python scripts/run_multi_agent_case.py
python scripts/run_multi_agent_case.py --enable-audit
python scripts/run_multi_agent_case.py --input scripts/sample_case.json
```

## FastAPI 调用方式

```http
POST /api/v1/drug-safety/check?use_multi_agent=true
```

请求体示例：

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

返回仍然保持现有统一响应协议：

- `request_id`
- `timestamp`
- `status`
- `error_code`
- `message`
- `data`
- `metadata`

其中 `metadata.multi_agent` 会补充多 Agent 执行信息。

## 后续扩展方向

- `LLMReportAgent`
- `HumanReviewAgent`
- `DailyMedEvidenceAgent`
- `Neo4jKGAgent`
- `PatientQuestionAgent`
