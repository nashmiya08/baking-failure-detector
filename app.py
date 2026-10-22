"""Streamlit frontend: login, new diagnosis, history."""
import json
from collections import Counter

import streamlit as st
from PIL import Image

import db
from classifier import predict
from diagnosis import diagnose
from knowledge_base import SYMPTOMS, PRODUCT_RANGES

st.set_page_config(page_title="Baking Failure Detector", page_icon="🧁", layout="wide")
db.init_db()

if "user_id" not in st.session_state:
    st.session_state.user_id = None
    st.session_state.username = None


# ---------- helpers ----------
def show_result(res):
    if not res["symptoms"]:
        st.info("No clear failure found in the photo. Pick a guess from the list and try again.")
    for s in res["symptoms"]:
        st.subheader(f"Likely issue: {s['label']}")
        st.caption(f"Detected from: {s['source']}  |  confidence: {s['confidence']:.0%}")
        for i, c in enumerate(s["causes"]):
            tag = " (matches your inputs)" if c["matched"] else ""
            with st.expander(f"{c['name']} - {c['score']:.0%} likely{tag}", expanded=(i == 0)):
                st.markdown(f"**Science:** {c['science']}")
                st.markdown(f"**Recipe adjustment:** {c['recipe_fix']}")
                st.markdown(f"**Process change:** {c['process_fix']}")
    if res["notes"]:
        st.markdown("#### Checks based on your oven settings")
        for n in res["notes"]:
            st.write(f"- {n}")
    if res["plan"]["recipe"] or res["plan"]["process"]:
        st.markdown("#### Your revised plan for the next bake")
        for r in res["plan"]["recipe"]:
            st.write(f"- Recipe: {r}")
        for p in res["plan"]["process"]:
            st.write(f"- Process: {p}")
        st.caption("Change only one or two things at a time so you can see what worked.")


def login_page():
    st.title("🧁 Intelligent Baking Failure Detection")
    st.write("Log in to save your bakes and see your history.")
    tab1, tab2 = st.tabs(["Login", "Register"])
    with tab1:
        u = st.text_input("Username", key="lu")
        p = st.text_input("Password", type="password", key="lp")
        if st.button("Login"):
            uid = db.login(u, p)
            if uid:
                st.session_state.user_id, st.session_state.username = uid, u
                st.rerun()
            else:
                st.error("Wrong username or password.")
    with tab2:
        u = st.text_input("Choose username", key="ru")
        p = st.text_input("Choose password", type="password", key="rp")
        if st.button("Create account"):
            if len(u) < 3 or len(p) < 4:
                st.warning("Username needs 3+ characters and password 4+.")
            elif db.register(u, p):
                st.success("Account created. Go to the Login tab.")
            else:
                st.error("That username is taken.")


# ---------- pages ----------
def new_diagnosis():
    st.header("New diagnosis")
    with st.form("bake_form"):
        left, right = st.columns(2)
        with left:
            photo = st.file_uploader("Photo of the failed bake", type=["jpg", "jpeg", "png"])
            product = st.selectbox("What did you bake?", list(PRODUCT_RANGES))
            recipe = st.text_area("Recipe used (paste ingredients / method)", height=150)
        with right:
            temp = st.number_input("Oven temperature (C)", 100, 300, 180)
            minutes = st.number_input("Minutes baked", 1, 180, 30)
            rod = st.selectbox("Which rods were on?",
                               ["Top and bottom", "Top rod only", "Bottom rod only", "Fan / convection", "Not sure"])
            tin = st.selectbox("Tin used", ["Light metal tin", "Dark / non-stick metal tin",
                                            "Glass / ceramic dish", "Silicone mould", "Baking tray (cookies)"])
            preheated = st.checkbox("Oven was preheated", value=True)
            opened = st.checkbox("I opened the oven door during baking")
        guesses = st.multiselect("Do you already know / guess the problem? (optional)",
                                 list(SYMPTOMS), format_func=lambda k: SYMPTOMS[k]["label"])
        go = st.form_submit_button("Diagnose")

    if go:
        image = Image.open(photo) if photo else None
        inp = {"product": product, "temp": temp, "minutes": minutes, "rod": rod, "tin": tin,
               "recipe": recipe, "guesses": guesses, "preheated": preheated, "opened_door": opened}
        image_symptoms = predict(image) if image else []
        result = diagnose(inp, image_symptoms)
        db.save_history(st.session_state.user_id, inp, image, result)
        if image:
            st.image(image, width=300)
        show_result(result)


def history_page():
    st.header("My history")
    rows = db.get_history(st.session_state.user_id)
    if not rows:
        st.info("No saved diagnoses yet.")
        return

    counts = Counter(s["label"] for r in rows for s in json.loads(r["result"])["symptoms"])
    repeated = [(k, v) for k, v in counts.items() if v >= 2]
    if repeated:
        st.warning("Repeated mistakes: " + ", ".join(f"{k} ({v} times)" for k, v in repeated))

    for r in rows:
        res = json.loads(r["result"])
        issues = ", ".join(s["label"] for s in res["symptoms"]) or "No issue detected"
        with st.expander(f"{r['created']} - {r['product']} - {issues}"):
            st.write(f"{r['temp']:.0f} C for {r['minutes']:.0f} min | rods: {r['rod']} | tin: {r['tin']}")
            if r["image_path"]:
                st.image(r["image_path"], width=250)
            show_result(res)


# ---------- main ----------
if st.session_state.user_id is None:
    login_page()
else:
    st.sidebar.write(f"Logged in as **{st.session_state.username}**")
    page = st.sidebar.radio("Menu", ["New diagnosis", "History"])
    if st.sidebar.button("Logout"):
        st.session_state.user_id = None
        st.rerun()
    new_diagnosis() if page == "New diagnosis" else history_page()
