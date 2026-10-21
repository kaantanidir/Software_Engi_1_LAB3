"""Real-model regression for changing drinks over a longer page conversation."""

from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile

from check_assistant_conversations import ROOT, append_history, check_turn
from smartbrew.assistant import LocalAssistant
from smartbrew.service import Store


def main():
    """Purpose: detect stuck/repeated suggestions. Inputs: running local model. Returns: None; records failures and exits nonzero."""
    evidence = {"recordedAt": datetime.now(timezone.utc).isoformat(), "results": [],
                "liveInference": True, "simulatedModelResponses": False, "passed": False}
    try:
        with tempfile.TemporaryDirectory(dir=ROOT / "tmp" / "tests") as folder:
            store = Store(Path(folder) / "long-chat.db")
            client = LocalAssistant(store)
            history, context = [], None
            turns = [
                ("Something strong, slightly sweet, and without dairy.", {"strength": "strong"}),
                ("I want something sweet but also bitter.", {}),
                ("Make it an oat latte instead.", {"drink": "latte", "milk": "oat"}),
                ("Actually, hot chocolate with oat milk, no syrup, no extra espresso.", {"drink": "cocoa", "milk": "oat", "syrup": 0, "extra": 0}),
                ("No, I want a cappuccino with dairy milk and two syrup shots.", {"drink": "cappuccino", "milk": "dairy", "syrup": 2}),
                ("Make that mild.", {"strength": "mild"}),
                ("Now forget that drink. An espresso without milk or syrup, regular strength, and no extras.",
                 {"drink": "espresso", "milk": "none", "strength": "regular", "syrup": 0, "extra": 0}),
                ("Give me a different drink instead, still without milk.", {"milk": "none"}),
                ("Go back to an oat latte at 80 degrees.", {"drink": "latte", "milk": "oat", "temperature": 80}),
            ]
            for message, fields in turns:
                if message == "Make that mild." and context:
                    fields = {**context, **fields}
                previous = context
                result = check_turn(client, store, evidence, message, "recipe", history, context, fields)
                actual = evidence["results"][-1].get("response")
                if actual:
                    history = append_history(history, message, actual)
                    if actual["quote"]:
                        context = actual["quote"]["config"]
                if result and "different drink" in message and previous and context["drink"] == previous["drink"]:
                    evidence["results"][-1].update(passed=False, error="Repeated the same base drink after explicit alternative request")
                if result:
                    aliases = [context["drink"]] if context["drink"] != "cocoa" else ["cocoa", "hot chocolate"]
                    evidence["results"][-1]["namesProposedDrink"] = any(name in result["message"].lower() for name in aliases)
            evidence["runtime"] = client.request("/api/version")
            evidence["passed"] = all(row["passed"] for row in evidence["results"])
            evidence["wordingChecksPassed"] = all(row.get("namesProposedDrink", False) for row in evidence["results"])
    except Exception as error:
        evidence["error"] = f"{type(error).__name__}: {error}"
    finally:
        target = ROOT / "evidence" / "current" / "assistant-long-chat.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(evidence, indent=2), encoding="utf-8", newline="\n")
        print(f"Saved {target}", flush=True)
    if not evidence["passed"]:
        raise SystemExit("Long conversation regression failed; inspect recorded responses.")


if __name__ == "__main__":
    main()
