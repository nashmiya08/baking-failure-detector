"""Diagnosis engine: image symptoms + user inputs + knowledge base -> ranked causes."""
from knowledge_base import SYMPTOMS, PRODUCT_RANGES


def build_flags(inp):
    """Turn the user's inputs into True/False 'rules' and human-readable notes."""
    flags, notes = set(), []
    rng = PRODUCT_RANGES.get(inp["product"])
    if rng:
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
    if "Dark" in inp["tin"]:
        flags.add("dark_tin")
        notes.append("A dark tin absorbs more heat and browns faster.")
    if any(w in inp["tin"] for w in ("Glass", "Silicone")):
        flags.add("insulating_tin")
        notes.append("Glass/silicone/ceramic conducts heat slowly and may under-bake.")

    if not inp["preheated"]:
        flags.add("no_preheat")
        notes.append("The oven was not preheated.")
    if inp["opened_door"]:
        flags.add("opened_door")
        notes.append("Opening the oven door drops the temperature and can collapse the bake.")

    text = inp["recipe"].lower()
    if any(w in text for w in ("blender", "high speed", "beat well", "whisk vigorously", "mix well")):
        flags.add("overmix_hint")
        notes.append("Recipe text suggests vigorous mixing, which can toughen the crumb.")
    if inp["product"] == "Cookies":
        if "melted butter" in text or "melted" in text:
            flags.add("melted_fat")
        if "chill" not in text and "refrigerat" not in text and text.strip():
            flags.add("no_chill")
    return flags, notes


def diagnose(inp, image_symptoms):
    """image_symptoms: list of (symptom_key, confidence, source)."""
    flags, notes = build_flags(inp)

    # merge image predictions and the user's own guesses
    found = {}
    for key, conf, src in image_symptoms:
        found[key] = (conf, src)
    for key in inp["guesses"]:
        if key not in found or found[key][0] < 0.8:
            found[key] = (0.8, "your guess")

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

    return {"symptoms": results, "notes": notes,
            "plan": {"recipe": plan_recipe, "process": plan_process}}
