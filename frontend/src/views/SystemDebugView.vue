<template>
  <div class="page-view">
    <PageHeader
      title="系统调试与审计"
      subtitle="集中查看 API 地址、后端健康状态、知识图谱后端状态、LLM 状态和最近一次请求的完整 JSON。"
    />

    <SystemStatusBar />

    <div class="stack-md">
      <InfoCard title="当前系统配置">
        <div class="metric-grid">
          <div class="metric-tile">
            <div class="metric-label">API 地址</div>
            <div class="metric-value mono">{{ store.settings.apiBaseUrl }}</div>
          </div>
          <div class="metric-tile">
            <div class="metric-label">知识图谱后端</div>
            <div class="metric-value">{{ backendToLabel(store.settings.knowledgeBackend) }}</div>
          </div>
          <div class="metric-tile">
            <div class="metric-label">显示完整 JSON</div>
            <div class="metric-value">{{ booleanToLabel(store.settings.showJson) }}</div>
          </div>
          <div class="metric-tile">
            <div class="metric-label">显示 Agent 执行链路</div>
            <div class="metric-value">{{ booleanToLabel(store.settings.showAgentChain) }}</div>
          </div>
        </div>
      </InfoCard>

      <InfoCard title="后端健康状态">
        <div class="metric-grid">
          <div class="metric-tile">
            <div class="metric-label">后端连接</div>
            <div class="metric-value">{{ healthStatus?.connected ? '已连接' : '未连接' }}</div>
          </div>
          <div class="metric-tile">
            <div class="metric-label">service</div>
            <div class="metric-value text-body">{{ healthStatus?.service || '暂无' }}</div>
          </div>
          <div class="metric-tile">
            <div class="metric-label">engine_version</div>
            <div class="metric-value text-body">{{ healthStatus?.engine_version || '暂无' }}</div>
          </div>
        </div>
      </InfoCard>

      <InfoCard title="知识图谱后端状态">
        <div v-if="knowledgeBackendStatus" class="metric-grid">
          <div class="metric-tile">
            <div class="metric-label">configured_backend</div>
            <div class="metric-value">
              {{ backendToLabel(knowledgeBackendStatus.configured_knowledge_backend || knowledgeBackendStatus.configured_backend) }}
            </div>
          </div>
          <div class="metric-tile">
            <div class="metric-label">active_backend</div>
            <div class="metric-value">
              {{ backendToLabel(knowledgeBackendStatus.active_knowledge_backend || knowledgeBackendStatus.active_backend) }}
            </div>
          </div>
          <div class="metric-tile">
            <div class="metric-label">neo4j_connected</div>
            <div class="metric-value">{{ booleanToLabel(knowledgeBackendStatus.neo4j_connected) }}</div>
          </div>
          <div class="metric-tile">
            <div class="metric-label">fallback_used</div>
            <div class="metric-value">{{ booleanToLabel(knowledgeBackendStatus.fallback_used) }}</div>
          </div>
          <div class="metric-tile">
            <div class="metric-label">fallback_reason</div>
            <div class="metric-value text-body">{{ knowledgeBackendStatus.fallback_reason || '暂无' }}</div>
          </div>
          <div class="metric-tile">
            <div class="metric-label">neo4j_version</div>
            <div class="metric-value text-body">{{ knowledgeBackendStatus.neo4j_version || '暂无' }}</div>
          </div>
        </div>
        <el-empty v-else description="暂无知识图谱后端状态" />
      </InfoCard>

      <InfoCard title="最近一次药物安全检查响应">
        <div v-if="drugResponse" class="stack-sm">
          <div><strong>request_id：</strong>{{ drugResponse.request_id || '暂无' }}</div>
          <div><strong>audit_id：</strong>{{ drugResponse.metadata?.audit?.audit_id || '暂无' }}</div>
          <div><strong>agents_executed：</strong>{{ formatAgentList(drugResponse.metadata?.multi_agent?.agents_executed) }}</div>
          <div><strong>agents_failed：</strong>{{ formatAgentList(drugResponse.metadata?.multi_agent?.agents_failed) }}</div>
          <div><strong>knowledge_backend：</strong>{{ backendToLabel(drugResponse.metadata?.knowledge_backend) }}</div>
          <div><strong>active_knowledge_backend：</strong>{{ backendToLabel(drugResponse.metadata?.active_knowledge_backend) }}</div>
          <div><strong>fallback_used：</strong>{{ booleanToLabel(drugResponse.metadata?.fallback_used) }}</div>
          <div><strong>fallback_reason：</strong>{{ drugResponse.metadata?.fallback_reason || '暂无' }}</div>
          <div><strong>llm_enabled：</strong>{{ booleanToLabel(drugResponse.metadata?.multi_agent?.llm_enabled) }}</div>
          <div><strong>llm_used：</strong>{{ booleanToLabel(drugResponse.metadata?.multi_agent?.llm_used) }}</div>
          <div><strong>llm_provider：</strong>{{ llmProviderToLabel(drugResponse.metadata?.multi_agent?.llm_provider) }}</div>
          <div><strong>llm_model：</strong>{{ drugResponse.metadata?.multi_agent?.llm_model || '暂无' }}</div>
          <div><strong>llm_error：</strong>{{ drugResponse.metadata?.multi_agent?.llm_error || '暂无' }}</div>
          <JsonViewer v-if="store.settings.showJson" :data="drugResponse" />
        </div>
        <el-empty v-else description="暂无药物安全检查 JSON" />
      </InfoCard>

      <InfoCard title="最近一次症状问诊响应">
        <div v-if="symptomResponse" class="stack-sm">
          <div><strong>request_id：</strong>{{ symptomResponse.request_id || '暂无' }}</div>
          <div><strong>audit_id：</strong>{{ symptomResponse.metadata?.audit?.audit_id || '暂无' }}</div>
          <div><strong>red_flag_triggered：</strong>{{ booleanToLabel(symptomResponse.metadata?.red_flag_triggered) }}</div>
          <div><strong>debate_enabled：</strong>{{ booleanToLabel(symptomResponse.metadata?.debate_enabled) }}</div>
          <div><strong>symptom_agents_executed：</strong>{{ formatAgentList(symptomResponse.metadata?.symptom_agents_executed) }}</div>
          <div><strong>debate_agents_executed：</strong>{{ formatAgentList(symptomResponse.metadata?.debate_agents_executed) }}</div>
          <JsonViewer v-if="store.settings.showJson" :data="symptomResponse" />
        </div>
        <el-empty v-else description="暂无症状问诊 JSON" />
      </InfoCard>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import InfoCard from '@/components/common/InfoCard.vue'
import JsonViewer from '@/components/common/JsonViewer.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import SystemStatusBar from '@/components/common/SystemStatusBar.vue'
import {
  agentNameToLabel,
  backendToLabel,
  booleanToLabel,
  llmProviderToLabel,
} from '@/utils/formatters'
import { useAppStateStore } from '@/stores/appState'

const store = useAppStateStore()
const healthStatus = computed(() => store.healthStatus)
const knowledgeBackendStatus = computed(() => store.knowledgeBackendStatus)
const drugResponse = computed(() => store.latestDrugSafetyResponse)
const symptomResponse = computed(() => store.latestSymptomConsultResponse)

function formatAgentList(values) {
  if (!Array.isArray(values) || values.length === 0) {
    return '暂无'
  }
  return values.map((item) => agentNameToLabel(item)).join('、')
}
</script>

<style scoped>
.text-body {
  color: var(--color-text-main);
  font-size: 14px;
  font-weight: 500;
  line-height: 1.6;
}
</style>
