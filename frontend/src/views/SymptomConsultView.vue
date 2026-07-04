<template>
  <div class="page-view">
    <PageHeader
      title="症状问诊辅助"
      subtitle="面向药店问诊场景，辅助识别红旗症状、复核当前用药，并给出可选 OTC 药物方向。"
      disclaimer="以下内容仅用于药师问诊辅助，不构成诊断或处方建议。"
    />

    <SymptomConsultForm
      :drug-options="drugOptions"
      :loading-options="loadingOptions"
      :load-options-failed="loadOptionsFailed"
      :submitting="submitting"
      @submit="handleSubmit"
    />

    <InfoCard title="问诊辅助结果" description="根据当前症状，系统提示需要关注的情况和下一步处理建议。">
      <div v-if="!response" class="compact-empty">
        请先填写症状信息和患者信息。当前用药可留空，系统仍可生成候选 OTC 药物，并提示后续结合用药信息复核。
      </div>

      <div v-else class="result-section">
        <section class="judgement-card" :class="{ 'is-warning': redFlagTriggered || referralRequired }">
          <div class="metric-label">初步判断</div>
          <h3>{{ riskJudgementText }}</h3>
          <p>{{ initialSummary }}</p>
        </section>

        <section class="business-card">
          <h4>可能情况</h4>
          <DiseaseCandidateList
            :items="diseaseCandidates"
            :referral-required="referralRequired"
            :summary="diseaseMatchSummary"
          />
        </section>

        <section v-if="currentDrugReviewItems.length" class="business-card">
          <h4>当前用药复核</h4>
          <div class="review-list">
            <div v-for="item in currentDrugReviewItems" :key="item.name" class="review-item">
              <el-tag type="warning" round>已在使用</el-tag>
              <div>
                <strong>{{ item.name }}</strong>
                <p>患者已在使用，建议确认剂量、每日次数和连续使用天数，避免重复购买或叠加服用。</p>
              </div>
            </div>
          </div>
        </section>

        <section v-if="!redFlagTriggered && !referralRequired" class="business-card">
          <h4>可选 OTC 药物</h4>
          <div v-if="availableOtcCandidates.length" class="otc-grid">
            <div v-for="(item, index) in availableOtcCandidates" :key="index" class="otc-card">
              <div class="otc-head">
                <strong>{{ item.drug_class || '候选药物类别' }}</strong>
                <el-tag v-if="item.requires_doctor_confirmation" type="warning" round>需谨慎</el-tag>
              </div>
              <div class="candidate-drugs">{{ (item.candidate_drugs || []).join('、') }}</div>
              <p>{{ item.reason || item.caution || '请结合患者情况进一步复核。' }}</p>
            </div>
          </div>
          <div v-else class="compact-empty">当前未生成新的可选 OTC 药物；如已有用药，请优先完成当前用药复核。</div>
        </section>

        <section v-if="redFlags.length" class="business-card">
          <h4>红旗症状</h4>
          <div class="review-list">
            <div v-for="(item, index) in redFlags" :key="index" class="review-item">
              <el-tag type="danger" round>需关注</el-tag>
              <div>
                <strong>{{ item.title || item.description || '红旗症状' }}</strong>
                <p>{{ item.action || '建议由医生进一步评估。' }}</p>
              </div>
            </div>
          </div>
        </section>

        <div class="next-step-grid">
          <section class="business-card">
            <h4>药师需补充询问</h4>
            <ol class="advice-list">
              <li v-for="(item, index) in pharmacistQuestions" :key="index">{{ item }}</li>
            </ol>
          </section>

          <section class="business-card">
            <h4>用药处理建议</h4>
            <ol class="advice-list">
              <li v-for="(item, index) in handlingAdvice" :key="index">{{ item }}</li>
            </ol>
          </section>

          <section class="business-card">
            <h4>建议就医情况</h4>
            <ol class="advice-list">
              <li v-for="(item, index) in referralAdvice" :key="index">{{ item }}</li>
            </ol>
          </section>
        </div>

        <el-collapse class="advanced-collapse">
          <el-collapse-item title="高级详情" name="advanced">
            <div class="stack-sm">
              <CandidateSafetyList v-if="!redFlagTriggered && !referralRequired" :items="candidateSafetyResults" />
              <DebateSummary v-if="!redFlagTriggered && !referralRequired" :summary="debateSummary" />
              <JsonViewer :data="response" title="完整 JSON" />
            </div>
          </el-collapse-item>
        </el-collapse>
      </div>
    </InfoCard>
  </div>
</template>

<script setup>
import { ElMessage } from 'element-plus'
import { computed, onMounted, ref } from 'vue'
import { fetchDrugOptions } from '@/api/drugOptions'
import { checkSymptomConsult } from '@/api/symptomConsult'
import InfoCard from '@/components/common/InfoCard.vue'
import JsonViewer from '@/components/common/JsonViewer.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import DebateSummary from '@/components/debate/DebateSummary.vue'
import CandidateSafetyList from '@/components/symptom/CandidateSafetyList.vue'
import DiseaseCandidateList from '@/components/symptom/DiseaseCandidateList.vue'
import SymptomConsultForm from '@/components/symptom/SymptomConsultForm.vue'
import { useAppStateStore } from '@/stores/appState'

const store = useAppStateStore()
const loadingOptions = ref(false)
const loadOptionsFailed = ref(false)
const submitting = ref(false)
const lastPayload = ref(null)
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
const currentDrugNames = computed(() => buildCurrentDrugNameSet(lastPayload.value?.current_drugs || []))

const currentDrugReviewItems = computed(() => {
  const names = new Set()
  for (const item of otcCandidates.value) {
    for (const drug of item.candidate_drugs || []) {
      if (matchesCurrentDrug(drug, currentDrugNames.value)) {
        names.add(drug)
      }
    }
  }
  return [...names].map((name) => ({ name }))
})

const availableOtcCandidates = computed(() =>
  otcCandidates.value
    .map((item) => ({
      ...item,
      candidate_drugs: (item.candidate_drugs || []).filter((drug) => !matchesCurrentDrug(drug, currentDrugNames.value)),
    }))
    .filter((item) => (item.candidate_drugs || []).length > 0)
)

const riskJudgementText = computed(() => {
  if (redFlagTriggered.value || referralRequired.value) {
    return '当前描述提示需要优先排除较高风险情况'
  }
  return '当前未触发明确红旗阻断，可继续进行 OTC 用药辅助判断'
})

const initialSummary = computed(() => {
  if (redFlagTriggered.value || referralRequired.value) {
    return '建议药师先询问严重程度、持续时间和伴随症状，必要时建议顾客及时就医。'
  }
  return '根据当前症状，系统提示可结合发热、疼痛、过敏或上呼吸道症状方向进行进一步询问。'
})

const pharmacistQuestions = computed(() => [
  '症状从什么时候开始，是否持续加重或反复出现？',
  '是否伴随胸痛、呼吸困难、意识异常、咳血、剧烈腹痛等情况？',
  '近期是否已经使用退烧药、止痛药、复方感冒药或抗过敏药？',
  '是否有胃病、肝肾功能异常、妊娠、哺乳或药物过敏史？',
])

const handlingAdvice = computed(() => {
  if (redFlagTriggered.value || referralRequired.value) {
    return [
      '暂不建议直接推荐 OTC 药物，应先完成风险问诊。',
      '如症状明显或存在红旗表现，建议顾客及时就医。',
      '如顾客坚持购药，应明确提醒不能替代医生诊疗。',
    ]
  }
  return [
    '可根据主要症状选择单一成分 OTC 药物，避免重复叠加复方药。',
    '若顾客已有当前用药，应先确认剂量、频次和连续用药天数。',
    '推荐前需结合年龄、基础疾病、过敏史和特殊人群因素复核。',
  ]
})

const referralAdvice = computed(() => {
  if (redFlags.value.length) {
    return redFlags.value.map((item) => item.action || item.description || '存在需医生评估的情况，建议就医。')
  }
  return [
    '发热超过 3 天、疼痛加重或症状反复，应建议就医。',
    '出现胸痛、呼吸困难、黑便、咳血、意识异常等情况，应立即就医。',
    '儿童、老年人、孕妇或基础疾病患者症状较重时，应降低转诊阈值。',
  ]
})

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
  lastPayload.value = payload
  store.setSymptomConsultRequest(payload)
  let timeoutId = null
  try {
    const timeoutPromise = new Promise((_, reject) => {
      timeoutId = window.setTimeout(() => reject(new Error('请求超时')), queryTimeoutMs)
    })
    const { data } = await Promise.race([checkSymptomConsult(payload), timeoutPromise])
    store.setSymptomConsultResponse(data)
    store.addAuditRecord(buildSymptomConsultAuditRecord(payload, data))
    store.cacheTemporaryUiResult(data)
    if (data.status === 'success') {
      ElMessage.success(data.message || '症状问诊辅助分析完成')
    } else {
      ElMessage.error(`${data.message || '症状问诊辅助分析失败'}${data.error_code ? ` (${data.error_code})` : ''}`)
    }
  } catch (error) {
    const message =
      error instanceof Error && error.message === '请求超时'
        ? '症状问诊辅助分析请求超时，请稍后重试。'
        : '请求失败：无法连接后端服务，请确认 FastAPI 已启动，并检查 API 地址设置。'
    store.setUiQueryError(message)
    ElMessage.error(message)
  } finally {
    if (timeoutId) window.clearTimeout(timeoutId)
    submitting.value = false
    store.endUiQuery()
  }
}

function normalizeDrugText(value) {
  return String(value || '').trim().toLowerCase()
}

function buildCurrentDrugNameSet(currentDrugs) {
  const names = new Set()
  for (const drug of currentDrugs) {
    const normalized = normalizeDrugText(drug)
    if (!normalized) continue
    names.add(normalized)

    const option = store.drugOptions.find((item) => {
      const aliases = Array.isArray(item.aliases) ? item.aliases : []
      return [item.display_name, item.standard_name, item.label, item.pinyin, ...aliases]
        .filter(Boolean)
        .some((field) => normalizeDrugText(field) === normalized)
    })

    if (option) {
      const aliases = Array.isArray(option.aliases) ? option.aliases : []
      for (const field of [option.display_name, option.standard_name, option.label, option.pinyin, ...aliases]) {
        const text = normalizeDrugText(field)
        if (text) names.add(text)
      }
    }
  }
  return names
}

function matchesCurrentDrug(candidateName, currentNames) {
  const normalized = normalizeDrugText(candidateName)
  if (!normalized) return false
  if (currentNames.has(normalized)) return true
  return [...currentNames].some((name) => normalized.includes(name) || name.includes(normalized))
}

function buildSymptomConsultAuditRecord(payload, response) {
  const responseData = response?.data || {}
  const redFlag = Boolean(responseData.referral_required || response?.metadata?.red_flag_triggered)
  const riskLevel = redFlag ? 'high' : 'low'
  return {
    request_id: response?.request_id || '',
    analysis_type: 'symptom_consult',
    analysis_name: '症状问诊辅助',
    created_at: response?.timestamp || new Date().toISOString(),
    status: response?.status || 'success',
    risk_level: riskLevel,
    request: payload,
    response,
    input_summary: `症状：${payload.symptom_text || '暂无'}；体温：${payload.temperature_c ?? '暂无'}℃；持续时间：${payload.duration_days ?? '暂无'}天；年龄：${payload.age ?? '暂无'}；性别：${sexLabel(payload.sex)}；当前用药：${joinList(payload.current_drugs)}；基础疾病：${joinList(payload.diseases)}；过敏史：${joinList(payload.allergies)}`,
    output_summary: `红旗判断：${redFlag ? '需优先就医或进一步评估' : '未触发明确红旗阻断'}；候选疾病：${summarizeDiseaseCandidates(responseData.disease_candidates)}；候选 OTC 药物：${summarizeOtcCandidates(responseData.otc_candidates)}。`,
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

function summarizeDiseaseCandidates(values) {
  if (!Array.isArray(values) || values.length === 0) return '暂无'
  return values.slice(0, 3).map((item) => item.disease_name || item.name || item.label || '候选情况').join('、')
}

function summarizeOtcCandidates(values) {
  if (!Array.isArray(values) || values.length === 0) return '暂无'
  return values
    .flatMap((item) => (Array.isArray(item.candidate_drugs) ? item.candidate_drugs : []))
    .filter(Boolean)
    .slice(0, 6)
    .join('、') || '暂无'
}
</script>

<style scoped>
.judgement-card {
  padding: 16px 18px;
  border: 1px solid #bbf7d0;
  border-radius: var(--radius-md);
  background: #f0fdf4;
}

.judgement-card.is-warning {
  border-color: #fed7aa;
  background: #fff7ed;
}

.judgement-card h3 {
  margin: 4px 0 6px;
  color: var(--color-primary-dark);
  font-size: 21px;
}

.judgement-card p,
.business-card p {
  margin: 0;
  color: var(--color-text-secondary);
  line-height: 1.75;
}

.business-card {
  padding: 14px 16px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: #fff;
}

.business-card h4,
.detail-title {
  margin: 0 0 10px;
  color: var(--color-primary-dark);
  font-size: 16px;
  font-weight: 800;
}

.review-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.review-item {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  padding: 10px 12px;
  border-radius: var(--radius-md);
  background: #f8fbff;
}

.otc-grid,
.next-step-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.next-step-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.otc-card {
  padding: 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: #f8fbff;
}

.otc-head {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  align-items: center;
}

.candidate-drugs {
  margin-top: 8px;
  color: var(--color-primary-dark);
  font-weight: 800;
}

.otc-card p {
  margin-top: 8px;
}

.advice-list {
  margin: 0;
  padding-left: 20px;
  color: var(--color-text-main);
  line-height: 1.75;
}

@media (max-width: 980px) {
  .otc-grid,
  .next-step-grid {
    grid-template-columns: 1fr;
  }
}
</style>
