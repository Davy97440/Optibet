import streamlit as st
import json
import itertools
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Opti-Bet Miroir & Couverture", layout="wide", page_icon="🪞")

st.markdown("""
<style>
div[data-testid="stCheckbox"] {
    display: flex;
    justify-content: center;
}
.header-box {
    font-weight: bold;
    text-align: center;
    background-color: #1e293b;
    color: white;
    padding: 6px;
    border-radius: 4px;
}
</style>
""", unsafe_allow_html=True)

st.title("🪞 OPTI-BET — Système Favoris & Miroirs Outsiders")

# --- 1. IMPORT DU FICHIER JSON ---
with st.expander("📂 Importer ou coller la liste des matchs bruts", expanded=False):
    col_up, col_txt = st.columns([1, 1])
    with col_up:
        fichier_json = st.file_uploader("Fichier JSON brut", type=["json"])
    with col_txt:
        json_texte = st.text_area("Ou coller le JSON brut ici :", height=100)

matchs_bruts = []

if fichier_json is not None:
    try:
        data = json.load(fichier_json)
        matchs_bruts = data.get("matchs", data) if isinstance(data, dict) else data
    except Exception:
        st.error("Erreur de lecture du fichier JSON.")
elif json_texte.strip():
    try:
        data = json.loads(json_texte)
        matchs_bruts = data.get("matchs", data) if isinstance(data, dict) else data
    except Exception:
        st.error("JSON invalide dans la zone de texte.")

if not matchs_bruts:
    matchs_bruts = [
        {"id": 1, "match": "ADA Blois - Poitiers", "c1": 1.34, "cN": 11.0, "c2": 2.75},
        {"id": 2, "match": "Orléans - Rouen", "c1": 1.25, "cN": 13.0, "c2": 3.05},
        {"id": 3, "match": "Landerneau (F) - Angers (F)", "c1": 1.48, "cN": 10.0, "c2": 2.30},
        {"id": 4, "match": "Landes (F) - Villeneuve (F)", "c1": 1.15, "cN": 14.0, "c2": 3.95},
        {"id": 5, "match": "Unicaja - Tenerife", "c1": 1.30, "cN": 12.0, "c2": 2.90},
        {"id": 6, "match": "Manresa - Breogan", "c1": 1.49, "cN": 11.0, "c2": 2.25},
        {"id": 7, "match": "Napoli - Reggio Emilia", "c1": 1.23, "cN": 14.0, "c2": 3.30},
        {"id": 8, "match": "Bursaspor - Türk Telekom", "c1": 2.80, "cN": 12.0, "c2": 1.32}
    ]

# --- 2. CONFIGURATION MANUELLE DES ISSUES ---
st.subheader("1. Sélection manuelle des Favoris et Miroirs Outsiders")
st.caption("Pour chaque match, sélectionne quelle issue constitue le Favori et quelle issue constitue le Miroir Outsider.")

h_id, h_m, h_fav, h_out = st.columns([0.8, 3.5, 2.5, 2.5])
h_id.markdown("<div class='header-box'>N°</div>", unsafe_allow_html=True)
h_m.markdown("<div class='header-box'>Affiche</div>", unsafe_allow_html=True)
h_fav.markdown("<div class='header-box'>⭐ Issue Favori / Base</div>", unsafe_allow_html=True)
h_out.markdown("<div class='header-box'>💣 Issue Miroir Outsider</div>", unsafe_allow_html=True)

selection_favoris = []
selection_outsiders = []

for m in matchs_bruts:
    mid = m.get("id", 1)
    nom_m = m.get("match", f"Match {mid}")
    c1 = m.get("c1", 1.0)
    cn = m.get("cN", None)
    c2 = m.get("c2", 1.0)

    options = ["Aucun", f"1 (@{c1:.2f})"]
    if cn:
        options.append(f"N (@{cn:.2f})")
    options.append(f"2 (@{c2:.2f})")

    # Pré-sélections par défaut selon les cotes
    def_fav = 1 if c1 <= c2 else (len(options) - 1)
    def_out = (len(options) - 1) if def_fav == 1 else 1

    c_id, c_m, c_fav, c_out = st.columns([0.8, 3.5, 2.5, 2.5])
    c_id.write(f"**{mid}**")
    c_m.write(nom_m)

    choix_fav = c_fav.selectbox("Favori", options, index=def_fav, key=f"fav_{mid}", label_visibility="collapsed")
    choix_out = c_out.selectbox("Miroir", options, index=def_out, key=f"out_{mid}", label_visibility="collapsed")

    if choix_fav != "Aucun":
        signe = choix_fav.split()[0]
        cote = c1 if signe == "1" else (cn if signe == "N" else c2)
        selection_favoris.append({"id": mid, "match": nom_m, "signe": signe, "cote": float(cote)})

    if choix_out != "Aucun":
        signe = choix_out.split()[0]
        cote = c1 if signe == "1" else (cn if signe == "N" else c2)
        selection_outsiders.append({"id": mid, "match": nom_m, "signe": signe, "cote": float(cote)})

st.markdown("---")

# --- 3. PARAMÉTRAGE TOTAL DES DEUX UNIVERS ---
st.subheader("2. Paramétrage des Univers & Filtres")

col_par_fav, col_par_out = st.columns(2)

with col_par_fav:
    st.markdown("#### ⭐ Univers 1 : Système Favoris")
    nb_fav_dispos = max(1, len(selection_favoris))
    taille_bloc_fav = st.number_input("Taille des blocs de favoris", min_value=1, max_value=nb_fav_dispos, value=min(4, nb_fav_dispos))
    k_fav = st.number_input("Formule combinatoire Favoris (k)", min_value=1, max_value=int(taille_bloc_fav), value=min(2, int(taille_bloc_fav)))
    mise_fav = st.number_input("Mise par ticket Favori (€)", min_value=0.1, value=1.0, step=0.5)

with col_par_out:
    st.markdown("#### 💣 Univers 2 : Miroir Outsiders")
    c_min_out = st.number_input("Cote minimale de l'outsider", min_value=1.0, value=2.0, step=0.2)
    outsiders_filtres = [o for o in selection_outsiders if o["cote"] >= c_min_out]
    st.caption(f"{len(outsiders_filtres)} outsiders retenus après filtrage")
    
    nb_out_dispos = max(1, len(outsiders_filtres))
    k_out = st.number_input("Formule combinatoire Outsiders (k)", min_value=1, max_value=nb_out_dispos, value=min(3, nb_out_dispos))
    mise_out = st.number_input("Mise par ticket Outsider (€)", min_value=0.1, value=0.5, step=0.1)

st.markdown("---")

# --- 4. VÉRIFICATION DES RÉSULTATS RÉELS ---
st.subheader("3. Vérification des Résultats réels")
st.caption("Coche les issues qui sont passées pour vérifier simultanément tes deux univers :")

resultats_valides = set()
cols_verif = st.columns(min(len(matchs_bruts), 4) if matchs_bruts else 1)

for idx, m in enumerate(matchs_bruts):
    mid = m.get("id", 1)
    nom_m = m.get("match", f"Match {mid}")
    with cols_verif[idx % len(cols_verif)]:
        st.write(f"**{nom_m}**")
        if st.checkbox("1 gagné", key=f"res_1_{mid}"):
            resultats_valides.add((mid, "1"))
        if m.get("cN") and st.checkbox("N gagné", key=f"res_n_{mid}"):
            resultats_valides.add((mid, "N"))
        if st.checkbox("2 gagné", key=f"res_2_{mid}"):
            resultats_valides.add((mid, "2"))

st.markdown("---")

# --- 5. INITIALISATION DES LISTES ET CALCULS ---
tickets_fav = []
gains_fav = 0.0

tickets_out = []
gains_out = 0.0

# Génération Favoris (par blocs)
if selection_favoris and taille_bloc_fav > 0:
    blocs_fav = [selection_favoris[i:i + int(taille_bloc_fav)] for i in range(0, len(selection_favoris), int(taille_bloc_fav))]
    for b_idx, b in enumerate(blocs_fav, 1):
        if len(b) >= k_fav:
            combis = list(itertools.combinations(b, int(k_fav)))
            for c in combis:
                cote_t = 1.0
                for it in c:
                    cote_t *= it["cote"]
                gagne = all((it["id"], it["signe"]) in resultats_valides for it in c)
                gain_t = (cote_t * mise_fav) if gagne else 0.0
                gains_fav += gain_t
                tickets_fav.append({
                    "Univers": f"Favori (Bloc {b_idx})",
                    "Détail": " + ".join([f"{it['match']} [{it['signe']}]" for it in c]),
                    "Cote": round(cote_t, 2),
                    "Mise (€)": mise_fav,
                    "Statut": "✅ Gagné" if gagne else "❌ Perdu / En cours",
                    "Gain (€)": round(gain_t, 2)
                })

# Génération Outsiders
if len(outsiders_filtres) >= k_out:
    combis_out = list(itertools.combinations(outsiders_filtres, int(k_out)))
    for c in combis_out:
        cote_t = 1.0
        for it in c:
            cote_t *= it["cote"]
        gagne = all((it["id"], it["signe"]) in resultats_valides for it in c)
        gain_t = (cote_t * mise_out) if gagne else 0.0
        gains_out += gain_t
        tickets_out.append({
            "Univers": "Miroir Outsider",
            "Détail": " + ".join([f"{it['match']} [{it['signe']}]" for it in c]),
            "Cote": round(cote_t, 2),
            "Mise (€)": mise_out,
            "Statut": "✅ Gagné" if gagne else "❌ Perdu / En cours",
            "Gain (€)": round(gain_t, 2)
        })

# Synthèse financière consolidée
mise_totale_fav = len(tickets_fav) * mise_fav
mise_totale_out = len(tickets_out) * mise_out
mise_globale = mise_totale_fav + mise_totale_out
gain_global = gains_fav + gains_out
benefice_global = gain_global - mise_globale
roi_global = (benefice_global / mise_globale * 100) if mise_globale > 0 else 0.0

st.subheader("4
