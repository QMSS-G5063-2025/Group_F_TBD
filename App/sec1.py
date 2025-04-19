import json
import sys
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import pydeck as pdk
import streamlit as st

########################################
# global setting
########################################
# load local modules
BASE_DIR = Path(__file__).parent
sys.path.append(BASE_DIR)

from utils.data import load_data, load_shapefile
from utils.map import get_view_state
from utils.utils import get_color_map, NAME_MAPPING

DATA_BASE = BASE_DIR.parent / "data"

# set styling of control components
st.markdown(
    """
<style>
div[data-baseweb="slider"] {
    padding: 0 1rem;
}
div[data-baseweb="select"] {
    min-width: 240px;
}
</style>
""",
    unsafe_allow_html=True,
)


def render_sec1():
    # title
    st.title("Water Quality Change over Time")

    # read in data
    water_quality = load_data(DATA_BASE / "water_quality.csv")
    neighbourhood = load_shapefile(DATA_BASE / "raw_data/nynta2010_25a/nynta2010.shp")

    # visualize geometric info
    st.subheader("Water Quality of NYC")

    # add control components
    col1, col2, col3 = st.columns(3)

    with col1:
        selected_param = st.radio(
            "Water Quality Monitoring Indicators",
            options=["Residual_Chlorine", "Turbidity"],
            format_func=lambda x: NAME_MAPPING[x],
            index=0,
        )

    with col2:
        months = [
            f"{year}-{month:02d}"
            for year in range(2015, 2025)
            for month in range(1, 13)
            if not (year == 2024 and month > 12)
        ]
        selected_time = st.select_slider("Sample Time", options=months, value="2024-01")

    with col3:
        neighborhood_names = ["Whole NYC"] + sorted(water_quality["Neighbourhood"].unique().tolist())
        selected_area = st.selectbox(
            "Your Interested Area",
            options=neighborhood_names,
            index=0,
            help="Enter text to quickly filter the area",
        )

    subset = water_quality.loc[water_quality["year_month"] == selected_time]
    rgba_colors, colorbar_html = get_color_map(subset[selected_param], NAME_MAPPING[selected_param])
    subset["color"] = rgba_colors.tolist()

    # map layer
    ## help zoom in to interested area
    view_state = get_view_state(neighbourhood, selected_area)

    # polygon layer
    neighbourhood_json = json.loads(neighbourhood.to_json())
    polygon_layer = pdk.Layer(
        "GeoJsonLayer",
        neighbourhood_json,
        stroked=True,
        filled=True,
        extruded=False,
        opacity=0.6,
        get_fill_color=[200, 200, 200, 150],
        get_line_color=[100, 100, 100, 200],
        get_line_width=2,
        line_width_units="pixels",
        line_width_min_pixels=1,
        line_width_max_pixels=4,
        pickable=False,
    )

    # point layer
    point_layer = pdk.Layer(
        "ScatterplotLayer",
        data=subset,
        get_position=["longitude", "latitude"],
        get_radius=200,
        get_fill_color="color",
        pickable=True,
        auto_highlight=True,
    )

    # combine
    deck = pdk.Deck(
        layers=[polygon_layer, point_layer],
        initial_view_state=view_state,
        tooltip={
            "html": f"""
            <b>{NAME_MAPPING[selected_param]}: </b> {{{selected_param}}} <br/>
            <b>Neighbourhood: </b>{{Neighbourhood}}<br/>
            <b>Time: </b>{selected_time}
            """,
            "style": {
                "backgroundColor": "rgba(50, 50, 50, 0.9)",
                "color": "white",
                "fontFamily": "Arial",
                "padding": "10px",
            },
        },
        map_style="mapbox://styles/mapbox/light-v9",
    )

    st.pydeck_chart(deck)

    # set color bar
    st.markdown(colorbar_html, unsafe_allow_html=True)

    # preview raw data
    st.subheader("Data Preview")
    st.dataframe(water_quality[["year_month", "Residual_Chlorine", "Turbidity", "Neighbourhood"]])
