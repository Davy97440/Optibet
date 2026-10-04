import streamlit as st
import json
import itertools
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Opti-Bet Briques Pro", layout="wide", page_icon="🧱")

st.title("🧱 OPTI-BET — Système de Briques Modulaires & Blocs")

# --- 1. IMPORT OU DONNÉES BRUTES ---
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
        {"id": 1, "match": "Panathinaikos - Fenerbahce", "c1": 1.38, "cN": 14.0, "c2": 2.25},
        {"id": 2, "match": "Valence - Hapoel Tel-Aviv", "c1": 1.70, "cN": 13.0, "c2": 1.72},
        {"id": 3, "match": "Real Madrid - Partizan", "c1": 1.14, "cN": 16.0, "c2": 3.50},
        {"id": 4, "match": "Dubai - Étoile Rouge", "c1": 1.27, "cN": 15.0, "c2": 2.65},
        {"id": 5, "match": "Bayern Munich - Virtus Bologne", "c1": 1.27, "cN": 15.0, "c2": 2.65},
        {"id": 6, "match": "Paris Basketball - ASVEL", "c1": 1.31, "cN": 14.0, "c2": 2.45},
        {"id": 7, "match": "ADA Blois - Poitiers", "c1": 1.34, "cN": 11.0, "c2": 2.75},
        {"id": 8, "match": "Orléans - Rouen", "c1": 1.25, "cN": 13.0, "c2": 3.05}
    ]

# Liste des identifiants de briques possibles
NOMS_BRIQUES = [f"Brique {chr(65 + i)}" for i in range(15)] # Brique A, Brique B, etc.

# --- 2. SÉLECTION DE L'ISSUE ET AFFECTATION AUX BRIQUES ---
st.subheader("1. Définir les issues et assembler les briques")
st.caption("Choisis l'issue de chaque match et affecte-le à une brique (mets plusieurs matchs dans la même brique pour créer un mini-combiné).")

briques_brutes = {}

for m in matchs_bruts:
    c1, c2, c3 = st.columns([3, 2, 2])
    nom_m = m.get("match", f"Match {m.get('id', '')}")
    c1_val = m.get("c1", 1.0)
    cn_val = m.get("cN", None)
    c2_val = m.get("c2", 1.0)

    options_issues = ["Ignorer", f"1 (@{c1_val:.2f})"]
    if cn_val:
        options_issues.append(f"N (@{cn_val:.2f})")
    options_issues.append(f"2 (@{c2_val:.2f})")

    with c1:
        st.write(f"**{nom_m}**")
    with c2:
        choix_issue = st.selectbox("Issue", options_issues, key=f"iss_{m.get('id', nom_m)}", label_visibility="collapsed")
    with c3:
        brique_choisie = st.selectbox("Affecter à", NOMS_BRIQUES, index=min(m.get("id", 1)-1, len(NOMS_BRIQUES)-1), key=f"brk_{m.get('id', nom_m)}", label_visibility="collapsed")

    if choix_issue != "Ignorer":
        if choix_issue.startswith("1"):
            signe, cote = "1", c1_val
        elif choix_issue.startswith("N"):
            signe, cote = "N", cn_val
        else:
            signe, cote = "2", c2_val

        element = {"match": nom_m, "signe": signe, "cote": float(cote)}
        briques_brutes.setdefault(brique_choisie, []).append(element)

# Consolidation des briques
liste_briques_construites = []
for nom_b, items in briques_brutes.items():
    if items:
        cote_brique = 1.0
        details = []
        for it in items:
            cote_brique *= it["cote"]
            details.append(f"{it['match']} [{it['signe']}@{it['cote']:.2f}]")
        
        liste_briques_construites.append({
            "nom": nom_b,
            "nb_matchs": len(items),
            "description": " + ".join(details),
            "cote": round(cote_brique, 2)
        })

# Affichage des briques construites
if liste_briques_construites:
    st.markdown("#### Briques formées :")
    df_briques_view = pd.DataFrame([
        {"Brique": b["nom"], "Contenu": b["description"], "Nb matchs": b["nb_matchs"], "Cote totale": b["cote"]}
        for b in liste_briques_construites
    ])
    st.dataframe(df_briques_view, use_container_width=True)
else:
    st.info("Aucun match sélectionné pour le moment.")
    st.stop()

st.markdown("---")

# --- 3. FILTRES SUR LES BRIQUES ---
st.subheader("2. Filtres sur les briques")
c_f1, c_f2 = st.columns(2)
with c_f1:
    cote_brique_min = st.number_input("Cote minimale de la brique", min_value=1.0, value=1.10, step=0.05)
with c_f2:
    cote_brique_max = st.number_input("Cote maximale de la brique", min_value=1.0, value=20.0, step=0.5)

briques_filtrees = [b for b in liste_briques_construites if cote_brique_min <= b["cote"] <= cote_brique_max]
st.info(f"**{len(briques_filtrees)} brique(s) validée(s)** après filtrage de cote.")

if len(briques_filtrees) < 2:
    st.warning("Il faut au minimum deux briques validées pour former des blocs et des combinés.")
    st.stop()

st.markdown("---")

# --- 4. CONFIGURATION DES BLOCS & COMBINAISONS ---
st.subheader("3. Configuration des Blocs et Formats de jeu")
c_p1, c_p2, c_p3 = st.columns(3)

with c_p1:
    taille_bloc = st.number_input(
        "Nombre de briques par bloc",
        min_value=2,
        max_value=len(briques_filtrees),
        value=min(4, len(briques_filtrees))
    )
with c_p2:
    k_combinaison = st.number_input(
        "Formule combinatoire (k)",
        min_value=1,
        max_value=int(taille_bloc),
        value=min(2, int(taille_bloc)),
        help="Exemple : 2 pour des doubles de briques, 3 pour des triples de briques"
    )
with c_p3:
    mise_ticket = st.number_input("Mise par ticket (€)", min_value=0.1, value=1.0, step=0.1)

# Découpage des briques en blocs
blocs = [briques_filtrees[i:i + taille_bloc] for i in range(0, len(briques_filtrees), taille_bloc)]

# --- 5. GÉNÉRATION DES COMBINAISONS ---
st.markdown("---")
st.subheader("4. Récapitulatif et Tickets générés")

total_tickets = 0
recap_export = []
num_ticket_global = 1

for idx_b, bloc in enumerate(blocs, 1):
    combis_bloc = list(itertools.combinations(bloc, min(k_combinaison, len(bloc))))
    nb_t = len(combis_bloc)
    total_tickets += nb_t

    st.markdown(f"#### 📌 Bloc {idx_b} ({len(bloc)} briques) — Formule {k_combinaison}/{len(bloc)} ({nb_t} tickets)")

    with st.expander(f"Détail des tickets du Bloc {idx_b}", expanded=False):
        lignes = []
        for c in combis_bloc:
            nom_combis = " × ".join([b["nom"] for b in c])
            detail_combi = " | ".join([f"({b['description']})" for b in c])
            cote_ticket = 1.0
            for b in c:
                cote_ticket *= b["cote"]
            gain_pot = cote_ticket * mise_ticket

            lignes.append({
                "N°": num_ticket_global,
                "Briques": nom_combis,
                "Détail": detail_combi,
                "Cote": round(cote_ticket, 2),
                "Mise (€)": mise_ticket,
                "Gain Potentiel (€)": round(gain_pot, 2)
            })
            recap_export.append(lignes[-1])
            num_ticket_global += 1

        st.dataframe(pd.DataFrame(lignes), use_container_width=True)

# --- 6. BILAN & EXPORT EXCEL ---
st.markdown("---")
c_bilan1, c_bilan2 = st.columns(2)
c_bilan1.metric("Nombre total de tickets générés", total_tickets)
c_bilan2.metric("Mise totale engagée", f"{total_tickets * mise_ticket:.2f} €")

if recap_export:
    df_export = pd.DataFrame(recap_export)
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df_export.to_excel(writer, sheet_name="Tickets Briques", index=False)
    st.download_button(
        "📥 Exporter tous les tickets en Excel (.xlsx)",
        data=buf.getvalue(),
        file_name="mes_tickets_briques.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
