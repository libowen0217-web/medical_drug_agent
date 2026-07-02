# 批量案例库说明

`demo_cases.jsonl` 用于演示、回归测试和批量评测当前本地 CSV MVP 的药物安全检查流程。

## 文件格式

JSONL 采用“一行一个案例”的格式，每一行都是一个独立的 JSON 对象。

每条案例建议包含这些字段：

- `case_id`：案例唯一标识。
- `case_name`：案例名称，便于人工查看。
- `expected_risk_level`：成功案例的预期风险等级。
- `expected_status`：错误案例的预期状态，通常为 `error`。
- `expected_error_code`：错误案例的预期错误码。
- `request`：直接传给 `DrugSafetyService.check_from_dict()` 的请求体。

## 如何新增案例

1. 复制一行现有案例作为模板。
2. 修改 `case_id` 和 `case_name`。
3. 在 `request` 中填写当前用药、新增药物、年龄、疾病、患者因素和剂量。
4. 如果希望参与自动对比，补充 `expected_risk_level` 或 `expected_status` / `expected_error_code`。
5. 保存为 UTF-8 编码，保持每行一条 JSON。

## 如何运行

```bash
python scripts/run_batch_cases.py --input cases/demo_cases.jsonl
```

如需导出完整结果：

```bash
python scripts/run_batch_cases.py --input cases/demo_cases.jsonl --output outputs/batch_result.json
```
