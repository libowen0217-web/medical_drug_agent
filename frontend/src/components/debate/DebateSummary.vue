<template>
  <InfoCard title="候选药协作评估摘要">
    <div v-if="summary" class="stack-sm">
      <el-alert
        v-if="summary.red_flag_blocked"
        type="error"
        :closable="false"
        show-icon
        title="当前描述涉及严重疾病或红旗风险，系统已停止候选药协作评估。"
      />
      <div class="metric-grid">
        <div class="metric-tile">
          <div class="metric-label">协作评估启用</div>
          <div class="metric-value">{{ booleanToLabel(summary.debate_enabled) }}</div>
        </div>
        <div class="metric-tile">
          <div class="metric-label">红旗阻断</div>
          <div class="metric-value">{{ booleanToLabel(summary.red_flag_blocked) }}</div>
        </div>
      </div>
      <div><strong>结论：</strong>{{ summary.conclusion || '暂无' }}</div>
      <div><strong>说明：</strong>{{ summary.disclaimer || '暂无' }}</div>
    </div>
    <el-empty v-else description="暂无候选药协作评估摘要" />
  </InfoCard>
</template>

<script setup>
import InfoCard from '@/components/common/InfoCard.vue'
import { booleanToLabel } from '@/utils/formatters'

defineProps({
  summary: {
    type: Object,
    default: null,
  },
})
</script>
