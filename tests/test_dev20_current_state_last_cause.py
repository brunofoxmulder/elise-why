"""Regression tests for simple current-state causal questions in dev.20."""

from pathlib import Path

ROOT = Path(__file__).parents[1]
COMPONENT = ROOT / "custom_components" / "elise_why"


def test_simple_current_state_uses_latest_relevant_cause_without_time_injection():
    presentation = (COMPONENT / "presentation.py").read_text(encoding="utf-8")

    assert "Pourquoi le volet est fermé ?" in presentation
    assert "latest cause of the latest relevant state change" in presentation
    assert "do not pass observed_time" in presentation
    assert "Never derive observed_time from GetLiveContext" in presentation
    assert "use GetLiveContext first" not in presentation


def test_observed_time_parameter_is_reserved_for_explicit_user_time():
    llm = (COMPONENT / "llm.py").read_text(encoding="utf-8")

    assert "only when the user explicitly supplied" in llm
    assert "Never derive it from live context" in llm
    assert "last_changed" in llm
    assert "last_updated" in llm


def test_dev20_version_is_declared_consistently():
    const = (COMPONENT / "const.py").read_text(encoding="utf-8")
    manifest = (COMPONENT / "manifest.json").read_text(encoding="utf-8")

    assert 'VERSION = "0.2.0-dev.20"' in const
    assert '"version": "0.2.0-dev.20"' in manifest
