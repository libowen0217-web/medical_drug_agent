<template>
  <div class="stack-md">
    <template v-if="response">
      <InfoCard title="用药安全检查结果" description="聚焦综合风险、风险发现、证据引用和双版本报告输出。">
        <div class="metric-grid">
          <div class="metric-tile">
            <div class="metric-label">运行状态</div>
            <div class="metric-value">{{ statusToLabel(response.status) }}</div>
          </div>
          <div class="metric-tile">
            <div class="metric-label">综合风险等级</div>
            <div class="metric-value"><RiskTag :level="data.overall_risk_level" /></div>
          </div>
          <div class="metric-tile">
            <div class="metric-label">风险发现数量</div>
            <div class="metric-value">{{ (data.risk_findings || []).length }}</div>
          </div>
          <div class="metric-tile">
            <div class="metric-label">安全提示数量</div>
            <div class="metric-value">{{ (data.safety_warnings || []).length }}</div>
          </div>
        </div>
      </InfoCard>

      <InfoCard v-if="showAgentChain" title="Agent 执行链路">
        <div class="stack-sm">
          <div><strong>执行模式：</strong>{{ multiAgent.execution_mode || '暂无' }}</div>
          <div><strong>已执行 Agent：</strong>{{ agentList(multiAgent.agents_executed) }}</div>
          <div><strong>失败 Agent：</strong>{{ agentList(multiAgent.agents_failed) }}</div>
        </div>
      </InfoCard>

      <RiskFindingList :findings="data.risk_findings || []" />
      <EvidenceList :items="evidenceItems" />

      <InfoCard title="报告结果">
        <el-tabs>
          <el-tab-pane label="药师版报告">
            <ReportPanel :content="data.pharmacist_report || '暂无'" />
          </el-tab-pane>
          <el-tab-pane label="患者版报告">
            <ReportPanel :content="data.patient_report || '暂无'" />
          </el-tab-pane>
        </el-tabs>
      </InfoCard>

      <JsonViewer v-if="showJson" :data="response" title="查看完整 JSON" />
    </template>

    <EmptyState v-else description="请先在左侧输入药物和患者信息，再开始用药安全检查。" />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import EmptyState from '@/components/common/EmptyState.vue'
import InfoCard from '@/components/common/InfoCard.vue'
import JsonViewer from '@/components/common/JsonViewer.vue'
import ReportPanel from '@/components/common/ReportPanel.vue'
import RiskTag from '@/components/common/RiskTag.vue'
import { agentNameToLabel, formatEvidenceItems, statusToLabel } from '@/utils/formatters'
import EvidenceList from './EvidenceList.vue'
import RiskFindingList from './RiskFindingList.vue'

const props = defineProps({
  response: {
    type: Object,
    default: null,
  },
  showJson: {
    type: Boolean,
    default: false,
  },
  showAgentChain: {
    type: Boolean,
    default: false,
  },
})

const data = computed(() => props.response?.data || {})
const multiAgent = computed(() => props.response?.metadata?.multi_agent || {})
const evidenceItems = computed(() =>
  formatEvidenceItems((data.value.risk_findings || []).flatMap((item) => item.evidence_items || []))
)

function agentList(values) {
  if (!Array.isArray(values) || values.length === 0) {
    return '暂无'
  }
  return values.map((item) => agentNameToLabel(item)).join('、')
}
</script>
