import time
import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Contrôle qualité de l'eau", layout="wide")

# -------------------- STYLE (lisible en dark) --------------------
st.markdown(
    """
    <style>
      .block-container {padding-top: 1.6rem; padding-bottom: 2rem;}
      .card {background:#0b1220; border:1px solid #1f2937; border-radius:16px; padding:16px;}
      .big {font-size:1.2rem; font-weight:700;}
      .muted {opacity:0.85;}
      .okBox {background:#0f2a1a; border:1px solid #1f8b4c; padding:14px; border-radius:14px;}
      .warnBox {background:#2a210f; border:1px solid #f2b01e; padding:14px; border-radius:14px;}
      .badBox {background:#2a0f12; border:1px solid #ff5a5f; padding:14px; border-radius:14px;}
      div[data-testid="stDataFrame"] * { color:#ffffff !important; }
      div[data-testid="stDataFrame"] { background:#0e1117 !important; border-radius:12px; padding:6px; }
      div[data-testid="stDataFrame"] thead tr th { background:#111827 !important; color:#ffffff !important; }
      div[data-testid="stDataFrame"] tbody tr td { background:#1f2937 !important; color:#ffffff !important; }
      div[data-testid="stDataFrame"] tbody tr:nth-child(even) td { background:#111827 !important; }
    </style>
    """,
    unsafe_allow_html=True
)

# -------------------- NORMES (à ajuster si besoin) --------------------
NORMES = {
    "OMS": {
        "Eau du robinet": {"nitrates (mg/L)": 50, "plomb (µg/L)": 10, "pH": 8.5, "turbidite (NTU)": 1, "fer (mg/L)": 0.3, "magnesium (mg/L)": 50, "chlore (mg/L)": 0.5},
        "Eau minérale":   {"nitrates (mg/L)": 75, "plomb (µg/L)": 15, "pH": 8.5, "turbidite (NTU)": 5, "fer (mg/L)": 1.0, "magnesium (mg/L)": 125, "chlore (mg/L)": 1.0},
    },
    "Normes françaises": {
        "Eau du robinet": {"nitrates (mg/L)": 50, "plomb (µg/L)": 10, "pH": 8.5, "turbidite (NTU)": 1, "fer (mg/L)": 0.2, "magnesium (mg/L)": 60, "chlore (mg/L)": 0.4},
        "Eau minérale":   {"nitrates (mg/L)": 40, "plomb (µg/L)": 5,  "pH": 7.5, "turbidite (NTU)": 3, "fer (mg/L)": 0.3, "magnesium (mg/L)": 100, "chlore (mg/L)": 0.6},
    }
}

TESTS = ["nitrates (mg/L)", "plomb (µg/L)", "pH", "turbidite (NTU)", "fer (mg/L)", "magnesium (mg/L)", "chlore (mg/L)"]

# Nom “humain” pour le message
NOMS_HUMAINS = {
    "nitrates (mg/L)": "nitrates",
    "plomb (µg/L)": "plomb",
    "pH": "pH",
    "turbidite (NTU)": "turbidité",
    "fer (mg/L)": "fer",
    "magnesium (mg/L)": "magnésium",
    "chlore (mg/L)": "chlore",
}

def compute_status(value, seuil):
    # 🟢 si <= 0.9*seuil, 🟠 si <= seuil, 🔴 sinon
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "—"
    v = float(value)
    if v <= 0.9 * float(seuil):
        return "🟢 Conforme"
    elif v <= float(seuil):
        return "🟠 Limite proche"
    else:
        return "🔴 Non conforme"

def build_verdict(df):
    ok = int(df["Statut"].str.startswith("🟢").sum())
    warn = int(df["Statut"].str.startswith("🟠").sum())
    bad = int(df["Statut"].str.startswith("🔴").sum())

    # Paramètre “le plus problématique” (priorité : 🔴 puis 🟠)
    pb = df[df["Statut"].str.startswith("🔴")]
    if pb.empty:
        pb = df[df["Statut"].str.startswith("🟠")]

    if bad == 0 and warn == 0:
        return "ok", f"✅ {ok} conformes ! Vous pouvez boire 😀", None

    if not pb.empty:
        # on prend celui qui dépasse le plus en % du seuil
        pb = pb.copy()
        pb["ratio"] = pb["Valeur mesurée"] / pb["Seuil (max)"]
        worst = pb.sort_values("ratio", ascending=False).iloc[0]
        nom = NOMS_HUMAINS.get(worst["Test"], worst["Test"])
        valeur = worst["Valeur mesurée"]
        seuil = worst["Seuil (max)"]

        if str(worst["Statut"]).startswith("🔴"):
            return "bad", f"❌ Attention : votre eau est trop riche en {nom}. C’est potentiellement dangereux !", f"{nom} = {valeur} (seuil {seuil})"
        else:
            return "warn", f"⚠️ Faites attention : votre eau est proche de la limite en {nom}.", f"{nom} = {valeur} (seuil {seuil})"

    return "warn", "⚠️ Résultat à vérifier.", None

# -------------------- UI --------------------
st.title("💧 Contrôle qualité de l’eau")
st.caption("Réalisé par Wail Nefoussi, Marlon Drif et Killian Vienne")

colA, colB, colC = st.columns([1.2, 1.2, 1.6], vertical_alignment="top")
with colA:
    norme_type = st.selectbox("Type de normes", list(NORMES.keys()))
with colB:
    eau_type = st.selectbox("Type d’eau", list(NORMES[norme_type].keys()))
with colC:
    st.markdown('<div class="card"><div class="big">Infos</div><div class="muted">Clique “Analyser l’eau” pour lancer le contrôle avec animation.</div></div>', unsafe_allow_html=True)

normes = NORMES[norme_type][eau_type]

# -------------------- FORMULAIRE DE SAISIE --------------------
st.subheader("1) Saisis les mesures")

with st.form("form_mesures"):
    c1, c2, c3, c4 = st.columns(4)

    # Champs (tu peux réorganiser)
    nitrates = c1.number_input("Nitrates (mg/L)", min_value=0.0, value=0.0, step=0.1)
    plomb    = c2.number_input("Plomb (µg/L)", min_value=0.0, value=0.0, step=0.1)
    ph       = c3.number_input("pH", min_value=0.0, value=7.0, step=0.1)
    turbi    = c4.number_input("Turbidité (NTU)", min_value=0.0, value=0.0, step=0.1)

    c5, c6, c7 = st.columns(3)
    fer      = c5.number_input("Fer (mg/L)", min_value=0.0, value=0.0, step=0.01)
    mag      = c6.number_input("Magnésium (mg/L)", min_value=0.0, value=0.0, step=0.1)
    chlore   = c7.number_input("Chlore (mg/L)", min_value=0.0, value=0.0, step=0.01)

    submitted = st.form_submit_button("🔍 Analyser l’eau")

# -------------------- ANALYSE + ANIMATION --------------------
if submitted:
    # Animation "Veuillez patienter"
    with st.spinner("Veuillez patienter… analyse en cours 🧪"):
        prog = st.progress(0)
        for i in range(101):
            time.sleep(0.02)   # vitesse de l’animation
            prog.progress(i)
        time.sleep(0.15)

    # Construire le tableau
    values = {
        "nitrates (mg/L)": nitrates,
        "plomb (µg/L)": plomb,
        "pH": ph,
        "turbidite (NTU)": turbi,
        "fer (mg/L)": fer,
        "magnesium (mg/L)": mag,
        "chlore (mg/L)": chlore,
    }

    df = pd.DataFrame({
        "Test": TESTS,
        "Valeur mesurée": [values[t] for t in TESTS],
        "Seuil (max)": [normes[t] for t in TESTS],
    })
    df["Statut"] = [compute_status(v, s) for v, s in zip(df["Valeur mesurée"], df["Seuil (max)"])]

    # Verdict
    kind, message, detail = build_verdict(df)

    st.subheader("2) Verdict")
    if kind == "ok":
        st.markdown(f'<div class="okBox"><div class="big">{message}</div></div>', unsafe_allow_html=True)
    elif kind == "warn":
        st.markdown(f'<div class="warnBox"><div class="big">{message}</div><div class="muted">{detail or ""}</div></div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="badBox"><div class="big">{message}</div><div class="muted">{detail or ""}</div></div>', unsafe_allow_html=True)

    st.subheader("3) Détails (tableau)")
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.subheader("4) Export")
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Télécharger les résultats (CSV)", csv, file_name="qualite_eau_resultats.csv", mime="text/csv")
