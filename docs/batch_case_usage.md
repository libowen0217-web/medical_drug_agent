# 批量案例库与批量运行器

## 为什么需要批量案例库

批量案例库用于把当前本地 CSV MVP 的典型场景固化下来，方便我们做演示、回归测试、规则调整后的快速验证，以及后续接入 API 或前端后的联调检查。

## 如何运行批量案例

```bash
python scripts/run_batch_cases.py --input cases/demo_cases.jsonl
```

## 如何查看风险统计

脚本运行后会在终端输出：

- 案例总数
- 成功数和错误数
- 风险等级统计
- 错误码统计
- 预期匹配率

## 如何导出完整结果

```bash
python scripts/run_batch_cases.py --input cases/demo_cases.jsonl --output outputs/batch_result.json
```

输出文件会保存每条案例的原始响应、实际风险等级、实际错误码和是否匹配预期。

## 如何配合审计日志使用

如果希望每条案例也进入审计日志，可以加上：

```bash
python scripts/run_batch_cases.py --input cases/demo_cases.jsonl --enable-audit
```

这样批量运行器内部仍然会调用 `DrugSafetyService.check_from_dict()`，并沿用现有审计日志机制。

## 当前限制

- 当前实现基于本地 CSV MVP。
- 预期风险等级依赖当前规则引擎和本地剂量参考，不是临床标准答案。
- 案例库目前主要覆盖演示和回归场景。
- 不接 Neo4j。
- 不接 RAG。
- 不接真实 LLM。
- 结果不能替代医生或药师判断。

## 后续扩展方向

- 增加更多药物组合和高风险场景。
- 增加更多疾病、年龄和患者因素维度。
- 对接自动化回归流水线，持续输出评测报告。
- 后续可无缝接入 FastAPI、前端或 LangGraph 调用链。
