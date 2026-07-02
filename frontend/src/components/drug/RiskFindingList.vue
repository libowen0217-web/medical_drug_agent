<template>
  <InfoCard title="风险发现" description="仅展示结构化风险信息，不直接生成额外医疗建议。">
    <div v-if="findings.length" class="stack-sm">
      <el-collapse>
        <el-collapse-item
          v-for="(item, index) in findings"
          :key="`${item.title}-${index}`"
          :title="`${index + 1}. ${item.title || '风险发现'}`"
          :name="index"
        >
          <div class="stack-sm">
            <RiskTag :level="item.risk_level" />
            <div><strong>来源：</strong>{{ item.source || '暂无' }}</div>
            <div><strong>描述：</strong>{{ item.description || '暂无' }}</div>
            <div><strong>机制：</strong>{{ item.mechanism || '暂无' }}</div>
            <div><strong>处理提示：</strong>{{ item.recommendation || '暂无' }}</div>
            <div><strong>证据说明：</strong>{{ item.evidence_note || '暂无' }}</div>
            <div><strong>相关药物：</strong>{{ (item.related_drugs || []).join('、') || '暂无' }}</div>
            <div><strong>相关疾病：</strong>{{ (item.related_diseases || []).join('、') || '暂无' }}</div>
          </div>
        </el-collapse-item>
      </el-collapse>
    </div>
    <el-empty v-else description="暂无风险发现" />
  </InfoCard>
</template>

<script setup>
import InfoCard from '@/components/common/InfoCard.vue'
import RiskTag from '@/components/common/RiskTag.vue'

defineProps({
  findings: {
    type: Array,
    default: () => [],
  },
})
</script>
