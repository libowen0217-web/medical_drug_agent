export function normalizeSearchText(text) {
  return String(text || '').trim().toLowerCase()
}

export function matchDrugOption(option, query) {
  const q = normalizeSearchText(query)
  if (!q) {
    return true
  }
  const fields = [
    option?.display_name,
    option?.standard_name,
    option?.pinyin,
    option?.label,
    ...(Array.isArray(option?.aliases) ? option.aliases : []),
  ]
  return fields.some((item) => normalizeSearchText(item).includes(q))
}

export function filterDrugOptions(options, query) {
  if (!Array.isArray(options)) {
    return []
  }
  return options.filter((option) => matchDrugOption(option, query))
}
