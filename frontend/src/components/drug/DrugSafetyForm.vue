<template>
  <div class="stack-md">
    <InfoCard title="药物信息" description="支持药库搜索、当前用药多选、拟新增药物单选，并可快速填入演示案例。">
      <div class="stack-sm">
        <div>
          <div class="field-label">当前用药</div>
          <DrugSearchSelect
            v-model="localForm.currentDrugs"
            :options="drugOptions"
            multiple
            :loading="loadingOptions"
            :load-failed="loadOptionsFailed"
          />
        </div>
        <div>
          <div class="field-label">拟新增药物</div>
          <DrugSearchSelect
            v-model="localForm.newDrug"
            :options="drugOptions"
            :loading="loadingOptions"
            :load-failed="loadOptionsFailed"
          />
        </div>
        <div class="example-row">
          <el-button @click="applyExample(['硝苯地平'], '布洛芬')">硝苯地平 + 布洛芬</el-button>
          <el-button @click="applyExample(['华法林'], '布洛芬')">华法林 + 布洛芬</el-button>
          <el-button @click="applyExample(['华法林'], '阿司匹林')">华法林 + 阿司匹林</el-button>
        </div>
      </div>
    </InfoCard>

    <InfoCard title="患者信息" description="支持基础疾病、特殊患者因素和一致性校验。">
      <div class="stack-sm">
        <el-form label-position="top">
          <el-form-item label="年龄">
            <el-input-number v-model="localForm.age" :min="0" :max="120" style="width: 100%" />
          </el-form-item>
          <el-form-item label="性别">
            <el-select v-model="localForm.sex" style="width: 100%">
              <el-option label="未知" value="unknown" />
              <el-option label="男" value="male" />
              <el-option label="女" value="female" />
            </el-select>
          </el-form-item>
          <el-form-item label="基础疾病">
            <el-select
              v-model="localForm.diseases"
              multiple
              filterable
              allow-create
              default-first-option
              style="width: 100%"
            >
              <el-option v-for="item in diseaseOptions" :key="item" :label="item" :value="item" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <SpecialPatientSelector
              v-model="localForm.specialFactors"
              :age="localForm.age"
              :sex="localForm.sex"
            />
          </el-form-item>
        </el-form>
      </div>
    </InfoCard>

    <InfoCard title="剂量评估方式" description="可选择使用说明书参考剂量模拟，或手动填写本次计划使用的剂量。">
      <div class="stack-sm">
        <el-radio-group v-model="localForm.doseMode" class="dose-mode-group">
          <el-radio value="label_reference">使用说明书参考剂量模拟</el-radio>
          <el-radio value="user_input">手动填写剂量</el-radio>
        </el-radio-group>

        <div class="dose-note">
          说明书参考剂量仅用于系统初步评估，不代表患者实际服用剂量，也不构成处方建议。
        </div>

        <template v-if="localForm.doseMode === 'user_input'">
          <el-form label-position="top">
            <el-form-item label="单次剂量（mg）">
              <el-input-number v-model="localForm.singleDoseMg" :min="0" :step="50" style="width: 100%" />
            </el-form-item>
            <el-form-item label="每日次数">
              <el-input-number v-model="localForm.timesPerDay" :min="1" :step="1" style="width: 100%" />
            </el-form-item>
            <el-form-item label="使用天数">
              <el-input-number v-model="localForm.durationDays" :min="1" :step="1" style="width: 100%" />
            </el-form-item>
          </el-form>
        </template>

        <el-button type="primary" size="large" :loading="submitting" @click="handleSubmit">
          开始多智能体用药安全检查
        </el-button>
      </div>
    </InfoCard>
  </div>
</template>

<script setup>
import { ElMessage } from 'element-plus'
import { reactive } from 'vue'
import InfoCard from '@/components/common/InfoCard.vue'
import SpecialPatientSelector from '@/components/common/SpecialPatientSelector.vue'
import { deriveSpecialFactors, validatePatientContext } from '@/utils/validators'
import DrugSearchSelect from './DrugSearchSelect.vue'

defineProps({
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
  submitting: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['submit'])

const diseaseOptions = ['高血压', '糖尿病', '胃溃疡', '肝功能异常', '肾功能不全', '哮喘', '冠心病']

const localForm = reactive({
  currentDrugs: ['硝苯地平'],
  newDrug: '布洛芬',
  age: 68,
  sex: 'unknown',
  diseases: ['高血压'],
  specialFactors: [],
  doseMode: 'label_reference',
  singleDoseMg: 400,
  timesPerDay: 3,
  durationDays: 5,
})

function applyExample(currentDrugs, newDrug) {
  localForm.currentDrugs = currentDrugs
  localForm.newDrug = newDrug
}

function handleSubmit() {
  const finalSpecialFactors = deriveSpecialFactors({
    age: localForm.age,
    sex: localForm.sex,
    selectedFactors: localForm.specialFactors,
  })
  const finalValidation = validatePatientContext({
    age: localForm.age,
    sex: localForm.sex,
    specialFactors: finalSpecialFactors,
  })

  finalValidation.warnings.forEach((message) => ElMessage.warning(message))
  if (!finalValidation.valid) {
    finalValidation.errors.forEach((message) => ElMessage.error(message))
    return
  }

  emit('submit', {
    current_drugs: localForm.currentDrugs,
    new_drug: localForm.newDrug,
    age: localForm.age,
    diseases: localForm.diseases,
    patient_factors: finalSpecialFactors,
    dose:
      localForm.doseMode === 'user_input'
        ? {
            dose_mode: 'user_input',
            single_dose_mg: localForm.singleDoseMg,
            times_per_day: localForm.timesPerDay,
            duration_days: localForm.durationDays,
          }
        : {
            dose_mode: 'label_reference',
          },
  })
}
</script>

<style scoped>
.field-label {
  margin-bottom: 8px;
  color: var(--color-primary-dark);
  font-size: 14px;
  font-weight: 600;
}

.example-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.dose-mode-group {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.dose-note {
  padding: 12px 14px;
  border-radius: 12px;
  background: #f3f8ff;
  border: 1px solid #d9e8ff;
  color: #49627f;
  font-size: 13px;
  line-height: 1.7;
}
</style>
