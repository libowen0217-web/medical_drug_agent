<template>
  <InfoCard title="证据引用" description="展示命中的本地证据摘要与匹配原因。">
    <div v-if="items.length" class="stack-sm">
      <div v-for="(item, index) in items" :key="`${item.citationLabel}-${index}`" class="metric-tile">
        <div class="metric-label">{{ item.citationLabel }}</div>
        <div><strong>来源：</strong>{{ item.sourceName }}</div>
        <div><strong>证据内容：</strong>{{ item.evidenceText }}</div>
        <div><strong>匹配原因：</strong>{{ item.matchedReason }}</div>
        <div><strong>分数 / 排名：</strong>{{ item.score }} / {{ item.rank }}</div>
      </div>
    </div>
    <el-empty v-else description="暂无证据引用" />
  </InfoCard>
</template>

<script setup>
import InfoCard from '@/components/common/InfoCard.vue'

defineProps({
  items: {
    type: Array,
    default: () => [],
  },
})
</script>
