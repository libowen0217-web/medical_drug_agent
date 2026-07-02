<template>
  <div class="page-header card-shell">
    <div class="card-body header-body">
      <h1 class="title">{{ title }}</h1>
      <p v-if="subtitle" class="subtitle">{{ subtitle }}</p>
      <div class="disclaimer">
        本系统仅用于药师或医生的用药安全辅助参考，不构成诊断、处方或最终用药建议。
      </div>
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
})
</script>

<style scoped>
.header-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.title {
  margin: 0;
  color: var(--color-primary-dark);
  font-size: 30px;
  font-weight: 700;
}

.subtitle {
  margin: 0;
  max-width: 900px;
  color: var(--color-text-secondary);
  line-height: 1.8;
}

.disclaimer {
  padding: 12px 14px;
  border-radius: 14px;
  background: linear-gradient(180deg, #f3f8ff 0%, #ebf4ff 100%);
  border: 1px solid #d8e8ff;
  color: #49627f;
  font-size: 13px;
  line-height: 1.7;
}
</style>
