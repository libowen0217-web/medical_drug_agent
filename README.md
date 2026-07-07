# 社区药店药物交互检查助手

本项目是一个面向社区药店柜台场景的用药安全辅助原型系统，主要用于课程汇报、项目演示和原型验证。系统基于结构化药物知识库、规则引擎、剂量检查、RAG 证据增强和可选 LLM 报告润色，辅助药师围绕“当前用药能否叠加新增药物、是否存在特殊人群风险、如何向顾客说明注意事项”等问题进行结构化评估。

**重要声明：本系统仅用于药师或医生的用药安全辅助参考，不构成诊断、处方或最终用药建议。**

## 项目简介

当前系统支持本地 CSV 知识库运行，也支持可选 Neo4j 知识图谱后端；支持本地 Markdown RAG 文档知识库检索，也支持可选 LLMReportAgent 对药师版报告和患者版提醒进行润色。系统设计原则是：风险等级、规则命中、剂量检查和药物关系判断仍由规则引擎、结构化知识库与本地逻辑决定，RAG 和 LLM 只作为证据参考与报告表达增强，不参与真实风险等级决策。

项目默认可以在没有 Neo4j、没有真实大模型 API 的情况下完成本地 MVP 演示；如果配置了 Neo4j、RAG 索引和 LLM API，则可以展示更完整的知识图谱查询、参考证据检索和报告润色链路。

## 核心功能

- 当前用药与拟新增药物的交互检查。
- 疾病、年龄、性别、儿童、老年人、孕妇等特殊因素评估。
- 基于规则引擎、剂量逻辑和知识库关系的风险等级判断。
- 药师版报告和患者版提醒话术生成。
- RAG 本地 Markdown 文档参考证据检索。
- LLMReportAgent 可选报告润色，失败时自动回退模板报告。
- 症状问诊辅助、红旗症状筛查和候选 OTC 药物提示。
- 候选药协作评估，用于演示多 Agent 协作过程。
- 审计记录与审计追溯，用于回溯当次输入、输出和依据。
- Vue 前端业务页面展示和 FastAPI HTTP 接口。

## 技术栈

- 后端：FastAPI、Python dataclasses、pytest。
- 药物知识库：PrimeKG 子集、本地 CSV、可选 Neo4j。
- RAG：本地 Markdown 文档库、`bge-small-zh-v1.5`、SentenceTransformer、Chroma。
- LLM：OpenAI-compatible / Anthropic-compatible 接口，主要用于报告润色。
- 前端：Vue 3、Vite、Element Plus、Pinia。
- 启动与演示：`scripts/run_api.py`、`scripts/run_all.py`、Swagger UI。

## 系统亮点

- **规则优先**：风险等级不交给 LLM 或 RAG 决定，避免生成式模型影响安全判断。
- **本地可运行**：基于 CSV、规则文件和本地 RAG 索引即可完成完整 MVP。
- **可选增强**：Neo4j、RAG、LLM 都是增强能力，失败时不应破坏主流程。
- **证据增强**：RAG 只检索本地文档证据，当前模板文档中的“待补充”内容会被过滤，不作为正式医学证据。
- **报告分层**：面向药师的处理建议和面向顾客的提醒话术分开生成。
- **审计可追溯**：保留请求编号、输入摘要、输出摘要、证据和技术详情，便于演示复盘。

## 项目目录结构

```text
medical_drug_agent/
├─ medical_drug_agent/
│  └─ app/
│     ├─ agents/              # 多智能体、报告、RAG evidence agent 等
│     ├─ api/                 # FastAPI app、routes、models
│     ├─ audit/               # 审计日志与审计查询
│     ├─ debate/              # 候选药协作评估
│     ├─ dose/                # 剂量参考与剂量检查
│     ├─ evidence/            # 结构化证据引用
│     ├─ graph/               # 图式工作流相关代码
│     ├─ graphdb/             # Neo4j 配置、连接、导入与查询
│     ├─ knowledge/           # CSV / Neo4j 知识后端路由
│     ├─ llm/                 # LLM 客户端、解析器和 prompt
│     ├─ normalization/       # 药名标准化和药名映射表
│     ├─ rag/                 # RAG query 构造和 retriever
│     ├─ reporting/           # 报告生成、风险汇总和安全过滤
│     ├─ rules/               # 本地用药安全规则
│     ├─ symptom/             # 症状问诊、疾病库、红旗规则和 OTC 候选
│     ├─ service.py           # API-ready 本地服务层
│     └─ schemas.py           # 核心数据结构
├─ frontend/
│  ├─ src/
│  │  ├─ api/                 # 前端 API 封装
│  │  ├─ components/          # 通用、药物、症状、候选药组件
│  │  ├─ layouts/             # 主布局和侧边栏
│  │  ├─ router/              # Vue Router
│  │  ├─ stores/              # Pinia 状态
│  │  ├─ styles/              # 全局样式
│  │  ├─ utils/               # 搜索、校验、格式化、审计工具
│  │  └─ views/               # 四个业务页面
│  ├─ package.json
│  └─ vite.config.js
├─ data/
│  ├─ processed/primekg_core100_drug_dataset.csv
│  ├─ rag_docs/               # 可提交的 RAG Markdown 文档库
│  ├─ raw/                    # 原始大数据文件，默认不提交
│  └─ vector_db/              # Chroma 索引，默认不提交
├─ docs/                      # 项目设计、Neo4j、LLM、启动等文档
├─ models/                    # 本地 embedding 模型，默认不提交
├─ scripts/                   # 启动、构建索引、导入、查询、演示脚本
├─ tests/                     # 后端测试
├─ .env.example               # 示例配置，可提交
├─ .env                       # 本地真实配置，不提交
├─ .gitignore
├─ requirements.txt
└─ README.md
```

## 环境要求

- Python 3.10 或更高版本。
- Node.js 18 或更高版本。
- npm。
- 可选：Neo4j Desktop / Neo4j Server。
- 可选：ModelScope CLI，用于下载 embedding 模型。
- 可选：OpenAI-compatible 或 Anthropic-compatible LLM API Key。

## 安装步骤

### 1. 克隆项目

```bash
git clone <你的 GitHub 或 Gitee 仓库地址>
cd medical_drug_agent
```

### 2. 安装 Python 依赖

```bash
python -m pip install -r requirements.txt
```

如需虚拟环境：

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
```

macOS / Linux：

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

### 3. 安装前端依赖

```bash
cd frontend
npm install
cd ..
```

### 4. 复制环境变量模板

Windows PowerShell：

```powershell
Copy-Item .env.example .env
```

CMD：

```cmd
copy .env.example .env
```

macOS / Linux：

```bash
cp .env.example .env
```

然后根据本机情况填写 `.env`。不要把真实 `.env` 上传到仓库。

## 配置说明

`.env.example` 包含以下配置类别：

- `LLM_ENABLED`、`LLM_PROVIDER`、`LLM_BASE_URL`、`LLM_API_KEY`、`LLM_MODEL`：LLM 报告润色配置。
- `KG_BACKEND`、`NEO4J_URI`、`NEO4J_USER`、`NEO4J_PASSWORD`、`NEO4J_DATABASE`：知识图谱后端配置。
- `RAG_MODEL_PATH`、`RAG_DOCS_DIR`、`RAG_CHROMA_PATH`、`RAG_TOP_K`：RAG 文档知识库配置。
- `DRUG_DATA_PATH`：本地 PrimeKG CSV 数据路径。
- `BACKEND_HOST`、`BACKEND_PORT`、`CORS_ORIGINS`：后端开发配置。
- `AUDIT_ENABLED`、`LOG_LEVEL`：审计与日志配置。

常见知识后端配置：

```env
KG_BACKEND=csv
```

只使用本地 CSV，最适合首次运行。

```env
KG_BACKEND=auto
```

优先尝试 Neo4j，不可用时回退 CSV。

```env
KG_BACKEND=neo4j
```

强制使用 Neo4j，适合演示知识图谱后端。

## 数据与知识库说明

当前项目主要使用：

- `data/processed/primekg_core100_drug_dataset.csv`：PrimeKG 核心药物关系子集，包含药物-药物、药物-疾病、药物-副作用/表型关系。
- `medical_drug_agent/app/normalization/drug_name_map.csv`：中文药名、英文名、别名、类别映射。
- `medical_drug_agent/app/rules/pharmacy_safety_rules.csv`：本地用药安全规则。
- `medical_drug_agent/app/dose/dose_reference.csv`：剂量参考规则。
- `medical_drug_agent/app/evidence/evidence_store.csv`：结构化证据引用。
- `medical_drug_agent/app/symptom/`：症状问诊、疾病库、红旗症状和 OTC 候选药规则。
- `data/rag_docs/`：RAG Markdown 文档知识库，可提交到 Git。
- `data/vector_db/chroma/`：Chroma 向量库索引，由脚本生成，不提交到 Git。

`data/raw/`、`models/`、`data/vector_db/` 默认不上传。`data/rag_docs/` 可以上传，但当前部分文档仍为模板内容，真实说明书内容需要确认来源后再补充。

## RAG 说明

RAG 当前用于“参考证据增强”，不参与风险等级判断。

- RAG 不负责决定低风险、中风险或高风险。
- 风险等级仍由规则引擎、剂量逻辑、结构化知识库和业务规则决定。
- RAG 只从本地 Markdown 药品文档和指南文档中检索参考证据。
- LLM 只能参考 `rag_evidences` 组织报告表达，不能编造证据，不能改变风险等级。
- 如果向量库不存在、RAG 检索失败或没有命中证据，主流程应继续返回原有药物安全评估结果。
- 当前模板文档中包含“待补充：请根据药品说明书或权威资料填写”的内容会被过滤，不作为正式医学证据展示。
- `test_drug_a.md` 和 `test_drug_b.md` 仅用于 RAG 功能测试，不代表真实医学建议。

### 下载 embedding 模型

如果已安装 ModelScope：

```bash
modelscope download --model BAAI/bge-small-zh-v1.5 --local_dir ./models/bge-small-zh-v1.5
```

也可以使用其他方式下载到：

```text
models/bge-small-zh-v1.5
```

### 构建 RAG 索引

```bash
python scripts/build_rag_index.py
```

索引会写入：

```text
data/vector_db/chroma
```

如果文档有更新，建议删除旧索引目录后重新构建：

```powershell
Remove-Item -Recurse -Force data/vector_db/chroma
python scripts/build_rag_index.py
```

### RAG 检索接口

```http
POST /api/rag/search
```

请求示例：

```json
{
  "query": "测试药A和测试药B能一起用吗？",
  "top_k": 3
}
```

## 启动方式

### 推荐：一键启动前后端

```bash
python scripts/run_all.py
```

该脚本会：

- 启动 FastAPI 后端。
- 等待 `/health` 检查通过。
- 启动 Vue/Vite 前端。
- 打印本机访问地址和局域网访问地址。

默认不会自动打开浏览器。访问：

```text
http://localhost:5173/drug-safety
```

如果希望启动后自动打开一次页面：

```bash
python scripts/run_all.py --open
```

### 分别启动后端和前端

后端：

```bash
python scripts/run_api.py
```

接口文档：

```text
http://127.0.0.1:8000/docs
```

前端：

```bash
cd frontend
npm run dev
```

前端页面：

```text
http://localhost:5173/drug-safety
```

## 局域网访问

`scripts/run_api.py` 使用 `0.0.0.0:8000` 监听后端，Vite 前端也配置为 `0.0.0.0:5173`。同一局域网设备访问时，推荐访问运行项目电脑的前端地址：

```text
http://本机局域网IP:5173/drug-safety
```

如果其他设备无法访问，请检查：

- Windows 防火墙是否放行 TCP 5173 和 TCP 8000。
- Node.js 和 Python 是否允许入站访问。
- 当前网络是否为手机热点并启用了客户端隔离。
- Windows 当前网络类型是否为“公用网络”。
- 是否误用了 WSL、Docker、VMware、VPN 等虚拟网卡 IP。

另一台 Windows 电脑可用以下命令测试端口：

```powershell
Test-NetConnection 192.168.x.x -Port 5173
```

## 前端页面说明

主要页面：

```text
/drug-safety          用药安全检查
/symptom-consult      症状问诊辅助
/medication-debate    候选药协作评估
/system-debug         审计追溯中心
```

模块说明：

- 用药安全检查：输入当前用药、拟新增药物、患者因素和剂量方式，输出风险等级、药师建议、顾客提醒和参考证据。
- 症状问诊辅助：输入症状、体温、持续时间、严重程度和患者信息，输出红旗症状、候选疾病、当前用药复核和候选 OTC 药物。
- 候选药协作评估：基于最近一次症状问诊候选药，展示候选药排序和多 Agent 协作评估过程。
- 审计追溯中心：通过请求编号或审计编号回溯当次输入、输出、参考依据和系统技术详情。

## 后端接口说明

健康检查：

```http
GET /health
```

版本信息：

```http
GET /api/v1/version
```

药物选项：

```http
GET /api/v1/drugs/options
```

药物安全检查：

```http
POST /api/v1/drug-safety/check?use_multi_agent=true&enable_llm=true&knowledge_backend=auto
```

请求示例：

```json
{
  "current_drugs": ["硝苯地平"],
  "new_drug": "布洛芬",
  "age": 68,
  "diseases": ["高血压"],
  "patient_factors": ["老年人"],
  "dose": null
}
```

RAG 检索：

```http
POST /api/rag/search
```

知识图谱后端状态：

```http
GET /api/v1/kg/backend-status
```

症状问诊辅助：

```http
POST /api/v1/symptom-consult/check
```

审计记录查询：

```http
GET /api/v1/audit/records/{identifier}
```

多数业务接口采用统一 API-ready 响应结构：

```json
{
  "request_id": "...",
  "timestamp": "...",
  "status": "success",
  "error_code": null,
  "message": "...",
  "data": {},
  "metadata": {}
}
```

## 审计追溯说明

审计追溯中心用于课程演示和结果复盘，重点展示：

- 请求编号。
- 生成时间。
- 分析类型。
- 当时输入信息。
- 当时系统输出。
- 详细依据。
- 系统技术详情和原始 JSON。

相关脚本：

```bash
python scripts/show_audit_logs.py
python scripts/replay_audit_case.py
```

## 测试方式

### RAG 测试

```bash
python -m pytest tests/test_rag_retriever.py tests/test_rag_api.py
```

### 主流程测试

```bash
python -m pytest tests/test_fastapi_api.py tests/test_service.py tests/test_supervisor_agent.py
```

### 全量后端测试

```bash
python -m pytest
```

### 前端构建

```bash
cd frontend
npm run build
```

## Git 上传说明

上传 GitHub / Gitee 前请确认以下内容不会进入仓库：

- `.env`
- `models/`
- `data/vector_db/`
- `data/raw/`
- `logs/`
- `audit_logs/`
- `outputs/`
- `frontend/node_modules/`
- `frontend/dist/`
- `__pycache__/`
- `.pytest_cache/`

可提交内容：

- `.env.example`
- `data/rag_docs/`
- 业务代码、测试代码、文档和配置模板。

如果发现敏感或大文件已经被 Git 跟踪，请只从 Git 索引移除，不删除本地文件，例如：

```bash
git rm --cached .env
git rm -r --cached models
git rm -r --cached data/vector_db
git rm -r --cached data/raw
git rm -r --cached logs
git rm -r --cached frontend/node_modules
git rm -r --cached frontend/dist
```

建议本次提交信息：

```text
feat: integrate RAG evidence into drug safety workflow
```

## 常见问题

### 1. `rag_evidences` 返回空数组，是否代表 RAG 失败？

不一定。当前很多 RAG Markdown 文档仍是模板内容，包含“待补充”占位文本。主流程会过滤这类占位 evidence，因此 `rag_evidences=[]` 是正常结果。可以通过 `POST /api/rag/search` 或测试文档验证 RAG 检索链路。

### 2. 前端能打开，但提示后端连接失败

先确认 FastAPI 是否启动：

```text
http://127.0.0.1:8000/health
```

推荐使用：

```bash
python scripts/run_all.py
```

它会等待后端健康检查通过后再启动前端。

### 3. 药物搜索框没有数据

检查药物选项接口：

```text
http://127.0.0.1:8000/api/v1/drugs/options
```

前端开发代理下也可以访问：

```text
http://localhost:5173/api/v1/drugs/options
```

### 4. Neo4j 不可用怎么办？

首次运行建议使用：

```env
KG_BACKEND=csv
```

或使用：

```env
KG_BACKEND=auto
```

让系统自动回退 CSV。

### 5. LLM 调用失败怎么办？

LLM 调用失败不会影响主流程，系统会回退模板报告。可单独测试：

```bash
python scripts/test_llm_client.py
```

### 6. PowerShell 显示中文乱码怎么办？

如果接口实际返回 UTF-8 JSON，但 PowerShell 显示乱码，多数是终端编码或 `Invoke-RestMethod` 显示问题。可用浏览器、Swagger 或 Python `urllib` 验证。

## 项目演示建议

推荐演示流程：

1. 打开 `http://localhost:5173/drug-safety`。
2. 演示“硝苯地平 + 布洛芬”或“华法林 + 布洛芬”的用药安全检查。
3. 展示综合风险等级、药师处理建议、顾客提醒话术和参考证据。
4. 切换到症状问诊辅助，输入发热、头痛、咽痛等常见症状。
5. 展示红旗症状筛查、候选 OTC 药物和当前用药复核。
6. 切换到候选药协作评估，展示候选药排序和协作评估过程。
7. 切换到审计追溯中心，展示最近一次分析记录和输入输出回溯。
8. 如果配置了 Neo4j，可展示知识图谱后端状态；如果配置了 LLM，可展示报告润色效果。

演示时建议强调：

- 系统是辅助工具，不是自动诊断或自动开药工具。
- 风险等级由规则引擎、剂量逻辑和知识库判断，LLM 不参与风险等级决策。
- RAG 只提供本地文档参考证据，模板占位内容不会作为正式医学证据展示。

## 注意事项与安全边界

- 本系统仅用于药师或医生的用药安全辅助参考。
- 本系统不构成诊断、处方或最终用药建议。
- 不应将系统输出直接作为真实处方或临床决策依据。
- LLM 只能润色药师版报告和患者版提醒，不能修改风险等级、证据、规则命中、剂量检查和风险发现。
- RAG 不能决定风险等级，也不能替代权威药品说明书或临床指南。
- 对儿童、孕妇、老年人、基础疾病患者、过敏史患者等特殊情况，应由专业人员进一步复核。
- 出现严重不良反应、持续高热、呼吸困难、胸痛、黑便、意识异常等红旗情况时，应建议及时就医。
- 项目中的本地数据、规则和 RAG 文档适合课程演示和原型验证，不能覆盖所有药品、疾病和真实临床场景。
- `.env` 中的 API Key、Neo4j 密码等敏感信息不得提交到代码仓库。
