import streamlit as st
import json
import itertools
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Opti-Bet Pro", layout="wide", page_icon="⚡")

st.title("⚡ OPTI-BET PRO — Optimisation & Systèmes Combinatoires")

# Sélections par défaut (directement intégrées)
SELECTIONS_DEFAUT = {
    "session": "Basketball Combiné",
    "blocs": [
        {
            "nom": "Bloc 1 - Euroligue Choc",
            "matchs": [
                {"id": 1, "nom": "Panathinaikos - Fenerbahce", "pari": "Panathinaikos", "cote": 1.38},
                {"id": 2, "nom": "Valence - Hapoel Tel-Aviv", "pari": "Valence Basket", "cote": 1.70},
                {"id": 3, "nom": "Real Madrid - Partizan", "pari": "Real Madrid", "cote": 1.14},
                {"id": 4, "nom": "Dubai - Étoile Rouge", "pari": "Dubai", "cote": 1.27},
                {"id": 5, "nom": "Bayern Munich - Virtus Bologne", "pari": "Bayern Munich", "cote": 1.27}
            ]
        },
        {
            "nom": "Bloc 2 - Championnats & Favoris",
            "matchs": [
                {"id": 6, "nom": "AS Karditsas - Vikos BC", "pari": "AS Karditsas", "cote": 1.28},
                {"id": 7, "nom": "Aris Salonique - AEK Athènes", "pari": "Aris Salonique", "cote": 1.28},
                {"id": 8, "nom": "B.C. Peristeri - Iraklis", "pari": "Peristeri", "cote": 1.33},
                {"id": 9, "nom": "Maroussi B.C. - AO Mykonos", "pari": "Maroussi B.C.", "cote": 1.48},
                {"id": 10, "nom": "Besiktas - Trabzonspor", "pari": "Besiktas", "cote": 1.32}
            ]
        },
        {
            "nom": "Bloc 3 - Mixte Euroligue & ABA",
            "matchs": [
                {"id": 11, "nom": "Paris Basketball - ASVEL", "pari": "Paris Basketball", "cote": 1.31},
                {"id": 12, "nom": "Olympiakos - Anadolu Efes", "pari": "Olympiakos", "cote": 1.13},
                {"id": 13, "nom": "FC Barcelone - Zalgiris", "pari": "FC Barcelone", "cote": 1.50},
                {"id": 14, "nom": "Baskonia - Besiktas", "pari": "Baskonia", "cote": 1.54},
                {"id": 15, "nom": "Zadar - Studentski Centar", "pari": "Zadar", "cote": 1.46}
            ]
        }
    ]
}

# --- BARRE SUPÉRIEURE ---
col_top1, col_top2 = st.columns([2, 1])

with col_top1:
    uploaded_file = st.file_uploader("📂 Importer un autre fichier (.json)", type=["json"])

with col_top2:
    mise_defaut = st.number_input("Mise unitaire par ticket (€)", min_value=0.1, value=1.0, step=0.1)

if uploaded_file is not None:
    try:
        data = json.load(uploaded_file)
        st.success("Fichier personnalisé chargé !")
    except Exception:
        st.error("Erreur de lecture, utilisation des matchs par défaut.")
        data = SELECTIONS_DEFAUT
else:
    data = SELECTIONS_DEFAUT

# --- NAVIGATION DES MODES ---
mode = st.radio(
    "Mode de calcul :",
    ["Mode 1 : Blocs Système 3/5 (Triples)", "Mode 2 : Blocs Doubles (k=2)", "Mode 3 : Grand Réducteur"],
    horizontal=True
)

st.markdown("---")

total_mise_session = 0.0
total_gain_session = 0.0
recap_export = []

cols_blocs = st.columns(min(len(data["blocs"]), 3))

for idx, bloc in enumerate(data["blocs"]):
    col_courante = cols_blocs[idx % 3]
    with col_courante:
        st.subheader(f"📌 {bloc.get('nom', f'Bloc {idx+1}')}")
        matchs = bloc.get("matchs", [])
        k = 3 if "Mode 1" in mode else 2
        
        gagnants = []
        for m in matchs:
            cle = f"m_{idx}_{m['id']}"
            label = f"{m['nom']} ({m.get('pari', 'O')} @ {m['cote']:.2f})"
            if st.checkbox(label, key=cle):
                gagnants.append(m)
        
        combis = list(itertools.combinations(matchs, k))
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
        
        st.write(f"**Gagnants :** {len(gagnants)} / {len(matchs)}")
        st.write(f"**Tickets payés :** {tickets_gagnes} / {nb_tickets}")
        net_bloc = gain_bloc - mise_bloc
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
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Synthèse Session', index=False)
    st.download_button(
        label="📥 Télécharger le suivi en Excel (.xlsx)",
        data=buffer.getvalue(),
        file_name="session_paris.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
