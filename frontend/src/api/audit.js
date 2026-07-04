import request from './request'

export async function fetchAuditRecord(identifier) {
  const encoded = encodeURIComponent(String(identifier || '').trim())
  const response = await request.get(`/api/v1/audit/records/${encoded}`)
  return response.data
}
