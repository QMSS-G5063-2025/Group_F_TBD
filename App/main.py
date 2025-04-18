import streamlit as st
import pandas as pd
from pathlib import Path

current_dir = Path(__file__).parent
data_dir = current_dir.parent / "data"


water_quality = pd.read_csv(data_dir / "water_quality.csv", index_col=0)
demographic = pd.read_csv(data_dir / "nta_health_demographic.csv")

st.write("Simple visualize the dataframe")
st.dataframe(water_quality)
