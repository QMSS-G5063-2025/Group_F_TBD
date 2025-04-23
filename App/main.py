import sys
from pathlib import Path

import streamlit as st

########################################
# global setting
########################################
st.set_page_config(layout="wide")

if "current_section" not in st.session_state:
    st.session_state.current_section = "Home"

# load local modules
BASE_DIR = Path(__file__).parent
sys.path.append(BASE_DIR)

from home import render_home
from sec1 import render_sec1
from sec2 import render_sec2

########################################
# layout
########################################
with st.sidebar:
    st.title("Explorer")
    sections = {"Home": "🏠", "Water Quality Change over Time": "📈", "Water Quality and Health": "📊", "Section3": "📋"}

    for section, icon in sections.items():
        if st.button(f"{icon} {section}"):
            st.session_state.current_section = section

if st.session_state.current_section == "Home":
    render_home()
elif st.session_state.current_section == "Water Quality Change over Time":
    render_sec1()
elif st.session_state.current_section == "Water Quality and Health":
    render_sec2()
