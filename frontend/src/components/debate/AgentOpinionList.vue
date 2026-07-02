<template>
  <InfoCard title="各 Agent 观点">
    <div v-if="opinions.length" class="stack-sm">
      <div v-for="(item, index) in opinions" :key="index" class="metric-tile">
        <div><strong>{{ agentNameToLabel(item.agent_name) }}</strong></div>
        <div><strong>分值变化：</strong>{{ item.score_delta ?? '暂无' }}</div>
        <div><strong>风险等级：</strong>{{ riskLevelToLabel(item.risk_level) }}</div>
        <div><strong>观点：</strong>{{ item.opinion || '暂无' }}</div>
        <div><strong>原因：</strong>{{ (item.reasons || []).join('；') || '暂无' }}</div>
        <div><strong>证据引用：</strong>{{ (item.evidence_refs || []).join('；') || '暂无' }}</div>
      </div>
    </div>
    <el-empty v-else description="暂无 Agent 观点" />
  </InfoCard>
</template>

<script setup>
import InfoCard from '@/components/common/InfoCard.vue'
import { agentNameToLabel, riskLevelToLabel } from '@/utils/formatters'

defineProps({
  opinions: {
    type: Array,
    default: () => [],
  },
})
</script>
