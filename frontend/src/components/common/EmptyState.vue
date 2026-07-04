<template>
  <div class="empty-shell card-shell">
    <div class="card-body">
      <el-empty :description="description">
        <slot />
      </el-empty>
    </div>
  </div>
</template>

<script setup>
defineProps({
  description: {
    type: String,
    default: '暂无内容',
  },
})
</script>

<style scoped>
.empty-shell {
  min-height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.empty-shell :deep(.el-empty) {
  padding: 12px 0;
}

.empty-shell :deep(.el-empty__image) {
  display: none;
}
</style>
