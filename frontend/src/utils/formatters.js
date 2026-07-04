const riskLevelLabels = {
  high: '高风险',
  medium: '中风险',
  moderate: '中风险',
  low: '低风险',
  unknown: '风险待确认',
}

const riskLevelTypes = {
  high: 'danger',
  medium: 'warning',
  moderate: 'warning',
  low: 'success',
  unknown: 'info',
}

const statusLabels = {
  success: '成功',
  error: '错误',
  ok: '已连接',
}

const finalLevelLabels = {
  preferred_candidate: '相对优先',
  caution_candidate: '谨慎评估',
  not_preferred_without_review: '需复核后再考虑',
}

const agentNameLabels = {
  'symptom-fit-agent': '症状匹配 Agent',
  'interaction-risk-agent': '相互作用风险 Agent',
  'patient-factor-risk-agent': '患者因素 Agent',
  'dose-reasoning-agent': '剂量推理 Agent',
  'evidence-review-agent': '证据复核 Agent',
  'medication-debate-manager-agent': '协作评估管理 Agent',
  'drug-normalization-agent': '药名标准化 Agent',
  'kg-query-agent': '知识库查询 Agent',
  'rule-check-agent': '规则检查 Agent',
  'dose-check-agent': '剂量检查 Agent',
  'risk-aggregation-agent': '风险汇总 Agent',
  'report-agent': '模板报告 Agent',
  'llm-report-agent': 'LLM 润色 Agent',
  'safety-guard-agent': '安全过滤 Agent',
  'audit-agent': '审计 Agent',
}

const backendLabels = {
  neo4j: 'Neo4j',
  csv: '本地 CSV',
  auto: '自动选择',
}

const providerLabels = {
  anthropic: 'Anthropic 兼容接口',
  openai: 'OpenAI 兼容接口',
}

export function safeGet(obj, path, fallback = '暂无') {
  const parts = Array.isArray(path) ? path : String(path || '').split('.').filter(Boolean)
  let current = obj
  for (const part of parts) {
    if (current == null || !(part in current)) return fallback
    current = current[part]
  }
  if (current === '' || current == null) return fallback
  return current
}

export function riskLevelToLabel(level) {
  return riskLevelLabels[String(level || '').toLowerCase()] || riskLevelLabels.unknown
}

export function riskLevelToType(level) {
  return riskLevelTypes[String(level || '').toLowerCase()] || riskLevelTypes.unknown
}

export function statusToLabel(status) {
  return statusLabels[String(status || '').toLowerCase()] || '暂无'
}

export function finalLevelToLabel(level) {
  return finalLevelLabels[String(level || '').toLowerCase()] || '需进一步复核'
}

export function agentNameToLabel(name) {
  return agentNameLabels[String(name || '')] || (name || '暂无')
}

export function backendToLabel(backend) {
  return backendLabels[String(backend || '').toLowerCase()] || '暂无'
}

export function booleanToLabel(value) {
  if (value === true) return '是'
  if (value === false) return '否'
  return '暂无'
}

export function llmProviderToLabel(provider) {
  return providerLabels[String(provider || '').toLowerCase()] || (provider || '暂无')
}

export function llmStatusToLabel(metadata, enabledFallback = true) {
  const llmEnabled = metadata?.llm_enabled ?? enabledFallback
  const llmUsed = metadata?.llm_used
  const llmError = metadata?.llm_error

  if (!llmEnabled) return '未启用'
  if (llmUsed) return '已使用'
  if (llmError) return '已回退模板'
  return '已启用'
}

export function fallbackToLabel(metadata) {
  if (!metadata) return '暂无'
  if (!metadata.fallback_used) return '未回退'
  return metadata.fallback_reason ? `已回退：${metadata.fallback_reason}` : '已回退'
}

export function formatEvidenceItems(items) {
  if (!Array.isArray(items)) return []
  return items.map((item) => ({
    citationLabel: item.citation_label || '证据',
    sourceName: item.source_name || '暂无',
    evidenceText: item.evidence_text || '暂无',
    matchedReason: item.matched_reason || '暂无',
    score: item.score ?? '暂无',
    rank: item.rank ?? '暂无',
  }))
}
