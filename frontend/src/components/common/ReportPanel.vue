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
  border: 1px solid var(--color-border);
  border-radius: 16px;
  background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
  padding: 16px 18px;
}

.report-content {
  max-height: 360px;
  overflow: auto;
  color: var(--color-text-main);
  line-height: 1.9;
  white-space: pre-wrap;
  word-break: break-word;
}
</style>
