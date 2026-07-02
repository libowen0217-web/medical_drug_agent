from medical_drug_agent.app.evidence.store import EvidenceStore
from medical_drug_agent.app.schemas import EvidenceItem


def test_store_can_load_csv() -> None:
    store = EvidenceStore()
    dataframe = store.load()
    assert not dataframe.empty


def test_search_by_keywords_returns_results() -> None:
    results = EvidenceStore().search_by_keywords(["NSAID", "高血压"])
    assert results


def test_results_contain_evidence_item() -> None:
    result = EvidenceStore().search_by_keywords(["NSAID"], limit=1)[0]
    assert isinstance(result, EvidenceItem)


def test_matched_reason_is_not_empty() -> None:
    result = EvidenceStore().search_by_keywords(["NSAID"], limit=1)[0]
    assert result.matched_reason


def test_limit_is_effective() -> None:
    results = EvidenceStore().search_by_keywords(["风险"], limit=2)
    assert len(results) <= 2
