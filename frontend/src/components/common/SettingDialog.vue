<template>
  <el-dialog v-model="visible" title="系统设置" width="560px">
    <div class="stack-sm">
      <el-form label-position="top">
        <el-form-item label="API 地址">
          <el-input v-model="form.apiBaseUrl" placeholder="留空则使用同源 /api 代理" />
        </el-form-item>

        <el-form-item label="知识图谱后端">
          <el-select v-model="form.knowledgeBackend" style="width: 100%">
            <el-option label="自动" value="auto" />
            <el-option label="CSV" value="csv" />
            <el-option label="Neo4j" value="neo4j" />
          </el-select>
        </el-form-item>

        <el-alert
          type="info"
          :closable="false"
          show-icon
          title="正式前端只调用 FastAPI 接口，不直接读取 CSV 或 Neo4j。"
        />

        <el-form-item>
          <el-switch v-model="form.enableLlm" active-text="启用 LLM 报告润色" />
        </el-form-item>
        <el-form-item>
          <el-switch v-model="form.enableAudit" active-text="启用审计日志" />
        </el-form-item>
        <el-form-item>
          <el-switch v-model="form.showJson" active-text="显示完整 JSON" />
        </el-form-item>
        <el-form-item>
          <el-switch v-model="form.showAgentChain" active-text="显示 Agent 执行链路" />
        </el-form-item>
      </el-form>
    </div>

    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" @click="handleSave">保存设置</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { computed, reactive, watch } from 'vue'
import { useAppStateStore } from '@/stores/appState'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['update:modelValue'])
const store = useAppStateStore()

const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
})

const form = reactive({ ...store.settings })

watch(
  () => props.modelValue,
  () => {
    Object.assign(form, store.settings)
  }
)

function handleSave() {
  store.saveSettings(form)
  visible.value = false
}
</script>
