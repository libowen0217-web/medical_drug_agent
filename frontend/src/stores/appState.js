import { defineStore } from 'pinia'
import { normalizeApiBaseUrl } from '@/api/request'

const STORAGE_KEY = 'medical-drug-agent-settings'

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

export const useAppStateStore = defineStore('appState', {
  state: () => ({
    settings: loadSettings(),
    healthStatus: null,
    knowledgeBackendStatus: null,
    latestDrugSafetyResponse: null,
    latestSymptomConsultResponse: null,
    latestDebateSummary: null,
    latestDebateResults: [],
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
    setSymptomConsultResponse(response) {
      this.latestSymptomConsultResponse = response
      const data = response?.data || {}
      this.latestDebateSummary = data.medication_debate_summary || null
      this.latestDebateResults = Array.isArray(data.debate_results) ? data.debate_results : []
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
