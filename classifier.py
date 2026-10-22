"""
Image classifier.
 - If models/baking_cnn.keras exists (trained with train_cnn.py) -> uses the CNN.
 - Otherwise uses a simple colour-based fallback so the app still runs for demo.
"""
import json
import os
import numpy as np
from PIL import Image

MODEL_PATH = "models/baking_cnn.keras"
CLASSES_PATH = "models/class_names.json"
_model = None


def _load_model():
    global _model
    if _model is None and os.path.exists(MODEL_PATH):
        import tensorflow as tf  # imported only if a trained model exists
        _model = tf.keras.models.load_model(MODEL_PATH)
    return _model


def _colour_fallback(img):
    gray = np.asarray(img.convert("L").resize((224, 224)), dtype=float)
    h, w = gray.shape
    centre = gray[h // 4: 3 * h // 4, w // 4: 3 * w // 4]
    dark, pale = (centre < 60).mean(), (centre > 185).mean()
    out = []
    if dark > 0.25:
        out.append(("burnt_surface", min(0.95, 0.4 + dark), "colour analysis (demo mode)"))
    if pale > 0.35:
        out.append(("pale_underbaked", min(0.9, 0.3 + pale / 2), "colour analysis (demo mode)"))
    return out


def predict(img):
    """Returns list of (symptom_key, confidence, source)."""
    model = _load_model()
    if model is None:
        return _colour_fallback(img)
    classes = json.load(open(CLASSES_PATH))
    x = np.asarray(img.convert("RGB").resize((224, 224)), dtype="float32")[None]
    probs = model.predict(x, verbose=0)[0]
    out = []
    for name, p in sorted(zip(classes, probs), key=lambda t: -t[1])[:3]:
        if name != "good" and p >= 0.35:
            out.append((name, float(p), "CNN (MobileNetV2)"))
    return out
