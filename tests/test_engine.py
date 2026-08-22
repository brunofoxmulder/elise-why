"""Pure unit tests for Élise Why V0.1."""

from datetime import UTC, datetime, timedelta
import asyncio
import importlib.util
from pathlib import Path

ENGINE_PATH = Path(__file__).parents[1] / "custom_components" / "elise_why" / "engine.py"
spec = importlib.util.spec_from_file_location("elise_why_engine", ENGINE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
WhyEngine = module.WhyEngine

BASE = datetime(2026, 8, 22, 10, 0, tzinfo=UTC)


class FakeProvider:
    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    async def get_logbook(self, *, entity_id, start_time, end_time):
        self.calls.append(entity_id)
        return self.responses.get(entity_id, [])


def iso(dt):
    return dt.isoformat()


async def run_scenarios():
    # Confirmed automation + window state.
    provider = FakeProvider({
        "cover.volet_salon_2": [{
            "when": iso(BASE),
            "entity_id": "cover.volet_salon_2",
            "state": "open",
            "context_domain": "automation",
            "context_entity_id": "automation.volet_fenetre",
            "context_event_type": "automation_triggered",
            "context_source": "state of binary_sensor.fenetre_porte_contact",
            "context_state": "on",
        }]
    })
    result = await WhyEngine(provider).explain("cover.volet_salon_2", at_time=BASE)
    assert result["status"] == "confirmed"
    assert result["source_type"] == "automation"
    assert result["source_entity_id"] == "automation.volet_fenetre"
    assert result["reason"] == "Parce que la fenêtre est ouverte."

    # Final cover state can lose context; only walk back <= 2 minutes.
    provider = FakeProvider({
        "cover.volet_salon_2": [
            {
                "when": iso(BASE - timedelta(seconds=40)),
                "entity_id": "cover.volet_salon_2",
                "state": "opening",
                "context_event_type": "automation_triggered",
                "context_source": "numeric state of sensor.lumiere_soleil_illuminance",
            },
            {
                "when": iso(BASE),
                "entity_id": "cover.volet_salon_2",
                "state": "open",
            },
        ]
    })
    result = await WhyEngine(provider).explain("cover.volet_salon_2", at_time=BASE)
    assert result["status"] == "confirmed"
    assert result["reason"] == "Parce que la luminosité a franchi le seuil prévu."

    # Direct user action.
    provider = FakeProvider({
        "light.entree": [{
            "when": iso(BASE),
            "entity_id": "light.entree",
            "state": "on",
            "context_user_id": "user-123",
        }]
    })
    result = await WhyEngine(provider).explain("light.entree", at_time=BASE)
    assert result["status"] == "confirmed"
    assert result["source_type"] == "user"

    # Unknown automation trigger: linked but never invented.
    provider = FakeProvider({
        "light.entree": [{
            "when": iso(BASE),
            "entity_id": "light.entree",
            "state": "on",
            "context_event_type": "automation_triggered",
            "context_source": "event foo_bar",
        }]
    })
    result = await WhyEngine(provider).explain("light.entree", at_time=BASE)
    assert result["status"] == "probable"
    assert "déterminer précisément" in result["reason"]

    # Bare context ID is not proof.
    provider = FakeProvider({
        "light.entree": [{
            "when": iso(BASE),
            "entity_id": "light.entree",
            "state": "on",
            "context_id": "ctx-only",
        }]
    })
    result = await WhyEngine(provider).explain("light.entree", at_time=BASE)
    assert result["status"] == "indeterminate"

    # Negative-offset sunset trigger: do not claim sunset happened.
    provider = FakeProvider({
        "light.entree": [{
            "when": iso(BASE),
            "entity_id": "light.entree",
            "state": "on",
            "context_domain": "automation",
            "context_entity_id": "automation.ambiance_soir",
            "context_event_type": "automation_triggered",
            "context_source": "sun event sunset",
        }],
        "sun.sun": [{
            "when": iso(BASE - timedelta(hours=2)),
            "entity_id": "sun.sun",
            "state": "above_horizon",
        }],
    })
    result = await WhyEngine(provider).explain("light.entree", at_time=BASE)
    assert result["status"] == "probable"

    # Time-pattern automation is a known causal trigger.
    provider = FakeProvider({
        "light.entree": [{
            "when": iso(BASE),
            "entity_id": "light.entree",
            "state": "on",
            "context_domain": "automation",
            "context_entity_id": "automation.test_horaire",
            "context_event_type": "automation_triggered",
            "context_source": "time pattern",
        }]
    })
    result = await WhyEngine(provider).explain("light.entree", at_time=BASE)
    assert result["status"] == "confirmed"
    assert "horaire" in result["reason"]

    print("7/7 pure engine scenarios passed")


if __name__ == "__main__":
    asyncio.run(run_scenarios())
