import { defineStore } from 'pinia'
import { normalizeApiBaseUrl } from '@/api/request'

const STORAGE_KEY = 'medical-drug-agent-settings'
const AUDIT_STORAGE_KEY = 'medical-drug-agent-audit-records'

const defaultSettings = {
  enableLlm: true,
  enableAudit: true,
  showJson: false,
  showAgentChain: false,
  knowledgeBackend: 'auto',
  apiBaseUrl: '',
}

const defaultUiNavigationState = {
  loading: false,
  error: '',
  temporaryResultCache: null,
}

function loadSettings() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) {
      return { ...defaultSettings }
    }
    const parsed = { ...defaultSettings, ...JSON.parse(raw) }
    parsed.apiBaseUrl = normalizeApiBaseUrl(parsed.apiBaseUrl)
    parsed.knowledgeBackend = parsed.knowledgeBackend || 'auto'
    return parsed
  } catch (error) {
    return { ...defaultSettings }
  }
}

function loadAuditRecords() {
  try {
    localStorage.removeItem('lastDrugSafetyResult')
    localStorage.removeItem('lastDrugSafetyResponse')
    localStorage.removeItem('lastSafetyAudit')
    const raw = localStorage.getItem(AUDIT_STORAGE_KEY)
    const records = raw ? JSON.parse(raw) : []
    return Array.isArray(records) ? records : []
  } catch (error) {
    return []
  }
}

function persistAuditRecords(records) {
  try {
    localStorage.setItem(AUDIT_STORAGE_KEY, JSON.stringify(records.slice(0, 50)))
  } catch (error) {
    // Local storage may be unavailable or full; the in-memory list still works.
  }
}

function recordTime(record) {
  const raw = record?.created_at || record?.timestamp || record?.generated_at || record?.response?.timestamp || ''
  const time = new Date(raw).getTime()
  return Number.isNaN(time) ? 0 : time
}

export const useAppStateStore = defineStore('appState', {
  state: () => ({
    settings: loadSettings(),
    healthStatus: null,
    knowledgeBackendStatus: null,
    latestDrugSafetyResponse: null,
    latestDrugSafetyRequest: null,
    latestSymptomConsultResponse: null,
    latestSymptomConsultRequest: null,
    latestDebateSummary: null,
    latestDebateResults: [],
    auditRecords: loadAuditRecords(),
    drugOptions: [],
    drugOptionsLoaded: false,
    uiNavigationState: { ...defaultUiNavigationState },
  }),
  actions: {
    saveSettings(partialSettings) {
      const nextSettings = { ...this.settings, ...partialSettings }
      nextSettings.apiBaseUrl = normalizeApiBaseUrl(nextSettings.apiBaseUrl)
      nextSettings.knowledgeBackend = nextSettings.knowledgeBackend || 'auto'
      this.settings = nextSettings
      localStorage.setItem(STORAGE_KEY, JSON.stringify(this.settings))
    },
    setHealthStatus(status) {
      this.healthStatus = status || null
    },
    setKnowledgeBackendStatus(status) {
      this.knowledgeBackendStatus = status || null
    },
    setDrugSafetyResponse(response) {
      this.latestDrugSafetyResponse = response
    },
    setDrugSafetyRequest(request) {
      this.latestDrugSafetyRequest = request || null
    },
    setSymptomConsultResponse(response) {
      this.latestSymptomConsultResponse = response
      const data = response?.data || {}
      this.latestDebateSummary = data.medication_debate_summary || null
      this.latestDebateResults = Array.isArray(data.debate_results) ? data.debate_results : []
    },
    setSymptomConsultRequest(request) {
      this.latestSymptomConsultRequest = request || null
    },
    addAuditRecord(record) {
      const nextRecord = {
        ...record,
        created_at: record?.created_at || record?.timestamp || new Date().toISOString(),
      }
      const filtered = this.auditRecords.filter((item) => {
        const requestId = nextRecord.request_id || nextRecord.response?.request_id
        if (!requestId) return true
        return (item.request_id || item.response?.request_id) !== requestId
      })
      this.auditRecords = [nextRecord, ...filtered]
        .sort((a, b) => recordTime(b) - recordTime(a))
        .slice(0, 50)
      persistAuditRecords(this.auditRecords)
    },
    setDrugOptions(options) {
      this.drugOptions = Array.isArray(options) ? options : []
      this.drugOptionsLoaded = true
    },
    resetUiNavigationState() {
      this.uiNavigationState = {
        ...defaultUiNavigationState,
      }
    },
    beginUiQuery() {
      this.uiNavigationState = {
        loading: true,
        error: '',
        temporaryResultCache: null,
      }
    },
    endUiQuery() {
      this.resetUiNavigationState()
    },
    setUiQueryError(message) {
      this.uiNavigationState = {
        loading: false,
        error: message || '',
        temporaryResultCache: null,
      }
    },
    cacheTemporaryUiResult(result) {
      this.uiNavigationState = {
        ...this.uiNavigationState,
        temporaryResultCache: result || null,
      }
    },
    resetSymptomConsultState() {
      this.resetUiNavigationState()
    },
  },
})
