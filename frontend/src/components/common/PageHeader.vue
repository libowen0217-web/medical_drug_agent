<template>
  <div class="page-header card-shell">
    <div class="card-body header-body">
      <div>
        <h1 class="title">{{ title }}</h1>
        <p v-if="subtitle" class="subtitle">{{ subtitle }}</p>
      </div>
      <div v-if="disclaimer" class="disclaimer">{{ disclaimer }}</div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  title: {
    type: String,
    default: '',
  },
  subtitle: {
    type: String,
    default: '',
  },
  disclaimer: {
    type: String,
    default: '本系统仅用于药师或医生的用药安全辅助参考，不构成诊断、处方或最终用药建议。',
  },
})
</script>

<style scoped>
.header-body {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.title {
  margin: 0;
  color: var(--color-primary-dark);
  font-size: 26px;
  font-weight: 850;
}

.subtitle {
  margin: 6px 0 0;
  max-width: 980px;
  color: var(--color-text-secondary);
  font-size: 14px;
  line-height: 1.65;
}

.disclaimer {
  padding: 8px 10px;
  border-radius: var(--radius-md);
  background: #f3f8ff;
  border: 1px solid #d8e8ff;
  color: #49627f;
  font-size: 12px;
  line-height: 1.55;
}
</style>
