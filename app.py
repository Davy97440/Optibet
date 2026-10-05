# Export Excel consolidé
tous_les_tickets = tickets_fav + tickets_out
if tous_les_tickets:
    df_bilan = pd.DataFrame(tous_les_tickets)
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df_bilan.to_excel(writer, sheet_name="Bilan Favoris Miroirs", index=False)
    st.download_button(
        "📥 Exporter le bilan complet en Excel (.xlsx)",
        data=buf.getvalue(),
        file_name="bilan_favoris_miroirs.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
