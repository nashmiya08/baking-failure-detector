"""
Photo reading.
 - Measurements (image_features.py): colour, browning pattern -> always used as visible evidence.
 - CNN (if models/baking_cnn.keras exists, trained with train_cnn.py): recognises shape problems
   such as collapse, dense crumb and spread. Without it, the measurements give the symptoms.
"""
import json
import os
import numpy as np
from PIL import Image

from image_features import measure

MODEL_PATH = "models/baking_cnn.keras"
CLASSES_PATH = "models/class_names.json"
_model = None


def _load_model():
    global _model
    if _model is None and os.path.exists(MODEL_PATH):
        import tensorflow as tf  # imported only if a trained model exists
        _model = tf.keras.models.load_model(MODEL_PATH)
    return _model


def read_photo(img):
    """Returns (symptoms, findings).
    symptoms: list of (symptom_key, confidence, source) from the CNN if trained, else from photo measurements.
    findings: measured colour/browning evidence with its baking-science meaning (always computed)."""
    findings = measure(img)
    return (_cnn_symptoms(img) if _load_model() is not None else findings["symptoms"]), findings


def _cnn_symptoms(img):
    model = _load_model()
    classes = json.load(open(CLASSES_PATH))
    x = np.asarray(img.convert("RGB").resize((224, 224)), dtype="float32")[None]
    probs = model.predict(x, verbose=0)[0]
    out = []
    for name, p in sorted(zip(classes, probs), key=lambda t: -t[1])[:3]:
        if name != "good" and p >= 0.35:
            out.append((name, float(p), "CNN (MobileNetV2)"))
    return out
