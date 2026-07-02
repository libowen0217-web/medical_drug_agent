import request from './request'

export function checkDrugSafety(
  payload,
  { enableLlm = true, enableAudit = true, knowledgeBackend = 'auto' } = {}
) {
  return request.post('/api/v1/drug-safety/check', payload, {
    params: {
      use_multi_agent: true,
      enable_llm: enableLlm,
      enable_audit: enableAudit,
      knowledge_backend: knowledgeBackend || 'auto',
    },
  })
}
