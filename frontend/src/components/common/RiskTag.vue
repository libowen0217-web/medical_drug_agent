<template>
  <el-tag :type="riskLevelToType(level)" effect="dark" round>
    {{ riskLevelToLabel(level) }}
  </el-tag>
</template>

<script setup>
import { riskLevelToLabel, riskLevelToType } from '@/utils/formatters'

defineProps({
  level: {
    type: String,
    default: 'unknown',
  },
})
</script>
