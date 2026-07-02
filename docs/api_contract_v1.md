# API Contract V1

## 1. 接口定位

本接口是“社区药店药物交互检查 Agent”的本地 MVP 结构化接口层，用于接收 JSON 输入并返回统一 JSON 响应。

## 2. 当前不是正式医疗诊断接口

本接口仅用于本地规则检查、CSV 查询、剂量参考检查和模板报告生成。
它不是医疗诊断系统，不替代医生和药师判断。

## 3. 请求 JSON 示例

```json
{
  "current_drugs": ["硝苯地平"],
  "new_drug": "布洛芬",
  "age": 68,
  "diseases": ["高血压"],
  "patient_factors": [],
  "dose": {
    "single_dose_mg": 400,
    "times_per_day": 3,
    "duration_days": 5
  }
}
```

## 4. 成功响应 JSON 示例

```json
{
  "request_id": "c8d2c2d0-8f4f-4f3a-8a73-95f8a75e0e16",
  "timestamp": "2026-06-16T15:00:00+00:00",
  "status": "success",
  "error_code": null,
  "message": "检查完成",
  "data": {
    "overall_risk_level": "medium",
    "normalized_current_drugs": [],
    "normalized_new_drug": {},
    "risk_findings": [],
    "pharmacist_report": "",
    "patient_report": "",
    "safety_warnings": []
  },
  "metadata": {
    "engine_version": "local-csv-mvp-v1",
    "current_drug_count": 1,
    "disease_count": 1,
    "risk_finding_count": 0,
    "safety_warning_count": 0,
    "has_dose_input": true
  }
}
```

## 5. 错误响应 JSON 示例

```json
{
  "request_id": "2d566e58-1717-46d5-9d64-fb7cfba0ed5e",
  "timestamp": "2026-06-16T15:00:00+00:00",
  "status": "error",
  "error_code": "INVALID_INPUT",
  "message": "current_drugs 不能为空",
  "data": null,
  "metadata": {
    "engine_version": "local-csv-mvp-v1"
  }
}
```

## 6. 字段说明

- `request_id`: 每次响应自动生成的唯一标识。
- `timestamp`: ISO 格式时间戳。
- `status`: `success` 或 `error`。
- `error_code`: 错误码，成功时为 `null`。
- `message`: 成功或错误说明。
- `data`: 成功时的业务结果，错误时为 `null`。
- `metadata`: 调试和统计辅助字段。

## 7. error_code 说明

- `INVALID_INPUT`: 输入缺失、类型错误或值不合法。
- `UNKNOWN_DRUG`: 药物无法识别，映射表中不存在。
- `DATA_FILE_MISSING`: 本地 CSV 或规则文件缺失。
- `WORKFLOW_ERROR`: 工作流执行期间发生未预期错误。
- `JSON_PARSE_ERROR`: 输入 JSON 文件格式错误。

## 8. 当前 MVP 限制

- 不接 Neo4j
- 不接 RAG
- 不接真实 LLM
- 不替代医生和药师判断

## 9. 后续可接 FastAPI

当前响应结构已经适合作为 FastAPI、前端或 LangGraph 的统一协议层，后续可直接将 `DrugSafetyService.check_from_dict()` 暴露为接口处理函数。
