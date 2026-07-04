<template>
  <div class="page-view audit-page">
    <PageHeader
      title="审计追溯中心"
      subtitle="输入请求编号或审计编号，回溯当次问诊、用药检查或候选药评估的完整辅助建议。"
      disclaimer="本系统仅用于药师或医生的用药安全辅助参考，不构成诊断、处方或最终用药建议。"
    />

    <InfoCard title="审计记录查询" description="可查询当前会话最近记录，或读取已启用审计日志的本地历史记录。">
      <div class="query-row">
        <el-input
          v-model="queryText"
          clearable
          placeholder="请输入请求编号 / 审计编号"
          @keyup.enter="handleQuery"
        />
        <el-button type="primary" :loading="querying" @click="handleQuery">查询审计记录</el-button>
        <el-button @click="showLatestRecord">查看最近一次记录</el-button>
      </div>
      <div v-if="queryMessage" class="query-message">{{ queryMessage }}</div>
    </InfoCard>

    <InfoCard title="最近一次分析记录">
      <div v-if="latestRecord" class="latest-card">
        <div class="latest-main">
          <div class="latest-title">{{ latestRecord.analysisLabel }}</div>
          <div class="latest-desc">{{ latestRecord.primaryInput }}</div>
          <div class="latest-output">{{ latestRecord.primaryOutput }}</div>
          <div class="latest-time">{{ latestRecord.displayTime }}</div>
        </div>
        <div class="latest-side">
          <el-tag :type="riskTagType(latestRecord.riskLevel)" round>{{ riskLevelToLabel(latestRecord.riskLevel) }}</el-tag>
          <el-button type="primary" plain @click="selectRecord(latestRecord)">查看详情</el-button>
        </div>
      </div>
      <div v-else class="compact-empty">暂无分析记录。完成一次用药安全检查、症状问诊或候选药协作评估后，这里会显示可追溯摘要。</div>
    </InfoCard>

    <template v-if="selectedRecord">
      <InfoCard title="记录概览">
        <div class="overview-grid">
          <div class="overview-tile request-tile">
            <div class="metric-label">请求编号</div>
            <div class="overview-value">{{ selectedRecord.requestId || '暂无' }}</div>
          </div>
          <div class="overview-tile">
            <div class="metric-label">生成时间</div>
            <div class="overview-value">{{ selectedRecord.displayTime }}</div>
          </div>
          <div class="overview-tile">
            <div class="metric-label">分析类型</div>
            <div class="overview-value">{{ selectedRecord.analysisLabel }}</div>
          </div>
        </div>
      </InfoCard>

      <div class="audit-grid">
        <InfoCard title="当时输入信息">
          <div class="trace-list">
            <div v-for="item in selectedRecord.inputItems" :key="item.label" class="trace-row">
              <span class="trace-label">{{ item.label }}</span>
              <span class="trace-value">{{ item.value }}</span>
            </div>
          </div>
        </InfoCard>

        <InfoCard title="当时系统输出">
          <div class="trace-list">
            <div v-for="item in selectedRecord.outputItems" :key="item.label" class="trace-row">
              <span class="trace-label">{{ item.label }}</span>
              <span class="trace-value">{{ item.value }}</span>
            </div>
          </div>
        </InfoCard>
      </div>

      <InfoCard title="详细依据">
        <el-collapse class="advanced-collapse">
          <el-collapse-item title="证据来源、规则命中、药物关系和剂量依据" name="basis">
            <JsonViewer :data="selectedRecord.businessBasis" />
          </el-collapse-item>
        </el-collapse>
      </InfoCard>

      <InfoCard title="系统技术详情">
        <el-collapse class="advanced-collapse">
          <el-collapse-item title="运行状态与配置" name="status">
            <div class="metric-grid">
              <div class="metric-tile">
                <div class="metric-label">后端服务</div>
                <div class="metric-value">{{ healthStatus?.connected ? '已连接' : '待确认' }}</div>
              </div>
              <div class="metric-tile">
                <div class="metric-label">知识图谱后端</div>
                <div class="metric-value">{{ activeKnowledgeBackend }}</div>
              </div>
              <div class="metric-tile">
                <div class="metric-label">LLM 润色</div>
                <div class="metric-value">{{ selectedRecord.llmStatus }}</div>
              </div>
              <div class="metric-tile">
                <div class="metric-label">审计日志</div>
                <div class="metric-value">{{ store.settings.enableAudit ? '已启用' : '未启用' }}</div>
              </div>
            </div>
          </el-collapse-item>

          <el-collapse-item title="Agent 执行链路" name="agents">
            <div class="stack-sm">
              <div><strong>执行 Agent：</strong>{{ selectedRecord.agentChain }}</div>
              <div><strong>知识后端详情：</strong></div>
              <JsonViewer :data="knowledgeBackendStatus || {}" />
            </div>
          </el-collapse-item>

          <el-collapse-item title="原始 JSON" name="json">
            <JsonViewer :data="selectedRecord.raw" />
          </el-collapse-item>
        </el-collapse>
      </InfoCard>
    </template>
  </div>
</template>

<script setup>
import { ElMessage } from 'element-plus'
import { computed, ref } from 'vue'
import { fetchAuditRecord } from '@/api/audit'
import InfoCard from '@/components/common/InfoCard.vue'
import JsonViewer from '@/components/common/JsonViewer.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import {
  agentNameToLabel,
  backendToLabel,
  formatEvidenceItems,
  llmStatusToLabel,
  riskLevelToLabel,
  riskLevelToType,
} from '@/utils/formatters'
import { useAppStateStore } from '@/stores/appState'

const store = useAppStateStore()
const queryText = ref('')
const queryMessage = ref('')
const querying = ref(false)
const selectedRecord = ref(null)

const healthStatus = computed(() => store.healthStatus)
const knowledgeBackendStatus = computed(() => store.knowledgeBackendStatus)

const localRecords = computed(() => {
  const unifiedRecords = Array.isArray(store.auditRecords) ? store.auditRecords : []
  if (unifiedRecords.length > 0) {
    return unifiedRecords
      .map((record) => normalizeRecord(record))
      .filter(Boolean)
      .sort((a, b) => timestampMs(b) - timestampMs(a))
  }

  const records = []
  if (store.latestDrugSafetyResponse) {
    records.push(normalizeRecord({
      type: 'drug_safety',
      request: store.latestDrugSafetyRequest || {},
      response: store.latestDrugSafetyResponse,
      source: 'current_session',
    }))
  }
  if (store.latestSymptomConsultResponse) {
    records.push(normalizeRecord({
      type: 'symptom_consult',
      request: store.latestSymptomConsultRequest || {},
      response: store.latestSymptomConsultResponse,
      source: 'current_session',
    }))
  }
  if ((store.latestDebateResults || []).length || store.latestDebateSummary) {
    records.push(normalizeRecord({
      type: 'medication_debate',
      request: store.latestSymptomConsultRequest || {},
      response: {
        request_id: 'current-session-debate',
        timestamp: store.latestSymptomConsultResponse?.timestamp || '',
        status: 'success',
        data: {
          medication_debate_summary: store.latestDebateSummary,
          debate_results: store.latestDebateResults || [],
        },
        metadata: store.latestSymptomConsultResponse?.metadata || {},
      },
      source: 'current_session',
    }))
  }
  return records
    .filter(Boolean)
    .sort((a, b) => timestampMs(b) - timestampMs(a))
})

const latestRecord = computed(() => localRecords.value[0] || null)

const activeKnowledgeBackend = computed(() =>
  backendToLabel(
    knowledgeBackendStatus.value?.active_knowledge_backend ||
      knowledgeBackendStatus.value?.active_backend ||
      selectedRecord.value?.response?.metadata?.active_knowledge_backend
  )
)

function selectRecord(record) {
  selectedRecord.value = record
  queryText.value = record.requestId || record.auditId || ''
  queryMessage.value = ''
}

function showLatestRecord() {
  if (!latestRecord.value) {
    ElMessage.warning('当前会话暂无最近一次分析记录。')
    return
  }
  selectRecord(latestRecord.value)
}

async function handleQuery() {
  const query = String(queryText.value || '').trim()
  if (!query) {
    ElMessage.warning('请输入请求编号或审计编号。')
    return
  }

  const localRecord = findLocalRecord(query)
  if (localRecord) {
    selectedRecord.value = localRecord
    queryMessage.value = '已从当前会话记录中找到对应分析。'
    return
  }

  querying.value = true
  queryMessage.value = ''
  try {
    const payload = await fetchAuditRecord(query)
    if (payload?.status === 'success' && payload?.data?.record) {
      selectedRecord.value = normalizeRecord(payload.data.record)
      queryMessage.value = '已从本地审计日志中找到对应记录。'
    } else {
      selectedRecord.value = null
      queryMessage.value = payload?.message || '未找到对应的审计记录。'
      ElMessage.warning(queryMessage.value)
    }
  } catch (error) {
    selectedRecord.value = null
    queryMessage.value = '审计记录查询失败，请确认后端服务已启动且审计日志可读取。'
    ElMessage.error(queryMessage.value)
  } finally {
    querying.value = false
  }
}

function findLocalRecord(query) {
  return localRecords.value.find((record) => {
    const values = [record.requestId, record.auditId].filter(Boolean)
    return values.some((value) => String(value) === query)
  })
}

function normalizeRecord(record) {
  const response = record.response || {}
  const request = record.request || {}
  const type = record.analysis_type || record.type || inferAnalysisType(response)
  const data = response.data || {}
  const metadata = response.metadata || {}
  const riskLevel = record.risk_level || data.overall_risk_level || record.response_summary?.overall_risk_level || inferRiskLevel(type, data)
  const audit = metadata.audit || {}
  const rawTimestamp = record.created_at || record.generated_at || record.timestamp || response.timestamp || ''
  const normalized = {
    type,
    request,
    response,
    raw: record,
    requestId: record.request_id || response.request_id || '',
    auditId: record.audit_id || audit.audit_id || '',
    timestamp: rawTimestamp,
    displayTime: formatBeijingTime(rawTimestamp),
    status: response.status || record.response_summary?.status || 'success',
    riskLevel,
    analysisLabel: record.analysis_name || analysisTypeLabel(type),
    llmStatus: llmStatusToLabel(metadata.multi_agent, store.settings.enableLlm),
    agentChain: buildAgentChain(metadata, type),
    businessBasis: buildBusinessBasis(type, data, metadata),
  }

  normalized.primaryInput = record.input_summary || buildPrimaryInput(type, request)
  normalized.primaryOutput = record.output_summary || buildPrimaryOutput(type, data, riskLevel)
  normalized.inputItems = buildInputItems(type, request)
  normalized.outputItems = buildOutputItems(type, data, riskLevel)
  return normalized
}

function timestampMs(record) {
  const raw =
    record?.timestamp ||
    record?.raw?.created_at ||
    record?.raw?.generated_at ||
    record?.raw?.timestamp ||
    record?.response?.timestamp ||
    ''
  const time = new Date(raw).getTime()
  return Number.isNaN(time) ? 0 : time
}

function inferAnalysisType(response) {
  const data = response?.data || {}
  if (Array.isArray(data.debate_results) || data.medication_debate_summary) return 'medication_debate'
  if (Array.isArray(data.disease_candidates) || Array.isArray(data.otc_candidates)) return 'symptom_consult'
  return 'drug_safety'
}

function analysisTypeLabel(type) {
  const labels = {
    drug_safety: '用药安全检查',
    symptom_consult: '症状问诊辅助',
    medication_debate: '候选药协作评估',
  }
  return labels[type] || '辅助分析'
}

function inferRiskLevel(type, data) {
  if (type === 'symptom_consult') return data.referral_required ? 'high' : 'low'
  if (type === 'medication_debate') return 'medium'
  return 'unknown'
}

function buildPrimaryInput(type, request) {
  if (type === 'drug_safety') {
    return `当前用药：${joinList(request.current_drugs)}；拟新增：${request.new_drug || '暂无'}`
  }
  if (type === 'symptom_consult') {
    return `症状：${request.symptom_text || '暂无'}；当前用药：${joinList(request.current_drugs)}`
  }
  return '基于最近一次症状问诊的候选药协作评估。'
}

function buildPrimaryOutput(type, data, riskLevel) {
  if (type === 'drug_safety') {
    const count = Array.isArray(data.risk_findings) ? data.risk_findings.length : 0
    return `综合风险：${riskLevelToLabel(riskLevel)}；主要风险 ${count} 项。`
  }
  if (type === 'symptom_consult') {
    return data.referral_required ? '提示存在需优先就医或进一步评估的情况。' : '未触发明确红旗阻断，可查看候选 OTC 药物方向。'
  }
  return data.medication_debate_summary?.conclusion || '已生成候选药排序和协作意见。'
}

function buildInputItems(type, request) {
  if (type === 'drug_safety') {
    return [
      item('当前用药', joinList(request.current_drugs)),
      item('拟新增药物', request.new_drug),
      item('年龄', request.age),
      item('性别', sexLabel(request.sex)),
      item('基础疾病', joinList(request.diseases)),
      item('过敏史', joinList(request.allergies)),
      item('剂量方式', request.dose?.dose_mode === 'user_input' ? '手动填写剂量' : '说明书参考剂量'),
    ]
  }
  return [
    item('症状描述', request.symptom_text),
    item('体温', request.temperature_c ? `${request.temperature_c}℃` : ''),
    item('持续时间', request.duration_days != null ? `${request.duration_days}天` : ''),
    item('年龄', request.age),
    item('性别', sexLabel(request.sex)),
    item('当前用药', joinList(request.current_drugs)),
    item('基础疾病', joinList(request.diseases)),
    item('过敏史', joinList(request.allergies)),
  ]
}

function buildOutputItems(type, data, riskLevel) {
  if (type === 'drug_safety') {
    return [
      item('综合风险等级', riskLevelToLabel(riskLevel)),
      item('主要风险提示', summarizeRiskFindings(data.risk_findings)),
      item('评估结果', data.pharmacist_report ? '已生成药师辅助报告' : '暂无药师报告'),
    ]
  }
  if (type === 'symptom_consult') {
    return [
      item('初步判断', data.referral_required ? '建议优先就医或进一步评估' : '可继续 OTC 用药辅助判断'),
      item('候选疾病', summarizeDiseaseCandidates(data.disease_candidates)),
      item('候选 OTC 药物', summarizeOtcCandidates(data.otc_candidates)),
      item('当前用药复核', '候选药如已在使用，应确认剂量、频次和连续用药天数。'),
    ]
  }
  return [
    item('候选药排序', summarizeDebateResults(data.debate_results)),
    item('最终推荐结论', data.medication_debate_summary?.conclusion),
  ]
}

function buildBusinessBasis(type, data, metadata) {
  return {
    evidence_items: formatEvidenceItems((data.risk_findings || []).flatMap((item) => item.evidence_items || [])),
    risk_findings: data.risk_findings || [],
    rule_matches: data.rule_matches || [],
    dose_results: data.dose_results || data.dose_check || null,
    drug_relations: data.drug_relations || data.relations || [],
    disease_candidates: data.disease_candidates || [],
    otc_candidates: data.otc_candidates || [],
    debate_results: data.debate_results || [],
    metadata_summary: {
      knowledge_backend: metadata.active_knowledge_backend || metadata.knowledge_backend,
      fallback_used: metadata.fallback_used,
      fallback_reason: metadata.fallback_reason,
    },
  }
}

function buildAgentChain(metadata, type) {
  const values =
    metadata?.multi_agent?.agents_executed ||
    metadata?.symptom_agents_executed ||
    (type === 'medication_debate' ? ['medication-debate-manager-agent'] : [])
  if (!Array.isArray(values) || values.length === 0) return '暂无'
  return values.map((name) => agentNameToLabel(name)).join('、')
}

function formatBeijingTime(value) {
  if (!value) return '暂无'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return String(value)
  const parts = new Intl.DateTimeFormat('zh-CN', {
    timeZone: 'Asia/Shanghai',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  }).formatToParts(date)
  const map = Object.fromEntries(parts.map((part) => [part.type, part.value]))
  return `${map.year}-${map.month}-${map.day} ${map.hour}:${map.minute}:${map.second}（北京时间）`
}

function riskTagType(level) {
  return riskLevelToType(level)
}

function item(label, value) {
  return { label, value: normalizeValue(value) }
}

function normalizeValue(value) {
  if (Array.isArray(value)) return joinList(value)
  if (value === '' || value == null) return '暂无'
  return String(value)
}

function joinList(values) {
  if (!Array.isArray(values) || values.length === 0) return '暂无'
  return values.filter(Boolean).join('、') || '暂无'
}

function sexLabel(value) {
  if (value === 'male') return '男'
  if (value === 'female') return '女'
  if (value === '男' || value === '女') return value
  return '未知'
}

function summarizeRiskFindings(values) {
  if (!Array.isArray(values) || values.length === 0) return '未发现明确风险提示'
  return values.slice(0, 3).map((item) => item.title || item.description || '风险提示').join('；')
}

function summarizeDiseaseCandidates(values) {
  if (!Array.isArray(values) || values.length === 0) return '暂无'
  return values.slice(0, 3).map((item) => item.disease_name || item.name || item.label || '候选情况').join('、')
}

function summarizeOtcCandidates(values) {
  if (!Array.isArray(values) || values.length === 0) return '暂无'
  return values
    .flatMap((item) => item.candidate_drugs || [])
    .slice(0, 5)
    .join('、') || '暂无'
}

function summarizeDebateResults(values) {
  if (!Array.isArray(values) || values.length === 0) return '暂无'
  return values.slice(0, 5).map((item) => item.candidate_drug || item.drug_name || '候选药').join('、')
}
</script>

<style scoped>
.audit-page {
  gap: 26px;
}

.audit-page :deep(.card-body) {
  padding: 24px;
}

.audit-page :deep(.header) {
  margin-bottom: 18px;
}

.query-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto auto;
  gap: 16px;
  align-items: center;
  margin-top: 6px;
}

.query-message {
  margin-top: 12px;
  color: var(--color-text-secondary);
  font-size: 13px;
}

.latest-card {
  display: flex;
  justify-content: space-between;
  gap: 22px;
  align-items: center;
}

.latest-main {
  min-width: 0;
}

.latest-title {
  color: var(--color-primary-dark);
  font-size: 18px;
  font-weight: 850;
}

.latest-desc,
.latest-output,
.latest-time {
  margin-top: 8px;
  color: var(--color-text-secondary);
  line-height: 1.7;
}

.latest-time {
  font-size: 13px;
}

.latest-side {
  display: flex;
  flex-direction: column;
  gap: 12px;
  align-items: flex-end;
  flex: 0 0 auto;
}

.overview-grid {
  display: grid;
  grid-template-columns: minmax(300px, 1.4fr) minmax(260px, 1fr) minmax(200px, 0.8fr);
  gap: 16px;
}

.overview-tile {
  padding: 18px 20px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
}

.overview-value {
  margin-top: 8px;
  color: var(--color-primary-dark);
  font-size: 15px;
  font-weight: 800;
  line-height: 1.7;
  word-break: break-word;
}

.request-tile .overview-value {
  color: var(--color-text-main);
  font-size: 14px;
}

.audit-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 20px;
  align-items: start;
}

.trace-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.trace-row {
  display: grid;
  grid-template-columns: 120px minmax(0, 1fr);
  gap: 16px;
  padding: 14px 16px;
  border-radius: var(--radius-md);
  background: #f8fbff;
}

.trace-label {
  color: var(--color-text-secondary);
  font-size: 14px;
  line-height: 1.7;
}

.trace-value {
  color: var(--color-text-main);
  font-weight: 600;
  line-height: 1.75;
  word-break: break-word;
}

@media (max-width: 1000px) {
  .query-row,
  .overview-grid,
  .audit-grid {
    grid-template-columns: 1fr;
  }

  .latest-card {
    align-items: flex-start;
    flex-direction: column;
  }

  .latest-side {
    width: 100%;
    align-items: stretch;
  }
}

@media (max-width: 640px) {
  .trace-row {
    grid-template-columns: 1fr;
  }
}
</style>
