<template>
  <el-select
    ref="selectRef"
    :model-value="modelValue"
    :multiple="multiple"
    :loading="loading"
    :placeholder="placeholder"
    :no-data-text="noDataText"
    loading-text="正在加载药物选项..."
    filterable
    clearable
    remote
    :reserve-keyword="false"
    :remote-method="handleSearch"
    style="width: 100%"
    @update:model-value="handleModelUpdate"
    @change="handleChange"
    @visible-change="handleVisibleChange"
    @clear="handleClear"
    @blur="handleBlur"
  >
    <el-option
      v-for="item in filteredOptions"
      :key="item.standard_name || item.display_name || item.label"
      :label="item.display_name || item.standard_name"
      :value="item.display_name || item.standard_name"
    >
      <div class="option-main">{{ item.display_name || item.standard_name }}</div>
      <div class="option-sub">
        {{ [item.standard_name, item.pinyin, ...(Array.isArray(item.aliases) ? item.aliases : [])].filter(Boolean).join(' / ') }}
      </div>
    </el-option>

    <template #empty>
      <div class="empty-text">{{ noDataText }}</div>
    </template>
  </el-select>
</template>

<script setup>
import { computed, nextTick, ref } from 'vue'
import { filterDrugOptions } from '@/utils/drugSearch'

const props = defineProps({
  modelValue: {
    type: [Array, String],
    default: () => [],
  },
  options: {
    type: Array,
    default: () => [],
  },
  multiple: {
    type: Boolean,
    default: false,
  },
  loading: {
    type: Boolean,
    default: false,
  },
  loadFailed: {
    type: Boolean,
    default: false,
  },
  placeholder: {
    type: String,
    default: '请输入药物名称、英文名、别名或拼音',
  },
})

const emit = defineEmits(['update:modelValue'])

const selectRef = ref(null)
const query = ref('')

const normalizedOptions = computed(() => (Array.isArray(props.options) ? props.options : []))
const filteredOptions = computed(() => filterDrugOptions(normalizedOptions.value, query.value))

const noDataText = computed(() => {
  if (props.loading) {
    return '正在加载药物选项...'
  }
  if (props.loadFailed) {
    return '药物选项加载失败，请确认 /api/v1/drugs/options 接口可用。'
  }
  if (normalizedOptions.value.length === 0) {
    return '暂无药物数据，请检查后端药物选项接口。'
  }
  return '暂无匹配药物'
})

function handleModelUpdate(value) {
  emit('update:modelValue', value)
}

async function handleChange(value) {
  emit('update:modelValue', value)
  query.value = ''
  await nextTick()
  selectRef.value?.blur?.()
}

function handleVisibleChange(visible) {
  if (!visible) {
    query.value = ''
  }
}

function handleClear() {
  query.value = ''
}

function handleBlur() {
  query.value = ''
}

function handleSearch(value) {
  query.value = value
}
</script>

<style scoped>
.empty-text {
  padding: 12px 16px;
  color: var(--color-text-secondary);
  font-size: 13px;
  line-height: 1.6;
}

.option-main {
  color: var(--color-text-main);
  font-weight: 700;
  line-height: 1.4;
}

.option-sub {
  color: var(--color-text-secondary);
  font-size: 12px;
  line-height: 1.4;
}
</style>
