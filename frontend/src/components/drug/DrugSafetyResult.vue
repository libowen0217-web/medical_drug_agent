<template>
  <InfoCard title="评估结果" description="优先展示药师处理结论、顾客提醒话术和关键风险。">
    <div v-if="response" class="result-section">
      <div class="conclusion-card" :class="riskClass">
        <div>
          <div class="metric-label">评估结论</div>
          <div class="conclusion-title">{{ conclusionText }}</div>
          <div class="conclusion-action">{{ actionText }}</div>
        </div>
        <div class="risk-pill">{{ riskLabel }}</div>
      </div>

      <div class="business-grid">
        <section class="business-card">
          <h4>药师处理建议</h4>
          <ol class="advice-list">
            <li v-for="(item, index) in pharmacistAdvice" :key="index">{{ item }}</li>
          </ol>
        </section>

        <section class="business-card customer-card">
          <h4>顾客提醒话术</h4>
          <div class="customer-scroll">
            <div class="speech-block">
              <div class="speech-label">推荐话术：</div>
              <p class="speech-quote">“{{ customerSpeech.recommended }}”</p>
            </div>
            <div class="speech-block">
              <div class="speech-label">补充提醒：</div>
              <ol class="advice-list">
                <li v-for="(item, index) in customerSpeech.reminders" :key="index">{{ item }}</li>
              </ol>
            </div>
            <div class="speech-block">
              <div class="speech-label">就医提示：</div>
              <p class="plain-note">{{ customerSpeech.medicalAdvice }}</p>
            </div>
          </div>
        </section>
      </div>

      <section class="business-card risk-card">
        <h4>风险提示</h4>
        <div v-if="riskFindings.length" class="risk-summary-list">
          <div v-for="(item, index) in riskFindings.slice(0, 3)" :key="index" class="risk-summary-item">
            <RiskTag :level="item.risk_level" />
            <span>{{ item.description || item.title || '系统发现该药物组合需要关注。' }}</span>
          </div>
        </div>
        <div v-else class="plain-note">未发现明确禁忌，仍建议按说明书剂量使用，并结合顾客基础疾病、过敏史和合并用药进行确认。</div>
      </section>

      <div class="evidence-line">
        本次评估参考了本地药物关系库、剂量规则和患者因素规则。
      </div>

      <el-collapse class="advanced-collapse">
        <el-collapse-item title="展开查看详细依据" name="evidence">
          <div class="stack-sm">
            <section>
              <h4 class="detail-title">详细风险依据</h4>
              <div v-if="riskFindings.length" class="detail-list">
                <div v-for="(item, index) in riskFindings" :key="index" class="detail-item">
                  <div class="risk-item-head">
                    <strong>{{ item.title || `风险提示 ${index + 1}` }}</strong>
                    <RiskTag :level="item.risk_level" />
                  </div>
                  <p>{{ item.description || '暂无描述' }}</p>
                </div>
              </div>
              <div v-else class="compact-empty">暂无结构化风险发现。</div>
            </section>

            <section>
              <h4 class="detail-title">证据来源</h4>
              <div v-if="evidenceItems.length" class="detail-list">
                <div v-for="(item, index) in evidenceItems" :key="index" class="detail-item">
                  <strong>{{ item.citationLabel }}</strong>
                  <div>{{ item.sourceName }}</div>
                  <p>{{ item.evidenceText }}</p>
                </div>
              </div>
              <div v-else class="compact-empty">暂无可展示证据引用。</div>
            </section>

            <section>
              <h4 class="detail-title">系统执行信息</h4>
              <div class="tech-grid">
                <div>执行 Agent：{{ agentList(multiAgent.agents_executed) }}</div>
                <div>失败 Agent：{{ agentList(multiAgent.agents_failed) }}</div>
                <div>知识后端：{{ activeBackend }}</div>
                <div>LLM 润色：{{ multiAgent.llm_used ? '已使用' : '未使用或已回退' }}</div>
              </div>
            </section>

            <JsonViewer :data="response" title="完整 JSON" />
          </div>
        </el-collapse-item>
      </el-collapse>
    </div>

    <div v-else class="compact-empty">
      填写评估信息后点击“开始用药安全评估”，这里将展示风险等级、药师建议和顾客提醒话术。
    </div>
  </InfoCard>
</template>

<script setup>
import { computed } from 'vue'
import InfoCard from '@/components/common/InfoCard.vue'
import JsonViewer from '@/components/common/JsonViewer.vue'
import RiskTag from '@/components/common/RiskTag.vue'
import {
  agentNameToLabel,
  backendToLabel,
  formatEvidenceItems,
  riskLevelToLabel,
} from '@/utils/formatters'

const props = defineProps({
  response: {
    type: Object,
    default: null,
  },
})

const data = computed(() => props.response?.data || {})
const multiAgent = computed(() => props.response?.metadata?.multi_agent || {})
const riskFindings = computed(() => data.value.risk_findings || [])
const evidenceItems = computed(() => formatEvidenceItems(riskFindings.value.flatMap((item) => item.evidence_items || [])))
const riskLevel = computed(() => String(data.value.overall_risk_level || 'unknown').toLowerCase())
const riskLabel = computed(() => riskLevelToLabel(data.value.overall_risk_level))
const riskClass = computed(() => `is-${riskLevel.value}`)
const activeBackend = computed(() => backendToLabel(props.response?.metadata?.active_knowledge_backend || props.response?.metadata?.knowledge_backend))

const conclusionText = computed(() => {
  if (riskLevel.value.includes('high')) return '不建议直接销售，需进一步核实或建议就医'
  if (riskLevel.value.includes('medium') || riskLevel.value.includes('moderate')) return '可以考虑使用，但需要重点询问并提醒风险'
  if (riskLevel.value.includes('low')) return '未发现明确禁忌，可按说明书短期使用'
  return riskFindings.value.length ? '系统发现该药物组合需要关注' : '未发现明确禁忌'
})

const actionText = computed(() => {
  if (riskLevel.value.includes('high')) return '处理动作：暂停推荐，补充询问病史和合并用药，必要时转诊。'
  if (riskLevel.value.includes('medium') || riskLevel.value.includes('moderate')) return '处理动作：确认胃病、肾功能异常、抗凝药使用史和重复用药情况。'
  return '处理动作：按说明书推荐剂量短期使用，并提醒观察不适反应。'
})

const pharmacistAdvice = computed(() => {
  if (riskLevel.value.includes('high')) {
    return [
      '暂不建议直接推荐该用药组合，需先核实当前用药和基础疾病。',
      '重点询问是否正在使用抗凝药、抗血小板药、其他 NSAID 或复方感冒药。',
      '如存在出血风险、明显胃肠道症状、肾功能异常或症状加重，建议就医。',
      '如必须使用，应由医生或药师进一步评估后决定。',
    ]
  }

  if (riskLevel.value.includes('medium') || riskLevel.value.includes('moderate')) {
    return [
      '可在确认风险因素后谨慎短期使用。',
      '重点询问胃病、肾功能异常、抗凝药使用史和近期是否已服用同类药。',
      '提醒顾客按说明书剂量服用，不要自行加量或延长疗程。',
      '出现胃痛、黑便、皮疹、呼吸不适或症状加重时应停止使用并就医。',
    ]
  }

  return [
    '可按说明书推荐剂量短期使用，避免超量或长期连续使用。',
    '避免与其他止痛药、退烧药或复方感冒药重复使用。',
    '若患者存在胃病、肾功能异常、正在使用抗凝药，应进一步确认。',
    '若症状持续或加重，建议及时就医。',
  ]
})

const customerSpeech = computed(() => {
  const sentences = splitSentences(data.value.patient_report)

  if (riskLevel.value.includes('high')) {
    return {
      recommended: sentences[0] || '您目前的用药情况需要进一步确认，建议先不要自行叠加使用这个药。',
      reminders: [
        '请告诉药师或医生您正在使用的所有药物，包括处方药、保健品和复方感冒药。',
        '如果有胃出血、黑便、明显胃痛、肾功能异常或正在服用抗凝药，请不要自行使用。',
        '如果症状明显或持续加重，请及时就医。',
      ],
      medicalAdvice: '如出现呼吸困难、黑便、持续高热、疼痛明显加重等情况，应尽快就医。',
    }
  }

  return {
    recommended:
      sentences[0] ||
      '这个药可以短期用于止痛或退热，但不要和其他止痛药、退烧药或复方感冒药重复服用。',
    reminders: [
      sentences[1] || '如果出现胃部不适、黑便、皮疹等情况，请停止使用并咨询医生。',
      sentences[2] || '如果发热超过 3 天、疼痛加重或症状反复，应及时就医。',
      '如正在使用抗凝药、胃病药，或存在肾功能异常，请先咨询医生或药师。',
    ],
    medicalAdvice: '如症状持续、加重或出现异常反应，请停止自行用药并及时就医。',
  }
})

function splitSentences(text) {
  return String(text || '')
    .replace(/\n+/g, ' ')
    .split(/(?<=[。！？!?；;])/)
    .map((item) => item.trim().replace(/^["“”]+|["“”]+$/g, ''))
    .filter(Boolean)
}

function agentList(values) {
  if (!Array.isArray(values) || values.length === 0) return '暂无'
  return values.map((item) => agentNameToLabel(item)).join('、')
}
</script>

<style scoped>
.conclusion-card {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: center;
  padding: 16px 18px;
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
  background: #f8fbff;
}

.conclusion-card.is-low {
  background: #f0fdf4;
  border-color: #bbf7d0;
}

.conclusion-card.is-medium,
.conclusion-card.is-moderate {
  background: #fff7ed;
  border-color: #fed7aa;
}

.conclusion-card.is-high {
  background: #fef2f2;
  border-color: #fecaca;
}

.conclusion-title {
  margin-top: 4px;
  color: var(--color-primary-dark);
  font-size: 22px;
  font-weight: 850;
}

.conclusion-action {
  margin-top: 6px;
  color: var(--color-text-secondary);
  font-size: 14px;
  line-height: 1.6;
}

.risk-pill {
  flex: 0 0 auto;
  padding: 8px 14px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.82);
  color: var(--color-primary-dark);
  font-weight: 800;
  box-shadow: inset 0 0 0 1px rgba(15, 63, 134, 0.08);
}

.business-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
  align-items: stretch;
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

.advice-list {
  margin: 0;
  padding-left: 20px;
  color: var(--color-text-main);
  line-height: 1.75;
}

.customer-card {
  min-height: 0;
}

.customer-scroll {
  max-height: 210px;
  overflow-y: auto;
  padding-right: 6px;
}

.speech-block + .speech-block {
  margin-top: 12px;
}

.speech-label {
  margin-bottom: 5px;
  color: var(--color-primary-dark);
  font-size: 14px;
  font-weight: 800;
}

.speech-quote,
.plain-note {
  margin: 0;
  color: var(--color-text-main);
  line-height: 1.8;
}

.speech-quote {
  padding: 10px 12px;
  border-radius: var(--radius-md);
  background: #f8fbff;
}

.risk-card {
  grid-column: 1 / -1;
}

.risk-summary-list,
.detail-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.risk-summary-item {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  color: var(--color-text-main);
  line-height: 1.7;
}

.evidence-line {
  padding: 10px 12px;
  border-radius: var(--radius-md);
  background: #f8fbff;
  color: var(--color-text-secondary);
  font-size: 13px;
}

.detail-item {
  padding: 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: #f8fbff;
}

.detail-item p {
  margin: 8px 0 0;
  color: var(--color-text-secondary);
  line-height: 1.7;
}

.risk-item-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
}

.tech-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px 14px;
  color: var(--color-text-secondary);
  font-size: 13px;
}

@media (max-width: 860px) {
  .business-grid,
  .tech-grid {
    grid-template-columns: 1fr;
  }

  .conclusion-card {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
