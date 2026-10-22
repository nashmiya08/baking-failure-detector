"""
Train the CNN with transfer learning (MobileNetV2).
Folder layout (folder name = class):
  dataset/burnt_surface/*.jpg
  dataset/pale_underbaked/*.jpg
  dataset/collapsed_centre/*.jpg
  dataset/dense_crumb/*.jpg
  dataset/cracked_top/*.jpg
  dataset/cookies_spread/*.jpg
  dataset/dry_crumbly/*.jpg
  dataset/good/*.jpg
Run:  python train_cnn.py
"""
import json
import os
import tensorflow as tf

os.makedirs("models", exist_ok=True)
IMG = (224, 224)
train = tf.keras.utils.image_dataset_from_directory(
    "dataset", validation_split=0.2, subset="training", seed=42, image_size=IMG, batch_size=16)
val = tf.keras.utils.image_dataset_from_directory(
    "dataset", validation_split=0.2, subset="validation", seed=42, image_size=IMG, batch_size=16)
class_names = train.class_names

base = tf.keras.applications.MobileNetV2(input_shape=IMG + (3,), include_top=False, weights="imagenet")
base.trainable = False  # transfer learning: keep ImageNet features

augment = tf.keras.Sequential([
    tf.keras.layers.RandomFlip("horizontal"),
    tf.keras.layers.RandomRotation(0.1),
    tf.keras.layers.RandomZoom(0.1),
    tf.keras.layers.RandomBrightness(0.1),
])

inputs = tf.keras.Input(shape=IMG + (3,))
x = augment(inputs)
x = tf.keras.applications.mobilenet_v2.preprocess_input(x)
x = base(x, training=False)
x = tf.keras.layers.GlobalAveragePooling2D()(x)
x = tf.keras.layers.Dropout(0.3)(x)
outputs = tf.keras.layers.Dense(len(class_names), activation="softmax")(x)
model = tf.keras.Model(inputs, outputs)

model.compile(optimizer="adam", loss="sparse_categorical_crossentropy", metrics=["accuracy"])
model.fit(train, validation_data=val, epochs=10)

model.save("models/baking_cnn.keras")
json.dump(class_names, open("models/class_names.json", "w"))
print("Saved model. Classes:", class_names)
