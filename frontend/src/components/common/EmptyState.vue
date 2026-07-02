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
  min-height: 280px;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
