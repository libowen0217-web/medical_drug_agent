<template>
  <InfoCard :title="`第 ${item.rank || index + 1} 候选 | ${item.candidate_drug || '候选药'}`">
    <div class="stack-sm">
      <div><strong>综合分数：</strong>{{ item.total_score ?? '暂无' }}</div>
      <div><strong>评估等级：</strong>{{ finalLevelToLabel(item.final_level) }}</div>
      <div><strong>摘要：</strong>{{ item.summary || '暂无' }}</div>
      <div><strong>主要支持点：</strong>{{ (item.strengths || []).join('；') || '暂无' }}</div>
      <div><strong>主要注意事项：</strong>{{ (item.cautions || []).join('；') || '暂无' }}</div>
    </div>
  </InfoCard>
</template>

<script setup>
import InfoCard from '@/components/common/InfoCard.vue'
import { finalLevelToLabel } from '@/utils/formatters'

defineProps({
  item: {
    type: Object,
    required: true,
  },
  index: {
    type: Number,
    default: 0,
  },
})
</script>
