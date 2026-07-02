<template>
  <div class="stack-md">
    <InfoCard title="症状信息" description="聚焦社区药店和基层轻症场景，用于辅助筛查红旗风险与 OTC 候选药。">
      <div class="stack-sm">
        <el-form label-position="top">
          <el-form-item label="症状描述">
            <el-input
              v-model="localForm.symptomText"
              type="textarea"
              :rows="5"
              placeholder="请输入症状、持续时间和补充信息，例如：发热、头痛、咽痛，两天了"
            />
          </el-form-item>
          <el-form-item label="体温（℃）">
            <el-input-number v-model="localForm.temperatureC" :min="34" :max="43" :step="0.1" style="width: 100%" />
          </el-form-item>
          <el-form-item label="持续天数">
            <el-input-number v-model="localForm.durationDays" :min="0" :max="60" style="width: 100%" />
          </el-form-item>
        </el-form>

        <div class="example-row">
          <el-button @click="applyDefaultCase">默认案例</el-button>
          <el-button type="warning" @click="applyRedFlagCase">红旗案例</el-button>
          <el-button type="info" @click="applyHeadacheCase">轻症案例</el-button>
        </div>
      </div>
    </InfoCard>

    <InfoCard title="患者信息" description="即使未提供当前用药，系统也会继续结合疾病、过敏史、特殊人群和剂量做初步评估。">
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
          <el-form-item label="当前用药">
            <DrugSearchSelect
              v-model="localForm.currentDrugs"
              :options="drugOptions"
              multiple
              :loading="loadingOptions"
              :load-failed="loadOptionsFailed"
              placeholder="可留空；如有长期用药，请继续补充"
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
          <el-form-item label="过敏史">
            <TagTextInput
              v-model="localForm.allergies"
              placeholder="请输入过敏药物或过敏源，如：青霉素、阿司匹林、磺胺类"
            />
          </el-form-item>
        </el-form>
      </div>
    </InfoCard>

    <InfoCard title="剂量评估方式" description="默认使用说明书参考剂量模拟；如已有明确计划剂量，也可手动填写。">
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
              <el-input-number v-model="localForm.doseDurationDays" :min="1" :step="1" style="width: 100%" />
            </el-form-item>
          </el-form>
        </template>

        <el-button type="primary" size="large" :loading="submitting" @click="handleSubmit">
          开始症状问诊辅助分析
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
  localForm.symptomText = '发热、头痛、咽痛，两天了'
  localForm.age = 68
  localForm.sex = 'unknown'
  localForm.temperatureC = 38.5
  localForm.durationDays = 2
  localForm.currentDrugs = ['硝苯地平']
  localForm.diseases = ['高血压']
  localForm.specialFactors = []
  localForm.allergies = []
  localForm.doseMode = 'label_reference'
}

function applyRedFlagCase() {
  localForm.symptomText = '胸痛，伴呼吸困难，最近还有咯血'
  localForm.age = 70
  localForm.sex = 'unknown'
  localForm.temperatureC = 37.2
  localForm.durationDays = 7
  localForm.currentDrugs = ['硝苯地平']
  localForm.diseases = ['高血压']
  localForm.specialFactors = []
  localForm.allergies = []
  localForm.doseMode = 'label_reference'
}

function applyHeadacheCase() {
  localForm.symptomText = '头痛，一天了'
  localForm.age = 30
  localForm.sex = 'female'
  localForm.temperatureC = 36.8
  localForm.durationDays = 1
  localForm.currentDrugs = []
  localForm.diseases = []
  localForm.specialFactors = []
  localForm.allergies = []
  localForm.doseMode = 'label_reference'
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
