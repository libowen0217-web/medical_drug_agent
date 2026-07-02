<template>
  <InfoCard title="OTC 候选药" description="仅面向社区药店和基层轻症场景的辅助候选药，不替代医生处方。">
    <div v-if="items.length" class="stack-sm">
      <div v-for="(item, index) in items" :key="index" class="metric-tile">
        <div class="candidate-head">
          <div class="candidate-title">{{ item.drug_class || '候选药类别' }}</div>
          <el-tag v-if="item.requires_doctor_confirmation" type="warning" round>需医生确认</el-tag>
        </div>
        <div><strong>候选药：</strong>{{ (item.candidate_drugs || []).join('、') || '暂无' }}</div>
        <div><strong>注意事项：</strong>{{ item.caution || '请结合说明书和个体情况进一步确认。' }}</div>
        <div><strong>说明：</strong>{{ item.reason || '暂无' }}</div>
      </div>
    </div>
    <el-empty v-else description="当前未匹配到适合展示的 OTC 候选药。" />
  </InfoCard>
</template>

<script setup>
import InfoCard from '@/components/common/InfoCard.vue'

defineProps({
  items: {
    type: Array,
    default: () => [],
  },
})
</script>

<style scoped>
.candidate-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
  margin-bottom: 10px;
}

.candidate-title {
  color: var(--color-primary-dark);
  font-size: 16px;
  font-weight: 700;
}
</style>
