<template>
  <div class="page-view">
    <PageHeader
      title="候选药协作评估"
      subtitle="读取最近一次症状问诊结果，展示候选药排序、协作评估摘要，以及各 Agent 的结构化观点。"
    />

    <EmptyState
      v-if="!summary && results.length === 0 && !referralRequired"
      description="请先在“症状问诊辅助”页面完成一次分析，然后查看候选药协作评估结果。"
    />

    <InfoCard v-else-if="referralRequired" title="红旗阻断">
      <el-alert
        type="error"
        :closable="false"
        show-icon
        title="当前描述涉及严重疾病或红旗风险，不适合由本系统生成 OTC 候选药，请由医生进一步评估。"
      />
    </InfoCard>

    <template v-else>
      <InfoCard title="协作评估总览">
        <div class="metric-grid">
          <div class="metric-tile">
            <div class="metric-label">候选药数量</div>
            <div class="metric-value">{{ results.length }}</div>
          </div>
          <div class="metric-tile">
            <div class="metric-label">红旗阻断</div>
            <div class="metric-value">{{ summary?.red_flag_blocked ? '是' : '否' }}</div>
          </div>
        </div>
      </InfoCard>

      <DebateSummary :summary="summary" />

      <template v-if="!summary?.red_flag_blocked">
        <div class="stack-md">
          <CandidateRankCard
            v-for="(item, index) in results"
            :key="`${item.candidate_drug}-${index}`"
            :item="item"
            :index="index"
          />
          <AgentOpinionList
            v-for="(item, index) in results"
            :key="`opinions-${item.candidate_drug}-${index}`"
            :opinions="item.agent_opinions || []"
          />
        </div>
      </template>
    </template>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import EmptyState from '@/components/common/EmptyState.vue'
import InfoCard from '@/components/common/InfoCard.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import AgentOpinionList from '@/components/debate/AgentOpinionList.vue'
import CandidateRankCard from '@/components/debate/CandidateRankCard.vue'
import DebateSummary from '@/components/debate/DebateSummary.vue'
import { useAppStateStore } from '@/stores/appState'

const store = useAppStateStore()
const summary = computed(() => store.latestDebateSummary)
const results = computed(() => store.latestDebateResults || [])
const referralRequired = computed(() => Boolean(store.latestSymptomConsultResponse?.data?.referral_required))
</script>
