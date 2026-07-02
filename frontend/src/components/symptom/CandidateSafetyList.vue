<template>
  <InfoCard title="候选药安全检查" description="用于辅助复核候选药与患者当前信息之间的风险提示。">
    <div v-if="items.length" class="stack-sm">
      <el-collapse>
        <el-collapse-item
          v-for="(item, index) in items"
          :key="`${item.candidate_drug}-${index}`"
          :title="`${item.candidate_drug || '候选药'} | ${riskLevelToLabel(item.safety_response?.data?.overall_risk_level)}`"
          :name="index"
        >
          <div class="stack-sm">
            <div><strong>综合风险等级：</strong>{{ riskLevelToLabel(item.safety_response?.data?.overall_risk_level) }}</div>
            <div><strong>剂量来源：</strong>{{ getDoseSourceLabel(item) }}</div>

            <div v-if="isReferenceDose(item)" class="note-box">
              本次基于说明书参考剂量模拟评估，不代表患者实际用药剂量，也不构成处方建议。
              <div v-if="getReferenceDoseText(item)" class="sub-note">
                参考剂量：{{ getReferenceDoseText(item) }}
              </div>
            </div>

            <div v-if="item.safety_response?.metadata?.current_drug_count === 0" class="note-box">
              未提供当前用药，因而未进行药物-药物相互作用检查；当前结果主要基于疾病、特殊人群、过敏史和剂量信息。
            </div>

            <div v-if="isMissingDose(item)" class="note-box note-box--muted">
              当前药物未提供实际剂量，且没有可直接使用的患者真实剂量信息；请结合说明书和专业判断复核。
            </div>

            <div
              v-for="(finding, findingIndex) in item.safety_response?.data?.risk_findings || []"
              :key="findingIndex"
              class="metric-tile"
            >
              <div><strong>{{ finding.title || '风险发现' }}</strong></div>
              <div>{{ finding.description || '暂无' }}</div>
            </div>
          </div>
        </el-collapse-item>
      </el-collapse>
    </div>
    <el-empty v-else description="当前暂无候选药安全检查结果。" />
  </InfoCard>
</template>

<script setup>
import InfoCard from '@/components/common/InfoCard.vue'
import { riskLevelToLabel } from '@/utils/formatters'

defineProps({
  items: {
    type: Array,
    default: () => [],
  },
})

function getDoseResult(item) {
  return item?.safety_response?.data?.dose_results?.[0] || {}
}

function getDoseSourceLabel(item) {
  return getDoseResult(item).dose_source_label || '未提供剂量'
}

function isReferenceDose(item) {
  return getDoseResult(item).dose_source === 'label_reference'
}

function isMissingDose(item) {
  const doseResult = getDoseResult(item)
  return doseResult.dose_source === 'missing' && doseResult.status === 'missing_dose'
}

function getReferenceDoseText(item) {
  const referenceDose = getDoseResult(item).reference_dose
  if (!referenceDose) {
    return ''
  }
  return `单次 ${referenceDose.single_dose_mg} mg，每日 ${referenceDose.times_per_day} 次，使用 ${referenceDose.duration_days} 天`
}
</script>

<style scoped>
.note-box {
  padding: 12px 14px;
  border-radius: 12px;
  background: #f3f8ff;
  border: 1px solid #d9e8ff;
  color: #4d6481;
  line-height: 1.7;
}

.note-box--muted {
  background: #f7f9fc;
  border-color: #dde6f0;
}

.sub-note {
  margin-top: 6px;
  font-size: 13px;
}
</style>
