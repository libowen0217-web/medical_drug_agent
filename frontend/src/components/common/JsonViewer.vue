<template>
  <el-collapse>
    <el-collapse-item :title="title" name="json">
      <pre class="json-block">{{ prettyJson }}</pre>
    </el-collapse-item>
  </el-collapse>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  title: {
    type: String,
    default: '查看完整 JSON',
  },
  data: {
    type: [Object, Array, String, Number, Boolean, null],
    default: null,
  },
})

const prettyJson = computed(() => JSON.stringify(props.data, null, 2))
</script>

<style scoped>
.json-block {
  margin: 0;
  padding: 16px;
  overflow: auto;
  border-radius: 12px;
  background: #0f172a;
  color: #dbeafe;
  font-size: 12px;
  line-height: 1.6;
}
</style>
