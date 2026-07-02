<template>
  <InfoCard title="常见疾病候选" description="以下为基于症状关键词匹配的常见疾病候选，仅用于问诊辅助，不构成诊断。">
    <div class="stack-sm">
      <el-alert
        v-if="referralRequired"
        type="error"
        :closable="false"
        show-icon
        title="当前描述涉及严重疾病或红旗风险，不适合由本系统生成 OTC 候选药，请由医生进一步评估。"
      />
      <el-alert
        v-else-if="summary"
        type="info"
        :closable="false"
        show-icon
        :title="summary"
      />

      <div v-if="items.length" class="stack-sm">
        <div v-for="item in items" :key="item.disease_id" class="metric-tile">
          <div class="candidate-head">
            <div class="candidate-title">{{ item.disease_name_cn || '常见疾病候选' }}</div>
            <el-tag :type="tagType(item.scope)" round>{{ scopeLabel(item.scope) }}</el-tag>
          </div>
          <div v-if="(item.matched_keywords || []).length">
            <strong>匹配：</strong>{{ item.matched_keywords.join('、') }}
          </div>
          <div v-if="(item.candidate_drug_classes || []).length">
            <strong>候选药类别：</strong>{{ item.candidate_drug_classes.join('、') }}
          </div>
          <div v-if="item.advice">
            <strong>提示：</strong>{{ item.advice }}
          </div>
        </div>
      </div>
      <el-empty v-else description="未匹配到明确常见疾病候选。" />
    </div>
  </InfoCard>
</template>

<script setup>
import InfoCard from '@/components/common/InfoCard.vue'

defineProps({
  items: {
    type: Array,
    default: () => [],
  },
  referralRequired: {
    type: Boolean,
    default: false,
  },
  summary: {
    type: String,
    default: '',
  },
})

function scopeLabel(scope) {
  if (scope === 'referral_required') return '需医生评估'
  if (scope === 'otc_caution') return '谨慎评估'
  return '可辅助评估'
}

function tagType(scope) {
  if (scope === 'referral_required') return 'danger'
  if (scope === 'otc_caution') return 'warning'
  return 'success'
}
</script>

<style scoped>
.candidate-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
  margin-bottom: 10px;
}

.candidate-title {
  color: var(--color-primary-dark);
  font-size: 16px;
  font-weight: 700;
}
</style>
