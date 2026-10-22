"""
Recipe checker: reads the user's ingredient list, converts amounts to grams,
compares them with typical baker's ratios (flour = 100%) and suggests a corrected recipe.
These ratios are general home-baking guidance, not exact for every recipe.
"""
import re

FRACTIONS = {"½": " 1/2", "¼": " 1/4", "¾": " 3/4", "⅓": " 1/3", "⅔": " 2/3"}

# keyword -> ingredient group
CATEGORY_WORDS = {
    "leavener": ["baking powder", "baking soda", "bicarbonate", "soda", "yeast"],
    "cocoa": ["cocoa"],
    "salt": ["salt"],
    "egg": ["egg"],
    "flour": ["flour", "maida", "atta"],
    "sugar": ["sugar", "jaggery"],
    "fat": ["butter", "oil", "ghee", "margarine", "shortening"],
    "liquid": ["milk", "water", "buttermilk", "curd", "yogurt", "yoghurt", "cream"],
}
LABEL = {"flour": "flour", "sugar": "sugar", "fat": "butter / oil", "egg": "",
         "liquid": "milk / water", "leavener": "baking powder / soda / yeast",
         "salt": "salt", "cocoa": "cocoa powder"}
NICE = {"flour": "Flour", "sugar": "Sugar", "fat": "Butter / oil", "egg": "Eggs",
        "liquid": "Milk / water", "leavener": "Baking powder / soda / yeast",
        "salt": "Salt", "cocoa": "Cocoa powder"}

CUP_G = {"flour": 120, "sugar": 200, "fat": 227, "liquid": 240, "cocoa": 85}  # grams per cup
TSP_G = {"leavener": 4.5, "salt": 6.0}                                          # grams per tsp
EGG_G = 50

# product -> ingredient -> (min %, target %, max %, required?)   (% of flour weight)
TARGETS = {
    "Cake": {
        "sugar": (60, 85, 110, True), "fat": (35, 55, 100, True), "egg": (40, 60, 100, True),
        "liquid": (30, 60, 100, True), "leavener": (1.5, 3, 4.5, True), "salt": (0.5, 1, 2.2, True)},
    "Brownie": {
        "sugar": (100, 180, 300, True), "fat": (60, 100, 150, True), "egg": (50, 90, 130, True),
        "cocoa": (15, 35, 70, False), "leavener": (0, 0.5, 2.5, False), "salt": (0.5, 1, 2.2, True)},
    "Cupcake / Muffin": {
        "sugar": (30, 65, 90, True), "fat": (20, 35, 50, True), "egg": (20, 35, 50, True),
        "liquid": (60, 85, 110, True), "leavener": (2.5, 4, 5.5, True), "salt": (0.5, 1, 2.2, True)},
    "Cookies": {
        "sugar": (55, 85, 115, True), "fat": (45, 62, 85, True), "egg": (15, 30, 45, True),
        "leavener": (0.7, 1.3, 2.2, True), "salt": (0.5, 1.2, 2.2, True)},
    "Bread": {
        "liquid": (58, 65, 72, True), "leavener": (0.8, 1.2, 2, True), "salt": (1.5, 2, 2.5, True),
        "sugar": (0, 3, 10, False), "fat": (0, 4, 10, False)},
}

WHY = {
    ("sugar", "high"): "Too much sugar burns easily, weakens the structure and can make the bake collapse or spread.",
    ("sugar", "low"): "Too little sugar gives a pale, dry, tough bake because sugar holds moisture and helps browning.",
    ("fat", "high"): "Too much fat/oil makes the crumb heavy and greasy and makes cookies spread.",
    ("fat", "low"): "Too little fat makes the bake dry, crumbly and tough.",
    ("egg", "high"): "Too many eggs make the bake rubbery or eggy and can make it dense.",
    ("egg", "low"): "Eggs give structure and moisture; too few makes it crumbly and weak.",
    ("liquid", "high"): "Too much liquid makes a wet batter that sinks in the middle and bakes gummy.",
    ("liquid", "low"): "Too little liquid gives a stiff, dry, cracked bake.",
    ("leavener", "high"): "Too much baking powder/soda makes it rise fast and then collapse, with a bitter taste.",
    ("leavener", "low"): "Too little (or no) leavening means the bake will not rise and turns dense.",
    ("salt", "high"): "Too much salt tastes harsh and slows yeast.",
    ("salt", "low"): "Salt balances flavour and strengthens the structure.",
    ("cocoa", "high"): "Too much cocoa makes it dry and bitter because cocoa absorbs liquid.",
    ("cocoa", "low"): "Too little cocoa gives a weak chocolate flavour.",
}

LINE = re.compile(
    r"^\s*(?P<qty>\d+\s+\d+/\d+|\d+/\d+|\d+(?:\.\d+)?)\s*"
    r"(?P<unit>kg|grams?|gm|g|ml|litres?|liters?|l|cups?|tbsp|tablespoons?|tsp|teaspoons?)?\b\s*"
    r"(?:of\s+)?(?P<name>.+?)\s*$", re.I)


def _to_number(text):
    total = 0.0
    for part in text.split():
        if "/" in part:
            a, b = part.split("/")
            total += float(a) / float(b)
        else:
            total += float(part)
    return total


def _category(name):
    if ("chocolate" in name or "chips" in name) and "cocoa" not in name:
        return None
    for cat, words in CATEGORY_WORDS.items():
        for w in words:
            if re.search(rf"\b{w}s?\b", name):
                return cat
    return None


def _per_tsp(cat, name):
    if cat == "leavener":
        return 3.0 if "yeast" in name else TSP_G["leavener"]
    if cat == "salt":
        return TSP_G["salt"]
    return CUP_G[cat] / 48 if cat in CUP_G else None


def _grams(qty, unit, cat, name):
    unit = (unit or "").lower()
    if unit in ("g", "gm", "gram", "grams", "ml"):
        return qty
    if unit in ("kg", "l", "litre", "litres", "liter", "liters"):
        return qty * 1000
    if unit in ("cup", "cups"):
        cup = 120 if (cat == "sugar" and ("powder" in name or "icing" in name)) else CUP_G.get(cat)
        return qty * cup if cup else None
    if unit in ("tsp", "teaspoon", "teaspoons", "tbsp", "tablespoon", "tablespoons"):
        tsp = _per_tsp(cat, name)
        if tsp is None:
            return None
        return qty * tsp * (3 if unit.startswith("tb") else 1)
    if not unit and cat == "egg":
        return qty * EGG_G
    return None


def parse_recipe(text):
    """Returns (items, others, unparsed)."""
    for k, v in FRACTIONS.items():
        text = text.replace(k, v)
    items, others, unparsed = [], [], []
    for raw in text.splitlines():
        line = re.sub(r"^[\s\-\u2022*]+", "", raw).strip()
        if not line:
            continue
        m = LINE.match(line)
        if not m:
            unparsed.append(line)
            continue
        name = m.group("name").lower()
        cat = _category(name)
        if cat is None:
            others.append(line)  # vanilla, chocolate chips, etc. kept as they are
            continue
        grams = _grams(_to_number(m.group("qty")), m.group("unit"), cat, name)
        if grams is None:
            unparsed.append(line)
        else:
            items.append({"cat": cat, "grams": grams, "line": line})
    return items, others, unparsed


def _num(cat, g):
    if cat == "egg":
        return f"{g / EGG_G:g} egg(s)"
    if cat in TSP_G:
        return f"{g:.1f} g (~{g / TSP_G[cat]:.1f} tsp)"
    return f"{g:.0f} g"


def _suggest(cat, flour, target):
    g = target * flour / 100
    if cat == "egg":
        return EGG_G * max(1, round(g / EGG_G))
    if cat in TSP_G:
        return max(0.5, round(g * 2) / 2)
    return max(5, 5 * round(g / 5))


def _range_text(cat, lo, hi, flour):
    a, b = lo * flour / 100, hi * flour / 100
    if cat == "egg":
        return f"{a / EGG_G:.1f}-{b / EGG_G:.1f} eggs"
    if cat in TSP_G:
        return f"{a:.1f}-{b:.1f} g"
    return f"{a:.0f}-{b:.0f} g"


def analyze(text, product):
    """Returns a JSON-friendly dict, or None when there is no recipe text."""
    spec = TARGETS.get(product)
    if not text or not text.strip() or spec is None:
        return None
    items, others, unparsed = parse_recipe(text)
    totals = {}
    for it in items:
        totals[it["cat"]] = totals.get(it["cat"], 0) + it["grams"]
    flour = totals.get("flour")
    if not flour:
        return {"flour_g": None, "rows": [], "flags": [], "corrected": [], "unparsed": unparsed,
                "message": "I could not find the flour amount. Write it like '200 g flour' (one ingredient per line) so I can check the ratios."}

    rows, flags, corrected = [], set(), [f"{flour:.0f} g flour"]
    for cat, (lo, target, hi, required) in spec.items():
        g = totals.get(cat)
        if g is None and not required:
            continue
        ideal = _range_text(cat, lo, hi, flour)
        if g is None:
            status, why = "missing", "Not found in your recipe. " + WHY[(cat, "low")]
            flags.update({f"{cat}_low", f"{cat}_missing"})
        else:
            pct = g / flour * 100
            if pct > hi:
                status, why = "high", WHY[(cat, "high")]
                flags.add(f"{cat}_high")
            elif pct < lo:
                status, why = "low", WHY[(cat, "low")]
                flags.add(f"{cat}_low")
            else:
                status, why = "ok", ""
        fixed = _suggest(cat, flour, target) if status != "ok" else g
        tag = {"high": "  <- reduced", "low": "  <- increased", "missing": "  <- added"}.get(status, "")
        corrected.append(f"{_num(cat, fixed)} {LABEL[cat]}".replace(") ", ")", 1) + tag if cat == "egg" else f"{_num(cat, fixed)} {LABEL[cat]}{tag}")
        rows.append({"ingredient": NICE[cat], "used": _num(cat, g) if g is not None else "none",
                     "ideal": ideal, "suggested": _num(cat, fixed) if status != "ok" else "keep as it is",
                     "status": status, "why": why})
    corrected.extend(others)

    if sum(f"{c}_low" in flags for c in ("sugar", "fat", "liquid", "egg")) >= 2:
        flags.add("flour_heavy")
    if flags & {"liquid_high", "fat_high", "sugar_high"}:
        flags.add("weak_structure")
    if flags & {"liquid_high", "fat_high"}:
        flags.add("liquid_or_fat_high")
    if flags & {"sugar_high", "fat_high"}:
        flags.add("sugar_fat_high")

    return {"flour_g": flour, "rows": rows, "flags": sorted(flags), "corrected": corrected,
            "unparsed": unparsed, "message": ""}
