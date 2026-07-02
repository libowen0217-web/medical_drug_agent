from __future__ import annotations

from fastapi import APIRouter

from medical_drug_agent.app.agents.supervisor_agent import SupervisorAgent
from medical_drug_agent.app.api.models import DrugSafetyAPIRequest
from medical_drug_agent.app.api_contract import build_error_response, build_success_response
from medical_drug_agent.app.knowledge.knowledge_router import KnowledgeBackendRouter
from medical_drug_agent.app.normalization.mapper import DrugNameMapper
from medical_drug_agent.app.service import DrugSafetyService
from medical_drug_agent.app.symptom.symptom_workflow import SymptomConsultWorkflow

try:
    from pypinyin import Style, lazy_pinyin
except ImportError:  # pragma: no cover - optional dependency fallback
    Style = None
    lazy_pinyin = None


router = APIRouter()
service = DrugSafetyService()
symptom_workflow = SymptomConsultWorkflow()
drug_mapper = DrugNameMapper()

PINYIN_OVERRIDES = {
    "硝苯地平": "xiaobendiping",
    "氨氯地平": "anlvdiping",
    "缬沙坦": "xieshatan",
    "厄贝沙坦": "ebeishatan",
    "美托洛尔": "meituoluoer",
    "氢氯噻嗪": "qinglvsaiqin",
    "布洛芬": "buluofen",
    "阿司匹林": "asipilin",
    "双氯芬酸": "shuanglvfensuan",
    "塞来昔布": "sailaixibu",
    "对乙酰氨基酚": "duiyixiananjifen",
    "华法林": "huafalin",
    "二甲双胍": "erjiashuanggua",
    "阿托伐他汀": "atuofatating",
    "奥美拉唑": "aomeilazuo",
    "氯雷他定": "lvleitading",
    "西替利嗪": "xitiliqin",
    "氨溴索": "anxiusuo",
    "愈创甘油醚": "yuchuangganyoumi",
}


def _to_pinyin(text: str) -> str:
    cleaned = str(text or "").strip()
    if lazy_pinyin is not None and Style is not None:
        return "".join(lazy_pinyin(cleaned, style=Style.NORMAL))
    return PINYIN_OVERRIDES.get(cleaned, "")


def _build_drug_option(drug_info: object) -> dict:
    display_name = str(getattr(drug_info, "zh_name", "") or "").strip()
    standard_name = str(getattr(drug_info, "en_name", "") or "").strip()
    aliases = list(dict.fromkeys([display_name, *list(getattr(drug_info, "aliases", []) or []), standard_name]))
    pinyin = _to_pinyin(display_name)
    label = " / ".join(part for part in [display_name, standard_name, pinyin] if part)
    return {
        "display_name": display_name,
        "standard_name": standard_name,
        "aliases": aliases,
        "pinyin": pinyin,
        "label": label,
    }


@router.get("/health")
def health_check() -> dict:
    return {
        "status": "ok",
        "service": "medical-drug-agent",
        "engine_version": DrugSafetyService.ENGINE_VERSION,
    }


@router.get("/api/v1/version")
def version() -> dict:
    return {
        "service": "medical-drug-agent",
        "api_version": "v1",
        "engine_version": DrugSafetyService.ENGINE_VERSION,
        "mode": "local-csv-mvp",
    }


@router.get("/api/v1/drugs/options")
def drug_options() -> dict:
    try:
        options = [_build_drug_option(item) for item in drug_mapper.list_supported_drugs()]
    except FileNotFoundError as exc:
        return build_error_response(
            error_code="DATA_FILE_MISSING",
            message=str(exc),
            metadata={"source": "drug_name_map", "engine_version": DrugSafetyService.ENGINE_VERSION},
        )
    except Exception as exc:
        return build_error_response(
            error_code="WORKFLOW_ERROR",
            message=f"药物选项加载失败：{exc}",
            metadata={"source": "drug_name_map", "engine_version": DrugSafetyService.ENGINE_VERSION},
        )

    return build_success_response(
        data={"options": options},
        metadata={"source": "drug_name_map", "engine_version": DrugSafetyService.ENGINE_VERSION},
        message="药物选项加载成功",
    )


@router.post("/api/v1/drug-safety/check")
def check_drug_safety(
    payload: DrugSafetyAPIRequest,
    use_graph: bool = False,
    use_agent: bool = False,
    use_multi_agent: bool = False,
    enable_llm: bool = True,
    enable_audit: bool = True,
    knowledge_backend: str | None = None,
) -> dict:
    if use_multi_agent:
        try:
            supervisor = SupervisorAgent(
                use_graph=use_graph,
                enable_audit=enable_audit,
                enable_llm=enable_llm,
                knowledge_backend=knowledge_backend,
            )
        except ValueError as exc:
            return build_error_response(
                error_code="INVALID_INPUT",
                message=str(exc),
                metadata={"engine_version": DrugSafetyService.ENGINE_VERSION},
            )
        return supervisor.run(payload.model_dump())
    effective_service = DrugSafetyService(use_graph=use_graph) if use_graph else service
    _ = use_agent
    return effective_service.check_from_dict(payload.model_dump(), enable_audit=enable_audit)


@router.get("/api/v1/kg/backend-status")
def get_kg_backend_status(knowledge_backend: str | None = None) -> dict:
    try:
        router_instance = KnowledgeBackendRouter(backend=knowledge_backend)
        status = router_instance.get_status()
    except Exception as exc:
        return build_error_response(
            error_code="WORKFLOW_ERROR",
            message=f"知识图谱后端状态检查失败：{exc}",
            metadata={"engine_version": DrugSafetyService.ENGINE_VERSION},
        )
    return build_success_response(
        data=status,
        metadata={"engine_version": DrugSafetyService.ENGINE_VERSION},
        message="知识图谱后端状态获取成功",
    )


@router.post("/api/v1/symptom-consult/check")
def check_symptom_consult(payload: dict) -> dict:
    return symptom_workflow.run(payload)
