"""
Reads measurable visual evidence from the photo (colour and browning pattern) and links each
measurement to a baking-science meaning. No training data needed, so the app can explain WHAT it saw.
Uses only numpy + PIL. The thresholds are starting values: calibrate them with your own bake photos.
"""
import numpy as np


def _box_blur(a, k=9):
    """Average over a k x k window (k odd) using cumulative sums."""
    pad = k // 2
    p = np.pad(a, pad, mode="edge")
    c = np.pad(p.cumsum(0).cumsum(1), ((1, 0), (1, 0)))
    h, w = a.shape
    s = c[k:k + h, k:k + w] - c[0:h, k:k + w] - c[k:k + h, 0:w] + c[0:h, 0:w]
    return s / (k * k)


def measure(img):
    """Returns {'rows': table for the user, 'symptoms': [(key, confidence, source)], 'support': [rule names]}."""
    im = img.convert("RGB")
    im.thumbnail((256, 256))
    a = np.asarray(im, dtype=float)
    h, w, _ = a.shape
    a = a[int(h * .1):int(h * .9), int(w * .1):int(w * .9)]          # drop the border (plate / counter)
    gray = a @ np.array([0.299, 0.587, 0.114])
    sat = (a.max(2) - a.min(2)) / np.maximum(a.max(2), 1)
    h, w = gray.shape
    centre = gray[h // 4:3 * h // 4, w // 4:3 * w // 4]
    ring_mask = np.ones_like(gray, dtype=bool)
    ring_mask[h // 4:3 * h // 4, w // 4:3 * w // 4] = False

    dark_ratio = float((gray < 60).mean())
    pale_ratio = float(((gray > 170) & (sat < 0.35)).mean())
    edge_gap = float(centre.mean() - gray[ring_mask].mean())          # > 0: edges darker than the centre
    blocks = [gray[i * h // 3:(i + 1) * h // 3, j * w // 3:(j + 1) * w // 3].mean() for i in range(3) for j in range(3)]
    unevenness = float(np.std(blocks) / max(np.mean(blocks), 1))

    rows, symptoms, support = [], {}, set()

    def add(label, value, meaning, symptom=None, conf=0.0, rules=()):
        rows.append({"Measurement": label, "Value": value, "What it means": meaning})
        if symptom:
            symptoms[symptom] = max(symptoms.get(symptom, 0), conf)
        support.update(rules)

    if dark_ratio > 0.25:
        add("Very dark surface area", f"{dark_ratio:.0%} of the photo",
            "Sugars and proteins have over-browned (caramelisation and the Maillard reaction). This happens when the oven is too hot or the bake runs too long.",
            "burnt_surface", min(0.95, 0.4 + dark_ratio), ("temp_high", "time_long", "top_rod"))
    if pale_ratio > 0.5:
        add("Pale surface area", f"{pale_ratio:.0%} of the photo",
            "Browning reactions have barely started, so the oven was too cool, the time too short, or the oven was not preheated.",
            "pale_underbaked", min(0.9, 0.3 + pale_ratio / 2), ("temp_low", "time_short", "no_preheat"))
    if edge_gap > 25:
        add("Edges darker than the centre", f"{edge_gap:.0f} brightness levels",
            "Edges get heat from the tin and the oven air first, so they bake faster than the centre. Typical of a dark or glass tin, a high temperature or a long bake.",
            "burnt_surface" if edge_gap > 45 else None, 0.5, ("dark_tin", "temp_high", "time_long"))
    if unevenness > 0.15:
        add("Uneven browning", f"{unevenness:.0%} variation between areas",
            "Hot spots: strong top-rod heat, a high rack position, or an uneven batter level cooks some areas faster.",
            None, 0, ("top_rod",))
    if not rows:
        rows.append({"Measurement": "Colour and browning pattern", "Value": "within normal limits",
                     "What it means": "No strong colour or browning problem was measured. Shape problems such as a sunken centre, cracks or a dense crumb need the trained CNN or your typed guess. Use a clearer photo, or type your guess."})
    return {"rows": rows, "symptoms": [(k, v, "photo measurements") for k, v in symptoms.items()],
            "support": sorted(support),
            "numbers": {"dark_ratio": dark_ratio, "pale_ratio": pale_ratio, "edge_gap": edge_gap,
                        "unevenness": unevenness}}
