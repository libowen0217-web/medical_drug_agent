<template>
  <article class="rank-card">
    <div class="rank-head">
      <div>
        <div class="rank-index">第 {{ item.rank || index + 1 }} 位</div>
        <h4>{{ item.candidate_drug || '候选药' }}</h4>
      </div>
      <el-tag round>{{ finalLevelToLabel(item.final_level) }}</el-tag>
    </div>
    <div class="score-line">综合分数：{{ item.total_score ?? '暂无' }}</div>
    <p>{{ item.summary || '暂无摘要' }}</p>
    <div class="mini-list">
      <div><strong>支持点：</strong>{{ (item.strengths || []).join('；') || '暂无' }}</div>
      <div><strong>注意事项：</strong>{{ (item.cautions || []).join('；') || '暂无' }}</div>
    </div>
  </article>
</template>

<script setup>
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

<style scoped>
.rank-card {
  padding: 16px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: #f8fbff;
}

.rank-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
}

.rank-index {
  color: var(--color-text-secondary);
  font-size: 13px;
}

h4 {
  margin: 4px 0 0;
  color: var(--color-primary-dark);
  font-size: 18px;
}

.score-line {
  margin-top: 12px;
  color: var(--color-primary-dark);
  font-weight: 700;
}

p,
.mini-list {
  color: var(--color-text-secondary);
  line-height: 1.7;
}
</style>
