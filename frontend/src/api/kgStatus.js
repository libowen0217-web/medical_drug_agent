import request from './request'

export async function getHealthStatus() {
  const response = await request.get('/health')
  return response?.data || null
}

export async function getKnowledgeBackendStatus(knowledgeBackend = 'auto') {
  const response = await request.get('/api/v1/kg/backend-status', {
    params: {
      knowledge_backend: knowledgeBackend || 'auto',
    },
  })
  return response?.data || null
}
