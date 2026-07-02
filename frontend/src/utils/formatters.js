const riskLevelLabels = {
  high: '高风险',
  medium: '中等风险',
  low: '低风险',
  unknown: '风险待确认',
}

const riskLevelTypes = {
  high: 'danger',
  medium: 'warning',
  low: 'success',
  unknown: 'info',
}

const statusLabels = {
  success: '成功',
  error: '错误',
  ok: '已连接',
}

const finalLevelLabels = {
  preferred_candidate: '当前规则下风险提示相对较少的候选项',
  caution_candidate: '需要谨慎评估的候选项',
  not_preferred_without_review: '未复核前不宜优先考虑',
}

const agentNameLabels = {
  'symptom-fit-agent': '症状匹配智能体',
  'interaction-risk-agent': '交互风险智能体',
  'patient-factor-risk-agent': '患者因素智能体',
  'dose-reasoning-agent': '剂量推理智能体',
  'evidence-review-agent': '证据复核智能体',
  'medication-debate-manager-agent': '候选药协作管理智能体',
  'drug-normalization-agent': '药名标准化智能体',
  'kg-query-agent': '知识图谱查询智能体',
  'rule-check-agent': '规则检查智能体',
  'dose-check-agent': '剂量检查智能体',
  'risk-aggregation-agent': '风险汇总智能体',
  'report-agent': '模板报告智能体',
  'llm-report-agent': 'LLM 润色智能体',
  'safety-guard-agent': '安全过滤智能体',
  'audit-agent': '审计智能体',
}

const backendLabels = {
  neo4j: 'Neo4j',
  csv: '本地 CSV',
  auto: '自动',
}

const providerLabels = {
  anthropic: 'Anthropic 兼容接口',
  openai: 'OpenAI 兼容接口',
}

export function safeGet(obj, path, fallback = '暂无') {
  const parts = Array.isArray(path) ? path : String(path || '').split('.').filter(Boolean)
  let current = obj
  for (const part of parts) {
    if (current == null || !(part in current)) {
      return fallback
    }
    current = current[part]
  }
  if (current === '' || current == null) {
    return fallback
  }
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
  return finalLevelLabels[String(level || '').toLowerCase()] || '需要进一步复核'
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
  if (!Array.isArray(items)) {
    return []
  }
  return items.map((item) => ({
    citationLabel: item.citation_label || '证据',
    sourceName: item.source_name || '暂无',
    evidenceText: item.evidence_text || '暂无',
    matchedReason: item.matched_reason || '暂无',
    score: item.score ?? '暂无',
    rank: item.rank ?? '暂无',
  }))
}
