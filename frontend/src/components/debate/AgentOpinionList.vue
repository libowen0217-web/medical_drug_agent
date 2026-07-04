<template>
  <div v-if="opinions.length" class="opinion-list">
    <article v-for="(item, index) in opinions" :key="index" class="opinion-card">
      <div class="opinion-head">
        <strong>{{ agentNameToLabel(item.agent_name) }}</strong>
        <el-tag :type="riskLevelToType(item.risk_level)" round>{{ riskLevelToLabel(item.risk_level) }}</el-tag>
      </div>
      <p>{{ item.opinion || '暂无观点' }}</p>
      <div class="opinion-meta">
        <span>分值变化：{{ item.score_delta ?? '暂无' }}</span>
        <span v-if="(item.reasons || []).length">原因：{{ item.reasons.join('；') }}</span>
      </div>
    </article>
  </div>
  <div v-else class="compact-empty">暂无 Agent 意见。</div>
</template>

<script setup>
import { agentNameToLabel, riskLevelToLabel, riskLevelToType } from '@/utils/formatters'

defineProps({
  opinions: {
    type: Array,
    default: () => [],
  },
})
</script>

<style scoped>
.opinion-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.opinion-card {
  padding: 12px 14px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: #f8fbff;
}

.opinion-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
}

p {
  margin: 8px 0;
  color: var(--color-text-main);
  line-height: 1.7;
}

.opinion-meta {
  display: flex;
  flex-direction: column;
  gap: 4px;
  color: var(--color-text-secondary);
  font-size: 13px;
  line-height: 1.6;
}
</style>
