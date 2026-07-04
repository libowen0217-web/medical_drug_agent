<template>
  <div class="report-panel">
    <div class="report-content">{{ content || '暂无内容' }}</div>
  </div>
</template>

<script setup>
defineProps({
  content: {
    type: String,
    default: '',
  },
})
</script>

<style scoped>
.report-panel {
  padding: 14px 16px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
}

.report-content {
  color: var(--color-text-main);
  font-size: 14px;
  line-height: 1.85;
  white-space: pre-wrap;
  word-break: break-word;
}
</style>
