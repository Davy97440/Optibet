import streamlit as st
import json
import itertools
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Opti-Bet Pro", layout="wide", page_icon="⚡")

# Initialisation de la mémoire de session
if "blocs" not in st.session_state:
    st.session_state["blocs"] = [
        {"nom": "Bloc 1", "matchs": []},
        {"nom": "Bloc 2", "matchs": []},
        {"nom": "Bloc 3", "matchs": []}
    ]

st.title("⚡ OPTI-BET PRO — Optimisation & Systèmes")

# --- PANNEAU DE CONFIGURATION & SAISIE ---
with st.expander("🛠️ Gestion des sélections (Ajout / Import)", expanded=False):
    tab_saisie, tab_coller, tab_fichier = st.tabs(["✍️ Ajouter un match", "📋 Coller du JSON", "📂 Fichier"])

    # 1. Ajout manuel direct
    with tab_saisie:
        col_b, col_m, col_p, col_c = st.columns([1.5, 2.5, 1.5, 1])
        bloc_cible = col_b.selectbox("Bloc", [b["nom"] for b in st.session_state["blocs"]], key="sel_bloc")
        match_nom = col_m.text_input("Affiche (ex: Paris - ASVEL)", key="nom_in")
        pari_nom = col_p.text_input("Pronostic (ex: Paris)", key="pari_in")
        cote_val = col_c.number_input("Cote", min_value=1.01, value=1.50, step=0.05, key="cote_in")

        if st.button("➕ Ajouter ce match"):
            if match_nom.strip():
                for b in st.session_state["blocs"]:
                    if b["nom"] == bloc_cible:
                        nouvel_id = len(b["matchs"]) + 1
                        b["matchs"].append({
                            "id": nouvel_id,
                            "nom": match_nom.strip(),
                            "pari": pari_nom.strip() or "1",
                            "cote": float(cote_val)
                        })
                st.rerun()

    # 2. Collage texte JSON
    with tab_coller:
        json_texte = st.text_area("Colle ici le texte JSON généré :", height=120)
        if st.button("Valider le texte JSON"):
            try:
                donnees = json.loads(json_texte)
                if "blocs" in donnees:
                    st.session_state["blocs"] = donnees["blocs"]
                    st.success("Sélections mises à jour avec succès !")
                    st.rerun()
                else:
                    st.error("Format invalide : clé 'blocs' introuvable.")
            except Exception as e:
                st.error(f"Erreur d'analyse JSON : {e}")

    # 3. Import par fichier classique
    with tab_fichier:
        f_up = st.file_uploader("Fichier JSON", type=["json"], label_visibility="collapsed")
        if f_up is not None:
            try:
                donnees = json.load(f_up)
                if "blocs" in donnees:
                    st.session_state["blocs"] = donnees["blocs"]
                    st.success("Fichier chargé !")
                    st.rerun()
            except Exception:
                st.error("Impossible de lire ce fichier.")

    # Bouton de remise à zéro
    if st.button("🗑️ Réinitialiser tous les blocs"):
        st.session_state["blocs"] = [
            {"nom": "Bloc 1", "matchs": []},
            {"nom": "Bloc 2", "matchs": []},
            {"nom": "Bloc 3", "matchs": []}
        ]
        st.rerun()

# --- PARAMÈTRES GÉNÉRAUX ---
col_param1, col_param2 = st.columns([2, 1])

with col_param1:
    mode = st.radio(
        "Mode de calcul combinatoire :",
        ["Mode 1 : Blocs Système 3/5 (Triples)", "Mode 2 : Blocs Doubles (k=2)", "Mode 3 : Grand Réducteur"],
        horizontal=True
    )

with col_param2:
    mise_defaut = st.number_input("Mise unitaire par ticket (€)", min_value=0.1, value=1.0, step=0.1)

st.markdown("---")

# --- CALCULS ET AFFICHAGE DES BLOCS ---
total_mise_session = 0.0
total_gain_session = 0.0
recap_export = []

blocs_actifs = [b for b in st.session_state["blocs"] if b.get("matchs")]

if not blocs_actifs:
    st.info("💡 Aucun match dans la grille. Ouvre le volet « 🛠️ Gestion des sélections » ci-dessus pour ajouter des matchs ou coller une sélection.")
else:
    cols_blocs = st.columns(min(len(blocs_actifs), 3))

    for idx, bloc in enumerate(blocs_actifs):
        col_courante = cols_blocs[idx % 3]
        with col_courante:
            st.subheader(f"📌 {bloc.get('nom', f'Bloc {idx+1}')}")
            matchs = bloc.get("matchs", [])
            k = 3 if "Mode 1" in mode else 2

            gagnants = []
            for m in matchs:
                cle = f"chk_{idx}_{m['id']}"
                label = f"{m['nom']} ({m.get('pari', '')} @ {m['cote']:.2f})"
                if st.checkbox(label, key=cle):
                    gagnants.append(m)

            combis = list(itertools.combinations(matchs, min(k, len(matchs)))) if len(matchs) >= k else []
            nb_tickets = len(combis)
            mise_bloc = nb_tickets * mise_defaut
            total_mise_session += mise_bloc

            gain_bloc = 0.0
            tickets_gagnes = 0

            for c in combis:
                if all(item in gagnants for item in c):
                    tickets_gagnes += 1
                    cote_ticket = 1.0
                    for item in c:
                        cote_ticket *= item["cote"]
                    gain_bloc += mise_defaut * cote_ticket

            total_gain_session += gain_bloc
            net_bloc = gain_bloc - mise_bloc

            st.write(f"**Gagnants :** {len(gagnants)} / {len(matchs)}")
            st.write(f"**Tickets payés :** {tickets_gagnes} / {nb_tickets}")
            st.metric("Résultat du Bloc", f"{gain_bloc:.2f} €", delta=f"{net_bloc:+.2f} €")

            recap_export.append({
                "Bloc": bloc.get("nom", f"Bloc {idx+1}"),
                "Matchs Gagnants": f"{len(gagnants)}/{len(matchs)}",
                "Tickets Payés": f"{tickets_gagnes}/{nb_tickets}",
                "Mise (€)": mise_bloc,
                "Gain Brut (€)": round(gain_bloc, 2),
                "Net (€)": round(net_bloc, 2)
            })

    # --- SYNTHÈSE GLOBALE ---
    st.markdown("---")
    st.header("📊 Bilan Financier de la Session")
    net_global = total_gain_session - total_mise_session
    roi = (net_global / total_mise_session * 100) if total_mise_session > 0 else 0.0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Capital Engagé", f"{total_mise_session:.2f} €")
    c2.metric("Gains Bruts", f"{total_gain_session:.2f} €")
    c3.metric("Bénéfice Net", f"{net_global:+.2f} €")
    c4.metric("ROI", f"{roi:+.1f} %")

    if recap_export:
        df = pd.DataFrame(recap_export)
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="Synthèse Session", index=False)
        st.download_button(
            label="📥 Télécharger le suivi en Excel (.xlsx)",
            data=buffer.getvalue(),
            file_name="bilan_session.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
