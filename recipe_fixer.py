"""
Recipe checker driven by a DATASET of correct reference recipes (recipes_dataset.csv).

How it works (easy to explain):
 1. Read the user's typed ingredient lines and convert every amount to grams.
 2. Express each ingredient as a % of the flour weight (baker's percentage).
 3. From the dataset, learn the normal range for this product (min / median / max of its reference recipes).
 4. Find the closest reference recipe (nearest neighbour on the ratios).
 5. Flag ingredients that are too high, too low or missing, and suggest corrected grams
    based on the closest reference recipe.
"""
import csv
import os
import re
import statistics

from knowledge_base import PANS

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "recipes_dataset.csv")
CATS = ["sugar", "fat", "egg", "liquid", "leavener", "salt", "cocoa"]
TOLERANCE = 0.2          # accept 20% beyond the dataset's min / max
REQUIRED_SHARE = 0.75    # an ingredient is "required" if 75%+ of reference recipes use it

FRACTIONS = {"½": " 1/2", "¼": " 1/4", "¾": " 3/4", "⅓": " 1/3", "⅔": " 2/3"}
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
CUP_G = {"flour": 120, "sugar": 200, "fat": 227, "liquid": 240, "cocoa": 85}   # grams per cup
TSP_G = {"leavener": 4.5, "salt": 6.0}                                          # grams per tsp
EGG_G = 50
STICK_G = 113

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


# ---------------- the dataset ----------------
def load_dataset():
    recipes = []
    with open(DATA_FILE, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            extras = []
            for part in (row.get("extras") or "").split(";"):
                if ":" in part:
                    name, grams = part.split(":")
                    extras.append((name.strip(), float(grams)))
            r = {"product": row["product"].strip(), "name": row["recipe"].strip(),
                 "flour": float(row["flour"]), "method": row.get("method", "").strip(),
                 "temp_c": float(row["temp_c"]), "minutes": float(row["minutes"]),
                 "pan": row["pan"].strip(), "extras": extras, "source": row.get("source", "").strip()}
            for c in CATS:
                r[c] = float(row[c] or 0)
            recipes.append(r)
    return recipes


def ref_weight(r):
    """Total batter / dough weight of a reference recipe in grams."""
    return r["flour"] + sum(r[c] for c in CATS) + sum(g for _, g in r["extras"])


def build_targets(recipes):
    """For each product and ingredient: (low %, median %, high %, required?) of flour weight."""
    targets = {}
    for product in {r["product"] for r in recipes}:
        rs = [r for r in recipes if r["product"] == product]
        spec = {}
        for c in CATS:
            pcts = [r[c] / r["flour"] * 100 for r in rs if r[c] > 0]
            if not pcts:
                continue
            required = c != "cocoa" and len(pcts) / len(rs) >= REQUIRED_SHARE
            spec[c] = (min(pcts) * (1 - TOLERANCE), statistics.median(pcts),
                       max(pcts) * (1 + TOLERANCE), required)
        targets[product] = spec
    return targets


RECIPES = load_dataset()
TARGETS = build_targets(RECIPES)


def products():
    return sorted(TARGETS)


def reference_table(product):
    rows = []
    for r in RECIPES:
        if r["product"] == product:
            rows.append({"Recipe": r["name"], "Flour (g)": f"{r['flour']:g}", "Sugar (g)": f"{r['sugar']:g}",
                         "Butter/oil (g)": f"{r['fat']:g}", "Eggs (g)": f"{r['egg']:g}",
                         "Milk/water (g)": f"{r['liquid']:g}", "Leavener (g)": f"{r['leavener']:g}",
                         "Salt (g)": f"{r['salt']:g}", "Cocoa (g)": f"{r['cocoa']:g}",
                         "Other (g)": ", ".join(f"{n} {g:g}" for n, g in r["extras"]) or "-",
                         "Oven": f"{r['temp_c']:.0f} C, {r['minutes']:.0f} min", "Pan": r["pan"]})
    return rows


def reference_methods(product):
    return [(r["name"], r["method"]) for r in RECIPES if r["product"] == product]


def range_table(product):
    rows = []
    for c, (lo, med, hi, req) in TARGETS.get(product, {}).items():
        rows.append({"Ingredient": NICE[c], "Normal range (% of flour weight)": f"{lo:.1f} - {hi:.1f} %",
                     "Usually included": "Yes" if req else "Optional"})
    return rows


# ---------------- reading the user's recipe ----------------
UNIT = r"kg|grams?|gms?|g|ml|litres?|liters?|l|cups?|tbsp|tablespoons?|tsp|teaspoons?|sticks?"
NUM = r"\d+\s+\d+/\d+|\d+/\d+|\d+(?:\.\d+)?"
LINE_A = re.compile(rf"^\s*(?P<qty>{NUM})\s*(?P<unit>{UNIT})?\b\s*(?:of\s+)?(?P<name>.+?)\s*$", re.I)
LINE_B = re.compile(rf"^\s*(?P<name>[A-Za-z][A-Za-z\s\-/'()]*?)\s*[:\-,]?\s*(?P<qty>{NUM})\s*(?P<unit>{UNIT})?\s*$", re.I)
PAREN_G = re.compile(r"\(\s*(\d+(?:\.\d+)?)\s*(?:g|gm|gms|grams?)\s*\)", re.I)


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
    if re.search(r"\bcorn", name):
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
    if unit in ("g", "gm", "gms", "gram", "grams", "ml"):
        return qty
    if unit in ("kg", "l", "litre", "litres", "liter", "liters"):
        return qty * 1000
    if unit in ("stick", "sticks"):
        return qty * STICK_G if cat == "fat" else None
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
    """Returns (items, others, unparsed, other_g). Understands '200 g flour', '2 cups (250g) flour', 'flour 200g'."""
    for k, v in FRACTIONS.items():
        text = text.replace(k, v)
    items, others, unparsed, other_g = [], [], [], 0.0
    for raw in text.splitlines():
        line = re.sub(r"^[\s\-\u2022*]+", "", raw).strip()
        if not line:
            continue
        if not re.search(r"\d", line):
            others.append(line)          # e.g. "a pinch of salt", "vanilla"
            continue
        paren = PAREN_G.search(line)
        clean = PAREN_G.sub("", line).strip() if paren else line
        m = LINE_A.match(clean) or LINE_B.match(clean)
        if not m:
            unparsed.append(line)
            continue
        name = m.group("name").lower().strip(" ,:-")
        cat = _category(name)
        if cat is None:
            others.append(line)          # vanilla, chocolate chips, bananas ... kept as they are
            g = float(paren.group(1)) if paren else _grams(_to_number(m.group("qty")), m.group("unit"), None, name)
            other_g += g or 0
            continue
        grams = float(paren.group(1)) if paren else _grams(_to_number(m.group("qty")), m.group("unit"), cat, name)
        if grams is None:
            unparsed.append(line)
        else:
            items.append({"cat": cat, "grams": grams, "line": line})
    return items, others, unparsed, other_g


# ---------------- formatting helpers ----------------
def _num(cat, g):
    if cat == "egg":
        return f"{g / EGG_G:g} egg(s)"
    if cat in TSP_G:
        return f"{g:.1f} g (~{g / TSP_G[cat]:.1f} tsp)"
    return f"{g:.0f} g"


def _suggest(cat, flour, pct):
    g = pct * flour / 100
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


def _closest(product, pcts):
    """Nearest reference recipe: smallest total difference in ingredient ratios."""
    best, best_d = None, 1e9
    for r in RECIPES:
        if r["product"] != product:
            continue
        d = 0
        for c in CATS:
            rp = r[c] / r["flour"] * 100
            d += abs(pcts[c] - rp) / (max(pcts[c], rp) + 5)
        if d < best_d:
            best, best_d = r, d
    return best


def _bake_plan(ref, total_g, setup):
    """Suggested oven temperature and time for THIS pan, tin and oven, starting from the reference recipe."""
    setup = setup or {}
    temp, minutes, science = ref["temp_c"], ref["minutes"], []
    area_user, area_ref = PANS.get(setup.get("pan")), PANS.get(ref["pan"])
    ratio = None
    if area_user and area_ref and total_g:
        ratio = (total_g / area_user) / (ref_weight(ref) / area_ref)   # batter depth vs reference pan
        if ratio > 1.3:
            drop = 15 if ratio > 1.6 else 10
            temp -= drop
            minutes *= min(ratio, 1.8)
            science.append(f"Your batter is about {(ratio - 1) * 100:.0f}% deeper than in the reference pan. Heat needs longer to reach "
                           f"the centre, so the outside browns and sets before the middle cooks. Lower the temperature by {drop} C and bake longer.")
        elif ratio < 0.75:
            minutes *= max(ratio, 0.6)
            science.append(f"Your batter is a thinner layer (about {(1 - ratio) * 100:.0f}% shallower than the reference), so it cooks "
                           "and dries out faster. Shorten the bake and start checking early.")
    tin, rod = setup.get("tin", ""), setup.get("rod", "")
    if "Dark" in tin or "Glass" in tin:
        temp -= 10
        science.append("Dark metal absorbs more heat and glass/ceramic holds heat longer, so the edges and base overbake. Lower the temperature by 10 C.")
    if "Silicone" in tin:
        minutes += 3
        science.append("Silicone insulates, so the batter heats slowly. Add a few minutes and stand the mould on a metal tray.")
    if rod == "Fan / convection":
        temp -= 15
        science.append("A fan circulates hot air and transfers heat faster, so reduce the recipe temperature by about 15 C.")
    if rod == "Top rod only":
        science.append("Top-rod-only heat browns the surface first. Use a lower rack or switch on the bottom rod as well.")
    temp = 5 * round(temp / 5)
    return {"temp_c": temp, "min_lo": round(minutes * 0.85), "min_hi": round(minutes * 1.15),
            "ref_name": ref["name"], "ref_temp": ref["temp_c"], "ref_minutes": ref["minutes"],
            "ref_pan": ref["pan"], "depth_ratio": ratio, "science": science}


# ---------------- main function ----------------
def analyze(text, product, setup=None):
    """Returns a JSON-friendly dict, or None when there is no recipe text."""
    spec = TARGETS.get(product)
    if not text or not text.strip() or spec is None:
        return None
    items, others, unparsed, other_g = parse_recipe(text)
    understood = [{"line": it["line"], "ingredient": NICE[it["cat"]],
                   "grams": f"{it['grams']:.1f}" if it["grams"] < 20 else f"{it['grams']:.0f}"} for it in items]
    totals = {}
    for it in items:
        totals[it["cat"]] = totals.get(it["cat"], 0) + it["grams"]
    flour = totals.get("flour")
    if not flour:
        return {"flour_g": None, "rows": [], "flags": [], "corrected": [], "unparsed": unparsed,
                "understood": understood, "reference": None, "bake_plan": None,
                "message": "I could not find the flour amount. Write it like '200 g flour' (one ingredient per line) so I can check the ratios."}

    pcts = {c: totals.get(c, 0) / flour * 100 for c in CATS}
    ref = _closest(product, pcts)
    ref_pcts = {c: ref[c] / ref["flour"] * 100 for c in CATS}

    rows, flags, corrected = [], set(), [f"{flour:.0f} g flour"]
    for cat, (lo, median, hi, required) in spec.items():
        g = totals.get(cat)
        if g is None and (not required or ref_pcts[cat] == 0):
            continue
        target = ref_pcts[cat] if ref_pcts[cat] > 0 else median
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
        corrected.append(f"{_num(cat, fixed)} {LABEL[cat]}".strip() + tag)
        rows.append({"ingredient": NICE[cat], "used": _num(cat, g) if g is not None else "none",
                     "ideal": _range_text(cat, lo, hi, flour),
                     "suggested": _num(cat, fixed) if status != "ok" else "keep as it is",
                     "status": status, "why": why})
    corrected.extend(others)

    if sum(f"{c}_low" in flags for c in ("sugar", "fat", "liquid", "egg")) >= 2:
        flags.add("flour_heavy")
    plan = _bake_plan(ref, sum(totals.values()) + other_g, setup)
    if plan["depth_ratio"] is not None:
        if plan["depth_ratio"] > 1.3:
            flags.add("deep_batter")
        elif plan["depth_ratio"] < 0.75:
            flags.add("shallow_batter")
    if flags & {"liquid_high", "fat_high", "sugar_high"}:
        flags.add("weak_structure")
    if flags & {"liquid_high", "fat_high"}:
        flags.add("liquid_or_fat_high")
    if flags & {"sugar_high", "fat_high"}:
        flags.add("sugar_fat_high")

    scaled = [f"{flour:.0f} g flour"]
    for c in CATS:
        if ref_pcts[c] > 0:
            scaled.append(f"{_num(c, _suggest(c, flour, ref_pcts[c]))} {LABEL[c]}".strip())
    for name, g in ref["extras"]:
        scaled.append(f"{5 * round(g * flour / ref['flour'] / 5):.0f} g {name}")

    return {"flour_g": flour, "rows": rows, "flags": sorted(flags), "corrected": corrected,
            "unparsed": unparsed, "understood": understood, "message": "",
            "reference": {"name": ref["name"], "scaled": scaled, "method": ref["method"]},
            "bake_plan": plan}
