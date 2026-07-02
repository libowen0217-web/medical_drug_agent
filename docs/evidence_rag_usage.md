# 本地 Evidence RAG 使用说明

## 为什么需要证据检索

规则命中和剂量检查可以告诉我们“哪里有风险”，证据检索则补充“为什么要关注”。这样能让 `risk_findings`、药师报告和 API 响应带上更可解释的本地证据摘要。

## 当前实现定位

当前 evidence RAG 仍然是本地 `evidence_store.csv` 关键词检索，不是向量数据库，也不调用外部 API。

## 检索流程

1. 生成关键词
2. 扫描本地证据表
3. 按字段加权评分
4. 去重
5. Top-K 排序
6. 生成 `citation_label`

## 评分规则

- 命中 `topic`：+3
- 命中 `drug_or_class`：+3
- 命中 `disease_or_factor`：+3
- 命中 `risk`：+2
- 命中 `evidence_text`：+1

## evidence_store.csv 字段

- `evidence_id`
- `topic`
- `drug_or_class`
- `disease_or_factor`
- `risk`
- `source_type`
- `source_name`
- `evidence_text`
- `notes`

## citation_label 的作用

检索结果会生成如 `[证据1]`、`[证据2]` 的标签，便于在药师报告中引用，但这里只表示“本地证据摘要”，不是正式医学文献引用。

## API 中的位置

证据结果位于：

- `data.risk_findings[*].evidence_items`

每条 evidence item 现在包含：

- `score`
- `rank`
- `citation_label`
- `matched_keywords`

## 报告展示方式

药师报告会显示“证据提示”，包含引用编号、来源名称和证据摘要。患者报告只保留谨慎说明，不堆叠原始证据文本。

## 如何查询证据

```bash
python scripts/query_evidence.py --keyword NSAID --keyword 高血压 --limit 3
```

## 当前限制

- 证据是本地摘要，不是实时说明书原文
- 不接 DailyMed/openFDA
- 不接真实 RAG/向量数据库
- 仍不是正式医学文献引用

## 后续升级

- DailyMed/openFDA 原文切片
- 向量检索
- BM25
- 证据版本号
- 证据来源 URL
- 药品说明书原文引用
