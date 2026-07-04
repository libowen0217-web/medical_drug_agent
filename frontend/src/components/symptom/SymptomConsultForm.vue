<template>
  <div class="stack-md">
    <InfoCard title="症状信息" description="录入顾客主要症状，辅助药师进行红旗症状筛查和 OTC 用药判断。">
      <el-form label-position="top" class="symptom-form">
        <el-form-item label="症状描述">
          <el-input
            v-model="localForm.symptomText"
            type="textarea"
            :rows="3"
            placeholder="请输入症状、持续时间和补充信息，例如：发热、头痛、咽痛，两天了"
          />
        </el-form-item>

        <div class="symptom-grid">
          <el-form-item label="体温（℃）">
            <el-input-number v-model="localForm.temperatureC" :min="34" :max="43" :step="0.1" style="width: 100%" />
          </el-form-item>
          <el-form-item label="持续时间（天）">
            <el-input-number v-model="localForm.durationDays" :min="0" :max="60" style="width: 100%" />
          </el-form-item>
          <el-form-item label="严重程度">
            <el-select v-model="localForm.severity" style="width: 100%">
              <el-option label="轻度" value="mild" />
              <el-option label="中度" value="moderate" />
              <el-option label="较重" value="severe" />
            </el-select>
          </el-form-item>
        </div>

        <div class="quick-cases">
          <div class="subsection-title">快捷案例</div>
          <div class="quick-row">
            <el-button size="small" plain @click="applyDefaultCase">普通感冒案例</el-button>
            <el-button size="small" type="warning" plain @click="applyRedFlagCase">红旗症状案例</el-button>
            <el-button size="small" type="info" plain @click="applyHeadacheCase">轻症头痛案例</el-button>
          </div>
        </div>
      </el-form>
    </InfoCard>

    <InfoCard title="患者信息" description="当前用药可留空；如已知用药，系统会优先用于重复用药和相互作用复核。">
      <el-form label-position="top" class="patient-form">
        <div class="patient-grid">
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

          <el-form-item label="当前用药">
            <DrugSearchSelect
              v-model="localForm.currentDrugs"
              :options="drugOptions"
              multiple
              :loading="loadingOptions"
              :load-failed="loadOptionsFailed"
              placeholder="可留空；如有长期用药请补充"
            />
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
        </div>

        <div class="consult-action-panel">
          <div class="consult-action-content">
            <section class="inline-section">
              <div class="subsection-title">特殊人群</div>
              <SpecialPatientSelector v-model="localForm.specialFactors" :age="localForm.age" :sex="localForm.sex" />
            </section>

            <section class="inline-section">
              <div class="subsection-title">用药方式</div>
              <el-radio-group v-model="localForm.doseMode" size="small">
                <el-radio-button value="label_reference">说明书参考剂量</el-radio-button>
                <el-radio-button value="user_input">手动填写剂量</el-radio-button>
              </el-radio-group>
            </section>
          </div>

          <div class="consult-action-footer">
            <span class="action-note">未填写当前用药时，仍可生成候选 OTC 药物，后续建议结合用药信息复核。</span>
            <el-button type="primary" size="large" :loading="submitting" @click="handleSubmit">
              开始问诊辅助分析
            </el-button>
          </div>
        </div>

        <div v-if="localForm.doseMode === 'user_input'" class="dose-detail-grid">
          <el-form-item label="单次剂量（mg）">
            <el-input-number v-model="localForm.singleDoseMg" :min="0" :step="50" style="width: 100%" />
          </el-form-item>
          <el-form-item label="每日次数">
            <el-input-number v-model="localForm.timesPerDay" :min="1" :step="1" style="width: 100%" />
          </el-form-item>
          <el-form-item label="用药天数">
            <el-input-number v-model="localForm.doseDurationDays" :min="1" :step="1" style="width: 100%" />
          </el-form-item>
        </div>
      </el-form>
    </InfoCard>
  </div>
</template>

<script setup>
import { ElMessage } from 'element-plus'
import { reactive } from 'vue'
import InfoCard from '@/components/common/InfoCard.vue'
import SpecialPatientSelector from '@/components/common/SpecialPatientSelector.vue'
import TagTextInput from '@/components/common/TagTextInput.vue'
import DrugSearchSelect from '@/components/drug/DrugSearchSelect.vue'
import { deriveSpecialFactors, validatePatientContext } from '@/utils/validators'

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
  symptomText: '发热、头痛、咽痛，两天了',
  age: 68,
  sex: 'unknown',
  temperatureC: 38.5,
  durationDays: 2,
  severity: 'moderate',
  currentDrugs: ['硝苯地平'],
  diseases: ['高血压'],
  specialFactors: [],
  allergies: [],
  doseMode: 'label_reference',
  singleDoseMg: 400,
  timesPerDay: 3,
  doseDurationDays: 3,
})

function applyDefaultCase() {
  Object.assign(localForm, {
    symptomText: '发热、头痛、咽痛，两天了',
    age: 68,
    sex: 'unknown',
    temperatureC: 38.5,
    durationDays: 2,
    severity: 'moderate',
    currentDrugs: ['硝苯地平'],
    diseases: ['高血压'],
    specialFactors: [],
    allergies: [],
    doseMode: 'label_reference',
  })
}

function applyRedFlagCase() {
  Object.assign(localForm, {
    symptomText: '胸痛，伴呼吸困难，最近还有咳血',
    age: 70,
    sex: 'unknown',
    temperatureC: 37.2,
    durationDays: 7,
    severity: 'severe',
    currentDrugs: ['硝苯地平'],
    diseases: ['高血压'],
    specialFactors: [],
    allergies: [],
    doseMode: 'label_reference',
  })
}

function applyHeadacheCase() {
  Object.assign(localForm, {
    symptomText: '头痛，一天了',
    age: 30,
    sex: 'female',
    temperatureC: 36.8,
    durationDays: 1,
    severity: 'mild',
    currentDrugs: [],
    diseases: [],
    specialFactors: [],
    allergies: [],
    doseMode: 'label_reference',
  })
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
    symptom_text: localForm.symptomText,
    age: localForm.age,
    sex: localForm.sex,
    temperature_c: localForm.temperatureC,
    duration_days: localForm.durationDays,
    severity: localForm.severity,
    current_drugs: localForm.currentDrugs,
    diseases: localForm.diseases,
    patient_factors: finalSpecialFactors,
    allergies: localForm.allergies,
    dose:
      localForm.doseMode === 'user_input'
        ? {
            dose_mode: 'user_input',
            single_dose_mg: localForm.singleDoseMg,
            times_per_day: localForm.timesPerDay,
            duration_days: localForm.doseDurationDays,
          }
        : {
            dose_mode: 'label_reference',
          },
  })
}
</script>

<style scoped>
.symptom-form,
.patient-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.symptom-grid,
.patient-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  column-gap: 24px;
  row-gap: 14px;
}

.symptom-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.quick-cases {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding-top: 14px;
  border-top: 1px dashed var(--color-border);
}

.quick-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.subsection-title {
  color: var(--color-primary-dark);
  font-size: 14px;
  font-weight: 800;
}

.consult-action-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding-top: 16px;
  border-top: 1px dashed var(--color-border);
}

.consult-action-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
  align-items: stretch;
}

.inline-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.consult-action-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding-top: 14px;
  border-top: 1px solid var(--color-border);
}

.action-note {
  flex: 1;
  color: var(--color-text-secondary);
  font-size: 13px;
  line-height: 1.6;
}

.consult-action-footer .el-button {
  flex: 0 0 auto;
  min-width: 200px;
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

:deep(.el-form-item) {
  margin-bottom: 0;
}

:deep(.el-form-item__label) {
  padding-bottom: 6px;
  color: var(--color-primary-dark);
  font-weight: 700;
}

@media (max-width: 900px) {
  .symptom-grid,
  .patient-grid,
  .dose-detail-grid {
    grid-template-columns: 1fr;
  }

  .consult-action-footer {
    align-items: stretch;
    flex-direction: column;
  }

  .consult-action-footer .el-button {
    width: 100%;
    min-width: 0;
  }
}
</style>
