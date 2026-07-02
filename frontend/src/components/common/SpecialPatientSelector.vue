<template>
  <div class="special-selector">
    <div class="title-row">
      <div class="section-label">特殊患者因素</div>
      <div class="section-desc">
        系统会根据年龄自动识别儿童或老年人；孕妇需结合性别和年龄手动确认。
      </div>
    </div>

    <div class="stack-sm">
      <div class="group-block">
        <div class="group-label">自动识别</div>
        <div class="chip-row">
          <el-tag :type="uiState.childActive ? 'warning' : 'info'" round>
            儿童：{{ uiState.childActive ? '是' : '否' }}
          </el-tag>
          <el-tag :type="uiState.elderlyActive ? 'warning' : 'info'" round>
            老年人：{{ uiState.elderlyActive ? '是' : '否' }}
          </el-tag>
        </div>
      </div>

      <div class="group-block">
        <div class="group-label">手动确认</div>
        <el-tooltip v-if="uiState.pregnancyDisabledReason" :content="uiState.pregnancyDisabledReason" placement="top">
          <div class="pregnancy-wrap">
            <el-checkbox
              :model-value="uiState.pregnancyChecked"
              :disabled="uiState.pregnancyDisabled"
              @change="handlePregnancyChange"
            >
              孕妇
            </el-checkbox>
          </div>
        </el-tooltip>
        <div v-else class="pregnancy-wrap">
          <el-checkbox
            :model-value="uiState.pregnancyChecked"
            :disabled="uiState.pregnancyDisabled"
            @change="handlePregnancyChange"
          >
            孕妇
          </el-checkbox>
        </div>
      </div>

      <el-alert
        v-for="warning in uiState.validation.warnings"
        :key="warning"
        :title="warning"
        type="warning"
        :closable="false"
        show-icon
      />
      <el-alert
        v-if="uiState.pregnancyDisabledReason"
        :title="uiState.pregnancyDisabledReason"
        type="info"
        :closable="false"
        show-icon
      />
      <el-alert
        v-for="error in uiState.validation.errors"
        :key="error"
        :title="error"
        type="error"
        :closable="false"
        show-icon
      />
    </div>
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

const uiState = computed(() =>
  getSpecialPatientUIState({
    age: props.age,
    sex: props.sex,
    selectedFactors: pregnancySelected.value ? ['孕妇'] : [],
  })
)

watch(
  () => props.modelValue,
  (value) => {
    pregnancySelected.value = Array.isArray(value) && value.includes('孕妇')
  },
  { immediate: true }
)

watch(
  () => [props.age, props.sex, pregnancySelected.value],
  () => {
    const nextFactors = deriveSpecialFactors({
      age: props.age,
      sex: props.sex,
      selectedFactors: pregnancySelected.value ? ['孕妇'] : [],
    })
    if (JSON.stringify(nextFactors) !== JSON.stringify(props.modelValue || [])) {
      emit('update:modelValue', nextFactors)
    }
    if (!nextFactors.includes('孕妇') && pregnancySelected.value) {
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
}

.title-row {
  margin-bottom: 10px;
}

.section-label {
  margin-bottom: 6px;
  color: var(--color-primary-dark);
  font-size: 14px;
  font-weight: 700;
}

.section-desc {
  color: var(--color-text-secondary);
  font-size: 13px;
  line-height: 1.6;
}

.group-block {
  padding: 12px 14px;
  border: 1px solid var(--color-border);
  border-radius: 12px;
  background: #f8fbff;
}

.group-label {
  margin-bottom: 10px;
  color: var(--color-primary-dark);
  font-size: 13px;
  font-weight: 700;
}

.chip-row {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.pregnancy-wrap {
  display: inline-flex;
}
</style>
