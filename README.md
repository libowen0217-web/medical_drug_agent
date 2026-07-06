# 社区药店多智能体用药安全辅助系统

本项目是一个面向社区药店柜台场景的用药安全辅助原型系统，主要用于课程汇报、项目演示和原型验证。系统围绕药师日常接待顾客时常见的“能不能用、有什么风险、如何提醒顾客、是否需要进一步就医”等问题，提供用药安全检查、症状问诊辅助、候选药协作评估和审计追溯功能。

**重要说明：本系统仅用于药师或医生的用药安全辅助参考，不构成诊断、处方或最终用药建议。**

## 项目简介

系统采用 FastAPI 后端、Vue 3 + Vite 前端、本地 CSV 知识库、可选 Neo4j 知识图谱后端和可选 LLM 报告润色能力。当前版本重点服务于项目演示和教学汇报，不定位为生产级医疗软件，也不替代医生诊疗、处方审核或药师最终判断。

系统默认可以在没有 Neo4j、没有真实大模型 API 的情况下基于本地 CSV 数据运行；如果配置了 Neo4j 和 LLM API，则可以启用知识图谱优先查询和报告润色能力。LLM 仅用于润色药师版报告和患者版提醒话术，不参与风险等级判断，也不修改规则命中、证据、剂量检查和风险发现结果。

## 功能模块

### 1. 用药安全检查

面向药店柜台新增用药场景，输入当前用药、拟新增药物、年龄、性别、基础疾病、过敏史、特殊人群和剂量信息后，系统辅助输出：

- 综合风险等级
- 主要风险提示
- 药师处理建议
- 顾客提醒话术
- 证据来源与详细依据
- 可折叠的系统技术详情

### 2. 症状问诊辅助

面向 OTC 问诊场景，输入症状描述、体温、持续时间、严重程度、患者信息和当前用药后，系统辅助输出：

- 初步症状风险判断
- 红旗症状筛查
- 可能情况提示
- 当前用药复核
- 可选 OTC 药物方向
- 药师下一步询问和处理建议

### 3. 候选药协作评估

读取最近一次症状问诊结果中的候选 OTC 药物，展示多 Agent 协作评估过程，包括：

- 候选药排序
- 各 Agent 协作意见
- 风险和适配性摘要
- 最终推荐结论

该模块主要用于课程演示多智能体协作过程，不用于自动开药。

### 4. 审计追溯中心

通过请求编号或审计编号回溯当次辅助分析记录，展示：

- 请求编号和生成时间
- 分析类型
- 当时输入信息
- 当时系统输出
- 详细依据
- 系统技术详情和原始 JSON

审计追溯用于展示系统可追溯性、辅助分析责任边界和演示复盘。

## 系统亮点

- **面向社区药店场景**：页面文案和结果展示偏向药师柜台使用，而不是技术调试页面。
- **多智能体辅助流程**：包含药名标准化、知识库查询、规则检查、剂量检查、证据复核、风险汇总、报告生成和安全过滤等步骤。
- **本地可运行 MVP**：默认基于 `data/processed/primekg_core100_drug_dataset.csv` 和规则 CSV 文件运行。
- **Neo4j 可选接入**：`KG_BACKEND=auto` 时优先尝试 Neo4j，不可用时回退 CSV。
- **LLM 可选润色**：支持 OpenAI-compatible / Anthropic-compatible 接口，调用失败自动回退模板报告。
- **统一 API-ready 响应协议**：后端返回固定顶层字段，便于后续接入前端、移动端或其他 Agent 编排框架。
- **审计追溯能力**：保留请求编号、审计编号、输入输出摘要和技术详情，便于项目演示复盘。
- **局域网演示支持**：一键启动脚本会打印本机和局域网访问地址，便于同一 WiFi 下演示。

## 技术架构

```text
Vue 3 + Vite + Element Plus
        |
        | /api, /health
        v
FastAPI HTTP API
        |
        +-- DrugSafetyService / SupervisorAgent
        +-- SymptomConsultWorkflow
        +-- KnowledgeBackendRouter
        |     +-- CSV Repository
        |     +-- Neo4j Repository（可选）
        +-- Rule Engine / Dose Checker / Evidence Store
        +-- LLMReportAgent（可选，只润色报告）
        +-- SafetyGuard / SafetyFilter
        +-- AuditLogger
```

前端开发环境通过 Vite proxy 将 `/api` 和 `/health` 转发到本机 FastAPI：

```text
浏览器 -> http://localhost:5173 -> Vite proxy -> http://127.0.0.1:8000
```

局域网其他设备访问时，也应访问运行项目电脑的 `5173` 端口，由 Vite proxy 代为转发后端请求。

## 项目目录结构

```text
medical_drug_agent/
├─ medical_drug_agent/
│  └─ app/
│     ├─ agents/              # 多智能体相关模块
│     ├─ api/                 # FastAPI 应用、路由和请求模型
│     ├─ audit/               # 审计日志与追溯
│     ├─ debate/              # 候选药协作评估
│     ├─ dose/                # 剂量检查与剂量参考表
│     ├─ evidence/            # 证据引用与证据库
│     ├─ graph/               # LangGraph / 图式流程相关代码
│     ├─ graphdb/             # Neo4j 配置、驱动、导入和查询
│     ├─ knowledge/           # CSV / Neo4j 知识库路由与查询
│     ├─ llm/                 # LLM 客户端、解析器和提示词
│     ├─ normalization/       # 药名标准化与药名映射表
│     ├─ reporting/           # 报告生成、风险汇总和安全过滤
│     ├─ rules/               # 本地用药安全规则
│     ├─ symptom/             # 症状问诊、疾病库、红旗规则、OTC 候选
│     ├─ service.py           # 本地 JSON 服务层
│     ├─ workflow.py          # 用药安全基础工作流
│     └─ schemas.py           # 核心数据结构
├─ frontend/
│  ├─ src/
│  │  ├─ api/                 # 前端 API 封装
│  │  ├─ components/          # 通用、药物、症状、候选药组件
│  │  ├─ layouts/             # 主布局与侧边栏
│  │  ├─ router/              # Vue Router
│  │  ├─ stores/              # Pinia 全局状态
│  │  ├─ styles/              # 全局样式与卡片样式
│  │  ├─ utils/               # 校验、格式化和搜索工具
│  │  └─ views/               # 四个主页面
│  ├─ package.json
│  └─ vite.config.js
├─ data/
│  ├─ raw/kg.csv
│  └─ processed/primekg_core100_drug_dataset.csv
├─ docs/                      # 项目设计、Neo4j、LLM、启动说明等文档
├─ logs/                      # 审计日志和运行日志
├─ outputs/                   # 示例输出结果
├─ scripts/                   # 启动、查询、导入、演示和测试脚本
├─ tests/                     # 后端单元测试
├─ .env.example               # 配置模板，可提交
├─ .env                       # 本地私密配置，不应提交
├─ requirements.txt
└─ README.md
```

## 环境要求

建议环境：

- Python 3.10 或更高版本
- Node.js 18 或更高版本
- npm
- Windows PowerShell、CMD、Git Bash 或 macOS/Linux shell
- 可选：Neo4j Desktop 或 Neo4j Server
- 可选：OpenAI-compatible 或 Anthropic-compatible LLM API Key

Python 依赖见 [requirements.txt](requirements.txt)，前端依赖见 [frontend/package.json](frontend/package.json)。

## 安装步骤

### 1. 克隆项目

```bash
git clone <你的 Gitee 仓库地址>
cd medical_drug_agent
```

### 2. 安装 Python 依赖

```bash
python -m pip install -r requirements.txt
```

如需使用虚拟环境，可先创建并激活：

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

## 配置说明

项目根目录提供 [.env.example](.env.example)，首次运行前建议复制为 `.env`：

Windows：

```bash
copy .env.example .env
```

macOS / Linux：

```bash
cp .env.example .env
```

`.env` 示例：

```env
LLM_PROVIDER=auto
LLM_API_KEY=your_api_key_here
LLM_BASE_URL=https://your-openai-compatible-base-url/v1
LLM_MODEL=your_model_name_here
LLM_DEBUG=false

KG_BACKEND=auto
NEO4J_URI=bolt://127.0.0.1:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_neo4j_password_here
NEO4J_DATABASE=neo4j

VITE_API_BASE_URL=
```

配置说明：

- `.env` 是本地私密配置，不要提交到 Gitee。
- `.env.example` 不包含真实密钥，可以提交。
- `LLM_PROVIDER` 可填写 `auto`、`openai` 或 `anthropic`。
- `LLM_API_KEY`、`LLM_BASE_URL`、`LLM_MODEL` 未正确配置时，系统会回退模板报告。
- `KG_BACKEND` 可填写 `csv`、`neo4j` 或 `auto`。
- `KG_BACKEND=auto` 表示优先 Neo4j，不可用时回退 CSV。
- `NEO4J_URI=bolt://127.0.0.1:7687` 表示后端本机访问 Neo4j，不是浏览器直接访问 Neo4j。
- `VITE_API_BASE_URL` 默认留空，前端通过 Vite proxy 请求后端。

## 数据与知识库说明

当前项目主要使用以下本地数据：

- `data/processed/primekg_core100_drug_dataset.csv`：PrimeKG 核心药物关系子集，包含药物-药物、药物-疾病、药物-副作用/表型关系。
- `medical_drug_agent/app/normalization/drug_name_map.csv`：中文药名、英文名、别名、药物类别映射。
- `medical_drug_agent/app/rules/pharmacy_safety_rules.csv`：本地药店用药安全规则。
- `medical_drug_agent/app/dose/dose_reference.csv`：剂量参考规则。
- `medical_drug_agent/app/evidence/evidence_store.csv`：证据引用数据。
- `medical_drug_agent/app/symptom/*.csv`：症状问诊、红旗症状、疾病库和 OTC 候选规则。

原始数据文件：

- `data/raw/kg.csv`

请不要随意删除或覆盖 `data/processed/primekg_core100_drug_dataset.csv`，否则本地 CSV 查询和基础演示流程会受影响。

## Neo4j 知识图谱说明

Neo4j 是可选能力。没有 Neo4j 时，系统仍可使用 CSV 后端运行。

如只使用 CSV：

```env
KG_BACKEND=csv
```

如启用自动选择：

```env
KG_BACKEND=auto
```

如强制使用 Neo4j：

```env
KG_BACKEND=neo4j
NEO4J_URI=bolt://127.0.0.1:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=你的 Neo4j 密码
NEO4J_DATABASE=neo4j
```

导入核心数据到 Neo4j：

```bash
python scripts/import_core100_to_neo4j.py
```

测试 Neo4j 连接：

```bash
python scripts/test_neo4j_connection.py
```

查询 Neo4j 药物关系：

```bash
python scripts/query_neo4j_drug.py --drug 布洛芬
python scripts/query_neo4j_drug.py --drug 布洛芬 --pair 硝苯地平
```

更多说明可参考 `docs/neo4j_usage.md`。

## LLM 报告润色说明

系统支持可选 LLMReportAgent。当前设计中，LLM 只用于润色：

- 药师版报告
- 患者版提醒话术

LLM 不参与以下内容的判断或修改：

- 风险等级
- risk_findings
- evidence_items
- dose_results
- rule_matches
- 药物关系查询结果

如果 LLM 调用失败，系统会自动回退模板报告，并在 metadata 中记录错误信息。

单独测试 LLMClient：

```bash
python scripts/test_llm_client.py
```

运行多 Agent 案例：

```bash
python scripts/run_multi_agent_case.py
```

关闭 LLM：

```bash
python scripts/run_multi_agent_case.py --disable-llm
```

更多说明可参考 `docs/llm_report_agent_usage.md`。

## 启动方式

### 推荐：一键启动前后端

从项目根目录运行：

```bash
python scripts/run_all.py
```

该脚本会：

- 启动 FastAPI 后端：`http://0.0.0.0:8000`
- 等待 `/health` 检查通过
- 启动 Vue/Vite 前端：`http://0.0.0.0:5173`
- 打印本机访问地址和局域网访问地址

默认不会自动打开浏览器。访问：

```text
http://localhost:5173/drug-safety
```

如需启动完成后自动打开一次浏览器：

```bash
python scripts/run_all.py --open
```

### 分别启动后端和前端

后端：

```bash
python scripts/run_api.py
```

等价于启动：

```bash
python -m uvicorn medical_drug_agent.app.api.main:app --host 0.0.0.0 --port 8000
```

前端：

```bash
cd frontend
npm run dev
```

前端访问：

```text
http://localhost:5173/drug-safety
```

FastAPI Swagger 文档：

```text
http://127.0.0.1:8000/docs
```

### Streamlit 演示入口

项目仍保留 Streamlit 启动脚本：

```bash
python scripts/run_streamlit.py
```

当前正式演示建议优先使用 Vue 前端。

## 局域网访问方式

一键启动后，脚本会打印类似：

```text
[系统] 本机访问:
  - http://localhost:5173/drug-safety
[系统] 局域网访问:
  - http://192.168.x.x:5173/drug-safety
```

同一局域网内其他设备访问：

```text
http://运行项目电脑的局域网IP:5173/drug-safety
```

如果本机可以通过局域网 IP 打开，但其他设备打不开，通常需要检查：

- Windows 防火墙是否放行 TCP 5173 和 TCP 8000
- Node.js 和 Python 是否允许入站访问
- 当前网络是否为手机热点且启用了客户端隔离
- Windows 当前网络是否被识别为“公用网络”
- 是否使用了 WSL、Docker、VMware、VPN 等虚拟网卡 IP

另一台 Windows 电脑可用以下命令测试：

```powershell
Test-NetConnection 192.168.x.x -Port 5173
```

## 前端页面说明

Vue 前端包含四个主页面：

```text
/drug-safety          用药安全检查
/symptom-consult      症状问诊辅助
/medication-debate    候选药协作评估
/system-debug         审计追溯中心
```

页面左侧为模块导航，底部提供系统设置入口。系统设置中可配置：

- API 地址
- 是否启用 LLM 报告润色
- 是否启用审计日志
- 知识图谱后端选择
- 调试显示项

前端药物搜索支持：

- 中文药名
- 英文名
- 别名
- 拼音

## 后端接口说明

主要接口如下：

### 健康检查

```http
GET /health
```

### 版本信息

```http
GET /api/v1/version
```

### 药物选项

```http
GET /api/v1/drugs/options
```

返回前端药物搜索框所需的药物名称、英文名、别名和拼音。

### 用药安全检查

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

### 知识图谱后端状态

```http
GET /api/v1/kg/backend-status
```

可查看当前配置后端、实际后端、Neo4j 是否连接、是否发生回退等信息。

### 审计记录查询

```http
GET /api/v1/audit/records/{identifier}
```

`identifier` 可以是请求编号或审计编号。

### 症状问诊辅助

```http
POST /api/v1/symptom-consult/check
```

用于症状输入、红旗症状筛查、疾病候选和 OTC 候选药辅助分析。

## 统一响应协议

后端业务接口采用 API-ready 统一响应结构，典型字段包括：

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

成功时业务结果放在 `data` 中；错误时 `data` 通常为 `null`，错误原因通过 `error_code` 和 `message` 返回。

## 审计追溯说明

当启用审计时，系统会记录辅助分析过程中的关键信息，便于课程演示和结果复盘。

审计追溯中心支持：

- 查看最近一次分析记录
- 通过请求编号查询记录
- 通过审计编号查询记录
- 回溯当时输入信息
- 回溯当时系统输出
- 展开查看详细依据和原始 JSON

前端也会在本地保存当前会话的统一审计记录列表，用于在页面内快速展示最近一次分析记录。后端审计日志可通过接口或脚本查询。

相关脚本：

```bash
python scripts/show_audit_logs.py
python scripts/replay_audit_case.py
```

## 常用脚本

```bash
# 一键启动前后端
python scripts/run_all.py

# 启动 FastAPI
python scripts/run_api.py

# 命令行查询药物关系
python scripts/query_drug.py --drug 布洛芬
python scripts/query_drug.py --drug-a 硝苯地平 --drug-b 布洛芬

# JSON 案例运行
python scripts/run_json_case.py --input scripts/sample_case.json
python scripts/run_json_case.py --input scripts/sample_case_with_dose.json

# 多 Agent 案例
python scripts/run_multi_agent_case.py
python scripts/run_multi_agent_case.py --disable-llm

# 症状问诊案例
python scripts/run_symptom_case.py

# Neo4j 测试与查询
python scripts/test_neo4j_connection.py
python scripts/query_neo4j_drug.py --drug 布洛芬

# LLM 单独测试
python scripts/test_llm_client.py
```

## 测试方式

后端测试：

```bash
python -m pytest
```

前端构建检查：

```bash
cd frontend
npm run build
```

FastAPI 手动验证：

```text
http://127.0.0.1:8000/docs
http://127.0.0.1:8000/health
http://127.0.0.1:8000/api/v1/drugs/options
```

## 项目演示建议

建议课程展示顺序：

1. 打开 Vue 前端首页：`http://localhost:5173/drug-safety`
2. 在“用药安全检查”中演示 `硝苯地平 + 布洛芬` 或 `华法林 + 布洛芬`。
3. 展示综合风险等级、药师处理建议、顾客提醒话术和详细依据折叠区。
4. 切换到“症状问诊辅助”，输入发热、头痛、咽痛等常见症状。
5. 展示红旗症状筛查、候选 OTC 药物和当前用药复核。
6. 切换到“候选药协作评估”，展示候选药排序和多 Agent 协作意见。
7. 切换到“审计追溯中心”，查看最近一次分析记录，说明系统具备可追溯性。
8. 如配置了 Neo4j，可展示知识图谱后端状态；如配置了 LLM，可展示报告润色效果。

演示时建议强调：

- 系统是辅助工具，不替代医生或药师。
- 风险判断来自规则、剂量、知识库和证据引用，LLM 只润色报告。
- Neo4j 和 LLM 都是可选增强能力，本地 CSV 模式也能运行完整 MVP。

## 常见问题

### 1. 前端可以打开，但提示后端连接失败

先确认 FastAPI 是否启动：

```text
http://127.0.0.1:8000/health
```

如果使用一键启动，脚本会等待后端 `/health` 通过后再启动前端。若手动分别启动，请先启动后端，再启动前端。

### 2. 药物搜索框没有数据

检查药物选项接口：

```text
http://127.0.0.1:8000/api/v1/drugs/options
```

如果通过前端代理访问：

```text
http://localhost:5173/api/v1/drugs/options
```

### 3. Neo4j 连接失败

可先改用 CSV：

```env
KG_BACKEND=csv
```

如果需要 Neo4j，请确认：

- Neo4j 服务已启动
- `NEO4J_PASSWORD` 正确
- Bolt 端口为 `7687`
- 已运行 `python scripts/import_core100_to_neo4j.py`

### 4. LLM 没有生效

检查 `.env`：

```env
LLM_PROVIDER=auto
LLM_API_KEY=你的真实 Key
LLM_BASE_URL=你的 Base URL
LLM_MODEL=你的模型名
```

单独测试：

```bash
python scripts/test_llm_client.py
```

如果失败，系统会自动回退模板报告，不影响主流程。

### 5. 局域网其他设备打不开前端

请优先检查：

- 是否访问了正确的局域网 IP
- Windows 防火墙是否放行 TCP 5173
- 当前网络是否允许设备互访
- 是否使用了虚拟网卡 IP

### 6. 审计追溯中心看不到最近一次记录

请先完成一次用药安全检查或症状问诊。审计追溯中心会优先读取当前前端会话中的统一审计记录列表，也可通过请求编号或审计编号查询后端审计日志。

## 注意事项与安全边界

- 本系统仅用于药师或医生的用药安全辅助参考。
- 本系统不构成诊断、处方或最终用药建议。
- 不应将系统输出直接作为临床决策或真实处方依据。
- LLM 只用于报告润色，不参与风险等级和证据判断。
- 对儿童、孕妇、老年人、基础疾病患者、过敏史患者等特殊情况，应由专业人员进一步复核。
- 出现红旗症状、严重不良反应、持续高热、呼吸困难、胸痛、黑便、意识异常等情况，应建议及时就医。
- 项目中的本地数据和规则适合原型验证与课程展示，不能覆盖所有药品、疾病和真实临床场景。
- `.env` 中的 API Key、Neo4j 密码等敏感信息不得提交到代码仓库。

## 维护建议

- 新增药物名称时，优先维护 `medical_drug_agent/app/normalization/drug_name_map.csv`。
- 新增药物安全规则时，优先维护 `medical_drug_agent/app/rules/pharmacy_safety_rules.csv`。
- 新增剂量规则时，优先维护 `medical_drug_agent/app/dose/dose_reference.csv`。
- 新增症状问诊规则时，维护 `medical_drug_agent/app/symptom/` 下的 CSV 规则文件。
- 修改 API 返回结构时，需要同步检查前端 `frontend/src/api/`、`frontend/src/views/` 和相关测试。
- 上传 Gitee 前请确认 `.env`、`frontend/node_modules/`、`frontend/dist/`、`__pycache__/`、`.pytest_cache/` 等不会被提交。
.