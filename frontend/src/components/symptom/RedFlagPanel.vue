<template>
  <InfoCard title="红旗症状筛查">
    <div class="stack-sm">
      <el-alert
        v-if="redFlagTriggered"
        type="error"
        :closable="false"
        show-icon
        title="当前描述涉及严重疾病或红旗风险，不适合由本系统生成 OTC 候选药，请由医生进一步评估。"
      />
      <el-alert
        v-else
        type="success"
        :closable="false"
        show-icon
        title="当前未触发明确红旗阻断，可继续查看候选药辅助评估结果。"
      />

      <div v-if="flags.length" class="stack-sm">
        <div v-for="(item, index) in flags" :key="index" class="metric-tile">
          <div><strong>紧急程度：</strong>{{ item.urgency_level || '暂无' }}</div>
          <div><strong>说明：</strong>{{ item.description || '暂无' }}</div>
          <div><strong>处理提示：</strong>{{ item.action || '暂无' }}</div>
          <div v-if="(item.matched_keywords || []).length">
            <strong>命中词：</strong>{{ item.matched_keywords.join('、') }}
          </div>
        </div>
      </div>
    </div>
  </InfoCard>
</template>

<script setup>
import InfoCard from '@/components/common/InfoCard.vue'

defineProps({
  redFlagTriggered: {
    type: Boolean,
    default: false,
  },
  flags: {
    type: Array,
    default: () => [],
  },
})
</script>
