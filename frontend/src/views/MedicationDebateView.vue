<template>
  <div class="page-view">
    <PageHeader
      title="候选药协作评估"
      subtitle="读取最近一次症状问诊结果，对候选 OTC 药物进行多 Agent 协作排序和风险意见汇总。"
    />

    <InfoCard v-if="!summary && results.length === 0 && !referralRequired" title="协作评估入口">
      <div class="demo-entry">
        <div>
          <h3>暂无症状问诊结果</h3>
          <p>请先完成一次症状问诊辅助分析，系统会自动带入候选 OTC 药物、候选药安全检查和多 Agent 协作意见。</p>
        </div>
        <div class="action-row">
          <el-button type="primary" @click="goSymptomConsult">前往症状问诊</el-button>
          <el-button @click="loadDemoCase">加载演示案例</el-button>
        </div>
      </div>
    </InfoCard>

    <InfoCard v-else-if="referralRequired" title="红旗阻断">
      <el-alert
        type="error"
        :closable="false"
        show-icon
        title="最近一次问诊涉及严重疾病或红旗风险，不适合进行候选 OTC 药物协作排序。"
      />
    </InfoCard>

    <template v-else>
      <InfoCard title="最终推荐结论">
        <div class="result-section">
          <el-alert
            type="info"
            :closable="false"
            show-icon
            :title="summary?.conclusion || '系统已完成候选药协作评估，最终选择仍需医生或药师复核。'"
          />
          <div class="metric-grid">
            <div class="metric-tile">
              <div class="metric-label">候选药数量</div>
              <div class="metric-value">{{ results.length }}</div>
            </div>
            <div class="metric-tile">
              <div class="metric-label">协作评估</div>
              <div class="metric-value">{{ summary?.debate_enabled ? '已启用' : '未启用' }}</div>
            </div>
            <div class="metric-tile">
              <div class="metric-label">红旗阻断</div>
              <div class="metric-value">{{ summary?.red_flag_blocked ? '是' : '否' }}</div>
            </div>
          </div>
        </div>
      </InfoCard>

      <InfoCard title="候选药排序">
        <div class="rank-grid">
          <CandidateRankCard
            v-for="(item, index) in results"
            :key="`${item.candidate_drug}-${index}`"
            :item="item"
            :index="index"
          />
        </div>
      </InfoCard>

      <InfoCard title="各 Agent 协作意见">
        <div class="opinion-grid">
          <div v-for="(item, index) in results" :key="`opinions-${item.candidate_drug}-${index}`" class="opinion-group">
            <h4>{{ item.candidate_drug }}</h4>
            <AgentOpinionList :opinions="item.agent_opinions || []" />
          </div>
        </div>
      </InfoCard>

      <el-collapse class="advanced-collapse">
        <el-collapse-item title="高级详情" name="advanced">
          <DebateSummary :summary="summary" />
        </el-collapse-item>
      </el-collapse>
    </template>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import InfoCard from '@/components/common/InfoCard.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import AgentOpinionList from '@/components/debate/AgentOpinionList.vue'
import CandidateRankCard from '@/components/debate/CandidateRankCard.vue'
import DebateSummary from '@/components/debate/DebateSummary.vue'
import { useAppStateStore } from '@/stores/appState'

const router = useRouter()
const store = useAppStateStore()
const summary = computed(() => store.latestDebateSummary)
const results = computed(() => store.latestDebateResults || [])
const referralRequired = computed(() => Boolean(store.latestSymptomConsultResponse?.data?.referral_required))

function goSymptomConsult() {
  router.push('/symptom-consult')
}

function loadDemoCase() {
  store.setSymptomConsultResponse({
    status: 'success',
    data: {
      referral_required: false,
      medication_debate_summary: {
        debate_enabled: true,
        red_flag_blocked: false,
        conclusion: '演示案例中，对乙酰氨基酚在当前信息下风险提示相对较少；最终仍需药师结合患者情况复核。',
      },
      debate_results: [
        {
          rank: 1,
          candidate_drug: '对乙酰氨基酚',
          total_score: 86,
          final_level: 'preferred_candidate',
          summary: '适用于发热和轻中度疼痛场景，需关注肝功能和剂量上限。',
          strengths: ['症状匹配度较高', '无当前用药时可先做剂量参考评估'],
          cautions: ['肝功能异常或饮酒者需谨慎'],
          agent_opinions: [
            {
              agent_name: 'symptom-fit-agent',
              score_delta: 12,
              risk_level: 'low',
              opinion: '与发热、头痛等症状匹配。',
              reasons: ['症状关键词命中'],
              evidence_refs: [],
            },
          ],
        },
        {
          rank: 2,
          candidate_drug: '布洛芬',
          total_score: 72,
          final_level: 'caution_candidate',
          summary: '可用于解热镇痛，但合并高血压、胃部疾病或老年人场景需谨慎。',
          strengths: ['解热镇痛匹配'],
          cautions: ['高血压或胃部疾病需谨慎'],
          agent_opinions: [
            {
              agent_name: 'patient-factor-risk-agent',
              score_delta: -8,
              risk_level: 'medium',
              opinion: '存在患者因素相关注意事项。',
              reasons: ['老年人或高血压场景需复核'],
              evidence_refs: [],
            },
          ],
        },
      ],
    },
    metadata: {
      debate_enabled: true,
    },
  })
}
</script>

<style scoped>
.demo-entry {
  display: flex;
  justify-content: space-between;
  gap: 18px;
  align-items: center;
}

.demo-entry h3,
.opinion-group h4 {
  margin: 0 0 8px;
  color: var(--color-primary-dark);
}

.demo-entry p {
  margin: 0;
  color: var(--color-text-secondary);
  line-height: 1.7;
}

.rank-grid,
.opinion-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 14px;
}

@media (max-width: 760px) {
  .demo-entry {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
