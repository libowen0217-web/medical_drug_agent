<template>
  <InfoCard title="评估信息" description="填写本次顾客用药场景，系统将辅助判断是否存在用药风险。">
    <el-form label-position="top" class="drug-safety-form">
      <section class="form-section">
        <div class="section-title">药物信息</div>
        <div class="workbench-grid">
          <el-form-item label="当前用药">
            <DrugSearchSelect
              v-model="localForm.currentDrugs"
              :options="drugOptions"
              multiple
              :loading="loadingOptions"
              :load-failed="loadOptionsFailed"
            />
          </el-form-item>
          <el-form-item label="拟新增药物">
            <DrugSearchSelect
              v-model="localForm.newDrug"
              :options="drugOptions"
              :loading="loadingOptions"
              :load-failed="loadOptionsFailed"
            />
          </el-form-item>
        </div>

        <div class="quick-combo">
          <div class="subsection-title">快捷组合</div>
          <div class="quick-row">
            <el-button size="small" plain @click="applyExample(['硝苯地平'], '布洛芬')">硝苯地平 + 布洛芬</el-button>
            <el-button size="small" plain @click="applyExample(['华法林'], '布洛芬')">华法林 + 布洛芬</el-button>
            <el-button size="small" plain @click="applyExample(['华法林'], '阿司匹林')">华法林 + 阿司匹林</el-button>
          </div>
        </div>
      </section>

      <section class="form-section">
        <div class="section-title">患者信息</div>
        <div class="workbench-grid">
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
              placeholder="可选或输入"
            >
              <el-option v-for="item in diseaseOptions" :key="item" :label="item" :value="item" />
            </el-select>
          </el-form-item>

          <el-form-item label="过敏史">
            <TagTextInput v-model="localForm.allergies" placeholder="如青霉素、阿司匹林" />
          </el-form-item>

          <el-form-item label="特殊人群">
            <SpecialPatientSelector v-model="localForm.specialFactors" :age="localForm.age" :sex="localForm.sex" />
          </el-form-item>

          <el-form-item label="用药方式">
            <div class="dose-mode-box">
              <el-radio-group v-model="localForm.doseMode" size="small">
                <el-radio-button value="label_reference">说明书参考剂量</el-radio-button>
                <el-radio-button value="user_input">手动填写剂量</el-radio-button>
              </el-radio-group>
            </div>
          </el-form-item>
        </div>

        <div v-if="localForm.doseMode === 'user_input'" class="dose-detail-grid">
          <el-form-item label="单次剂量（mg）">
            <el-input-number v-model="localForm.singleDoseMg" :min="0" :step="50" style="width: 100%" />
          </el-form-item>
          <el-form-item label="每日次数">
            <el-input-number v-model="localForm.timesPerDay" :min="1" :step="1" style="width: 100%" />
          </el-form-item>
          <el-form-item label="用药天数">
            <el-input-number v-model="localForm.durationDays" :min="1" :step="1" style="width: 100%" />
          </el-form-item>
        </div>
      </section>

      <div class="submit-row">
        <span class="submit-note">本工具用于药师辅助判断，不能替代处方审核或医生诊疗。</span>
        <el-button type="primary" size="large" :loading="submitting" @click="handleSubmit">
          开始用药安全评估
        </el-button>
      </div>
    </el-form>
  </InfoCard>
</template>

<script setup>
import { ElMessage } from 'element-plus'
import { reactive } from 'vue'
import InfoCard from '@/components/common/InfoCard.vue'
import SpecialPatientSelector from '@/components/common/SpecialPatientSelector.vue'
import TagTextInput from '@/components/common/TagTextInput.vue'
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
  allergies: [],
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
    allergies: localForm.allergies,
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
.drug-safety-form {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.form-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.form-section + .form-section {
  padding-top: 18px;
  border-top: 1px solid var(--color-border);
}

.section-title,
.subsection-title {
  color: var(--color-primary-dark);
  font-weight: 800;
}

.section-title {
  font-size: 15px;
}

.subsection-title {
  font-size: 14px;
}

.workbench-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  column-gap: 24px;
  row-gap: 14px;
}

.quick-combo {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 4px;
  padding: 12px 0 2px;
  border-top: 1px dashed var(--color-border);
}

.quick-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.dose-mode-box {
  display: flex;
  align-items: center;
  min-height: 32px;
}

.dose-detail-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
  padding: 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: #f8fbff;
}

.submit-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--color-border);
}

.submit-note {
  color: var(--color-text-secondary);
  font-size: 13px;
}

:deep(.el-form-item) {
  margin-bottom: 0;
}

:deep(.el-form-item__label) {
  padding-bottom: 6px;
  color: var(--color-primary-dark);
  font-weight: 700;
}

@media (max-width: 860px) {
  .workbench-grid,
  .dose-detail-grid {
    grid-template-columns: 1fr;
  }

  .submit-row {
    align-items: stretch;
    flex-direction: column;
  }
}
</style>
