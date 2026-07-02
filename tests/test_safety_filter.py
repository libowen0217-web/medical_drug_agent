from medical_drug_agent.app.reporting.safety_filter import SafetyFilter


def test_replace_can_eat_phrase() -> None:
    filter_ = SafetyFilter()
    text, warnings = filter_.validate_and_fix("你可以吃这个药。")
    assert "你可以吃" not in text
    assert warnings


def test_replace_completely_safe_phrase() -> None:
    filter_ = SafetyFilter()
    text, warnings = filter_.validate_and_fix("这个方案完全安全。")
    assert "完全安全" not in text
    assert warnings


def test_append_disclaimer_when_missing() -> None:
    filter_ = SafetyFilter()
    text, warnings = filter_.validate_and_fix("普通文本")
    assert SafetyFilter.DISCLAIMER_1 in text
    assert SafetyFilter.DISCLAIMER_2 in text
    assert warnings


def test_returns_warnings_list() -> None:
    filter_ = SafetyFilter()
    _, warnings = filter_.validate_and_fix("建议服用这个药。")
    assert isinstance(warnings, list)

