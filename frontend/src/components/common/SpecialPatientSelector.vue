<template>
  <div class="special-selector">
    <div class="special-line">
      <span class="summary-label">特殊人群：</span>
      <el-tag :type="summaryType" round>{{ summaryText }}</el-tag>
      <el-checkbox
        :model-value="uiState.pregnancyChecked"
        :disabled="uiState.pregnancyDisabled"
        @change="handlePregnancyChange"
      >
        孕妇
      </el-checkbox>
    </div>
    <div v-if="pregnancyError" class="special-error">{{ pregnancyError }}</div>
    <div v-else-if="summaryHint" class="special-hint">{{ summaryHint }}</div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { deriveSpecialFactors, getSpecialPatientUIState } from '@/utils/validators'

const props = defineProps({
  modelValue: {
    type: Array,
    default: () => [],
  },
  age: {
    type: Number,
    default: 0,
  },
  sex: {
    type: String,
    default: 'unknown',
  },
})

const emit = defineEmits(['update:modelValue'])

const pregnancySelected = ref(Array.isArray(props.modelValue) && props.modelValue.includes('孕妇'))
const selectedFactors = computed(() => (pregnancySelected.value ? ['孕妇'] : []))

const uiState = computed(() =>
  getSpecialPatientUIState({
    age: props.age,
    sex: props.sex,
    selectedFactors: selectedFactors.value,
  })
)

const finalFactors = computed(() =>
  deriveSpecialFactors({
    age: props.age,
    sex: props.sex,
    selectedFactors: selectedFactors.value,
  })
)

const summaryText = computed(() => {
  if (finalFactors.value.includes('儿童')) return '儿童'
  if (finalFactors.value.includes('老年人')) return '老年人'
  if (finalFactors.value.includes('孕妇')) return '孕妇'
  return '普通成人'
})

const summaryType = computed(() => (summaryText.value === '普通成人' ? 'info' : 'warning'))

const pregnancyError = computed(() => {
  if (!uiState.value.pregnancyDisabled || !pregnancySelected.value) return ''
  if (props.sex === 'male') return '患者性别与孕妇身份不匹配，请修改患者信息。'
  return '当前年龄与孕妇身份不匹配，请核实患者信息。'
})

const summaryHint = computed(() => {
  if (summaryText.value === '老年人') return '系统将按老年患者用药风险进行辅助判断。'
  if (summaryText.value === '儿童') return '系统将按儿童患者用药风险进行辅助判断。'
  if (uiState.value.pregnancyDisabledReason) return uiState.value.pregnancyDisabledReason
  return ''
})

watch(
  () => props.modelValue,
  (value) => {
    pregnancySelected.value = Array.isArray(value) && value.includes('孕妇')
  },
  { immediate: true }
)

watch(
  finalFactors,
  (nextFactors) => {
    if (JSON.stringify(nextFactors) !== JSON.stringify(props.modelValue || [])) {
      emit('update:modelValue', nextFactors)
    }
    if (!nextFactors.includes('孕妇') && pregnancySelected.value && uiState.value.pregnancyDisabled) {
      pregnancySelected.value = false
    }
  },
  { immediate: true }
)

function handlePregnancyChange(value) {
  pregnancySelected.value = Boolean(value)
}
</script>

<style scoped>
.special-selector {
  width: 100%;
  min-height: 36px;
}

.special-line {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
}

.summary-label {
  color: var(--color-primary-dark);
  font-size: 14px;
  font-weight: 700;
}

.special-hint,
.special-error {
  margin-top: 6px;
  font-size: 13px;
  line-height: 1.5;
}

.special-hint {
  color: var(--color-text-secondary);
}

.special-error {
  color: var(--color-danger);
}
</style>
