<template>
  <section class="card-shell">
    <div class="card-body">
      <div v-if="title || description" class="header">
        <h3 v-if="title" class="card-title">{{ title }}</h3>
        <p v-if="description" class="card-desc">{{ description }}</p>
      </div>
      <slot />
    </div>
  </section>
</template>

<script setup>
defineProps({
  title: {
    type: String,
    default: '',
  },
  description: {
    type: String,
    default: '',
  },
})
</script>

<style scoped>
.header {
  margin-bottom: 16px;
}
</style>
