import streamlit as st
from utils import definedge_get, definedge_post

def show():
    st.header("🔢 Margins & Span")
    st.subheader("Get Margin for Orders")
    # You can implement basket margin requests here

    st.subheader("Span Calculator")
    with st.form("span_calc"):
        positions = st.text_area("Positions JSON (as list)", value='[{}]')
        submit = st.form_submit_button("Calculate Span")
        if submit:
            try:
                import json
                pos_list = json.loads(positions)
                data = {"positions": pos_list}
                resp = definedge_post("/spancalculator", data)
                st.write(resp)
            except Exception as e:
                st.error(str(e))
