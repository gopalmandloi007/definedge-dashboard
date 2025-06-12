def show():
    # --- Load secrets
    api_token = st.secrets["integrate_api_token"]
    api_secret = st.secrets["integrate_api_secret"]
    uid = st.secrets["integrate_uid"]
    actid = st.secrets["integrate_actid"]
    api_session_key = st.secrets["integrate_api_session_key"]
    ws_session_key = st.secrets["integrate_ws_session_key"]

    conn = ConnectToIntegrate()
    conn.login(api_token, api_secret)
    conn.set_session_keys(uid, actid, api_session_key, ws_session_key)
    io = IntegrateOrders(conn)

    st.header("Holdings")
    try:
        holdings_book = io.holdings()
        st.write("DEBUG: holdings_book", holdings_book)  # <--- DEBUG LINE ADDED HERE
        if not holdings_book.get("data"):
            st.info("No holdings found or API returned: " + str(holdings_book))
        else:
            master_mapping = build_master_mapping_from_holdings(holdings_book)
            df_hold, summary = holdings_tabular(holdings_book, master_mapping, api_session_key)
            st.write("**Summary**")
            st.write(summary)
            st.write(f"**Total NSE Holdings: {len(df_hold)}**")
            st.dataframe(df_hold)
    except Exception as e:
        st.error(f"Failed to get holdings: {e}")
