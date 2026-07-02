import request from './request'

export function normalizeDrugOptionsResponse(res) {
  if (!res) return []

  if (Array.isArray(res?.data?.data?.options)) {
    return res.data.data.options
  }

  if (Array.isArray(res?.data?.options)) {
    return res.data.options
  }

  if (Array.isArray(res?.options)) {
    return res.options
  }

  if (Array.isArray(res)) {
    return res
  }

  return []
}

export async function fetchDrugOptions() {
  const response = await request.get('/api/v1/drugs/options')
  const options = normalizeDrugOptionsResponse(response)

  if (!Array.isArray(options) || options.length === 0) {
    console.warn('药物选项解析为空，请检查响应结构：', response)
  }

  return Array.isArray(options) ? options : []
}
