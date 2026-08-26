"""Pure dev.18 presentation-policy tests; no Home Assistant runtime required."""

import importlib.util
from pathlib import Path

MODULE_PATH = (
    Path(__file__).parents[1]
    / "custom_components"
    / "elise_why"
    / "presentation.py"
)
spec = importlib.util.spec_from_file_location("elise_why_presentation", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_human_is_default_and_short_policy_is_present():
    prompt = module.build_prompt("unknown")
    assert "Response style: Humaine." in prompt
    assert "no more than 35 words" in prompt


def test_control_requests_are_kept_out_of_investigator():
    prompt = module.build_prompt(module.RESPONSE_STYLE_HUMAN)
    assert "Never call InvestigateWhy for an action request" in prompt
    assert "standard Home Assistant Assist control tools" in prompt
    assert "Never refuse a Home Assistant control request" in prompt


def test_explicit_plural_is_not_forced_into_clarification():
    prompt = module.build_prompt(module.RESPONSE_STYLE_HUMAN)
    assert "explicit plural request" in prompt
    assert "all_matches=true" in prompt


def test_intermediate_acknowledgement_is_best_effort_only():
    prompt = module.build_prompt(module.RESPONSE_STYLE_HUMAN)
    assert 'first emit exactly "Je regarde…"' in prompt
    assert "If the transport cannot surface intermediate text" in prompt


def test_detail_levels_are_distinct():
    human = module.build_prompt(module.RESPONSE_STYLE_HUMAN)
    detailed = module.build_prompt(module.RESPONSE_STYLE_DETAILED)
    complete = module.build_prompt(module.RESPONSE_STYLE_COMPLETE)
    assert "Response style: Humaine." in human
    assert "Response style: Détaillée." in detailed
    assert "Response style: Complète." in complete
    assert len({human, detailed, complete}) == 3


def test_custom_prompt_is_style_only_and_capped():
    custom = "Réponds chaleureusement et donne l'heure quand elle est utile."
    prompt = module.build_prompt(module.RESPONSE_STYLE_HUMAN, custom)
    assert module.CUSTOM_STYLE_GUARD in prompt
    assert custom in prompt

    too_long = "x" * (module.MAX_CUSTOM_STYLE_PROMPT_LENGTH + 50)
    normalized = module.normalize_custom_style_prompt(too_long)
    assert len(normalized) == module.MAX_CUSTOM_STYLE_PROMPT_LENGTH
