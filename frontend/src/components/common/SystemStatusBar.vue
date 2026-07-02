<template>
  <section class="card-shell">
    <div class="card-body">
      <div class="status-header">
        <div>
          <div class="card-title">系统能力状态</div>
          <div class="card-desc">集中展示后端连接、知识图谱后端、LLM 润色和审计日志状态。</div>
        </div>
        <el-button text type="primary" @click="refreshStatus">刷新状态</el-button>
      </div>

      <div class="status-grid">
        <div class="status-tile">
          <div class="metric-label">后端状态</div>
          <el-tag :type="healthTagType" round effect="dark">{{ healthLabel }}</el-tag>
          <div class="status-note">{{ healthNote }}</div>
        </div>

        <div class="status-tile">
          <div class="metric-label">知识图谱后端</div>
          <el-tag :type="backendTagType" round>{{ backendLabel }}</el-tag>
          <div class="status-note">{{ backendNote }}</div>
        </div>

        <div class="status-tile">
          <div class="metric-label">LLM 润色</div>
          <el-tag :type="llmTagType" round>{{ llmLabel }}</el-tag>
          <div class="status-note">{{ llmNote }}</div>
        </div>

        <div class="status-tile">
          <div class="metric-label">审计日志</div>
          <el-tag :type="store.settings.enableAudit ? 'success' : 'info'" round>
            {{ store.settings.enableAudit ? '已启用' : '未启用' }}
          </el-tag>
          <div class="status-note">
            当前请求{{ store.settings.enableAudit ? '' : '不会' }}记录审计日志。
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, watch } from 'vue'
import { getHealthStatus, getKnowledgeBackendStatus } from '@/api/kgStatus'
import { backendToLabel, llmStatusToLabel } from '@/utils/formatters'
import { useAppStateStore } from '@/stores/appState'

const store = useAppStateStore()

const latestDrugMetadata = computed(() => store.latestDrugSafetyResponse?.metadata || {})
const latestMultiAgent = computed(() => latestDrugMetadata.value?.multi_agent || {})
const healthStatus = computed(() => store.healthStatus)
const backendStatus = computed(() => store.knowledgeBackendStatus)

const healthLabel = computed(() => (healthStatus.value?.connected ? '已连接' : '未连接'))
const healthTagType = computed(() => (healthStatus.value?.connected ? 'success' : 'danger'))
const healthNote = computed(() => {
  if (healthStatus.value?.connected) {
    return 'FastAPI 健康检查通过。'
  }
  return healthStatus.value?.error || '尚未获取到后端健康状态。'
})

const backendLabel = computed(() => {
  const activeBackend = backendStatus.value?.active_knowledge_backend || backendStatus.value?.active_backend
  return backendToLabel(activeBackend)
})
const backendTagType = computed(() => {
  const activeBackend = String(
    backendStatus.value?.active_knowledge_backend || backendStatus.value?.active_backend || ''
  ).toLowerCase()
  return activeBackend === 'neo4j' ? 'primary' : 'info'
})
const backendNote = computed(() => {
  const status = backendStatus.value
  if (!status) {
    return '尚未获取知识图谱后端状态。'
  }
  if (status.fallback_used) {
    return `当前已回退到 CSV，原因：${status.fallback_reason || '未提供'}`
  }
  return `配置后端：${backendToLabel(status.configured_knowledge_backend || status.configured_backend)}`
})

const llmLabel = computed(() => llmStatusToLabel(latestMultiAgent.value, store.settings.enableLlm))
const llmTagType = computed(() => {
  if (!store.settings.enableLlm) return 'info'
  if (latestMultiAgent.value?.llm_used) return 'success'
  if (latestMultiAgent.value?.llm_error) return 'warning'
  return 'primary'
})
const llmNote = computed(() => {
  const llmError = latestMultiAgent.value?.llm_error
  if (!store.settings.enableLlm) {
    return '设置中已关闭 LLM 报告润色。'
  }
  if (latestMultiAgent.value?.llm_used) {
    return '最近一次药物安全检查已使用 LLM 润色报告。'
  }
  if (llmError) {
    return `LLM 调用失败，已自动回退模板报告：${llmError}`
  }
  return '当前默认启用 LLM 润色，执行后会在此显示实际结果。'
})

async function refreshStatus() {
  try {
    const health = await getHealthStatus()
    store.setHealthStatus({
      connected: health?.status === 'ok',
      ...health,
    })
  } catch (error) {
    store.setHealthStatus({
      connected: false,
      error: '无法连接 FastAPI 后端，请确认服务已启动。',
    })
  }

  try {
    const payload = await getKnowledgeBackendStatus(store.settings.knowledgeBackend)
    if (payload?.status === 'success') {
      store.setKnowledgeBackendStatus(payload.data || null)
    } else {
      store.setKnowledgeBackendStatus(null)
    }
  } catch (error) {
    store.setKnowledgeBackendStatus(null)
  }
}

watch(
  () => [store.settings.apiBaseUrl, store.settings.knowledgeBackend],
  () => {
    refreshStatus()
  },
  { immediate: true }
)

onMounted(() => {
  refreshStatus()
})
</script>

<style scoped>
.status-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
}

.status-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
}

.status-tile {
  padding: 16px 18px;
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
  background: linear-gradient(180deg, #ffffff 0%, #f6fbff 100%);
}

.status-note {
  margin-top: 12px;
  color: var(--color-text-secondary);
  line-height: 1.6;
  font-size: 13px;
}
</style>
