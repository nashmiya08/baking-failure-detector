"""Streamlit frontend: colourful bakery theme, login, new diagnosis, history."""
import json
import os
from collections import Counter

import streamlit as st
from PIL import Image

import db
from classifier import predict
from diagnosis import diagnose
import recipe_fixer
from guess_parser import parse_guess
from knowledge_base import PRODUCT_RANGES, PANS

st.set_page_config(page_title="Baking Failure Detector", page_icon="🧁", layout="wide")
db.init_db()

# ---------------- colourful bakery theme (CSS) ----------------
CSS = """<style>
.stApp{background-color:#fff8f0;
 background-image:radial-gradient(#ffc2d9 2.5px,transparent 2.5px),radial-gradient(#ffe0a8 2.5px,transparent 2.5px),radial-gradient(#c9f0e4 2.5px,transparent 2.5px);
 background-size:90px 90px;background-position:0 0,30px 45px,60px 20px;}
.stApp, .stApp p, .stApp label, .stApp li, .stApp span, .stApp h1, .stApp h2, .stApp h3, .stApp h4{color:#4a2f22;}
div.block-container{background:rgba(255,255,255,.9);border-radius:28px;padding:2rem 2.5rem 3rem;margin-top:1rem;box-shadow:0 10px 30px rgba(255,111,165,.2);}
section[data-testid="stSidebar"]{background:linear-gradient(180deg,#ffd0e2,#ffe7c2);}
.stTextInput input,.stNumberInput input,.stTextArea textarea,div[data-baseweb="select"]>div{background:#fff !important;color:#4a2f22 !important;border-radius:12px;}
div.stButton>button,div[data-testid="stFormSubmitButton"] button{background:linear-gradient(90deg,#ff6fa5,#ff9a5a);border:none;border-radius:999px;padding:.5rem 1.6rem;font-weight:700;box-shadow:0 4px 12px rgba(255,111,165,.4);}
div.stButton>button *,div[data-testid="stFormSubmitButton"] button *{color:#fff !important;}
div[data-testid="stExpander"]{background:#fff;border:2px solid #ffd6e7;border-radius:16px;}
.hero{display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap;background:linear-gradient(120deg,#ff8fb8 0%,#ffb86b 55%,#ffd98a 100%);border-radius:26px;padding:22px 30px;margin-bottom:14px;box-shadow:0 8px 24px rgba(255,111,165,.35);}
.hero-title{font-size:2.1rem;font-weight:800;line-height:1.1;text-shadow:0 2px 6px rgba(120,60,40,.35);}
.hero-sub{font-size:1.02rem;margin-top:6px;}
.hero-art{display:flex;align-items:center;gap:8px;}
.hero-art svg{animation:float 3s ease-in-out infinite;}
.hero-art svg:nth-child(2){animation-delay:.8s;}
.hero-emoji{font-size:2.6rem;}
.strip{text-align:center;font-size:1.7rem;letter-spacing:10px;margin-bottom:10px;}
@keyframes float{0%,100%{transform:translateY(0)}50%{transform:translateY(-8px)}}
.hero,.hero *{color:#fff !important;}
</style>"""

CUPCAKE = ('<svg viewBox="0 0 100 100" width="84" height="84"><path d="M24 52h52l-7 40H31z" fill="#e8a24d"/>'
           '<path d="M34 52v40M44 52v40M56 52v40M66 52v40" stroke="#c9822f" stroke-width="2"/>'
           '<circle cx="50" cy="42" r="24" fill="#ff8fb8"/><circle cx="36" cy="36" r="14" fill="#ffb3d1"/>'
           '<circle cx="64" cy="36" r="14" fill="#ffb3d1"/><circle cx="50" cy="26" r="14" fill="#ff8fb8"/>'
           '<circle cx="50" cy="12" r="6" fill="#e63946"/></svg>')
BROWNIE = ('<svg viewBox="0 0 100 100" width="84" height="84"><path d="M10 50l40-22 40 22v22L50 94 10 72z" fill="#5b3a29"/>'
           '<path d="M10 50l40-22 40 22-40 22z" fill="#7b4a32"/><circle cx="38" cy="48" r="4" fill="#3b2418"/>'
           '<circle cx="54" cy="42" r="4" fill="#3b2418"/><circle cx="62" cy="54" r="4" fill="#3b2418"/>'
           '<circle cx="46" cy="58" r="3.5" fill="#3b2418"/></svg>')
HERO = ('<div class="hero"><div><div class="hero-title">Baking Failure Detector</div>'
        '<div class="hero-sub">Upload your failed bake and get the science, a corrected recipe and a better next bake.</div></div>'
        '<div class="hero-art">' + CUPCAKE + BROWNIE + '<span class="hero-emoji">🥐🍩</span></div></div>'
        '<div class="strip">🧁 🍫 🥐 🍩 🍪 🎂 🍰</div>')

st.markdown(CSS, unsafe_allow_html=True)
st.markdown(HERO, unsafe_allow_html=True)

if "user_id" not in st.session_state:
    st.session_state.user_id = None
    st.session_state.username = None

STATUS = {"ok": "✅ OK", "high": "⬆️ Too high / too much", "low": "⬇️ Too low / too little", "missing": "➕ Missing",
          "long": "⬆️ Too long", "short": "⬇️ Too short", "deep": "⬆️ Too deep", "shallow": "⬇️ Too shallow"}


# ---------------- helpers ----------------
def show_recipe_check(rc):
    st.markdown("#### 🧮 Recipe check: are your ingredient amounts right?")
    if rc.get("message"):
        st.warning(rc["message"])
    if rc.get("understood"):
        with st.expander("How I read your recipe (ingredients and grams detected)"):
            st.table([{"Your line": u["line"], "Understood as": u["ingredient"], "Grams": u["grams"]}
                      for u in rc["understood"]])
    if rc["rows"]:
        st.caption(f"Compared with the reference recipe dataset, using your flour amount ({rc['flour_g']:.0f} g) as the base.")
        st.table([{"Ingredient": r["ingredient"], "You used": r["used"], "Ideal range": r["ideal"],
                   "Suggested": r["suggested"], "Status": STATUS[r["status"]]} for r in rc["rows"]])
        for r in rc["rows"]:
            if r["status"] != "ok":
                st.write(f"- **{r['ingredient']}:** {r['why']}")
        st.success("**Corrected recipe for your next bake**\n\n" + "\n".join(f"- {line}" for line in rc["corrected"]))
    if rc.get("reference"):
        ref = rc["reference"]
        with st.expander(f"Closest correct reference recipe: {ref['name']} (scaled to your flour)"):
            st.write("\n".join(f"- {line}" for line in ref["scaled"]))
            st.info("Method: " + ref["method"])
    if rc.get("unparsed"):
        st.caption("I could not read these lines: " + "; ".join(rc["unparsed"]) + ". Write them like '200 g flour'.")


def show_bake_check(bc):
    st.markdown("#### 🔥 Bake check: temperature, time and pan")
    st.caption(f"Compared with the reference recipe '{bc['ref']}' ({bc['ref_oven']}), adjusted for your pan, tin and oven.")
    st.table([{"Check": r["what"], "You used": r["you"], "Should be": r["suggested"], "Status": STATUS[r["status"]]}
              for r in bc["rows"]])
    for line in bc["science"]:
        st.write(f"- {line}")


def show_result(res):
    if res.get("guess_text"):
        st.info(f"Your guess: {res['guess_text']}")
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
    if res.get("bake_check"):
        show_bake_check(res["bake_check"])
    if res.get("recipe_check"):
        show_recipe_check(res["recipe_check"])
    if res["notes"]:
        st.markdown("#### 🧰 Other checks (oven settings and method)")
        for n in res["notes"]:
            st.write(f"- {n}")
    if res["plan"]["recipe"] or res["plan"]["process"]:
        st.markdown("#### 📝 Your revised plan for the next bake")
        for r in res["plan"]["recipe"]:
            st.write(f"- Recipe: {r}")
        for p in res["plan"]["process"]:
            st.write(f"- Process: {p}")
        st.caption("Change only one or two things at a time so you can see what worked.")


def gallery():
    """Shows your own bakery photos if you add them to an 'images' folder on GitHub."""
    if os.path.isdir("images"):
        files = [f for f in sorted(os.listdir("images")) if f.lower().endswith((".jpg", ".jpeg", ".png"))][:4]
        if files:
            cols = st.columns(len(files))
            for col, f in zip(cols, files):
                col.image(os.path.join("images", f), width=230)


def login_page():
    st.write("Log in to save your bakes and see your history, so you never explain the same mistake twice.")
    gallery()
    tab1, tab2 = st.tabs(["🔑 Login", "🧁 Register"])
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


# ---------------- pages ----------------
def new_diagnosis():
    st.header("🍰 New diagnosis")
    with st.form("bake_form"):
        left, right = st.columns(2)
        with left:
            photo = st.file_uploader("Photo of the failed bake", type=["jpg", "jpeg", "png"])
            product = st.selectbox("What did you bake?", list(PRODUCT_RANGES))
            recipe = st.text_area(
                "Recipe used (one ingredient per line, with amounts)", height=190,
                placeholder="200 g flour\n150 g sugar\n100 g butter\n2 eggs\n1 tsp baking powder\n120 ml milk\n1/2 tsp salt")
            st.caption("Units understood: g, kg, ml, cup, tbsp, tsp, or a number of eggs.")
        with right:
            temp = st.number_input("Oven temperature (C)", 100, 300, 180)
            minutes = st.number_input("Minutes baked", 1, 180, 30)
            rod = st.selectbox("Which rods were on?",
                               ["Top and bottom", "Top rod only", "Bottom rod only", "Fan / convection", "Not sure"])
            pan = st.selectbox("Pan / tin size", list(PANS))
            tin = st.selectbox("Tin material", ["Light metal tin", "Dark / non-stick metal tin",
                                            "Glass / ceramic dish", "Silicone mould", "Baking tray (cookies)"])
            mixing = st.selectbox("How did you mix after adding the flour?",
                                  ["Not sure / skip", "Gently folded until just combined", "Mixed vigorously / for a long time"])
            preheated = st.checkbox("Oven was preheated", value=True)
            opened = st.checkbox("I opened the oven door during baking")
        guess_text = st.text_input(
            "Do you already know or suspect the problem? (optional, type it in your own words)",
            placeholder="e.g. the top is burnt and the middle is raw, I think the oven was too hot")
        st.caption("Useful words: burnt, raw, sunk, dense, cracked, spread, dry. You can also add a reason, "
                   "like 'oven too hot', 'overmixed', 'opened the oven door' or 'didn't preheat'.")
        go = st.form_submit_button("🔍 Diagnose")

    if go:
        image = Image.open(photo) if photo else None
        guess_keys, guess_flags = parse_guess(guess_text)
        inp = {"product": product, "temp": temp, "minutes": minutes, "rod": rod, "tin": tin,
               "recipe": recipe, "pan": pan, "guesses": guess_keys, "guess_flags": guess_flags, "guess_text": guess_text,
               "preheated": preheated, "opened_door": opened, "mixing": mixing}
        image_symptoms = predict(image) if image else []
        result = diagnose(inp, image_symptoms)
        db.save_history(st.session_state.user_id, inp, image, result)
        if image:
            st.image(image, width=300)
        show_result(result)


def history_page():
    st.header("📒 My history")
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


def library_page():
    st.header("📚 Reference recipe library")
    st.write("These correct reference recipes are the dataset the system uses to check your ingredient amounts "
             "and to suggest a corrected recipe. Everything is in grams (1 egg is about 50 g).")
    product = st.selectbox("Choose a bake", recipe_fixer.products())
    st.markdown("#### Reference recipes")
    st.table(recipe_fixer.reference_table(product))
    st.markdown("#### Normal ingredient ranges learned from these recipes")
    st.table(recipe_fixer.range_table(product))
    st.markdown("#### Method tips")
    for name, method in recipe_fixer.reference_methods(product):
        st.write(f"- **{name}:** {method}")
    st.caption("To add more recipes, add rows to recipes_dataset.csv in your GitHub repo.")


# ---------------- main ----------------
if st.session_state.user_id is None:
    login_page()
else:
    st.sidebar.markdown("### 🧁 Baking Lab")
    st.sidebar.write(f"Logged in as **{st.session_state.username}**")
    page = st.sidebar.radio("Menu", ["New diagnosis", "History", "Recipe library"])
    if st.sidebar.button("Logout"):
        st.session_state.user_id = None
        st.rerun()
    if page == "New diagnosis":
        new_diagnosis()
    elif page == "History":
        history_page()
    else:
        library_page()
