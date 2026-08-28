from pathlib import Path

ROOT = Path(__file__).parents[1]
COMPONENT = ROOT / "custom_components" / "elise_why"


def test_elise_why_uses_structured_journal_first_endpoint():
    const_text = (COMPONENT / "const.py").read_text(encoding="utf-8")
    client_text = (COMPONENT / "client.py").read_text(encoding="utf-8")

    assert 'INVESTIGATOR_WHY_PATH = "/api/v1/why"' in const_text
    assert "INVESTIGATOR_WHY_PATH" in client_text
    assert "self._url(INVESTIGATOR_WHY_PATH)" in client_text
    assert "INVESTIGATOR_INVESTIGATE_PATH" not in client_text


def test_dev19_version_is_declared_in_manifest_and_const():
    manifest_text = (COMPONENT / "manifest.json").read_text(encoding="utf-8")
    const_text = (COMPONENT / "const.py").read_text(encoding="utf-8")

    assert '"version": "0.2.0-dev.19"' in manifest_text
    assert 'VERSION = "0.2.0-dev.19"' in const_text
