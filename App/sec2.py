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
from utils.utils import NAME_MAPPING, HEALTH_MAPPING, COLOR_BAR_SETTING, COLOR_BAR_HEALTH, get_color_map, reset_view, select_subset

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
    nta_health.drop(columns=["HIV"])
    neighbourhood = load_shapefile(DATA_BASE / "raw_data/nynta2010_25a/nynta2010.shp")

    neighborhood_health_merged = pd.merge(left= nta_health, right= neighbourhood,
                                          left_on="NTA_Code", right_on= "NTACode",
                                          how = "left")
    neighborhood_health_merged.dropna(inplace=True)
    NEIGHBOUR_NAME = ["Whole NYC"] + sorted(water_quality["Neighbourhood"].unique().tolist())

    

    water_quality = water_quality[water_quality["year"]==2015]
    water_quality = (
    water_quality
    .groupby(["longitude", "latitude","Neighbourhood"], as_index=False)[["Residual_Chlorine", "Turbidity"]].mean()
    )

    #water_quality_neighborhood= water_quality.groupby("Neighbourhood",as_index=False)[["Residual_Chlorine", "Turbidity"]].mean()
    water_quality_neighborhood = pd.merge(water_quality, neighborhood_health_merged,
                                          left_on = "Neighbourhood", right_on= "NTA_Name")
    
    water_quality_neighborhood["geometry"] = water_quality_neighborhood["geometry"].apply(mapping)
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
        selected_param_health = st.selectbox(
            "Health Outcomes",
            options=["PrematureMortality", "PretermBirths", "SMM",
                      "HepB", "HepC", "TB"],
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

    subset = water_quality_neighborhood.copy()
    rgba_colors, colorbar_html = get_color_map(subset[selected_param_water], NAME_MAPPING[selected_param_water], **COLOR_BAR_SETTING[selected_param_water])
    subset["quality_color"] = rgba_colors.tolist()
    subset["tooltip"] = subset.apply(
        lambda row: f"<b>{NAME_MAPPING[selected_param_water]}:</b> {row[selected_param_water]:.2f}<br/><b>Neighbourhood:</b> {row['Neighbourhood']}",
        axis=1,
    )

    rgba_health, colorbar_health = get_color_map(subset[selected_param_health], HEALTH_MAPPING[selected_param_health], **COLOR_BAR_HEALTH[selected_param_health])


    subset["health_color"]= rgba_health.tolist()
    subset["tooltip_health"] = subset.apply(
        lambda row: f"<b>{HEALTH_MAPPING[selected_param_health]}:</b> {row[selected_param_health]}<br/><b>Neighbourhood:</b> {row['NTA_Name']}",
        axis=1,
    )
    subset = subset[subset.geometry.notnull()]


    # map layer
    ## help zoom in to interested area
    
    #manual creation of json to avoid recursion limits being reached
    view_state = get_view_state(neighbourhood, selected_area)
    neighbourhood_json = {
    "type": "FeatureCollection", "features": [
        {"type": "Feature",
            "geometry": row["geometry"],
            "properties": {
                "health_color": row["health_color"],
                "tooltip": row["tooltip_health"]}
        }
        for _, row in subset.iterrows()
    ]}
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
        data=subset,
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
        df = subset.groupby("Neighbourhood", as_index=False)[selected_param_health].mean()

        fig = go.Figure()
        fig.add_trace(
            go.Histogram(
                x=df[selected_param_health],
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
        if event and event.selection and event.selection.point_indices:
            criteria = {
                "Neighbourhood": df.iloc[event.selection.point_indices]["Neighbourhood"].unique().tolist(),
            }
            if criteria != st.session_state.selection_criteria:
                st.session_state.selection_criteria = criteria
            st.button(
                "View in Raw Data",
                key="view_hist",
                on_click=select_subset,
                kwargs={"method": "hist", "criteria": criteria},
                disabled=(st.session_state.active_view == "hist"),
                use_container_width=True,
            )
        else:
            if st.session_state.active_view == "hist":
                reset_view()
        

    with col2:
        ## LOWESS smoothing
        y= water_quality_neighborhood[selected_param_health]
        x=water_quality_neighborhood[selected_param_water]
        lowess_frac = 0.5  # adjust smoothing fraction as needed
        smoothed = lowess(y, x, frac=lowess_frac, return_sorted=True)
        x_smooth = smoothed[:, 0]
        y_smooth = smoothed[:, 1]

        #df = water_quality_neighborhood.groupby("Neighbourhood", as_index=False)[[selected_param_health, selected_param_water]].mean()
        #st.dataframe(df)
        # Create figure
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=x,
                y=y,
                mode="markers",
                name="Real Measure",
                marker=dict(color="lightblue", size=8),
                hoverinfo="text"
            )
        )
        fig.add_trace(
            go.Scatter(
                x=x_smooth,
                y=y_smooth,
                mode="lines",
                name="LOWESS Fit"

            )
        )
        fig.update_layout(
            title=f"{HEALTH_MAPPING[selected_param_health]} with respect to {NAME_MAPPING[selected_param_water]}",
            yaxis_title=HEALTH_MAPPING[selected_param_health],
            xaxis_title = NAME_MAPPING[selected_param_water],
            dragmode="select",
            clickmode="event+select",
        )

        event = st.plotly_chart(
            fig,
            use_container_width=True,
            on_select="rerun",
            selection_mode=("points", "box", "lasso"),
            key="change_over_time",
        )
        if event and event.selection and event.selection.point_indices:
            #st.dataframe(df.iloc[event.selection.point_indices])
            criteria = {
                selected_param_health: water_quality_neighborhood.iloc[event.selection.point_indices][selected_param_health].unique().tolist(),
                selected_param_water: water_quality_neighborhood.iloc[event.selection.point_indices][selected_param_water].unique().tolist(),

            }
            if criteria != st.session_state.selection_criteria:
                st.session_state.selection_criteria = criteria
            st.button(
                "View in Raw Data",
                key="view_trend",
                on_click=select_subset,
                kwargs={"method": "trend", "criteria": criteria},
                disabled=(st.session_state.active_view == "trend"),
                use_container_width=True,
            )
        else:
            if st.session_state.active_view == "trend":
                reset_view()

    st.subheader("Explore Raw Data")

    columns_to_display = ["Residual_Chlorine", "Turbidity", "Neighbourhood",
                          "PrematureMortality", "PretermBirths", "SMM",
                      "HepB", "HepC", "TB"]

    if st.session_state.view_subset:
        st.button(
            "View all data",
            key="view_all",
            on_click=reset_view,
            disabled=not st.session_state.view_subset,
        )

    display_df = water_quality_neighborhood[columns_to_display].copy()
    if st.session_state.view_subset:
        for col, vals in st.session_state.selection_criteria.items():
            display_df = display_df[display_df[col].isin(vals)]

    display_df.rename(columns={k: v for k, v in HEALTH_MAPPING.items() if k in water_quality_neighborhood.columns}, inplace=True)
    display_df.rename(columns={k: v for k, v in NAME_MAPPING.items() if k in water_quality_neighborhood.columns}, inplace=True)

    # build grid options
    gb = GridOptionsBuilder.from_dataframe(display_df)
    gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=15)
    gb.configure_default_column(
        filter=True,
        sortable=True,
        cellStyle={"textAlign": "center"},
        wrapHeaderText=True,
        autoHeaderHeight=True,
    )
    # we need to explicitly set the header class to normalize the header position
    for col in display_df.columns:
        gb.configure_column(col, headerClass="centered-header")

    grid_options = gb.build()

    AgGrid(display_df, gridOptions=grid_options, height=400, fit_columns_on_grid_load=True)

    if st.session_state.view_subset:
        with st.expander("View Current Selection Criteria", expanded=False):
            st.write({k: list(v) for k, v in st.session_state.selection_criteria.items()})
    