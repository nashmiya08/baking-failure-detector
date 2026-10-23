"""Diagnosis engine: image symptoms + typed guess + inputs + recipe check + bake check + knowledge base."""
from knowledge_base import SYMPTOMS, PRODUCT_RANGES
from recipe_fixer import analyze


def bake_check(inp, plan):
    """Compare the user's temperature, time and pan with the plan for THIS recipe. Returns (flags, check dict)."""
    flags, rows, science = set(), [], list(plan["science"])
    t, tp = inp["temp"], plan["temp_c"]
    if t > tp + 10:
        status = "high"
        flags.add("temp_high")
        science.append(f"At {t:.0f} C the surface and edges reach browning temperature (sugars caramelise, proteins go through the "
                       f"Maillard reaction) long before the centre is cooked, so the top burns while the middle stays raw or sinks later. "
                       f"Lower the oven to about {tp:.0f} C.")
    elif t < tp - 10:
        status = "low"
        flags.add("temp_low")
        science.append(f"At {t:.0f} C the batter heats too slowly, so egg protein and starch set late and the gas escapes before the "
                       f"crumb is firm. You get a pale, dense or gummy bake (and cookies spread). Raise the oven to about {tp:.0f} C.")
    else:
        status = "ok"
    rows.append({"what": "Oven temperature", "you": f"{t:.0f} C", "suggested": f"{tp:.0f} C", "status": status})

    m, lo, hi = inp["minutes"], plan["min_lo"], plan["min_hi"]
    if m > hi:
        status = "long"
        flags.add("time_long")
        science.append(f"{m:.0f} minutes is longer than the {lo}-{hi} minutes this recipe needs in your pan. After the centre sets, extra time only "
                       "evaporates moisture, giving a dry, crumbly bake with a hard dark crust.")
    elif m < lo:
        status = "short"
        flags.add("time_short")
        science.append(f"{m:.0f} minutes is shorter than the {lo}-{hi} minutes this recipe needs. The starch is not fully gelatinised and the "
                       "eggs are not set in the centre, so it stays wet and can collapse as it cools.")
    else:
        status = "ok"
    rows.append({"what": "Baking time", "you": f"{m:.0f} min", "suggested": f"{lo}-{hi} min", "status": status})

    r = plan["depth_ratio"]
    if r is not None:
        status = "deep" if r > 1.3 else "shallow" if r < 0.75 else "ok"
        rows.append({"what": "Batter depth in your pan", "you": f"{(r - 1) * 100:+.0f}% vs reference",
                     "suggested": "within -25% to +30%", "status": status})
    return flags, {"ref": plan["ref_name"], "ref_oven": f"{plan['ref_temp']:.0f} C, {plan['ref_minutes']:.0f} min in {plan['ref_pan']}",
                   "rows": rows, "science": science}


def build_flags(inp, use_ranges):
    """Turn the other inputs into True/False 'rules' and human-readable notes."""
    flags, notes = set(), []
    rng = PRODUCT_RANGES.get(inp["product"]) if use_ranges else None
    if rng:   # only used when there is no recipe to compare with
        lo, hi = rng["temp"]
        if inp["temp"] > hi:
            flags.add("temp_high")
            notes.append(f"{inp['temp']} C is above the usual {lo}-{hi} C for {inp['product'].lower()}.")
        elif inp["temp"] < lo:
            flags.add("temp_low")
            notes.append(f"{inp['temp']} C is below the usual {lo}-{hi} C for {inp['product'].lower()}.")
        tlo, thi = rng["time"]
        if inp["minutes"] > thi:
            flags.add("time_long")
            notes.append(f"{inp['minutes']} min is longer than the usual {tlo}-{thi} min.")
        elif inp["minutes"] < tlo:
            flags.add("time_short")
            notes.append(f"{inp['minutes']} min is shorter than the usual {tlo}-{thi} min.")

    if inp["rod"] == "Top rod only":
        flags.add("top_rod")
        notes.append("Top-rod-only heating browns the surface quickly in many ovens/OTGs.")
    if "Dark" in inp["tin"] or "Glass" in inp["tin"]:
        flags.add("dark_tin")
        notes.append("Dark metal and glass/ceramic hold more heat and brown the edges and base faster.")
    if "Silicone" in inp["tin"]:
        flags.add("insulating_tin")
        notes.append("Silicone insulates and may under-bake the batter.")

    if not inp["preheated"]:
        flags.add("no_preheat")
        notes.append("The oven was not preheated.")
    if inp["opened_door"]:
        flags.add("opened_door")
        notes.append("Opening the oven door drops the temperature and can collapse the bake.")
    if inp.get("mixing", "").startswith("Mixed vigorously"):
        flags.add("overmix_hint")
        notes.append("You mixed vigorously, which develops gluten and makes the crumb tough.")

    text = inp["recipe"].lower()
    if any(w in text for w in ("blender", "high speed", "beat well", "whisk vigorously", "mix well")):
        flags.add("overmix_hint")
        notes.append("Recipe text suggests vigorous mixing, which can toughen the crumb.")
    if inp["product"] == "Cookies":
        if "melted" in text:
            flags.add("melted_fat")
        if "chill" not in text and "refrigerat" not in text and text.strip():
            flags.add("no_chill")
    return flags, notes


def diagnose(inp, image_symptoms):
    """image_symptoms: list of (symptom_key, confidence, source).
    inp["guesses"] = symptom keys found in the typed guess; inp["guess_flags"] = {rule: sentence}."""
    setup = {"pan": inp.get("pan"), "tin": inp["tin"], "rod": inp["rod"]}
    recipe_check = analyze(inp["recipe"], inp["product"], setup)
    plan = recipe_check.get("bake_plan") if recipe_check else None

    flags, notes = build_flags(inp, use_ranges=plan is None)
    bake = None
    if plan:
        bake_flags, bake = bake_check(inp, plan)
        flags |= bake_flags
    if recipe_check:
        flags |= set(recipe_check["flags"])

    for rule, sentence in inp.get("guess_flags", {}).items():
        flags.add(rule)
        notes.append(f"You suspected that {sentence}; this was added to the analysis.")
    if inp.get("guess_text", "").strip() and not inp.get("guesses") and not inp.get("guess_flags"):
        notes.append("I could not match your typed guess to a known problem. Try words like burnt, sunk, dense, "
                     "cracked, spread, dry or raw.")

    found = {}
    for key, conf, src in image_symptoms:
        found[key] = (conf, src)
    for key in inp.get("guesses", []):
        if key not in found or found[key][0] < 0.8:
            found[key] = (0.8, "your typed guess")

    results, plan_recipe, plan_process = [], [], []
    for key, (conf, src) in sorted(found.items(), key=lambda x: -x[1][0]):
        causes = []
        for c in SYMPTOMS[key]["causes"]:
            score = 1.0 + (2.0 if c["rule"] in flags else 0.0)
            causes.append({**c, "score": score, "matched": c["rule"] in flags})
        total = sum(c["score"] for c in causes)
        for c in causes:
            c["score"] = c["score"] / total
        causes.sort(key=lambda c: -c["score"])
        top = causes[:3]
        results.append({"key": key, "label": SYMPTOMS[key]["label"],
                        "confidence": conf, "source": src, "causes": top})
        for c in top[:2]:
            for text, bucket in ((c["recipe_fix"], plan_recipe), (c["process_fix"], plan_process)):
                if "No ingredient change" not in text and text not in bucket:
                    bucket.append(text)

    if recipe_check and recipe_check.get("reference"):
        plan_process.append("Method from the closest reference recipe: " + recipe_check["reference"]["method"])

    return {"symptoms": results, "notes": notes, "recipe_check": recipe_check, "bake_check": bake,
            "guess_text": inp.get("guess_text", ""),
            "plan": {"recipe": plan_recipe, "process": plan_process}}
