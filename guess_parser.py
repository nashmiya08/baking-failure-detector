"""
Reads the user's typed guess (free text) and finds
 - which failure symptom they describe  (e.g. "top is burnt" -> burnt_surface)
 - which cause they suspect             (e.g. "oven too hot" -> temp_high)
Simple keyword matching, so it is easy to explain and extend.
"""
import re

SYMPTOM_WORDS = {
    "burnt_surface": ["burn", "charred", "too dark", "dark top", "blackened", "too brown", "over brown"],
    "pale_underbaked": ["pale", "raw", "underbak", "under bak", "undercook", "under cook", "not cooked",
                        "doughy", "gooey", "wet inside", "sticky inside", "not baked", "uncooked"],
    "collapsed_centre": ["collaps", "sunk", "sink", "sank", "dipped", "fell", "deflat", "caved",
                         "middle went down", "centre went down", "center went down"],
    "dense_crumb": ["dense", "heavy", "rubbery", "gummy", "tough", "did not rise", "didnt rise",
                    "not rise", "not fluffy", "brick", "compact"],
    "cracked_top": ["crack", "split"],
    "cookies_spread": ["spread", "flattened", "too flat", "flat cookie", "melted into"],
    "dry_crumbly": ["dry", "crumbly", "crumbles", "falls apart", "stale", "powdery"],
}

# rule name -> (sentence shown to the user, phrases that trigger it)
CAUSE_WORDS = {
    "temp_high": ("the oven was too hot", ["oven too hot", "too hot", "high temperature", "high temp", "temperature too high"]),
    "temp_low": ("the oven was too cold", ["oven too cold", "low temperature", "low temp", "temperature too low"]),
    "time_long": ("it was baked too long", ["baked too long", "bake too long", "baking too long", "overbak", "over bak", "left it too long"]),
    "time_short": ("it was baked too briefly", ["baked too short", "not baked long", "took it out early", "removed early"]),
    "no_preheat": ("the oven was not preheated", ["didnt preheat", "did not preheat", "not preheated", "no preheat", "forgot to preheat", "without preheating"]),
    "opened_door": ("the oven door was opened", ["opened the oven", "opened oven", "opened the door", "oven door", "door open"]),
    "overmix_hint": ("the batter was over-mixed", ["overmix", "over mix", "mixed too much", "mixed too long", "mixed too hard", "overbeat", "over beat", "overwhisk", "over whisk"]),
    "leavener_high": ("too much baking powder/soda", ["too much baking powder", "too much baking soda", "too much soda", "too much leaven", "too much yeast"]),
    "leavener_low": ("weak or missing baking powder/soda", ["old baking powder", "expired baking", "not enough baking powder", "forgot baking powder", "no baking powder", "old yeast", "dead yeast"]),
    "no_chill": ("the dough was not chilled", ["didnt chill", "did not chill", "not chilled", "no chill", "without chilling"]),
    "melted_fat": ("the butter was melted or too soft", ["melted butter", "butter was melted", "soft butter"]),
    "top_rod": ("the top rod was too strong", ["top rod", "top heat", "top coil"]),
    "dark_tin": ("a dark tin was used", ["dark tin", "non stick tin", "nonstick tin", "black tin"]),
}


def parse_guess(text):
    """Returns (list of symptom keys, dict of {rule_name: sentence})."""
    t = " " + re.sub(r"[^a-z0-9 ]+", " ", (text or "").lower().replace("'", "")) + " "
    symptoms = [k for k, words in SYMPTOM_WORDS.items() if any(w in t for w in words)]
    causes = {rule: label for rule, (label, phrases) in CAUSE_WORDS.items() if any(p in t for p in phrases)}
    return symptoms, causes
