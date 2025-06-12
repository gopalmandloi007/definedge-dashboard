import streamlit as st

st.set_page_config(
    page_title="Streamlit Config Test",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("Streamlit Config Test")
st.write("If you see this message and NO set_page_config error, everything is working fine!")

if st.button("Click me"):
    st.success("Button click works!")
