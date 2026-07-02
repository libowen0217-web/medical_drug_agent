<template>
  <div class="page-view">
    <PageHeader
      title="用药安全检查"
      subtitle="围绕药物输入、多智能体协作、Neo4j / CSV 知识图谱查询、规则与剂量检查、证据引用、LLM 润色和安全过滤，完整展示药物安全检查主线。"
    />

    <div class="page-grid">
      <DrugSafetyForm
        :drug-options="drugOptions"
        :loading-options="loadingOptions"
        :load-options-failed="loadOptionsFailed"
        :submitting="submitting"
        @submit="handleSubmit"
      />

      <DrugSafetyResult
        :response="response"
        :show-json="store.settings.showJson"
        :show-agent-chain="store.settings.showAgentChain"
      />
    </div>
  </div>
</template>

<script setup>
import { ElMessage } from 'element-plus'
import { computed, onMounted, ref } from 'vue'
import { fetchDrugOptions } from '@/api/drugOptions'
import { checkDrugSafety } from '@/api/drugSafety'
import { getKnowledgeBackendStatus } from '@/api/kgStatus'
import PageHeader from '@/components/common/PageHeader.vue'
import DrugSafetyForm from '@/components/drug/DrugSafetyForm.vue'
import DrugSafetyResult from '@/components/drug/DrugSafetyResult.vue'
import { useAppStateStore } from '@/stores/appState'

const store = useAppStateStore()
const loadingOptions = ref(false)
const loadOptionsFailed = ref(false)
const submitting = ref(false)

const response = computed(() => store.latestDrugSafetyResponse)
const drugOptions = computed(() => store.drugOptions)

onMounted(async () => {
  await refreshKnowledgeBackendStatus()
  if (!store.drugOptionsLoaded || store.drugOptions.length === 0) {
    await loadDrugOptions()
  }
})

async function refreshKnowledgeBackendStatus() {
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

async function loadDrugOptions() {
  loadingOptions.value = true
  loadOptionsFailed.value = false
  try {
    const options = await fetchDrugOptions()
    if (options.length > 0) {
      store.setDrugOptions(options)
    } else {
      loadOptionsFailed.value = true
      store.setDrugOptions([])
      ElMessage.error('药物选项为空，请检查 drug_name_map.csv 或 /api/v1/drugs/options 接口返回。')
    }
  } catch (error) {
    loadOptionsFailed.value = true
    store.setDrugOptions([])
    ElMessage.error('药物选项加载失败，请确认 FastAPI 后端已启动。')
  } finally {
    loadingOptions.value = false
  }
}

async function handleSubmit(payload) {
  store.beginUiQuery()
  submitting.value = true
  try {
    const { data } = await checkDrugSafety(payload, {
      enableLlm: store.settings.enableLlm,
      enableAudit: store.settings.enableAudit,
      knowledgeBackend: store.settings.knowledgeBackend,
    })
    store.setDrugSafetyResponse(data)
    store.cacheTemporaryUiResult(data)

    if (data?.metadata) {
      store.setKnowledgeBackendStatus({
        configured_knowledge_backend: data.metadata.configured_knowledge_backend,
        active_knowledge_backend: data.metadata.active_knowledge_backend,
        knowledge_backend: data.metadata.knowledge_backend,
        fallback_used: data.metadata.fallback_used,
        fallback_reason: data.metadata.fallback_reason,
      })
    }

    if (data.status === 'success') {
      ElMessage.success(data.message || '检查完成')
    } else {
      ElMessage.error(`${data.message || '检查失败'}${data.error_code ? ` (${data.error_code})` : ''}`)
    }
  } catch (error) {
    store.setUiQueryError('用药安全检查请求失败')
    ElMessage.error('请求失败：无法连接后端服务，请确认 FastAPI 已启动，并检查 API 地址设置。')
  } finally {
    submitting.value = false
    store.endUiQuery()
  }
}
</script>
