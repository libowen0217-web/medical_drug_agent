<template>
  <div class="tag-input-shell">
    <div v-if="modelValue.length" class="tag-list">
      <el-tag
        v-for="item in modelValue"
        :key="item"
        closable
        effect="plain"
        class="tag-item"
        @close="removeTag(item)"
      >
        {{ item }}
      </el-tag>
    </div>

    <el-input
      v-model="draft"
      :placeholder="placeholder"
      clearable
      @keydown.enter.prevent="commitDraft"
      @blur="commitDraft"
      @input="handleInput"
    />
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  modelValue: {
    type: Array,
    default: () => [],
  },
  placeholder: {
    type: String,
    default: '请输入内容，支持逗号、分号或回车分隔',
  },
})

const emit = defineEmits(['update:modelValue'])
const draft = ref('')

function normalizeParts(text) {
  const normalized = String(text || '')
    .replace(/，/g, ',')
    .replace(/；/g, ';')
    .replace(/\n/g, ',')
  return normalized
    .split(/[;,]/g)
    .map((item) => item.trim())
    .filter(Boolean)
}

function updateValue(nextItems) {
  const deduped = []
  const seen = new Set()
  for (const item of nextItems) {
    const cleaned = String(item || '').trim()
    if (cleaned && !seen.has(cleaned)) {
      seen.add(cleaned)
      deduped.push(cleaned)
    }
  }
  emit('update:modelValue', deduped)
}

function commitDraft() {
  const parts = normalizeParts(draft.value)
  if (!parts.length) {
    draft.value = ''
    return
  }
  updateValue([...(Array.isArray(props.modelValue) ? props.modelValue : []), ...parts])
  draft.value = ''
}

function handleInput(value) {
  if (/[,，;\n；]/.test(String(value || ''))) {
    commitDraft()
  }
}

function removeTag(item) {
  updateValue((Array.isArray(props.modelValue) ? props.modelValue : []).filter((value) => value !== item))
}
</script>

<style scoped>
.tag-input-shell {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tag-item {
  margin: 0;
}
</style>
