"""
Baking-science knowledge base (the 'dataset' for the diagnosis engine).
Each symptom has a list of possible causes. A cause can have a 'rule' name:
if that rule is true for the user's inputs, the cause scores higher.
Edit / extend this file to teach the system more baking science.
"""

# Typical home-baking ranges (general guidance, not exact for every recipe)
PRODUCT_RANGES = {
    "Brownie":          {"temp": (160, 180), "time": (22, 35)},
    "Cake":             {"temp": (160, 180), "time": (25, 45)},
    "Cupcake / Muffin": {"temp": (170, 190), "time": (18, 26)},
    "Cookies":          {"temp": (170, 190), "time": (8, 15)},
    "Bread":            {"temp": (190, 230), "time": (25, 45)},
    "Banana bread":     {"temp": (165, 180), "time": (50, 65)},
    "Scones":           {"temp": (200, 220), "time": (12, 18)},
    "Shortbread":       {"temp": (150, 170), "time": (20, 35)},
}

SYMPTOMS = {
    "burnt_surface": {
        "label": "Too dark / burnt surface",
        "causes": [
            {"name": "Oven temperature too high", "rule": "temp_high",
             "science": "Sugars and proteins brown quickly (caramelisation + Maillard reaction) at high heat, so the surface darkens before the centre sets.",
             "recipe_fix": "Lower the oven temperature by 10-15 C.",
             "process_fix": "Check the real oven temperature with an oven thermometer; many ovens run hotter than the dial."},
            {"name": "Baked for too long", "rule": "time_long",
             "science": "Extra time keeps drying and browning the crust after the inside is already cooked.",
             "recipe_fix": "Shorten the bake by 3-5 minutes.",
             "process_fix": "Start checking early with a toothpick; remove when it comes out with a few moist crumbs."},
            {"name": "Top rod / direct radiant heat too strong", "rule": "top_rod",
             "science": "Top-rod-only heating blasts the surface with radiant heat, browning it faster than heat can reach the centre.",
             "recipe_fix": "No ingredient change needed.",
             "process_fix": "Use top + bottom rods, move the tin to a lower rack, or cover loosely with foil halfway."},
            {"name": "Dark, glass or ceramic tin holds more heat", "rule": "dark_tin",
             "science": "Dark metal absorbs more radiant heat and glass/ceramic keeps its heat longer, so the edges and base overbake.",
             "recipe_fix": "Reduce temperature by about 10 C when using a dark tin.",
             "process_fix": "Use a light-coloured, thicker tin or line the tin with parchment."},
            {"name": "High sugar content on the surface", "rule": "sugar_high",
             "science": "Sugar caramelises and burns at a lower temperature than flour or fat.",
             "recipe_fix": "Reduce sugar by 10-15 percent or switch part of it to a less browning sweetener.",
             "process_fix": "Tent the top with foil once it reaches the colour you want."},
        ],
    },
    "pale_underbaked": {
        "label": "Pale / underbaked",
        "causes": [
            {"name": "Oven temperature too low", "rule": "temp_low",
             "science": "Below the browning range the structure sets slowly and the Maillard reaction barely starts.",
             "recipe_fix": "Raise the temperature by 10-15 C.",
             "process_fix": "Verify with an oven thermometer."},
            {"name": "Baking time too short", "rule": "time_short",
             "science": "Starch has not fully gelatinised and egg proteins have not set, so the centre stays wet.",
             "recipe_fix": "Add 5 minutes and re-test.",
             "process_fix": "Use the toothpick test instead of only the timer."},
            {"name": "Oven was not preheated", "rule": "no_preheat",
             "science": "Batter sits in a cold oven, so leavening and setting happen at the wrong speed.",
             "recipe_fix": "No ingredient change needed.",
             "process_fix": "Preheat for 15-20 minutes before baking."},
            {"name": "Oven door opened too often", "rule": "opened_door",
             "science": "Each opening drops the oven temperature by 20-30 C or more.",
             "recipe_fix": "No ingredient change needed.",
             "process_fix": "Keep the door shut for the first two thirds of baking; use the oven light."},
            {"name": "Silicone mould insulates", "rule": "insulating_tin",
             "science": "Silicone conducts heat poorly, so the batter heats slowly and browns less.",
             "recipe_fix": "Increase bake time by about 3-5 minutes.",
             "process_fix": "Place the silicone mould on a metal tray so it heats evenly."},
        ],
    },
    "collapsed_centre": {
        "label": "Collapsed / sunken centre",
        "causes": [
            {"name": "Opened the oven too early", "rule": "opened_door",
             "science": "Gas bubbles are still expanding and the structure has not set; cold air makes them shrink and the centre falls.",
             "recipe_fix": "No ingredient change needed.",
             "process_fix": "Do not open the door until at least 75 percent of the baking time has passed."},
            {"name": "Underbaked centre", "rule": "time_short",
             "science": "The crumb structure (set starch and egg protein) is too weak to hold up its own weight.",
             "recipe_fix": "Bake 5-8 minutes longer.",
             "process_fix": "Check with a toothpick in the centre, not the edge."},
            {"name": "Too much leavening (baking powder / soda)", "rule": "leavener_high",
             "science": "Gas forms faster than the batter can set, so bubbles grow too big, burst and the cake collapses.",
             "recipe_fix": "Reduce baking powder by 1/4 tsp per 1 cup (about 125 g) flour, or measure with level spoons.",
             "process_fix": "Level the spoon with a knife; do not use heaped spoons."},
            {"name": "Too much liquid, sugar or fat for the flour", "rule": "weak_structure",
             "science": "Flour and eggs build the structure; too much of the tenderising ingredients weakens it.",
             "recipe_fix": "Add 2-3 tbsp more flour or cut the liquid by about 10 percent.",
             "process_fix": "Weigh ingredients with a kitchen scale."},
        ],
    },
    "dense_crumb": {
        "label": "Dense / heavy crumb",
        "causes": [
            {"name": "Over-mixing after adding flour", "rule": "overmix_hint",
             "science": "Mixing develops gluten; too much gluten makes a tight, tough, rubbery crumb.",
             "recipe_fix": "No ingredient change needed.",
             "process_fix": "Fold the dry ingredients in gently with a spatula until just combined instead of mixing vigorously."},
            {"name": "Weak or expired leavening", "rule": "leavener_low",
             "science": "Old baking powder / soda produces less gas, so the batter does not rise.",
             "recipe_fix": "Use fresh baking powder (test: it should fizz in hot water).",
             "process_fix": "Sift the leavener with the flour so it spreads evenly."},
            {"name": "Not enough aeration (creaming / whipping)", "rule": None,
             "science": "Beating butter and sugar traps tiny air bubbles that expand in the oven.",
             "recipe_fix": "No ingredient change needed.",
             "process_fix": "Cream butter + sugar for 3-5 minutes until pale and fluffy; use room-temperature eggs."},
            {"name": "Too much flour (scooped / packed)", "rule": "flour_heavy",
             "science": "Extra flour absorbs liquid and builds more structure than the leavener can lift.",
             "recipe_fix": "Reduce flour by 2-3 tbsp per cup.",
             "process_fix": "Spoon flour into the cup and level it, or weigh it."},
            {"name": "Too much liquid or fat compared with structure", "rule": "liquid_or_fat_high",
             "science": "Excess liquid/fat weighs down the crumb and makes it gummy.",
             "recipe_fix": "Reduce liquid or fat by 10 percent.",
             "process_fix": "Measure liquids at eye level in a measuring jug."},
        ],
    },
    "cracked_top": {
        "label": "Cracked top",
        "causes": [
            {"name": "Oven too hot", "rule": "temp_high",
             "science": "The crust sets before the inside has finished rising, so the rising batter splits the crust.",
             "recipe_fix": "Lower the temperature by 10-15 C.",
             "process_fix": "Preheat properly and use an oven thermometer."},
            {"name": "Top rod too strong", "rule": "top_rod",
             "science": "Strong top heat forms a hard crust early.",
             "recipe_fix": "No ingredient change needed.",
             "process_fix": "Use top + bottom heat or a lower rack."},
            {"name": "Too much flour or too little liquid", "rule": "flour_heavy",
             "science": "A stiff batter cannot stretch as it rises, so it cracks.",
             "recipe_fix": "Add 1-2 tbsp milk or reduce flour slightly.",
             "process_fix": "Weigh the flour."},
        ],
    },
    "cookies_spread": {
        "label": "Cookies spread too much",
        "causes": [
            {"name": "Melted or very soft fat", "rule": "melted_fat",
             "science": "Warm fat melts before the dough sets, so the cookie flows outward.",
             "recipe_fix": "Use cold or room-temperature (not melted) butter.",
             "process_fix": "Cream butter only until combined."},
            {"name": "Dough not chilled", "rule": "no_chill",
             "science": "Cold dough keeps fat solid longer so the edges set before spreading.",
             "recipe_fix": "No ingredient change needed.",
             "process_fix": "Chill the dough 30-60 minutes before baking."},
            {"name": "Oven temperature too low", "rule": "temp_low",
             "science": "A cool oven melts the fat before the structure sets.",
             "recipe_fix": "Increase temperature by 10-15 C.",
             "process_fix": "Preheat fully."},
            {"name": "Too much sugar/fat or too little flour", "rule": "sugar_fat_high",
             "science": "Sugar liquefies as it heats; low flour means weak structure.",
             "recipe_fix": "Add 2-4 tbsp flour per batch or reduce sugar slightly.",
             "process_fix": "Use cool baking trays and parchment, not greased warm trays."},
        ],
    },
    "dry_crumbly": {
        "label": "Dry / crumbly texture",
        "causes": [
            {"name": "Baked too long", "rule": "time_long",
             "science": "Moisture keeps evaporating once the structure is set.",
             "recipe_fix": "Shorten bake by 3-5 minutes.",
             "process_fix": "Remove when a toothpick has a few moist crumbs."},
            {"name": "Oven too hot", "rule": "temp_high",
             "science": "High heat dries the outside before the inside finishes.",
             "recipe_fix": "Lower temperature by 10-15 C.",
             "process_fix": "Use an oven thermometer."},
            {"name": "Too much flour or not enough fat / egg", "rule": "flour_heavy",
             "science": "Flour absorbs moisture; fat and eggs keep the crumb soft.",
             "recipe_fix": "Reduce flour by 2-3 tbsp or add 1 egg yolk / 1-2 tbsp oil or butter.",
             "process_fix": "Spoon and level flour or weigh it."},
        ],
    },
}


# Pan sizes (top area in cm2). None = batter depth is not calculated for this pan.
PANS = {
    "20 cm / 8 inch round": 314,
    "23 cm / 9 inch round": 415,
    "20 cm / 8 inch square": 400,
    "23 cm / 9 inch square": 529,
    "23 x 33 cm / 9x13 inch rectangle": 759,
    "23 x 13 cm / 9x5 inch loaf tin": 299,
    "Muffin / cupcake tray": None,
    "Flat baking tray / sheet": None,
    "Other / not sure": None,
}

# Extra causes linked to the pan-size check in recipe_fixer.py
SYMPTOMS["burnt_surface"]["causes"].append({
    "name": "Batter too deep for the pan (small pan)", "rule": "deep_batter",
    "science": "In a deep batter the heat needs much longer to reach the centre, so the top and edges brown and burn first.",
    "recipe_fix": "Split the batter between two pans or use a bigger pan.",
    "process_fix": "Lower the temperature by 10-15 C, bake longer and cover the top with foil once it is golden."})
SYMPTOMS["burnt_surface"]["causes"].append({
    "name": "Thin layer in a very large pan", "rule": "shallow_batter",
    "science": "A thin layer cooks and dries out quickly, so it over-browns before you expect it to.",
    "recipe_fix": "Use a smaller pan so the batter is deeper.",
    "process_fix": "Shorten the bake time and start checking early."})
SYMPTOMS["pale_underbaked"]["causes"].append({
    "name": "Batter too deep for the pan (small pan)", "rule": "deep_batter",
    "science": "Heat moves slowly through thick batter, so the centre stays raw while the outside is done.",
    "recipe_fix": "Use a bigger pan or divide the batter into two pans.",
    "process_fix": "Lower the temperature by 10-15 C and bake longer so the centre can catch up."})
SYMPTOMS["collapsed_centre"]["causes"].append({
    "name": "Batter too deep for the pan (small pan)", "rule": "deep_batter",
    "science": "The centre of a deep batter sets last; if it is still liquid when the bake cools, it sinks.",
    "recipe_fix": "Use a bigger pan or divide the batter into two pans.",
    "process_fix": "Lower the temperature, bake longer and test the centre with a toothpick."})
SYMPTOMS["dry_crumbly"]["causes"].append({
    "name": "Thin layer in a very large pan", "rule": "shallow_batter",
    "science": "Thin batter loses moisture quickly and is overbaked by the time the timer ends.",
    "recipe_fix": "Use a smaller pan so the batter is deeper.",
    "process_fix": "Shorten the bake time and check early."})
