<template>
  <el-form label-position="top" class="patient-form">
    <div class="form-grid compact-patient-grid">
      <el-form-item label="年龄">
        <el-input-number v-model="model.age" :min="0" :max="120" style="width: 100%" />
      </el-form-item>

      <el-form-item label="性别">
        <el-select v-model="model.sex" style="width: 100%">
          <el-option label="未知" value="unknown" />
          <el-option label="男" value="male" />
          <el-option label="女" value="female" />
        </el-select>
      </el-form-item>

      <el-form-item v-if="showCurrentDrugs" label="当前用药" class="is-wide">
        <DrugSearchSelect
          v-model="model.currentDrugs"
          :options="drugOptions"
          multiple
          :loading="loadingOptions"
          :load-failed="loadOptionsFailed"
          placeholder="可留空；如有长期用药，请补充"
        />
      </el-form-item>

      <el-form-item label="基础疾病">
        <el-select
          v-model="model.diseases"
          multiple
          filterable
          allow-create
          default-first-option
          style="width: 100%"
          placeholder="可选或输入"
        >
          <el-option v-for="item in diseaseOptions" :key="item" :label="item" :value="item" />
        </el-select>
      </el-form-item>

      <el-form-item label="过敏史">
        <TagTextInput v-model="model.allergies" placeholder="如青霉素、阿司匹林" />
      </el-form-item>

      <el-form-item label="特殊人群" class="is-wide">
        <SpecialPatientSelector v-model="model.specialFactors" :age="model.age" :sex="model.sex" />
      </el-form-item>
    </div>
  </el-form>
</template>

<script setup>
import DrugSearchSelect from '@/components/drug/DrugSearchSelect.vue'
import SpecialPatientSelector from '@/components/common/SpecialPatientSelector.vue'
import TagTextInput from '@/components/common/TagTextInput.vue'

defineProps({
  model: {
    type: Object,
    required: true,
  },
  drugOptions: {
    type: Array,
    default: () => [],
  },
  loadingOptions: {
    type: Boolean,
    default: false,
  },
  loadOptionsFailed: {
    type: Boolean,
    default: false,
  },
  showCurrentDrugs: {
    type: Boolean,
    default: true,
  },
})

const diseaseOptions = ['高血压', '糖尿病', '胃溃疡', '肝功能异常', '肾功能不全', '哮喘', '冠心病']
</script>
