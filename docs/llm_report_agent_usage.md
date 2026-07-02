# LLMReportAgent 使用说明

`LLMReportAgent` 是多 Agent 体系中的报告润色层，只负责让模板报告更自然、更适合展示，不负责医学判断。
当前系统默认启用 `LLMReportAgent`。如果 `.env` 配置正确，会自动尝试对报告进行润色；如果未配置或调用失败，系统会自动回退到模板报告。

## 系统位置

执行顺序：
1. `DrugNormalizationAgent`
2. `KGQueryAgent`
3. `RuleCheckAgent`
4. `DoseCheckAgent`
5. `RiskAggregationAgent`
6. `ReportAgent`
7. `LLMReportAgent`
8. `SafetyGuardAgent`
9. `AuditAgent`（可选）

## 医疗安全边界

- 不做诊断
- 不开处方
- 不判断“可以吃/不能吃”
- 不修改风险等级
- 不修改 `risk_findings`
- 不修改 `evidence_items`
- 不修改 `dose_results`
- 不修改 `rule_matches`
- 不编造证据

LLM 只允许润色：

- `pharmacist_report`
- `patient_report`

## 环境变量

```text
LLM_PROVIDER
LLM_API_KEY
LLM_BASE_URL
LLM_MODEL
LLM_DEBUG
```

## 使用 .env 配置大模型

在项目根目录创建 `.env`：

```env
LLM_PROVIDER=auto
LLM_API_KEY=你的真实API_KEY
LLM_BASE_URL=你的base_url
LLM_MODEL=你的模型名称
LLM_DEBUG=false
```

### 使用 OpenAI-compatible

```env
LLM_PROVIDER=openai
LLM_API_KEY=你的key
LLM_BASE_URL=https://token-plan-cn.xiaomimimo.com/v1
LLM_MODEL=你的模型名
LLM_DEBUG=false
```

### 使用 Anthropic-compatible

```env
LLM_PROVIDER=anthropic
LLM_API_KEY=你的key
LLM_BASE_URL=https://token-plan-cn.xiaomimimo.com/anthropic
LLM_MODEL=你的模型名
LLM_DEBUG=false
```

说明：

- 如果使用 `/anthropic` 地址，通常应选择 `LLM_PROVIDER=anthropic`，或使用 `LLM_PROVIDER=auto`
- 如果使用 `/v1` 地址，通常选择 `LLM_PROVIDER=openai`
- `LLM_PROVIDER=auto` 会根据 `LLM_BASE_URL` 自动判断
- 修改 `.env` 后必须重启 FastAPI 后端

## 单独测试 LLMClient

不走多 Agent 流程，直接验证 LLM 接口：

```bash
python scripts/test_llm_client.py
```

脚本会输出：

- `provider`
- `base_url`
- `model`
- `success`
- `response_preview`
- `error`

## 开启调试日志

如果需要排查 Anthropic-compatible 返回结构，可在 `.env` 中设置：

```env
LLM_DEBUG=true
```

开启后会打印脱敏调试信息，不会打印 API Key，也不会打印敏感请求头。调试输出包括：

- provider
- request url
- model
- HTTP status code
- response JSON 顶层 keys
- response body 前 1000 个字符

示例：

```text
[LLM DEBUG] provider=anthropic
[LLM DEBUG] url=https://token-plan-cn.xiaomimimo.com/anthropic/v1/messages
[LLM DEBUG] model=your-model
[LLM DEBUG] status_code=200
[LLM DEBUG] response_keys=['content', 'id', 'model']
```

## 常见错误

- API Key 错误
- Model 名称错误
- Base URL 路径错误
- 返回格式不是标准 Anthropic messages
- 服务返回 OpenAI-like `choices` 结构

当前 Anthropic 解析兼容以下格式：

1. `content: [{"type":"text","text":"..."}]`
2. `content: "..."`
3. `completion: "..."`
4. `message.content`
5. `choices[0].message.content`
6. `error.message`

如果以上都不匹配，会抛出包含 `response_keys` 的错误，方便继续定位。

对于会默认输出 `thinking` 内容的 Anthropic-compatible 服务，当前客户端会主动发送：

```json
"thinking": {"type": "disabled"}
```

这样可以减少“思考内容占满 max_tokens，导致拿不到最终 text”的情况。

## 命令行运行多智能体案例

```bash
python scripts/run_multi_agent_case.py
python scripts/run_multi_agent_case.py --enable-audit
python scripts/run_multi_agent_case.py --disable-llm
```

## FastAPI 调用

```http
POST /api/v1/drug-safety/check?use_multi_agent=true
POST /api/v1/drug-safety/check?use_multi_agent=true&enable_llm=false
```

## 默认行为

- 多智能体药物安全检查默认启用 LLM 报告润色
- LLM 只允许润色 `pharmacist_report` 和 `patient_report`
- LLM 不参与风险等级、规则命中、证据项、剂量结果的修改
- 所有 LLM 输出仍必须经过 `SafetyGuardAgent` / `SafetyFilter`

## 症状问诊链路说明

当前默认 LLM 润色主要作用于 `drug-safety` 多智能体报告。
症状问诊辅助链路目前仍以模板报告为主，没有强行改造成统一的 LLM 润色流程。

## 回退机制

以下情况会自动回退模板报告：

- 没有配置 `LLM_API_KEY`
- 没有配置 `LLM_BASE_URL`
- 没有配置 `LLM_MODEL`
- LLM HTTP 调用失败
- LLM 返回非 JSON
- LLM 返回缺少 `pharmacist_report` 或 `patient_report`
- Anthropic-compatible 返回结构无法解析

## SafetyGuardAgent 兜底

无论 LLM 是否成功，最终输出都必须再次经过 `SafetyGuardAgent` / `SafetyFilter`。
因此即使 LLM 输出了“可以吃”“完全安全”“没有风险”“放心服用”等危险表述，最终响应中也会被替换，并保留免责声明。
