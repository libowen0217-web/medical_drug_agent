# Streamlit UI

这个前端页面用于演示“社区药店多智能体用药安全辅助系统”的现有能力。

## 当前前端主路径

前端默认围绕多智能体路径展示：

- 药物交互检查默认调用 `SupervisorAgent`
- 症状问诊辅助默认调用 `SymptomConsultWorkflow`
- 候选药协作辩论默认读取最近一次症状问诊结果中的
  - `medication_debate_summary`
  - `debate_results`

前端不再把 `service / graph / multi-agent` 三种后端路径并列暴露给普通用户，目的是保持页面主题清晰，突出“多智能体用药安全辅助”主线。已有后端路径仍然保留，没有删除。

## 启动方式

```bash
python scripts/run_streamlit.py
```

或：

```bash
streamlit run medical_drug_agent/ui/streamlit_app.py
```

启动后通常可访问：

- `http://localhost:8501`
- `http://127.0.0.1:8501`

## 页面结构

页面包含 4 个主 Tab：

1. `药物交互检查`
   左侧输入，右侧结果，默认走多智能体链路。

2. `症状问诊辅助`
   左侧输入，右侧输出，展示红旗症状筛查、OTC 候选药和候选药安全结果。

3. `候选药协作辩论`
   读取最近一次症状问诊结果，重点展示多 Agent 候选药协作评估。

4. `系统调试与审计`
   展示最近一次请求的 JSON、审计信息和智能体执行链路。

## 当前 UI 特点

- 顶部“设置”弹层承载高级设置，不再使用大面积侧边栏
- 所有按钮都带唯一 key，避免 `StreamlitDuplicateElementId`
- 药物选择默认从当前药库中搜索，不再要求用户完全手动输入药名
- 特殊患者因素支持合理性校验
- 页面尽量中文化展示

## 医疗安全边界

- 不做疾病诊断
- 不直接开药
- 不替代医生或药师判断
- 不把 `preferred_candidate` 解释成推荐用药
- 不输出“应该吃 / 可以吃 / 放心服用 / 完全安全”等不安全表述
- 红旗症状触发时，页面会明确阻断 OTC 候选药展示和候选药协作评估
