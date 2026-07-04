function normalizeSexValue(sex) {
  const raw = String(sex || '').trim().toLowerCase()
  if (raw === '男' || raw === 'male') return 'male'
  if (raw === '女' || raw === 'female') return 'female'
  return 'unknown'
}

function uniqueFactors(values) {
  return [...new Set((Array.isArray(values) ? values : []).filter(Boolean))]
}

export function deriveSpecialFactors({ age, sex, selectedFactors }) {
  const normalizedAge = Number(age ?? 0)
  const normalizedSex = normalizeSexValue(sex)
  const selected = uniqueFactors(selectedFactors)
  const factors = []

  if (normalizedAge < 14) {
    factors.push('儿童')
  } else if (normalizedAge >= 65) {
    factors.push('老年人')
  }

  const pregnancyAllowedBySex = normalizedSex !== 'male'
  const pregnancyAllowedByAge = normalizedAge >= 12 && normalizedAge <= 55
  if (selected.includes('孕妇') && pregnancyAllowedBySex && pregnancyAllowedByAge) {
    factors.push('孕妇')
  }

  return uniqueFactors(factors)
}

export function validatePatientContext({ age, sex, specialFactors }) {
  const warnings = []
  const errors = []
  const normalizedAge = Number(age ?? 0)
  const normalizedSex = normalizeSexValue(sex)
  const factors = uniqueFactors(specialFactors)

  if (normalizedAge < 14) warnings.push('当前年龄已按儿童场景处理。')
  if (normalizedAge >= 65) warnings.push('当前年龄已按老年患者场景处理。')

  if (factors.includes('儿童') && factors.includes('老年人')) {
    errors.push('儿童与老年人身份不能同时存在。')
  }
  if (normalizedAge < 14 && factors.includes('老年人')) {
    errors.push('当前年龄不能按老年人场景处理。')
  }
  if (normalizedAge >= 65 && factors.includes('儿童')) {
    errors.push('当前年龄不能按儿童场景处理。')
  }
  if (normalizedAge >= 14 && normalizedAge < 65 && factors.includes('儿童')) {
    errors.push('当前年龄不在儿童场景范围内。')
  }
  if (normalizedAge >= 14 && normalizedAge < 65 && factors.includes('老年人')) {
    errors.push('当前年龄不在老年人场景范围内。')
  }
  if (normalizedSex === 'male' && factors.includes('孕妇')) {
    errors.push('患者性别与孕妇身份不匹配，请修改患者信息。')
  }
  if (factors.includes('孕妇') && (normalizedAge < 12 || normalizedAge > 55)) {
    errors.push('当前年龄与孕妇身份不匹配，请核实患者信息。')
  }

  return {
    valid: errors.length === 0,
    warnings,
    errors,
  }
}

export function getSpecialPatientUIState({ age, sex, selectedFactors }) {
  const normalizedAge = Number(age ?? 0)
  const normalizedSex = normalizeSexValue(sex)
  const finalFactors = deriveSpecialFactors({ age: normalizedAge, sex: normalizedSex, selectedFactors })
  const validation = validatePatientContext({ age: normalizedAge, sex: normalizedSex, specialFactors: finalFactors })

  let pregnancyDisabledReason = ''
  if (normalizedSex === 'male') {
    pregnancyDisabledReason = '男性患者不能选择孕妇。'
  } else if (normalizedAge < 12 || normalizedAge > 55) {
    pregnancyDisabledReason = '当前年龄与孕妇身份不匹配，请核实患者信息。'
  }

  return {
    finalFactors,
    validation,
    childActive: normalizedAge < 14,
    elderlyActive: normalizedAge >= 65,
    pregnancyChecked: finalFactors.includes('孕妇'),
    pregnancyDisabled: Boolean(pregnancyDisabledReason),
    pregnancyDisabledReason,
  }
}
