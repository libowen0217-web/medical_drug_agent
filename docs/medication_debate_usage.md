# 候选药协作辩论与排序模块

## 目标

这一层用于在症状问诊流程里，对已经通过基础候选筛选和本地药物安全检查的 OTC 候选药做协作式辅助评估。它不是诊断模块，也不是处方模块，只提供“当前本地规则下的相对风险排序”。

## 多 Agent 分工

- `SymptomFitAgent`：判断候选药和当前症状的匹配度，输出 high / medium / insufficient。
- `InteractionRiskAgent`：读取候选药安全检查结果，按 `overall_risk_level` 给出扣分与风险说明。
- `PatientFactorRiskAgent`：结合年龄、疾病、患者因素和过敏史做附加扣分。
- `DoseReasoningAgent`：复核是否提供剂量，以及本地规则中是否已经给出剂量风险提示。
- `EvidenceReviewAgent`：整理本地证据引用，只做辅助支持，不加“安全分”。
- `MedicationDebateManagerAgent`：汇总各 Agent 观点，输出排名与总结。

## 评分规则

- 基础分：50
- 症状匹配
  - full / high：+20
  - partial / medium：+10
  - none / insufficient：0
- 交互风险扣分
  - low：0
  - medium：-15
  - high：-35
  - unknown：-5
- 患者因素扣分
  - 年龄 >= 65 且候选药为布洛芬：-10
  - 高血压 + 布洛芬：-15
  - 胃溃疡 + 布洛芬：-20
  - 肝功能异常 + 对乙酰氨基酚：-20
  - 肾功能不全 + 布洛芬 / 二甲双胍：-20
  - 妊娠相关因素：不直接做推荐，只追加医生确认提示
- 剂量因素
  - 未提供剂量：-5
  - 中等剂量风险：-10
  - 高剂量风险：-25

## 最终等级

- `preferred_candidate`：总分 >= 70
- `caution_candidate`：45 <= 总分 < 70
- `not_preferred_without_review`：总分 < 45

这些等级只表示“当前本地规则下的相对较低风险方向”或“需要进一步复核”，不表示直接用药建议。

## 红旗症状阻断

如果 `red_flag_triggered = true`：

- 不进入候选药协作辩论
- `otc_candidates = []`
- `candidate_safety_results = []`
- `debate_results = []`
- `medication_debate_summary.red_flag_blocked = true`

此时报告只保留及时就医或医生评估提示。

## 运行方式

```bash
python scripts/run_symptom_case.py
python scripts/run_symptom_case.py --red-flag-demo
python -m pytest
```

## API 使用

症状问诊接口保持不变：

```http
POST /api/v1/symptom-consult/check
```

返回结构仍沿用统一 API-ready 协议，新增字段位于 `data` 内：

- `medication_debate_summary`
- `debate_results`

## 安全边界

- 当前版本是本地 CSV MVP，不接 Neo4j。
- 当前版本不接 RAG。
- 当前版本不接真实 LLM 参与候选药排序。
- 不输出疾病诊断结论。
- 不直接输出“可以吃 / 不能吃 / 应该吃 / 放心服用”。
- 结果仅供医生或药师辅助参考，不替代专业判断。

## 后续升级方向

- 引入更细的症状结构化评分。
- 增加更多 OTC 候选药规则。
- 增加更细粒度的患者因素规则。
- 在保持安全边界的前提下，引入可解释的 LLM 文本润色层。
