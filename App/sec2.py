import json
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import pydeck as pdk
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder
from statsmodels.nonparametric.smoothers_lowess import lowess
from shapely.geometry import mapping

########################################
# global setting
########################################
# load local modules
BASE_DIR = Path(__file__).parent
sys.path.append(BASE_DIR)

from utils.data import load_data, load_shapefile
from utils.map import get_view_state
from utils.utils import NAME_MAPPING, HEALTH_MAPPING, get_color_map, reset_view, select_subset

DATA_BASE = BASE_DIR.parent / "data"


def render_sec2():
    # title
    st.title("Water Quality and Health Outcomes")

    # set subset global
    if "view_subset" not in st.session_state:
        st.session_state.view_subset = False
    if "selection_criteria" not in st.session_state:
        st.session_state.selection_criteria = {}
    if "active_view" not in st.session_state:
        st.session_state.active_view = None
    st.markdown(
        """
    <style>
        div[data-testid="stButton"] > button[kind="secondary"]:disabled {
            opacity: 1;
            border-color: #f63366;
            background-color: #ff4b4b;
            color: white;
        }
    </style>
    """,
        unsafe_allow_html=True,
    )

    ########################################
    # read in data
    ########################################
    water_quality = load_data(DATA_BASE / "water_quality.csv")
    nta_health = load_data(DATA_BASE / "nta_health_demographic.csv")
    neighbourhood = load_shapefile(DATA_BASE / "raw_data/nynta2010_25a/nynta2010.shp")

    print(neighbourhood.head())
    neighborhood_health_merged = pd.merge(left= nta_health, right= neighbourhood,
                                          left_on="NTA_Code", right_on= "NTACode",
                                          how = "left")
    
    NEIGHBOUR_NAME = ["Whole NYC"] + sorted(water_quality["Neighbourhood"].unique().tolist())


    water_quality = water_quality[water_quality["year"]==2015]
    water_quality = (
    water_quality
    .groupby("Sample.Number")
    .agg({col: "mean" if pd.api.types.is_numeric_dtype(dtype) else "first"
          for col, dtype in water_quality.dtypes.items() if col!="Sample.Number"})
    .reset_index()
    )

    
    ########################################
    # plot map
    ########################################
    st.subheader("Water Quality of NYC")

    # add control components
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            "<p style='font-size:17px; font-weight:bold;'>Water Quality Metric</p>",
            unsafe_allow_html=True,
        )  # use HTML to set font size and weight
        selected_param_water = st.radio(
            "Water Quality Monitoring Indicators",
            options=["Residual_Chlorine", "Turbidity"],
            format_func=lambda x: NAME_MAPPING[x],
            index=0,
            label_visibility="collapsed",  # hide original label
        )
        

    with col2:
        st.markdown(
            "<p style='font-size:17px; font-weight:bold;'>Health Outcomes</p>",
            unsafe_allow_html=True,
        )
        selected_param_health = st.radio(
            "Health Outcomes",
            options=["PrematureMortality", "PretermBirths", "SMM",
                     "HIV", "HepB", "HepC", "TB"],
            format_func=lambda x: HEALTH_MAPPING[x],
            index=0,
            label_visibility="collapsed",  
        )
    with col3:

        st.markdown(
            "<p style='font-size:17px; font-weight:bold;'>Your Interested Area</p>",
            unsafe_allow_html=True,
        )
        selected_area = st.selectbox(
            "Your Interested Area",
            options=NEIGHBOUR_NAME,
            index=0,
            help="Enter text to quickly filter the area",
            label_visibility="collapsed",
        )

    subset_quality = water_quality.copy()
    rgba_colors, colorbar_html = get_color_map(subset_quality[selected_param_water], NAME_MAPPING[selected_param_water])
    subset_quality["quality_color"] = rgba_colors.tolist()
    subset_quality["tooltip"] = subset_quality.apply(
        lambda row: f"<b>Sample ID:</b> {row['Sample.Number']}<br/><b>{NAME_MAPPING[selected_param_water]}:</b> {row[selected_param_water]}<br/><b>Neighbourhood:</b> {row['Neighbourhood']}",
        axis=1,
    )


    subset_health = neighborhood_health_merged.copy()
    rgba_health, colorbar_health = get_color_map(subset_health[selected_param_health], HEALTH_MAPPING[selected_param_health], cmap = "Blues")
    rgba_health = (rgba_health * 255).astype(int)

    subset_health["health_color"]= rgba_health.tolist()
    subset_health["tooltip"] = subset_health.apply(
        lambda row: f"<b>{HEALTH_MAPPING[selected_param_health]}:</b> {row[selected_param_health]}<br/><b>Neighbourhood:</b> {row['NTA_Name']}",
        axis=1,
    )
    subset_health = subset_health[subset_health.geometry.notnull()]


    # map layer
    ## help zoom in to interested area
    
    #manual creation of json to avoid recursion limits being reached
    neighbourhood_json = {
    "type": "FeatureCollection", "features": [
        {"type": "Feature",
            "geometry": mapping(row.geometry),
            "properties": {
                "health_color": row["health_color"],
                "tooltip": row["tooltip"],
            }
        }
        for _, row in subset_health.iterrows()
    ]}

    view_state = get_view_state(neighbourhood_json, selected_area)

    # polygon layer
    polygon_layer = pdk.Layer(
        "GeoJsonLayer",
        neighbourhood_json,
        stroked=True,
        filled=True,
        extruded=False,
        opacity=0.6,
        get_fill_color="properties.health_color",
        get_line_color=[100, 100, 100, 200],
        get_line_width=2,
        line_width_units="pixels",
        line_width_min_pixels=1,
        line_width_max_pixels=4,
        pickable=True,
        auto_highlight=True,
        highlight_color=[200, 200, 200, 150]
    )

    # point layer
    point_layer = pdk.Layer(
        "ScatterplotLayer",
        data=subset_quality,
        get_position=["longitude", "latitude"],
        get_radius=150,
        get_fill_color="quality_color",
        pickable=True,
        auto_highlight=True,
    )

    # combine
    deck = pdk.Deck(
        layers=[polygon_layer, point_layer],
        initial_view_state=view_state,
        tooltip={
            "html": "{tooltip}",
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
    st.markdown(colorbar_health, unsafe_allow_html=True)

    ########################################
    # plot summary plot
    ########################################
    st.subheader("Distributions of Health Outcomes")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            "<p style='font-size:17px; font-weight:bold;'>Choose Bin Counts</p>",
            unsafe_allow_html=True,
        )
        bin_count = st.slider(
            "Choose Bin Counts", min_value=5, max_value=100, value=50, step=1, label_visibility="collapsed"
        )

        # create histogram
        fig = go.Figure()
        fig.add_trace(
            go.Histogram(
                x=subset_health[selected_param_health],
                nbinsx=bin_count,
                opacity=0.75,  # transparency
                name=HEALTH_MAPPING[selected_param_health], 
                hovertemplate=(f"{HEALTH_MAPPING[selected_param_health]}: %{{x}}<br>" "Count: %{y}<extra></extra>"),
            )
        )
        fig.update_layout(
            title=f"Histogram of {HEALTH_MAPPING[selected_param_health]}<br>in NYC",
            xaxis_title=HEALTH_MAPPING[selected_param_health],
            dragmode="select",
            clickmode="event+select",
        )
        event = st.plotly_chart(
            fig,
            use_container_width=True,
            on_select="rerun",
            selection_mode=("points", "box", "lasso"),
            key="histogram",
        )
        

    with col2:
        ## LOWESS smoothing
        
        lowess_frac = 0.2  # adjust smoothing fraction as needed
        smoothed = lowess(y, x, frac=lowess_frac, return_sorted=True)
        x_smooth_ord = smoothed[:, 0]
        y_smooth = smoothed[:, 1]
        x_smooth = [datetime.fromordinal(int(xi)) for xi in x_smooth_ord]

    #     # Create ticks for x-axis
    #     start_date = datetime.strptime(slide_bar_min, "%Y-%m")
    #     end_date = datetime.strptime(slide_bar_max, "%Y-%m")
    #     ticks = pd.date_range(start_date, end_date, periods=6)
    #     tick_vals = list(ticks)
    #     tick_text = [dt.strftime("%Y-%m") for dt in ticks]

    #     # create hover text
    #     df_grouped = df.groupby("year_month")[selected_param].mean().reset_index()
    #     hover_text = df_grouped.apply(
    #         lambda row: (
    #             f"Sample Time: {row['year_month']}<br>"
    #             f"Neighbourhood: {selected_area}<br>"
    #             f"Mean {NAME_MAPPING[selected_param]}: {row[selected_param]:.2f}"
    #         ),
    #         axis=1,
    #     )

    #     # Create figure
    #     fig = go.Figure()
    #     fig.add_trace(
    #         go.Scatter(
    #             x=df_grouped["year_month"],
    #             y=df_grouped[selected_param],
    #             mode="markers",
    #             name="Real Measure",
    #             marker=dict(color="royalblue", size=8),
    #             hovertext=hover_text,
    #             hoverinfo="text",
    #         )
    #     )
    #     fig.add_trace(
    #         go.Scatter(
    #             x=x_smooth,
    #             y=y_smooth,
    #             mode="lines",
    #             name="LOWESS Fit",
    #         )
    #     )
    #     fig.update_layout(
    #         title=f"{NAME_MAPPING[selected_param]} Change <br>from {slide_bar_min} to {slide_bar_max} in {selected_area}",
    #         xaxis=dict(tickmode="array", tickvals=tick_vals, ticktext=tick_text),
    #         yaxis_title=NAME_MAPPING[selected_param],
    #         dragmode="select",
    #         clickmode="event+select",
    #     )

    #     event = st.plotly_chart(
    #         fig,
    #         use_container_width=True,
    #         on_select="rerun",
    #         selection_mode=("points", "box", "lasso"),
    #         key="change_over_time",
    #     )
    #     if event and event.selection and event.selection.point_indices:
    #         criteria = {
    #             "year_month": df_grouped.iloc[event.selection.point_indices]["year_month"].unique().tolist(),
    #             "Neighbourhood": ([selected_area] if selected_area != "Whole NYC" else NEIGHBOUR_NAME),
    #         }
    #         if criteria != st.session_state.selection_criteria:
    #             st.session_state.selection_criteria = criteria
    #         st.button(
    #             "View in Raw Data",
    #             key="view_trend",
    #             on_click=select_subset,
    #             kwargs={"method": "trend", "criteria": criteria},
    #             disabled=(st.session_state.active_view == "trend"),
    #             use_container_width=True,
    #         )
    #     else:
    #         if st.session_state.active_view == "trend":
    #             reset_view()

    