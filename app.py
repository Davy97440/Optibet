import streamlit as st
import json
import itertools
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Opti-Bet Grille Pro", layout="wide", page_icon="🎯")

st.markdown("""
<style>
div[data-testid="stCheckbox"] {
    display: flex;
    justify-content: center;
}
.grille-header {
    font-weight: bold;
    text-align: center;
    background-color: #1e293b;
    color: white;
    padding: 6px;
    border-radius: 4px;
}
</style>
""", unsafe_allow_html=True)

st.title("🎯 GRILLE DES PRONOSTICS & BRIQUES MODULAIRES")

# --- 1. IMPORT OU CHARGEMENT ---
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
        st.error("Erreur de lecture du fichier.")
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
        {"id": 3, "match": "ASVEL (F) - La TroncheM (F)", "c1": 1.02, "cN": 17.0, "c2": 6.25},
        {"id": 4, "match": "Landerneau (F) - Angers (F)", "c1": 1.48, "cN": 10.0, "c2": 2.30},
        {"id": 5, "match": "Landes (F) - Villeneuve (F)", "c1": 1.15, "cN": 14.0, "c2": 3.95},
        {"id": 6, "match": "Montpellier (F) - Bourges (F)", "c1": 1.62, "cN": 11.0, "c2": 2.05},
        {"id": 7, "match": "Toulouse (F) - Fla.Carolo (F)", "c1": 4.60, "cN": 14.0, "c2": 1.10},
        {"id": 8, "match": "Unicaja - Tenerife", "c1": 1.30, "cN": 12.0, "c2": 2.90}
    ]

NOMS_BRIQUES = [f"Brique {chr(65 + i)}" for i in range(20)]

# --- 2. GRILLE DE SÉLECTION STYLE PRONOSOFT ---
st.subheader("1. Grille interactive de sélection")

# En-tête du tableau
h_id, h_m, h_1, h_n, h_2, h_brk = st.columns([0.8, 4, 1.6, 1.6, 1.6, 2.2])
h_id.markdown("<div class='grille-header'>N°</div>", unsafe_allow_html=True)
h_m.markdown("<div class='grille-header'>Événement</div>", unsafe_allow_html=True)
h_1.markdown("<div class='grille-header'>1</div>", unsafe_allow_html=True)
h_n.markdown("<div class='grille-header'>N</div>", unsafe_allow_html=True)
h_2.markdown("<div class='grille-header'>2</div>", unsafe_allow_html=True)
h_brk.markdown("<div class='grille-header'>Affectation</div>", unsafe_allow_html=True)

briques_dict = {}

for m in matchs_bruts:
    mid = m.get("id", 1)
    nom_m = m.get("match", f"Match {mid}")
    c1 = m.get("c1", 1.0)
    cn = m.get("cN", None)
    c2 = m.get("c2", 1.0)

    c_id, c_match, c_1, c_n, c_2, c_brk = st.columns([0.8, 4, 1.6, 1.6, 1.6, 2.2])

    c_id.write(f"**{mid}**")
    c_match.write(nom_m)

    chk_1 = c_1.checkbox(f"{c1:.2f}", key=f"g1_{mid}")
    chk_n = c_n.checkbox(f"{cn:.2f}" if cn else "-", key=f"gn_{mid}", disabled=(cn is None))
    chk_2 = c_2.checkbox(f"{c2:.2f}", key=f"g2_{mid}")

    brk_target = c_brk.selectbox(
        "Brique",
        NOMS_BRIQUES,
        index=min(mid - 1, len(NOMS_BRIQUES) - 1),
        key=f"gbrk_{mid}",
        label_visibility="collapsed"
    )

    if chk_1:
        briques_dict.setdefault(brk_target, []).append({"match": nom_m, "signe": "1", "cote": float(c1)})
    if chk_n and cn:
        briques_dict.setdefault(brk_target, []).append({"match": nom_m, "signe": "N", "cote": float(cn)})
    if chk_2:
        briques_dict.setdefault(brk_target, []).append({"match": nom_m, "signe": "2", "cote": float(c2)})

# --- 3. CONSOLIDATION DES BRIQUES ---
st.markdown("---")
st.subheader("2. Briques formées")

liste_briques = []
for nom_b, items in briques_dict.items():
    if items:
        cote_b = 1.0
        details = []
        for it in items:
            cote_b *= it["cote"]
            details.append(f"{it['match']} [{it['signe']}@{it['cote']:.2f}]")
        liste_briques.append({
            "nom": nom_b,
            "nb_matchs": len(items),
            "description": " + ".join(details),
            "cote": round(cote_b, 2)
        })

if not liste_briques:
    st.info("💡 Coche au moins une case dans la grille pour former une brique.")
    st.stop()

df_briques = pd.DataFrame([
    {"Brique": b["nom"], "Contenu": b["description"], "Nb matchs": b["nb_matchs"], "Cote totale": b["cote"]}
    for b in liste_briques
])
st.dataframe(df_briques, use_container_width=True)

# --- 4. FILTRES SUR LES BRIQUES ---
st.markdown("---")
st.subheader("3. Filtres sur les briques")
cf1, cf2 = st.columns(2)
with cf1:
    c_min = cf1.number_input("Cote minimale acceptée", min_value=1.0, value=1.10, step=0.05)
with cf2:
    c_max = cf2.number_input("Cote maximale acceptée", min_value=1.0, value=30.0, step=0.5)

briques_valides = [b for b in liste_briques if c_min <= b["cote"] <= c_max]
st.write(f"👉 **{len(briques_valides)} brique(s) retenue(s)** après filtrage.")

if len(briques_valides) < 2:
    st.warning("Il faut au minimum deux briques validées pour créer des blocs et des tickets.")
    st.stop()

# --- 5. GESTION DES BLOCS ET FORMULES COMBINATOIRES ---
st.markdown("---")
st.subheader("4. Configuration des blocs et combinatoires")
cp1, cp2, cp3 = st.columns(3)

with cp1:
    taille_b = cp1.number_input("Nombre de briques par bloc", min_value=2, max_value=len(briques_valides), value=min(4, len(briques_valides)))
with cp2:
    k_val = cp2.number_input("Formule combinatoire (k)", min_value=1, max_value=int(taille_b), value=min(2, int(taille_b)), help="2 pour des doubles de briques, 3 pour des triples, etc.")
with cp3:
    mise = cp3.number_input("Mise unitaire par ticket (€)", min_value=0.1, value=1.0, step=0.1)

blocs_decoupes = [briques_valides[i:i + taille_b] for i in range(0, len(briques_valides), taille_b)]

# --- 6. RÉSULTATS & TICKETS ---
st.markdown("---")
st.subheader("5. Tickets finaux générés")

tickets_total = 0
export_lignes = []
num_ticket = 1

for idx, b_item in enumerate(blocs_decoupes, 1):
    combis = list(itertools.combinations(b_item, min(k_val, len(b_item))))
    tickets_total += len(combis)

    st.markdown(f"#### 📌 Bloc {idx} ({len(b_item)} briques) — Formule {k_val}/{len(b_item)} ({len(combis)} tickets)")
    with st.expander(f"Voir les tickets du Bloc {idx}", expanded=False):
        lignes = []
        for c in combis:
            cote_t = 1.0
            for b in c: cote_t *= b["cote"]
            gain_p = cote_t * mise
            lignes.append({
                "N°": num_ticket,
                "Briques": " × ".join([b["nom"] for b in c]),
                "Détail": " | ".join([f"({b['description']})" for b in c]),
                "Cote": round(cote_t, 2),
                "Mise (€)": mise,
                "Gain (€)": round(gain_p, 2)
            })
            export_lignes.append(lignes[-1])
            num_ticket += 1
        st.dataframe(pd.DataFrame(lignes), use_container_width=True)

# Bilan
c_bil1, c_bil2 = st.columns(2)
c_bil1.metric("Nombre total de tickets", tickets_total)
c_bil2.metric("Budget total nécessaire", f"{tickets_total * mise:.2f} €")

if export_lignes:
    df_exp = pd.DataFrame(export_lignes)
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df_exp.to_excel(writer, sheet_name="Tickets Opti-Bet", index=False)
    st.download_button(
        "📥 Exporter les tickets en Excel (.xlsx)",
        data=buf.getvalue(),
        file_name="tickets_grille_optibet.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
