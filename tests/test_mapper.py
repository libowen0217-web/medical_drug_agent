import pytest

from medical_drug_agent.app.normalization.mapper import DrugNameMapper


def test_normalize_chinese_name() -> None:
    mapper = DrugNameMapper()
    result = mapper.normalize("布洛芬")
    assert result.en_name == "Ibuprofen"


def test_normalize_english_name() -> None:
    mapper = DrugNameMapper()
    result = mapper.normalize("Ibuprofen")
    assert result.en_name == "Ibuprofen"


def test_normalize_alias_name() -> None:
    mapper = DrugNameMapper()
    result = mapper.normalize("芬必得")
    assert result.en_name == "Ibuprofen"


def test_unknown_drug_raises_value_error() -> None:
    mapper = DrugNameMapper()
    with pytest.raises(ValueError, match="未识别药物"):
        mapper.normalize("未知药物")

