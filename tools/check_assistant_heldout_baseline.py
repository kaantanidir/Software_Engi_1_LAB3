"""Multi-turn scenario evaluation for SmartBrew's local drink assistant.

Originally created for the baseline run (preserved in evidence/assistant-heldout-baseline.json)
and now used as a known multi-turn regression suite (writing to evidence/assistant-heldout-postchange.json).
Separates recipe correctness, multi-turn constraint retention, proposed temperature assumptions,
and conversational usefulness observations.
"""

from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from smartbrew.assistant import LocalAssistant
from smartbrew.service import Store


def append_history(history, message, result):
    """Purpose: mirror browser conversation history window. Inputs: prior history list, user message string, assistant result dict. Returns: bounded list of at most six messages."""
    if not result:
        return history[-6:]
    return (history + [
        {"role": "user", "content": message},
        {"role": "assistant", "content": result["message"]},
    ])[-6:]


def drink_named_in_message(drink_id, message):
    """Purpose: check whether the reply text names the proposed menu drink (heuristic signal only, not a standalone prose quality verdict). Inputs: drink id string and message string. Returns: bool."""
    lower = message.lower()
    aliases = {
        "espresso": ["espresso"],
        "americano": ["americano"],
        "latte": ["latte", "caffe latte"],
        "cappuccino": ["cappuccino"],
        "mocha": ["mocha"],
        "cocoa": ["cocoa", "hot chocolate"],
    }.get(drink_id, [drink_id])
    return any(alias in lower for alias in aliases)


def run_turn(client, store, scenario_id, turn_id, message, history, context_config, evaluate_fn):
    """Purpose: execute one live-model turn against an isolated DB and record separate evaluation dimensions. Inputs: LocalAssistant, Store, scenario/turn ids, prompt, history, context_config, evaluation callback. Returns: tuple of (turn_record_dict, response_dict_or_none)."""
    payload = {"message": message, "history": history, "context_config": context_config}
    before = store.state()
    started = time.perf_counter()
    response = None
    error_text = None
    try:
        response = client.suggest("", payload)
    except Exception as error:
        error_text = f"{type(error).__name__}: {error}"
    elapsed = round(time.perf_counter() - started, 3)
    no_side_effects = store.state() == before

    evaluation = evaluate_fn(response, context_config, error_text)
    if not no_side_effects:
        evaluation["recipeCorrect"] = False
        evaluation["notes"].append("Inference mutated persistent store state.")

    record = {
        "scenario": scenario_id,
        "turn": turn_id,
        "request": payload,
        "response": response,
        "seconds": elapsed,
        "noOrderingSideEffects": no_side_effects,
        "evaluation": evaluation,
    }
    if error_text:
        record["error"] = error_text

    status = "PASS" if (evaluation["recipeCorrect"] and evaluation["constraintsRetained"]) else "FAIL"
    print(f"[{status}] {scenario_id}.{turn_id} ({elapsed}s): {message}", flush=True)
    if response:
        cfg = response["quote"]["config"] if response.get("quote") else None
        print(f"       -> kind={response['kind']} config={cfg}", flush=True)
        print(f"       -> message={response['message']!r}", flush=True)
    elif error_text:
        print(f"       -> error={error_text}", flush=True)
    return record, response


def run_scenario_a(client, store):
    """Purpose: evaluate Scenario A (taste exploration, same-recipe/alternative handling, and persistent 'no milk' constraint). Inputs: LocalAssistant and Store. Returns: list of turn records."""
    records = []
    history, context = [], None

    # Turn A1
    msg1 = "I need an intense wake-up cup with just a touch of sweetness, no milk."
    def eval_a1(resp, prev_ctx, err):
        """Purpose: evaluate Turn A1 recipe and 'no milk' constraint. Inputs: response dict, prior config dict, error string. Returns: evaluation dict."""
        if not resp or resp["kind"] != "recipe" or not resp.get("quote"):
            return {"recipeCorrect": False, "constraintsRetained": False, "notes": [err or "Did not return a recipe."]}
        cfg = resp["quote"]["config"]
        recipe_ok = cfg["drink"] in ("espresso", "americano") and cfg["strength"] == "strong" and 1 <= cfg["syrup"] <= 2
        constraint_ok = cfg["milk"] == "none"
        notes = []
        if not recipe_ok:
            notes.append(f"Expected strong espresso/americano with 1-2 syrup, got {cfg}")
        if not constraint_ok:
            notes.append(f"Expected milk='none', got milk={cfg['milk']!r}")
        return {
            "recipeCorrect": recipe_ok,
            "constraintsRetained": constraint_ok,
            "conversationalSignals": {
                "namesProposedDrink": drink_named_in_message(cfg["drink"], resp["message"]),
            },
            "notes": notes,
        }

    rec1, resp1 = run_turn(client, store, "ScenarioA", "A1", msg1, history, context, eval_a1)
    records.append(rec1)
    if resp1:
        history = append_history(history, msg1, resp1)
        if resp1.get("quote"):
            context = resp1["quote"]["config"]

    # Turn A2
    msg2 = "Actually, I'm in the mood for something bittersweet."
    def eval_a2(resp, prev_ctx, err):
        """Purpose: evaluate Turn A2 bittersweet recipe and retained 'no milk' constraint. Inputs: response dict, prior config dict, error string. Returns: evaluation dict."""
        if not resp or resp["kind"] != "recipe" or not resp.get("quote"):
            return {"recipeCorrect": False, "constraintsRetained": False, "notes": [err or "Did not return a recipe."]}
        cfg = resp["quote"]["config"]
        recipe_ok = cfg["drink"] in ("americano", "espresso", "mocha") and 0 <= cfg["syrup"] <= 2
        constraint_ok = cfg["milk"] == "none"
        same_as_prev = prev_ctx is not None and cfg == prev_ctx
        notes = []
        if not recipe_ok:
            notes.append(f"Expected bittersweet drink (americano/espresso/mocha), got {cfg}")
        if not constraint_ok:
            notes.append(f"Failed to retain 'no milk' constraint from A1: got milk={cfg['milk']!r}")
        return {
            "recipeCorrect": recipe_ok,
            "constraintsRetained": constraint_ok,
            "conversationalSignals": {
                "namesProposedDrink": drink_named_in_message(cfg["drink"], resp["message"]),
                "identicalConfigToPreviousTurn": same_as_prev,
            },
            "notes": notes,
        }

    rec2, resp2 = run_turn(client, store, "ScenarioA", "A2", msg2, history, context, eval_a2)
    records.append(rec2)
    if resp2:
        history = append_history(history, msg2, resp2)
        if resp2.get("quote"):
            context = resp2["quote"]["config"]

    # Turn A3
    msg3 = "What else do you have that fits that?"
    def eval_a3(resp, prev_ctx, err):
        """Purpose: evaluate Turn A3 alternative base drink selection and retained 'no milk' constraint. Inputs: response dict, prior config dict, error string. Returns: evaluation dict."""
        if not resp or resp["kind"] != "recipe" or not resp.get("quote"):
            return {"recipeCorrect": False, "constraintsRetained": False, "notes": [err or "Did not return a recipe."]}
        cfg = resp["quote"]["config"]
        prev_drink = prev_ctx["drink"] if prev_ctx else None
        recipe_ok = cfg["drink"] != prev_drink and cfg["drink"] in ("americano", "espresso", "mocha")
        constraint_ok = cfg["milk"] == "none"
        leaked_placeholder = "latest validated recipe under discussion" in resp["message"].lower()
        notes = []
        if not recipe_ok:
            notes.append(f"Expected a different bittersweet drink from {prev_drink!r}, got {cfg['drink']!r}")
        if not constraint_ok:
            notes.append(f"Failed to retain 'no milk' constraint across A3: got milk={cfg['milk']!r}")
        if leaked_placeholder:
            notes.append("Leaked internal synthetic placeholder text in message.")
        return {
            "recipeCorrect": recipe_ok and not leaked_placeholder,
            "constraintsRetained": constraint_ok,
            "conversationalSignals": {
                "namesProposedDrink": drink_named_in_message(cfg["drink"], resp["message"]),
                "changedBaseDrink": cfg["drink"] != prev_drink,
                "leakedPlaceholderText": leaked_placeholder,
            },
            "notes": notes,
        }

    rec3, _ = run_turn(client, store, "ScenarioA", "A3", msg3, history, context, eval_a3)
    records.append(rec3)
    return records


def run_scenario_b(client, store):
    """Purpose: evaluate Scenario B (cozy/creamy/plant-based/not-too-hot request and multi-turn refinement carryover). Inputs: LocalAssistant and Store. Returns: list of turn records."""
    records = []
    history, context = [], None

    # Turn B1
    msg1 = "Something cozy, creamy, and plant-based, not too hot."
    def eval_b1(resp, prev_ctx, err):
        """Purpose: evaluate Turn B1 creamy oat drink and record proposed temperature<=65 assumption. Inputs: response dict, prior config dict, error string. Returns: evaluation dict."""
        if not resp or resp["kind"] != "recipe" or not resp.get("quote"):
            return {"recipeCorrect": False, "constraintsRetained": False, "notes": [err or "Did not return a recipe."]}
        cfg = resp["quote"]["config"]
        recipe_ok = cfg["drink"] in ("latte", "cappuccino", "cocoa", "mocha") and cfg["milk"] == "oat"
        temp_assumption_met = cfg["temperature"] <= 65
        notes = []
        if not recipe_ok:
            notes.append(f"Expected creamy oat-based drink, got {cfg}")
        if not temp_assumption_met:
            notes.append(f"Proposed evaluation assumption (temperature <= 65 for 'not too hot') not met: got {cfg['temperature']} C")
        return {
            "recipeCorrect": recipe_ok,
            "constraintsRetained": cfg["milk"] == "oat",
            "proposedAssumption_temp_le_65": temp_assumption_met,
            "conversationalSignals": {
                "namesProposedDrink": drink_named_in_message(cfg["drink"], resp["message"]),
            },
            "notes": notes,
        }

    rec1, resp1 = run_turn(client, store, "ScenarioB", "B1", msg1, history, context, eval_b1)
    records.append(rec1)
    if resp1:
        history = append_history(history, msg1, resp1)
        if resp1.get("quote"):
            context = resp1["quote"]["config"]

    # Turn B2
    msg2 = "Can we make it chocolatey?"
    def eval_b2(resp, prev_ctx, err):
        """Purpose: evaluate Turn B2 base-drink switch to mocha/cocoa while preserving oat milk and temperature. Inputs: response dict, prior config dict, error string. Returns: evaluation dict."""
        if not resp or resp["kind"] != "recipe" or not resp.get("quote"):
            return {"recipeCorrect": False, "constraintsRetained": False, "notes": [err or "Did not return a recipe."]}
        cfg = resp["quote"]["config"]
        recipe_ok = cfg["drink"] in ("mocha", "cocoa")
        prev_temp = prev_ctx["temperature"] if prev_ctx else 70
        constraint_ok = cfg["milk"] == "oat" and cfg["temperature"] == prev_temp
        notes = []
        if not recipe_ok:
            notes.append(f"Expected mocha or cocoa, got {cfg['drink']!r}")
        if not constraint_ok:
            notes.append(f"Expected milk='oat' and temperature={prev_temp} retained from B1, got milk={cfg['milk']!r}, temperature={cfg['temperature']}")
        return {
            "recipeCorrect": recipe_ok,
            "constraintsRetained": constraint_ok,
            "conversationalSignals": {
                "namesProposedDrink": drink_named_in_message(cfg["drink"], resp["message"]),
            },
            "notes": notes,
        }

    rec2, resp2 = run_turn(client, store, "ScenarioB", "B2", msg2, history, context, eval_b2)
    records.append(rec2)
    if resp2:
        history = append_history(history, msg2, resp2)
        if resp2.get("quote"):
            context = resp2["quote"]["config"]

    # Turn B3
    msg3 = "Keep that, just bump the heat up to 75 and add an extra shot of espresso."
    def eval_b3(resp, prev_ctx, err):
        """Purpose: evaluate Turn B3 temperature=75 and extra=1 update while retaining base drink and oat milk. Inputs: response dict, prior config dict, error string. Returns: evaluation dict."""
        if not resp or resp["kind"] != "recipe" or not resp.get("quote"):
            return {"recipeCorrect": False, "constraintsRetained": False, "notes": [err or "Did not return a recipe."]}
        cfg = resp["quote"]["config"]
        prev_drink = prev_ctx["drink"] if prev_ctx else None
        recipe_ok = cfg["temperature"] == 75 and cfg["extra"] == 1
        constraint_ok = cfg["drink"] == prev_drink and cfg["milk"] == "oat"
        notes = []
        if not recipe_ok:
            notes.append(f"Expected temperature=75 and extra=1, got temperature={cfg['temperature']}, extra={cfg['extra']}")
        if not constraint_ok:
            notes.append(f"Expected drink={prev_drink!r} and milk='oat' retained, got drink={cfg['drink']!r}, milk={cfg['milk']!r}")
        return {
            "recipeCorrect": recipe_ok,
            "constraintsRetained": constraint_ok,
            "conversationalSignals": {
                "namesProposedDrink": drink_named_in_message(cfg["drink"], resp["message"]),
            },
            "notes": notes,
        }

    rec3, _ = run_turn(client, store, "ScenarioB", "B3", msg3, history, context, eval_b3)
    records.append(rec3)
    return records


def run_scenario_c(client, store):
    """Purpose: evaluate Scenario C (unsupported iced/caramel refusal or clarification without silent substitution, followed by max-syrup boundary without unrequested extra espresso). Inputs: LocalAssistant and Store. Returns: list of turn records."""
    records = []
    history, context = [], None

    # Turn C1
    msg1 = "Give me the sweetest iced caramel latte you can make."
    def eval_c1(resp, prev_ctx, err):
        """Purpose: evaluate Turn C1 refusal/clarification of unsupported iced/caramel request without silent substitution. Inputs: response dict, prior config dict, error string. Returns: evaluation dict."""
        if not resp:
            return {"recipeCorrect": False, "constraintsRetained": False, "notes": [err or "No response."]}
        no_silent_sub = resp["kind"] in ("unavailable", "clarify") and resp.get("quote") is None
        notes = []
        if not no_silent_sub:
            notes.append(f"Silently substituted a recipe for unsupported iced/caramel request: {resp.get('quote', {}).get('config')}")
        return {
            "recipeCorrect": no_silent_sub,
            "constraintsRetained": no_silent_sub,
            "conversationalSignals": {
                "kindReturned": resp["kind"],
            },
            "notes": notes,
        }

    rec1, resp1 = run_turn(client, store, "ScenarioC", "C1", msg1, history, context, eval_c1)
    records.append(rec1)
    if resp1:
        history = append_history(history, msg1, resp1)
        if resp1.get("quote"):
            context = resp1["quote"]["config"]

    # Turn C2
    # Interpretation of "hot" in Turn C2:
    # SmartBrew dispenses only heated drinks (50-90 C in 5 C steps; 70 C is the standard default).
    # In C2, "a hot vanilla oat latte" contrasts with C1's rejected "iced caramel latte".
    # Therefore any supported machine temperature (50-90 C) is a heated drink, while >=70 C is recorded
    # separately as a proposed default-hot assumption. Unrequested extra espresso (extra != 0) is a failure.
    msg2 = "Okay, a hot vanilla oat latte with maximum sweetness then, and make it even sweeter on top of that."
    def eval_c2(resp, prev_ctx, err):
        """Purpose: evaluate Turn C2 max-syrup latte without unrequested extra espresso, plus documented 'hot' temperature check. Inputs: response dict, prior config dict, error string. Returns: evaluation dict."""
        if not resp or resp["kind"] != "recipe" or not resp.get("quote"):
            return {"recipeCorrect": False, "constraintsRetained": False, "notes": [err or "Did not return a recipe."]}
        cfg = resp["quote"]["config"]
        recipe_ok = cfg["drink"] == "latte" and cfg["syrup"] == 4 and cfg["extra"] == 0 and 50 <= cfg["temperature"] <= 90
        constraint_ok = cfg["milk"] == "oat"
        hot_default_assumption = cfg["temperature"] >= 70
        notes = []
        if cfg["drink"] != "latte" or cfg["syrup"] != 4:
            notes.append(f"Expected latte with syrup=4, got {cfg}")
        if cfg["extra"] != 0:
            notes.append(f"Modified unrelated field extra={cfg['extra']} (extra espresso) when user asked for more sweetness.")
        if not constraint_ok:
            notes.append(f"Expected milk='oat', got {cfg['milk']!r}")
        if not hot_default_assumption:
            notes.append(f"Proposed assumption (temperature >= 70 C when switching from rejected iced request to 'hot' drink) not met: got {cfg['temperature']} C")
        return {
            "recipeCorrect": recipe_ok,
            "constraintsRetained": constraint_ok,
            "proposedAssumption_temp_ge_70": hot_default_assumption,
            "conversationalSignals": {
                "namesProposedDrink": drink_named_in_message(cfg["drink"], resp["message"]),
                "noUnrequestedExtraEspresso": cfg["extra"] == 0,
            },
            "notes": notes,
        }

    rec2, _ = run_turn(client, store, "ScenarioC", "C2", msg2, history, context, eval_c2)
    records.append(rec2)
    return records


def main():
    """Purpose: run all multi-turn scenarios against the live local model using isolated temporary SQLite databases and save post-change evidence without overwriting assistant-heldout-baseline.json. Inputs: running local Ollama instance. Returns: None; exits nonzero if any turn fails recipeCorrect or constraintsRetained."""
    directory = ROOT / "tmp" / "tests"
    directory.mkdir(parents=True, exist_ok=True)
    evidence = {
        "recordedAt": datetime.now(timezone.utc).isoformat(),
        "liveInference": False,
        "simulatedModelResponses": False,
        "evaluationNote": (
            "Post-change evaluation of the three multi-turn scenarios (now known regression cases; "
            "original pre-change baseline is preserved in evidence/assistant-heldout-baseline.json). "
            "Separates recipeCorrect, constraintsRetained, proposed temperature assumptions, and conversationalSignals."
        ),
        "results": [],
        "passed": False,
    }
    try:
        with tempfile.TemporaryDirectory(dir=directory) as folder:
            db_path = Path(folder) / "heldout-postchange.db"
            store = Store(db_path)
            client = LocalAssistant(store)
            if not client.status()["available"]:
                raise RuntimeError("Local Ollama qwen3:4b is not currently available on 127.0.0.1:11434.")
            evidence["runtime"] = client.request("/api/version")
            evidence["model"] = next(
                item for item in client.request("/api/tags")["models"] if item["name"] == client.model
            )
            evidence["liveInference"] = True

            for runner in (run_scenario_a, run_scenario_b, run_scenario_c):
                scen_db = Path(folder) / f"{runner.__name__}.db"
                scen_store = Store(scen_db)
                scen_client = LocalAssistant(scen_store)
                evidence["results"].extend(runner(scen_client, scen_store))

            recipe_ok_count = sum(1 for r in evidence["results"] if r["evaluation"]["recipeCorrect"])
            constraint_ok_count = sum(1 for r in evidence["results"] if r["evaluation"]["constraintsRetained"])
            no_side_effects = all(r["noOrderingSideEffects"] for r in evidence["results"])
            total = len(evidence["results"])
            evidence["summary"] = {
                "totalTurns": total,
                "recipeCorrectCount": recipe_ok_count,
                "constraintsRetainedCount": constraint_ok_count,
                "noOrderingSideEffects": no_side_effects,
            }
            evidence["passed"] = (
                total == 8
                and recipe_ok_count == total
                and constraint_ok_count == total
                and no_side_effects
            )
    except Exception as error:
        evidence["error"] = f"{type(error).__name__}: {error}"
        raise
    finally:
        target = ROOT / "evidence" / "current" / "assistant-heldout-postchange.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(evidence, indent=2), encoding="utf-8", newline="\n")
        print(f"Saved post-change evidence to {target}", flush=True)
    if not evidence["passed"]:
        raise SystemExit("One or more turns failed recipeCorrect or constraintsRetained; inspect evidence/current/assistant-heldout-postchange.json.")


if __name__ == "__main__":
    main()
