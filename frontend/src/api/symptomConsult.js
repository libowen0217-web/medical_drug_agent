import request from './request'

export function checkSymptomConsult(payload) {
  return request.post('/api/v1/symptom-consult/check', payload)
}
