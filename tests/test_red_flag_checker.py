from medical_drug_agent.app.symptom.red_flag_checker import RedFlagChecker


def test_breathing_difficulty_triggers_red_flag() -> None:
    findings = RedFlagChecker().check("呼吸困难")
    assert any(item.red_flag_id == "RF001" for item in findings)


def test_chest_pain_triggers_red_flag() -> None:
    findings = RedFlagChecker().check("胸痛")
    assert any(item.red_flag_id == "RF002" for item in findings)


def test_temperature_40_triggers_red_flag() -> None:
    findings = RedFlagChecker().check("发热", temperature_c=40.0)
    assert any(item.red_flag_id == "RF007" for item in findings)


def test_long_duration_high_fever_triggers_red_flag() -> None:
    findings = RedFlagChecker().check("发热", temperature_c=39.2, duration_days=3)
    assert any(item.red_flag_id == "RF006" for item in findings)


def test_pregnancy_with_fever_triggers_red_flag() -> None:
    findings = RedFlagChecker().check("发热", temperature_c=38.0, patient_factors=["孕妇"])
    assert any(item.red_flag_id == "RF010" for item in findings)


def test_no_red_flag_returns_empty_list() -> None:
    findings = RedFlagChecker().check("流鼻涕、打喷嚏", temperature_c=37.0, duration_days=1)
    assert findings == []


def test_lung_cancer_keywords_trigger_serious_disease_block() -> None:
    findings = RedFlagChecker().check("肺癌，最近伴胸痛和咯血")
    assert any(item.red_flag_id == "RF900" for item in findings)
