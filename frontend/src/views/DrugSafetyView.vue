<template>
  <div class="page-view drug-safety-page">
    <PageHeader
      title="用药安全检查"
      subtitle="面向社区药店柜台场景，辅助药师判断新增用药是否合适，并生成顾客提醒话术。"
      disclaimer="本系统仅用于用药安全辅助参考，不替代医生诊疗、处方审核或药师最终判断。"
    />

    <DrugSafetyForm
      :drug-options="drugOptions"
      :loading-options="loadingOptions"
      :load-options-failed="loadOptionsFailed"
      :submitting="submitting"
      @submit="handleSubmit"
    />

    <DrugSafetyResult :response="response" />
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
    store.setKnowledgeBackendStatus(payload?.status === 'success' ? payload.data || null : null)
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
  store.setDrugSafetyRequest(payload)
  submitting.value = true
  try {
    const { data } = await checkDrugSafety(payload, {
      enableLlm: store.settings.enableLlm,
      enableAudit: store.settings.enableAudit,
      knowledgeBackend: store.settings.knowledgeBackend,
    })
    store.setDrugSafetyResponse(data)
    store.addAuditRecord(buildDrugSafetyAuditRecord(payload, data))
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
      ElMessage.success(data.message || '用药安全评估完成')
    } else {
      ElMessage.error(`${data.message || '评估失败'}${data.error_code ? ` (${data.error_code})` : ''}`)
    }
  } catch (error) {
    store.setUiQueryError('用药安全检查请求失败')
    ElMessage.error('请求失败：无法连接后端服务，请确认 FastAPI 已启动，并检查 API 地址设置。')
  } finally {
    submitting.value = false
    store.endUiQuery()
  }
}

function buildDrugSafetyAuditRecord(payload, response) {
  const responseData = response?.data || {}
  const riskFindings = Array.isArray(responseData.risk_findings) ? responseData.risk_findings : []
  const riskLevel = responseData.overall_risk_level || 'unknown'
  return {
    request_id: response?.request_id || '',
    analysis_type: 'drug_safety',
    analysis_name: '用药安全检查',
    created_at: response?.timestamp || new Date().toISOString(),
    status: response?.status || 'success',
    risk_level: riskLevel,
    request: payload,
    response,
    input_summary: `当前用药：${joinList(payload.current_drugs)}；拟新增：${payload.new_drug || '暂无'}；年龄：${payload.age ?? '暂无'}；性别：${sexLabel(payload.sex)}；基础疾病：${joinList(payload.diseases)}；过敏史：${joinList(payload.allergies)}`,
    output_summary: `综合风险：${riskLevelText(riskLevel)}；主要风险 ${riskFindings.length} 项。`,
  }
}

function joinList(values) {
  if (!Array.isArray(values) || values.length === 0) return '暂无'
  return values.filter(Boolean).join('、') || '暂无'
}

function sexLabel(value) {
  if (value === 'male' || value === '男') return '男'
  if (value === 'female' || value === '女') return '女'
  return '未知'
}

function riskLevelText(level) {
  const labels = {
    high: '高风险',
    medium: '中风险',
    moderate: '中风险',
    low: '低风险',
    unknown: '风险待确认',
  }
  return labels[String(level || '').toLowerCase()] || labels.unknown
}
</script>
