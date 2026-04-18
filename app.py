import streamlit as st
from components.progress import init_progress
from modules import statements

st.set_page_config(page_title="ControllerSim", page_icon="📊", layout="wide")

init_progress()

page = st.sidebar.selectbox("Navigate", ["Module 1: Financial Statements"])

if page == "Module 1: Financial Statements":
    statements.render()
