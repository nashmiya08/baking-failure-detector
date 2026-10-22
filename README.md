# Intelligent Baking Failure Detection and Recipe Correction System

Upload a photo of a failed bake + oven details -> get likely causes, the baking science, and a revised recipe/process.

## Run locally
    pip install -r requirements.txt
    streamlit run app.py

## Files
- app.py            Streamlit pages (login, new diagnosis, history)
- db.py             SQLite: users + history
- classifier.py     Image symptom detection (CNN or colour fallback)
- diagnosis.py      Rule-based diagnosis engine
- recipe_fixer.py   Checks ingredient grams/ratios and writes a corrected recipe
- knowledge_base.py Baking-science rules (symptom -> causes -> fixes)
- train_cnn.py      Transfer-learning training script (MobileNetV2)

## Deploy (Streamlit Community Cloud)
Push to GitHub, then at share.streamlit.io choose the repo and `app.py`.

## Optional: your own photos
Create a folder named `images` in the repo and add 2-4 bakery photos (.jpg/.png). They show on the login page.
