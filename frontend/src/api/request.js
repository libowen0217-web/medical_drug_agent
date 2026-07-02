import axios from 'axios'

export const DEFAULT_BASE_URL = import.meta.env.VITE_API_BASE_URL || ''
const STORAGE_KEY = 'medical-drug-agent-settings'

export function normalizeApiBaseUrl(value) {
  const raw = String(value || '').trim()
  if (!raw) {
    return DEFAULT_BASE_URL
  }

  try {
    const url = new URL(raw)
    const localHostnames = new Set(['localhost', '127.0.0.1'])
    const localDevPorts = new Set(['4173', '5173', '8000'])
    if (localHostnames.has(url.hostname) && localDevPorts.has(url.port)) {
      return DEFAULT_BASE_URL
    }
    return url.origin
  } catch (error) {
    return DEFAULT_BASE_URL
  }
}

function getBaseUrl() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    const settings = raw ? JSON.parse(raw) : {}
    return normalizeApiBaseUrl(settings.apiBaseUrl)
  } catch (error) {
    return DEFAULT_BASE_URL
  }
}

const request = axios.create({
  timeout: 60000,
})

request.interceptors.request.use((config) => {
  const nextConfig = { ...config }
  nextConfig.baseURL = getBaseUrl()
  return nextConfig
})

export default request
