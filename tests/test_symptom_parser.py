from medical_drug_agent.app.symptom.symptom_parser import SymptomParser


def test_fever_headache_sore_throat_can_be_parsed() -> None:
    parsed = SymptomParser().parse("发热、头痛、嗓子疼")
    names = {item.symptom_name for item in parsed}
    assert "发热" in names
    assert "头痛" in names
    assert "咽痛" in names


def test_empty_text_returns_empty_list() -> None:
    assert SymptomParser().parse("") == []


def test_throat_synonym_maps_to_sore_throat() -> None:
    parsed = SymptomParser().parse("喉咙痛")
    assert any(item.symptom_name == "咽痛" for item in parsed)


def test_runny_nose_and_sneeze_are_recognized() -> None:
    parsed = SymptomParser().parse("流鼻涕、打喷嚏")
    names = {item.symptom_name for item in parsed}
    assert "流鼻涕" in names
    assert "打喷嚏" in names
