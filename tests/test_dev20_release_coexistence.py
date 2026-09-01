"""Release-level coexistence checks for Élise Why dev.20."""

from pathlib import Path

ROOT = Path(__file__).parents[1]
LLM = ROOT / "custom_components" / "elise_why" / "llm.py"
MANIFEST = ROOT / "custom_components" / "elise_why" / "manifest.json"


def test_causal_and_thermal_tools_are_both_exposed():
    text = LLM.read_text(encoding="utf-8")
    assert 'name = "InvestigateWhy"' in text
    assert 'name = "AnalyseThermique"' in text
    assert "tools.insert(0, InvestigateWhyTool())" in text
    assert "tools: list[Tool] = [ThermalAnalysisTool()]" in text


def test_current_state_temporal_guard_survives_release_merge():
    text = LLM.read_text(encoding="utf-8")
    assert "only when the user explicitly supplied" in text
    assert "Never derive it from live context" in text
    assert "last_changed" in text
    assert "last_updated" in text


def test_release_keeps_dev20_version():
    manifest = MANIFEST.read_text(encoding="utf-8")
    assert '"version": "0.2.0-dev.20"' in manifest
