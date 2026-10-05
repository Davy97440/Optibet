import streamlit as st
import json
import itertools
import io
import math
import pandas as pd

st.set_page_config(page_title="Opti-Bet Miroir Pro", layout="wide", page_icon="🪞")

if "resultats_valides" not in st.session_state:
    st.session_state.resultats_valides = []

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

st.title("🪞 OPTI-BET — Favoris & Miroirs Outsiders Pro")

# --- 1. GESTION DE SESSION & IMPORT ---
with st.expander("📂 Gestion de session & Import des matchs", expanded=False):
    tab_imp1, tab_imp2 = st.tabs(["Charger session complète", "Importer matchs bruts"])
    
    with tab_imp1:
        f_session = st.file_uploader("Restaurer une session sauvegardée (.json)", type=["json"], key="session_loader")
        if f_session:
            try:
                sess_data = json.load(f_session)
                st.session_state.resultats_valides = sess_data.get("resultats", [])
                st.success("Session rechargée avec succès.")
            except Exception:
                st.error("Fichier de session invalide.")
                
    with tab_imp2:
        c_up, c_txt = st.columns(2)
        f_matchs = c_up.file_uploader("Fichier JSON brut", type=["json"], key="matchs_loader")
        txt_matchs = c_txt.text_area("Coller JSON brut :", height=80)

matchs_bruts = []
if f_matchs:
    try:
        data = json.load(f_matchs)
        matchs_bruts = data.get("matchs", data) if isinstance(data, dict) else data
    except Exception:
        st.error("Erreur lecture fichier.")
elif txt_matchs.strip():
    try:
        data = json.loads(txt_matchs)
        matchs_bruts = data.get("matchs", data) if isinstance(data, dict) else data
    except Exception:
        st.error("JSON texte invalide.")

if not matchs_bruts:
    matchs_bruts = [
        {"id": 1, "match": "Baskonia - Girona", "c1": 1.12, "cN": 15.0, "c2": 4.20},
        {"id": 2, "match": "Obradoiro - Real Madrid", "c1": 3.95, "cN": 16.0, "c2": 1.14},
        {"id": 3, "match": "Cayirova - Bahcesehir Kol", "c1": 4.70, "cN": 15.0, "c2": 1.09},
        {"id": 4, "match": "Virtus Bologne - Maxima Roma", "c1": 1.19, "cN": 14.0, "c2": 3.60},
        {"id": 5, "match": "Gravelines - Asvel", "c1": 3.00, "cN": 14.0, "c2": 1.28},
        {"id": 6, "match": "Pistoia - Basket Torino", "c1": 1.34, "cN": 12.0, "c2": 2.60},
        {"id": 7, "match": "Lleida - SP Burgos", "c1": 1.27, "cN": 13.0, "c2": 3.00},
        {"id": 8, "match": "Juve Caserta - Forti. Bologna", "c1": 2.75, "cN": 12.0, "c2": 1.30}
    ]

# --- 2. SÉLECTION DES ISSUES ---
st.subheader("1. Sélection Favoris et Miroirs Outsiders")

h_id, h_m, h_fav, h_out = st.columns([0.8, 3.5, 2.5, 2.5])
h_id.markdown("<div class='header-box'>N°</div>", unsafe_allow_html=True)
h_m.markdown("<div class='header-box'>Affiche</div>", unsafe_allow_html=True)
h_fav.markdown("<div class='header-box'>⭐ Issue Favori / Base</div>", unsafe_allow_html=True)
h_out.markdown("<div class='header-box'>💣 Issue Miroir Outsider</div>", unsafe_allow_html=True)

selection_fav = []
selection_out = []

for m in matchs_bruts:
    mid = m.get("id", 1)
    nom_m = m.get("match", f"Match {mid}")
    c1, cn, c2 = m.get("c1", 1.0), m.get("cN"), m.get("c2", 1.0)

    opts = ["Aucun", f"1 (@{c1:.2f})"]
    if cn:
        opts.append(f"N (@{cn:.2f})")
    opts.append(f"2 (@{c2:.2f})")

    def_fav = 1 if c1 <= c2 else len(opts) - 1
    def_out = (len(opts) - 1) if def_fav == 1 else 1

    c_id, c_m, c_f, c_o = st.columns([0.8, 3.5, 2.5, 2.5])
    c_id.write(f"**{mid}**")
    c_m.write(nom_m)

    ch_fav = c_f.selectbox("Fav", opts, index=def_fav, key=f"f_{mid}", label_visibility="collapsed")
    ch_out = c_o.selectbox("Out", opts, index=def_out, key=f"o_{mid}", label_visibility="collapsed")

    if ch_fav != "Aucun":
        s = ch_fav.split()[0]
        cote = c1 if s == "1" else (cn if s == "N" else c2)
        selection_fav.append({"id": mid, "match": nom_m, "signe": s, "cote": float(cote)})

    if ch_out != "Aucun":
        s = ch_out.split()[0]
        cote = c1 if s == "1" else (cn if s == "N" else c2)
        selection_out.append({"id": mid, "match": nom_m, "signe": s, "cote": float(cote)})

st.markdown("---")

# --- 3. PARAMÉTRAGE & AMORTISSEMENT ---
st.subheader("2. Paramètres des Univers & Couverture")

col_pf, col_po = st.columns(2)

with col_pf:
    st.markdown("#### ⭐ Univers Favoris")
    nb_fav = max(1, len(selection_fav))
    t_bloc_fav = st.number_input("Taille des blocs Favoris", 1, nb_fav, min(8, nb_fav))
    k_fav = st.number_input("Formule combinatoire Favoris (k)", 1, int(t_bloc_fav), min(int(t_bloc_fav), int(t_bloc_fav)))
    mise_fav = st.number_input("Mise unitaire Favoris (€)", 0.1, 500.0, 1.0, 0.5)

with col_po:
    st.markdown("#### 💣 Univers Miroir Outsiders")
    miroirs_par_bloc = st.toggle("🔒 Générer les miroirs par bloc (Recommandé)", value=True, help="Si activé, chaque bloc de favoris crée ses propres combinés miroirs indépendamment.")
    c_min_out = st.number_input("Cote minimale Outsider", 1.0, 50.0, 2.0, 0.2)
    outs_filtres = [o for o in selection_out if o["cote"] >= c_min_out]
    
    if miroirs_par_bloc:
        max_k_possible = int(t_bloc_fav)
    else:
        max_k_possible = max(1, len(outs_filtres))

    k_out = st.number_input("Formule combinatoire Outsiders (k)", 1, max_k_possible, min(int(t_bloc_fav) if miroirs_par_bloc else 3, max_k_possible))
    mise_out = st.number_input("Mise unitaire Outsiders (€)", 0.1, 500.0, 0.5, 0.1)

# --- 4. VÉRIFICATION DES RÉSULTATS ---
st.markdown("---")
st.subheader("3. Vérification des Résultats réels")

c_btn1, c_btn2, c_btn3 = st.columns(3)
if c_btn1.button("⚡ Scénario 100 % Favoris"):
    st.session_state.resultats_valides = [f"{f['id']}_{f['signe']}" for f in selection_fav]
    st.rerun()

if c_btn2.button("💣 Scénario 100 % Outsiders"):
    st.session_state.resultats_valides = [f"{o['id']}_{o['signe']}" for o in selection_out]
    st.rerun()

if c_btn3.button("🔄 Réinitialiser les résultats"):
    st.session_state.resultats_valides = []
    st.rerun()

cols_v = st.columns(min(len(matchs_bruts), 4) if matchs_bruts else 1)
for i, m in enumerate(matchs_bruts):
    mid = m.get("id", 1)
    nom_m = m.get("match", "")
    with cols_v[i % len(cols_v)]:
        st.write(f"**{nom_m}**")
        for s, label in [("1", "1"), ("N", "N"), ("2", "2")]:
            if s == "N" and not m.get("cN"):
                continue
            cle = f"{mid}_{s}"
            coche = cle in st.session_state.resultats_valides
            nouveau_statut = st.checkbox(f"{label} gagné", value=coche, key=f"chk_{cle}")
            if nouveau_statut and cle not in st.session_state.resultats_valides:
                st.session_state.resultats_valides.append(cle)
                st.rerun()
            elif not nouveau_statut and cle in st.session_state.resultats_valides:
                st.session_state.resultats_valides.remove(cle)
                st.rerun()

# --- 5. GÉNÉRATION DES COMBINAISONS ---
tickets_fav, gains_fav = [], 0.0
tickets_out, gains_out = [], 0.0

# Favoris
if selection_fav and t_bloc_fav > 0:
    blocs_fav = [selection_fav[i:i + int(t_bloc_fav)] for i in range(0, len(selection_fav), int(t_bloc_fav))]
    for b_idx, b in enumerate(blocs_fav, 1):
        if len(b) >= k_fav:
            for c in itertools.combinations(b, int(k_fav)):
                if len(set(it["id"] for it in c)) != len(c):
                    continue
                cote_t = 1.0
                for it in c:
                    cote_t *= it["cote"]
                gagne = all(f"{it['id']}_{it['signe']}" in st.session_state.resultats_valides for it in c)
                g = (cote_t * mise_fav) if gagne else 0.0
                gains_fav += g
                tickets_fav.append({
                    "Univers": f"Fav (B{b_idx})",
                    "Détail": " + ".join([f"{it['match']} [{it['signe']}]" for it in c]),
                    "Cote": round(cote_t, 2),
                    "Mise (€)": mise_fav,
                    "Statut": "✅ Gagné" if gagne else "❌ En attente / Perdu",
                    "Gain (€)": round(g, 2)
                })

# Outsiders
if miroirs_par_bloc and t_bloc_fav > 0:
    # Génération par blocs synchronisés avec les favoris
    for b_idx, b_fav in enumerate(blocs_fav, 1):
        ids_du_bloc = set(it["id"] for it in b_fav)
        outs_du_bloc = [o for o in outs_filtres if o["id"] in ids_du_bloc]
        if len(outs_du_bloc) >= k_out:
            for c in itertools.combinations(outs_du_bloc, int(k_out)):
                if len(set(it["id"] for it in c)) != len(c):
                    continue
                cote_t = 1.0
                for it in c:
                    cote_t *= it["cote"]
                gagne = all(f"{it['id']}_{it['signe']}" in st.session_state.resultats_valides for it in c)
                g = (cote_t * mise_out) if gagne else 0.0
                gains_out += g
                tickets_out.append({
                    "Univers": f"Miroir (B{b_idx})",
                    "Détail": " + ".join([f"{it['match']} [{it['signe']}]" for it in c]),
                    "Cote": round(cote_t, 2),
                    "Mise (€)": mise_out,
                    "Statut": "✅ Gagné" if gagne else "❌ En attente / Perdu",
                    "Gain (€)": round(g, 2)
                })
else:
    # Génération globale sans blocs
    if len(outs_filtres) >= k_out:
        for c in itertools.combinations(outs_filtres, int(k_out)):
            if len(set(it["id"] for it in c)) != len(c):
                continue
            cote_t = 1.0
            for it in c:
                cote_t *= it["cote"]
            gagne = all(f"{it['id']}_{it['signe']}" in st.session_state.resultats_valides for it in c)
            g = (cote_t * mise_out) if gagne else 0.0
            gains_out += g
            tickets_out.append({
                "Univers": "Miroir Global",
                "Détail": " + ".join([f"{it['match']} [{it['signe']}]" for it in c]),
                "Cote": round(cote_t, 2),
                "Mise (€)": mise_out,
                "Statut": "✅ Gagné" if gagne else "❌ En attente / Perdu",
                "Gain (€)": round(g, 2)
            })

# --- 6. BILAN FINANCIER & EXPORTS ---
st.markdown("---")
st.subheader("4. Bilan Financier Consolidé")

mise_tot_f = len(tickets_fav) * mise_fav
mise_tot_o = len(tickets_out) * mise_out
mise_globale = mise_tot_f + mise_tot_o
gain_global = gains_fav + gains_out
benefice = gain_global - mise_globale
roi = (benefice / mise_globale * 100) if mise_globale > 0 else 0.0

m1, m2, m3, m4 = st.columns(4)
m1.metric("Capital Engagé", f"{mise_globale:.2f} €", f"Fav: {mise_tot_f:.2f}€ | Out: {mise_tot_o:.2f}€")
m2.metric("Gains Favoris", f"{gains_fav:.2f} €", f"{sum(1 for t in tickets_fav if '✅' in t['Statut'])}/{len(tickets_fav)} payés")
m3.metric("Gains Outsiders", f"{gains_out:.2f} €", f"{sum(1 for t in tickets_out if '✅' in t['Statut'])}/{len(tickets_out)} payés")
m4.metric("Bénéfice Net", f"{benefice:+.2f} €", delta=f"{roi:+.1f} % ROI")

tab1, tab2 = st.tabs([f"⭐ Tickets Favoris ({len(tickets_fav)})", f"💣 Tickets Outsiders ({len(tickets_out)})"])
with tab1:
    if tickets_fav:
        st.dataframe(pd.DataFrame(tickets_fav), use_container_width=True)
with tab2:
    if tickets_out:
        st.dataframe(pd.DataFrame(tickets_out), use_container_width=True)

st.markdown("---")
c_exp1, c_exp2 = st.columns(2)

tous_tickets = tickets_fav + tickets_out
if tous_tickets:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        pd.DataFrame(tous_tickets).to_excel(w, sheet_name="Bilan_Paris", index=False)
    c_exp1.download_button(
        "📥 Exporter les tickets en Excel (.xlsx)",
        data=buf.getvalue(),
        file_name="bilan_paris_miroirs.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

etat_session = {
    "parametres": {
        "taille_bloc_fav": t_bloc_fav,
        "k_fav": k_fav,
        "mise_fav": mise_fav,
        "miroirs_par_bloc": miroirs_par_bloc,
        "k_out": k_out,
        "mise_out": mise_out,
        "cote_min_out": c_min_out
    },
    "resultats": st.session_state.resultats_valides
}
c_exp2.download_button(
    "💾 Sauvegarder la session (.json)",
    data=json.dumps(etat_session, indent=2),
    file_name="session_optibet.json",
    mime="application/json"
)
