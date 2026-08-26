"""Pure dev.17 boundary tests; no Home Assistant runtime required."""

import importlib.util
from pathlib import Path

MODULE_PATH = Path(__file__).parents[1] / "custom_components" / "elise_why" / "transport.py"
spec = importlib.util.spec_from_file_location("elise_why_transport", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_slug_resolution_handles_repository_prefix():
    apps = [
        {"slug": "other_app"},
        {"slug": "abc123_elise_investigator_02_test"},
    ]
    assert (
        module.find_investigator_slug(apps, "elise_investigator_02_test")
        == "abc123_elise_investigator_02_test"
    )


def test_internal_url_never_exposes_lan_address():
    assert module.investigator_url(
        "abc123_elise_investigator_02_test",
        "/api/v1/investigate",
        port=8099,
    ) == "http://abc123-elise-investigator-02-test:8099/api/v1/investigate"


def test_certainty_is_preserved_verbatim():
    for status in ("confirmed", "probable", "indeterminate"):
        payload = {"status": status, "entity_id": "cover.volet_salon_2"}
        result = module.validate_investigation_result(
            payload, expected_entity_id="cover.volet_salon_2"
        )
        assert result is payload
        assert result["status"] == status


def test_unknown_certainty_is_rejected():
    payload = {"status": "certain", "entity_id": "cover.volet_salon_2"}
    try:
        module.validate_investigation_result(
            payload, expected_entity_id="cover.volet_salon_2"
        )
    except ValueError:
        pass
    else:
        raise AssertionError("Unknown certainty status must be rejected")


def test_mismatched_entity_is_rejected():
    payload = {"status": "confirmed", "entity_id": "cover.volet_terrasse_2"}
    try:
        module.validate_investigation_result(
            payload, expected_entity_id="cover.volet_salon_2"
        )
    except ValueError:
        pass
    else:
        raise AssertionError("Mismatched entity_id must be rejected")
