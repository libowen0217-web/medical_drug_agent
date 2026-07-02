# LangGraph 工作流封装

## 为什么引入 LangGraph

引入 LangGraph 的目标不是替换现有业务逻辑，而是把已经稳定的本地药物安全检查流程整理成清晰的节点编排结构，方便后续扩展更多证据节点、人工复核节点或 LLM 节点。

## 当前实现定位

当前 LangGraph 版本不接真实大模型，不做推理增强，只负责确定性 Agent 工作流编排。节点内部全部复用现有模块：

- `DrugNameMapper`
- `LocalDrugQueryEngine`
- `SafetyRuleEngine`
- `DoseChecker`
- `RiskAggregator`
- `TemplateReportGenerator`
- `SafetyFilter`

## 节点说明

- `validate_input`：校验输入并提取结构化字段。
- `normalize_drugs`：做药名标准化和患者信息装配。
- `query_kg`：查询当前药物与新增药物的本地 CSV 关系。
- `rule_check`：执行确定性规则引擎。
- `dose_check`：执行本地剂量检查。
- `aggregate_risk`：汇总 KG、规则和剂量结果。
- `generate_report`：生成药师版和患者版报告。
- `safety_filter`：对报告做安全过滤并追加警告。
- `build_response`：生成统一 API-ready 响应结构。

## 状态字段

图状态保存在 `DrugSafetyGraphState` 中，包含：

- 输入字段：`input_payload`、`current_drug_inputs`、`new_drug_input`、`age`、`diseases`、`patient_factors`、`dose`
- 中间结果：`normalized_current_drugs`、`normalized_new_drug`、`patient_info`
- 查询与规则结果：`kg_pair_relations`、`kg_query_summary`、`rule_matches`、`dose_results`
- 最终业务结果：`risk_summary`、`pharmacist_report`、`patient_report`、`safety_warnings`
- 输出与错误：`response`、`error`

## 错误处理机制

- 输入校验失败或药物无法识别时，不直接崩溃，而是写入 `state["error"]`。
- 节点运行异常会转成结构化错误，并统一进入 `build_response`。
- 最终返回协议继续保持：
  - `request_id`
  - `timestamp`
  - `status`
  - `error_code`
  - `message`
  - `data`
  - `metadata`

## 如何运行

命令行：

```bash
python scripts/run_graph_case.py
python scripts/run_graph_case.py --input scripts/sample_case.json
python scripts/run_graph_case.py --input scripts/sample_case_with_dose.json
```

FastAPI：

```http
POST /api/v1/drug-safety/check?use_graph=true
```

## 当前限制

- 不接真实 LLM
- 不接 RAG
- 不接 Neo4j
- 仍然基于本地 CSV MVP

## 后续升级方向

- 增加 RAG 证据检索节点
- 增加 LLM 报告润色节点
- 增加人工复核节点
- 增加更复杂的条件分支与风险路由
