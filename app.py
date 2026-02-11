import time
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Analyse qualité de l'eau", layout="wide")

# ---------------- STYLE ----------------
st.markdown("""
<style>
.block-container {padding-top: 1.5rem; padding-bottom: 2rem;}
.card {background:#0f172a; border:1px solid #1e293b; border-radius:16px; padding:20px;}
.okBox {background:#052e16; border:1px solid #16a34a; padding:16px; border-radius:14px;}
.warnBox {background:#3f2d06; border:1px solid #facc15; padding:16px; border-radius:14px;}
.badBox {background:#3f0d0d; border:1px solid #ef4444; padding:16px; border-radius:14px;}
.infoBox {background:#0c2e4e; border:1px solid #3b82f6; padding:16px; border-radius:14px;}
.big {font-size:1.3rem; font-weight:700;}
div[data-testid="stDataFrame"] * { color:white !important; }
div[data-testid="stDataFrame"] { background:#0e1117 !important; border-radius:12px; }
</style>
""", unsafe_allow_html=True)

# ---------------- PARAMÈTRES ----------------
TESTS = [
    "pH",
    "fer (mg/L)",
    "nitrates (mg/L)",
    "potassium (mg/L)",
    "calcium (mg/L)",
    "durete totale (°f)",
    "chlore (mg/L)",
]

# Normes officielles / reconnues
NORMES = {
    "OMS": {
        "pH": (6.5, 8.5),
        "fer (mg/L)": 0.3,
        "nitrates (mg/L)": 50,
        "potassium (mg/L)": None,
        "calcium (mg/L)": None,
        "durete totale (°f)": None,
        "chlore (mg/L)": 0.5
    },

    "Normes françaises / UE": {
        "pH": (6.5, 9.0),
        "fer (mg/L)": 0.2,
        "nitrates (mg/L)": 50,
        "potassium (mg/L)": None,
        "calcium (mg/L)": None,
        "durete totale (°f)": None,
        "chlore (mg/L)": 0.2
    }
}

# ---------------- FONCTION STATUT ----------------
def compute_status(test, value, norme):

    if norme is None:
        return "🔵 Indicatif"

    if isinstance(norme, tuple):  # Cas pH
        if norme[0] <= value <= norme[1]:
            return "🟢 Conforme"
        return "🔴 Non conforme"

    if value <= 0.9 * norme:
        return "🟢 Conforme"
    elif value <= norme:
        return "🟠 Limite proche"
    return "🔴 Non conforme"

# ---------------- VERDICT GLOBAL ----------------
def verdict_global(df):
    sanitaires = df[df["Statut"].isin(["🔴 Non conforme", "🟠 Limite proche"])]

    if sanitaires.empty:
        return "ok", f"✅ Tous les paramètres réglementés sont conformes. Eau potable 😀"

    rouges = df[df["Statut"] == "🔴 Non conforme"]
    if not rouges.empty:
        probleme = rouges.iloc[0]["Test"]
        return "bad", f"❌ Non conformité détectée sur {probleme}. Eau déconseillée."

    return "warn", "⚠️ Eau globalement conforme mais proche d'une limite réglementaire."

# ---------------- INTERFACE ----------------
st.title("💧 Analyse officielle de la qualité de l’eau")
st.caption("Seuils basés sur recommandations OMS et Directive européenne 2020/2184.")

norme_type = st.selectbox("Choisissez le type de normes", list(NORMES.keys()))
normes_selectionnees = NORMES[norme_type]

st.subheader("Saisissez les mesures")

with st.form("form"):
    col1, col2, col3, col4 = st.columns(4)

    ph = col1.number_input("pH", value=7.0)
    fer = col2.number_input("Fer (mg/L)", value=0.0)
    nitrates = col3.number_input("Nitrates (mg/L)", value=0.0)
    chlore = col4.number_input("Chlore (mg/L)", value=0.0)

    col5, col6, col7 = st.columns(3)
    potassium = col5.number_input("Potassium (mg/L)", value=0.0)
    calcium = col6.number_input("Calcium (mg/L)", value=0.0)
    durete = col7.number_input("Dureté totale (°f)", value=0.0)

    submitted = st.form_submit_button("🔍 Analyser l’eau")

# ---------------- ANALYSE ----------------
if submitted:

    with st.spinner("Analyse en cours… veuillez patienter 🧪"):
        prog = st.progress(0)
        for i in range(101):
            time.sleep(0.015)
            prog.progress(i)
        prog.empty()

    values = {
        "pH": ph,
        "fer (mg/L)": fer,
        "nitrates (mg/L)": nitrates,
        "potassium (mg/L)": potassium,
        "calcium (mg/L)": calcium,
        "durete totale (°f)": durete,
        "chlore (mg/L)": chlore,
    }

    df = pd.DataFrame({
        "Test": TESTS,
        "Valeur mesurée": [values[t] for t in TESTS],
        "Norme": [normes_selectionnees[t] for t in TESTS],
    })

    df["Statut"] = [
        compute_status(t, values[t], normes_selectionnees[t])
        for t in TESTS
    ]

    kind, message = verdict_global(df)

    st.subheader("Verdict")

    if kind == "ok":
        st.markdown(f'<div class="okBox"><div class="big">{message}</div></div>', unsafe_allow_html=True)
    elif kind == "warn":
        st.markdown(f'<div class="warnBox"><div class="big">{message}</div></div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="badBox"><div class="big">{message}</div></div>', unsafe_allow_html=True)

    st.subheader("Détails techniques")
    st.dataframe(df, use_container_width=True, hide_index=True)

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Télécharger le rapport (CSV)", csv, "rapport_qualite_eau.csv")
