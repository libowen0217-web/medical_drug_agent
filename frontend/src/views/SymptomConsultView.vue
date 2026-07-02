<template>
  <div class="page-view">
    <PageHeader
      title="症状问诊辅助"
      subtitle="围绕红旗症状筛查、OTC 候选药生成、候选药安全检查与协作评估，帮助药师快速完成问诊辅助分析。"
    />

    <div class="page-grid">
      <SymptomConsultForm
        :drug-options="drugOptions"
        :loading-options="loadingOptions"
        :load-options-failed="loadOptionsFailed"
        :submitting="submitting"
        @submit="handleSubmit"
      />

      <div class="stack-md">
        <EmptyState
          v-if="!response"
          description="请先在左侧填写症状和患者信息，再开始症状问诊辅助分析。"
        />

        <template v-else>
          <RedFlagPanel :red-flag-triggered="redFlagTriggered" :flags="redFlags" />
          <DiseaseCandidateList
            :items="diseaseCandidates"
            :referral-required="referralRequired"
            :summary="diseaseMatchSummary"
          />

          <template v-if="!redFlagTriggered && !referralRequired">
            <OTCCandidateList :items="otcCandidates" />
            <CandidateSafetyList :items="candidateSafetyResults" />
            <DebateSummary :summary="debateSummary" />
          </template>

          <InfoCard title="问诊辅助报告">
            <ReportPanel :content="consultReport" />
          </InfoCard>

          <JsonViewer v-if="store.settings.showJson" :data="response" title="查看完整 JSON" />
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ElMessage } from 'element-plus'
import { computed, onMounted, ref } from 'vue'
import { fetchDrugOptions } from '@/api/drugOptions'
import { checkSymptomConsult } from '@/api/symptomConsult'
import EmptyState from '@/components/common/EmptyState.vue'
import InfoCard from '@/components/common/InfoCard.vue'
import JsonViewer from '@/components/common/JsonViewer.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import ReportPanel from '@/components/common/ReportPanel.vue'
import DebateSummary from '@/components/debate/DebateSummary.vue'
import CandidateSafetyList from '@/components/symptom/CandidateSafetyList.vue'
import DiseaseCandidateList from '@/components/symptom/DiseaseCandidateList.vue'
import OTCCandidateList from '@/components/symptom/OTCCandidateList.vue'
import RedFlagPanel from '@/components/symptom/RedFlagPanel.vue'
import SymptomConsultForm from '@/components/symptom/SymptomConsultForm.vue'
import { useAppStateStore } from '@/stores/appState'

const store = useAppStateStore()
const loadingOptions = ref(false)
const loadOptionsFailed = ref(false)
const submitting = ref(false)
const queryTimeoutMs = 15000

const response = computed(() => store.latestSymptomConsultResponse)
const drugOptions = computed(() => store.drugOptions)
const data = computed(() => response.value?.data || {})
const redFlagTriggered = computed(() => Boolean(response.value?.metadata?.red_flag_triggered))
const redFlags = computed(() => data.value.red_flags || [])
const diseaseCandidates = computed(() => data.value.disease_candidates || [])
const referralRequired = computed(() => Boolean(data.value.referral_required || response.value?.metadata?.referral_required))
const diseaseMatchSummary = computed(() => data.value.disease_match_summary || '')
const otcCandidates = computed(() => data.value.otc_candidates || [])
const candidateSafetyResults = computed(() => data.value.candidate_safety_results || [])
const debateSummary = computed(() => data.value.medication_debate_summary || null)
const consultReport = computed(() => data.value.consult_report || '暂无')

onMounted(async () => {
  if (!store.drugOptionsLoaded || store.drugOptions.length === 0) {
    await loadDrugOptions()
  }
})

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
  let timeoutId = null
  try {
    const timeoutPromise = new Promise((_, reject) => {
      timeoutId = window.setTimeout(() => {
        reject(new Error('请求超时'))
      }, queryTimeoutMs)
    })
    const { data } = await Promise.race([checkSymptomConsult(payload), timeoutPromise])
    store.setSymptomConsultResponse(data)
    store.cacheTemporaryUiResult(data)
    if (data.status === 'success') {
      ElMessage.success(data.message || '症状问诊辅助分析完成')
    } else {
      ElMessage.error(`${data.message || '症状问诊辅助分析失败'}${data.error_code ? ` (${data.error_code})` : ''}`)
    }
  } catch (error) {
    const message = error instanceof Error && error.message === '请求超时'
      ? '症状问诊辅助分析请求超时，请稍后重试。'
      : '请求失败：无法连接后端服务，请确认 FastAPI 已启动，并检查 API 地址设置。'
    store.setUiQueryError(message)
    ElMessage.error(message)
  } finally {
    if (timeoutId) {
      window.clearTimeout(timeoutId)
    }
    submitting.value = false
    store.endUiQuery()
  }
}
</script>
