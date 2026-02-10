import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Contrôle qualité de l'eau", layout="wide")

# ---------- Styling ----------
st.markdown(
    """
    /* --- DARK FIX: tableaux lisibles --- */
div[data-testid="stDataFrame"] * {
  color: #ffffff !important;
}

div[data-testid="stDataFrame"] {
  background: #0e1117 !important;
  border-radius: 12px;
  padding: 6px;
}

div[data-testid="stDataEditor"] * {
  color: #ffffff !important;
}

div[data-testid="stDataEditor"] {
  background: #0e1117 !important;
  border-radius: 12px;
  padding: 6px;
}

/* entêtes colonnes */
div[data-testid="stDataFrame"] thead tr th,
div[data-testid="stDataEditor"] thead tr th{
  background: #111827 !important;
  color: #ffffff !important;
}

/* cellules */
div[data-testid="stDataFrame"] tbody tr td,
div[data-testid="stDataEditor"] tbody tr td{
  background: #1f2937 !important;
  color: #ffffff !important;
}

/* alternance lignes */
div[data-testid="stDataFrame"] tbody tr:nth-child(even) td,
div[data-testid="stDataEditor"] tbody tr:nth-child(even) td{
  background: #111827 !important;
}

/* On passe tes cards en dark (sinon elles restent blanches) */
.card {
  background: #0b1220 !important;
  border: 1px solid #1f2937 !important;
  color: #ffffff !important;
}

/* Texte général */
h1,h2,h3,h4,p,li,span,label {
  color: #ffffff !important;
}
    <style>
      .block-container {padding-top: 1.6rem; padding-bottom: 2rem;}
      h1 {letter-spacing: -0.5px;}
      .pill {display:inline-block; padding:6px 10px; border-radius:999px; font-weight:600; font-size:0.95rem;}
      .ok {background:#e8f5e9; color:#1b5e20; border:1px solid #a5d6a7;}
      .warn {background:#fff8e1; color:#e65100; border:1px solid #ffe082;}
      .bad {background:#ffebee; color:#b71c1c; border:1px solid #ef9a9a;}
      .miss {background:#eceff1; color:#263238; border:1px solid #cfd8dc;}
      .card {background:#ffffff; border:1px solid #e6e6e6; border-radius:14px; padding:16px; box-shadow: 0 1px 4px rgba(0,0,0,0.04);}
      .small {opacity:0.85; font-size:0.95rem;}
    </style>
    """,
    unsafe_allow_html=True
)

# ---------- Normes ----------
# IMPORTANT : j'ai mis des valeurs d'exemple (à adapter si tes normes MATLAB sont différentes).
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

def compute_status(value, seuil):
    """
    Logique type MATLAB:
    - 🟢 si value <= 0.9*seuil
    - 🟠 si 0.9*seuil < value <= seuil
    - 🔴 si value > seuil
    """
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "—"
    try:
        v = float(value)
    except Exception:
        return "Valeur invalide"
    limite_orange_inf = 0.9 * float(seuil)
    if v <= limite_orange_inf:
        return "🟢 Conforme"
    elif v <= float(seuil):
        return "🟠 Limite proche"
    else:
        return "🔴 Non conforme"

def status_pill(status: str) -> str:
    if status.startswith("🟢"):
        return '<span class="pill ok">🟢 Conforme</span>'
    if status.startswith("🟠"):
        return '<span class="pill warn">🟠 Limite proche</span>'
    if status.startswith("🔴"):
        return '<span class="pill bad">🔴 Non conforme</span>'
    if status == "—":
        return '<span class="pill miss">— Manquant</span>'
    return f'<span class="pill miss">{status}</span>'

def row_class(status: str):
    if status.startswith("🟢"):
        return "background-color: #e8f5e9;"
    if status.startswith("🟠"):
        return "background-color: #fff8e1;"
    if status.startswith("🔴"):
        return "background-color: #ffebee;"
    return "background-color: #eceff1;"

# ---------- Header ----------
st.title("💧 Contrôle qualité de l'eau")
st.markdown('<div class="small">Site crée par Wail, Marlon et Killian.</div>', unsafe_allow_html=True)

top_left, top_right = st.columns([2, 1], vertical_alignment="top")
with top_left:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        norme_type = st.selectbox("Type de normes", list(NORMES.keys()))
    with c2:
        eau_type = st.selectbox("Type d'eau", list(NORMES[norme_type].keys()))
    with c3:
        st.write("")
        st.write("")
        st.caption("Astuce : tu peux aussi importer un CSV de mesures (optionnel).")
    st.markdown("</div>", unsafe_allow_html=True)

with top_right:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Seuils utilisés")
    normes = NORMES[norme_type][eau_type]
    seuils_df = pd.DataFrame({"Test": list(normes.keys()), "Seuil (max)": list(normes.values())})
    st.dataframe(seuils_df, use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ---------- Inputs (table editable) ----------
st.subheader("1) Saisie des mesures")
upload = st.file_uploader("Importer un CSV (colonnes attendues : Test,Valeur mesurée)", type=["csv"])

if "df_input" not in st.session_state:
    st.session_state.df_input = pd.DataFrame({"Test": TESTS, "Valeur mesurée": [np.nan]*len(TESTS)})

if upload is not None:
    try:
        up = pd.read_csv(upload)
        up_cols = [c.strip().lower() for c in up.columns]
        # simple mapping
        def find_col(name):
            name = name.lower()
            for c in up.columns:
                if c.strip().lower() == name:
                    return c
            return None
        test_col = find_col("test")
        val_col  = None
        for candidate in ["valeur mesurée", "valeur", "mesure", "value"]:
            c = find_col(candidate)
            if c:
                val_col = c
                break
        if test_col and val_col:
            merged = st.session_state.df_input.copy()
            tmp = up[[test_col, val_col]].rename(columns={test_col:"Test", val_col:"Valeur mesurée"})
            # keep only known tests, align
            tmp["Test"] = tmp["Test"].astype(str)
            for t in TESTS:
                m = tmp[tmp["Test"].str.strip().str.lower() == t.strip().lower()]
                if not m.empty:
                    merged.loc[merged["Test"] == t, "Valeur mesurée"] = m.iloc[0]["Valeur mesurée"]
            st.session_state.df_input = merged
            st.success("CSV importé ✅")
        else:
            st.warning("CSV non reconnu. Il faut au minimum les colonnes: Test et Valeur mesurée (ou Valeur/Value).")
    except Exception as e:
        st.error(f"Impossible de lire le CSV: {e}")

edited = st.data_editor(
    st.session_state.df_input,
    use_container_width=True,
    num_rows="fixed",
    column_config={
        "Test": st.column_config.TextColumn(disabled=True),
        "Valeur mesurée": st.column_config.NumberColumn(format="%.6g")
    },
    hide_index=True
)
st.session_state.df_input = edited

# ---------- Compute ----------
df = edited.copy()
df["Seuil (max)"] = df["Test"].map(normes)
df["Statut"] = [compute_status(v, s) for v, s in zip(df["Valeur mesurée"], df["Seuil (max)"])]

# Summary counts
ok = int(df["Statut"].str.startswith("🟢").sum())
warn = int(df["Statut"].str.startswith("🟠").sum())
bad = int(df["Statut"].str.startswith("🔴").sum())
miss = int((df["Statut"] == "—").sum())

st.subheader("2) Résultats")

k1, k2, k3, k4 = st.columns(4)
k1.metric("🟢 Conforme", ok)
k2.metric("🟠 Limite proche", warn)
k3.metric("🔴 Non conforme", bad)
k4.metric("— Manquants", miss)

# Display styled table
show_df = df[["Test", "Valeur mesurée", "Seuil (max)", "Statut"]].copy()
styled = show_df.style.apply(lambda r: [row_class(r["Statut"])]*len(r), axis=1)

st.dataframe(styled, use_container_width=True, hide_index=True)



# ---------- Export ----------
st.subheader("4) Export")
csv = df.to_csv(index=False).encode("utf-8")
st.download_button("⬇️ Télécharger les résultats (CSV)", csv, file_name="qualite_eau_resultats.csv", mime="text/csv")
