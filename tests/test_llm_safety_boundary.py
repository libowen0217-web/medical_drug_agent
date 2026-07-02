from medical_drug_agent.app.agents.supervisor_agent import SupervisorAgent


class MockLLMClient:
    def __init__(self, text: str) -> None:
        self.text = text
        self.model = "mock-model"

    def generate_text(self, system_prompt: str, user_prompt: str) -> str:
        return self.text


def _payload() -> dict:
    return {
        "current_drugs": ["硝苯地平"],
        "new_drug": "布洛芬",
        "age": 68,
        "diseases": ["高血压"],
        "patient_factors": [],
        "dose": None,
    }


def _run_with_text(text: str) -> dict:
    supervisor = SupervisorAgent(enable_llm=True)
    supervisor.llm_report_agent.client = MockLLMClient(text)
    return supervisor.run(_payload())


def test_llm_phrase_can_eat_is_filtered() -> None:
    response = _run_with_text('{"pharmacist_report":"你可以吃这个药","patient_report":"你可以吃这个药"}')
    assert "你可以吃" not in response["data"]["patient_report"]


def test_llm_phrase_completely_safe_is_filtered() -> None:
    response = _run_with_text('{"pharmacist_report":"这个方案完全安全","patient_report":"这个方案完全安全"}')
    assert "完全安全" not in response["data"]["pharmacist_report"]


def test_llm_phrase_no_risk_is_filtered() -> None:
    response = _run_with_text('{"pharmacist_report":"没有风险","patient_report":"没有风险"}')
    assert "没有风险" not in response["data"]["patient_report"]


def test_llm_phrase_relieved_is_filtered() -> None:
    response = _run_with_text('{"pharmacist_report":"可以放心服用","patient_report":"可以放心服用"}')
    assert "放心服用" not in response["data"]["pharmacist_report"]


def test_final_reports_still_contain_disclaimer() -> None:
    response = _run_with_text('{"pharmacist_report":"简化药师报告","patient_report":"简化患者报告"}')
    assert "本报告仅为用药安全辅助参考" in response["data"]["pharmacist_report"]
    assert "本报告仅为用药安全辅助参考" in response["data"]["patient_report"]
