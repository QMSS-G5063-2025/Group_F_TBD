import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import pydeck as pdk
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder
from statsmodels.nonparametric.smoothers_lowess import lowess

########################################
# global setting
########################################
# load local modules
BASE_DIR = Path(__file__).parent
sys.path.append(BASE_DIR)

from utils.data import load_data, load_shapefile
from utils.map import get_view_state
from utils.utils import COLOR_BAR_SETTING, NAME_MAPPING, get_color_map

DATA_BASE = BASE_DIR.parent / "data"


def select_subset(method):
    st.session_state.view_subset = True
    # st.session_state.selection_criteria[method] = criteria
    st.session_state.active_view = method


def reset_view(reset_key):
    st.session_state.view_subset = False
    st.session_state.selection_criteria[reset_key] = {}
    st.session_state.active_view = None


def render_sec1():
    # title
    st.title("Water Quality Change over Time")

    # set subset global
    if "view_subset" not in st.session_state:
        st.session_state.view_subset = False
    if "selection_criteria" not in st.session_state:
        st.session_state.selection_criteria = {"hist":{}, "trend":{}}
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
    water_quality = water_quality.groupby(
        ["year_month", "year", "month", "longitude", "latitude", "Neighbourhood"], as_index=False
    )[["Residual_Chlorine", "Turbidity"]].mean()
    neighbourhood = load_shapefile(DATA_BASE / "raw_data/nynta2010_25a/nynta2010.shp")
    MONTH = [
        f"{year}-{month:02d}"
        for year in range(2015, 2025)
        for month in range(1, 13)
        if not (year == 2024 and month > 12)
    ]
    NEIGHBOUR_NAME = ["Whole NYC"] + sorted(water_quality["Neighbourhood"].unique().tolist())

    ########################################
    # plot map
    ########################################
    st.subheader("Water Quality of NYC")

    # add control components
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            "<p style='font-size:17px; font-weight:bold;'>Water Quality Monitoring Indicators</p>",
            unsafe_allow_html=True,
        )  # use HTML to set font size and weight
        selected_param = st.radio(
            "Water Quality Monitoring Indicators",
            options=["Residual_Chlorine", "Turbidity"],
            format_func=lambda x: NAME_MAPPING[x],
            index=0,
            label_visibility="collapsed",  # hide original label
        )

    with col2:
        st.markdown(
            "<p style='font-size:17px; font-weight:bold;'>Sample Time</p>",
            unsafe_allow_html=True,
        )
        selected_time = st.select_slider(
            "Sample Time", options=MONTH, value="2024-01", label_visibility="collapsed"
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

    subset = water_quality.loc[water_quality["year_month"] == selected_time].copy()

    rgba_colors, colorbar_html = get_color_map(
        subset[selected_param], NAME_MAPPING[selected_param], **COLOR_BAR_SETTING[selected_param]
    )
    subset["color"] = rgba_colors.tolist()
    subset["tooltip"] = subset.apply(
        lambda row: f"<b>Neighbourhood:</b> {row['Neighbourhood']}<br/><b>Sample Time:</b> {selected_time}<br/><b>{NAME_MAPPING[selected_param]}:</b> {row[selected_param]:.2f}",
        axis=1,
    )

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
        pickable=True,
        auto_highlight=True,
    )

    # point layer
    point_layer = pdk.Layer(
        "ScatterplotLayer",
        data=subset,
        get_position=["longitude", "latitude"],
        get_radius=150,
        get_fill_color="color",
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

    ########################################
    # plot summary plot
    ########################################
    st.subheader("Summary Statistics")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            "<p style='font-size:17px; font-weight:bold;'>Choose Bin Counts</p>",
            unsafe_allow_html=True,
        )
        bin_count = st.slider(
            "Choose Bin Counts", min_value=5, max_value=100, value=50, step=1, label_visibility="collapsed"
        )

        df = subset.groupby("Neighbourhood", as_index=False)[selected_param].mean()
        # create histogram
        fig = go.Figure()
        fig.add_trace(
            go.Histogram(
                x=df[selected_param],
                nbinsx=bin_count,
                opacity=0.75,  # transparency
                name=None,  # legend name
                hovertemplate=(f"{NAME_MAPPING[selected_param]}: %{{x}}<br>" "Count: %{y}<extra></extra>"),
            )
        )

        if selected_area != "Whole NYC":
            x = df.loc[df["Neighbourhood"] == selected_area, selected_param]
            x_val = float(x.iloc[0])
            fig.add_vline(
                x=x_val,
                line=dict(color="red", width=2, dash="dash"),
                annotation_text=f"{selected_area}<br>{NAME_MAPPING[selected_param]}: {x_val:.2f}",
                annotation_position="top",
                annotation=dict(
                    font=dict(color="white", size=12, family="Arial Black"), 
                    bgcolor="rgba(0, 0, 0, 0.7)",
                    bordercolor="black", 
                    borderwidth=2,  
                    borderpad=4,  
                    align="center", 
                ),
            )

        fig.update_layout(
            title=f"Histogram of {NAME_MAPPING[selected_param]} in NYC at {selected_time}",
            xaxis_title=NAME_MAPPING[selected_param],
            dragmode="select",
            clickmode="event+select",
            showlegend=False
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
                "year_month": [selected_time],
                "Neighbourhood": df.iloc[event.selection.point_indices]["Neighbourhood"].unique().tolist(),
            }
            st.session_state.selection_criteria["hist"] = criteria
            st.button(
                "View in Raw Data",
                key="view_hist",
                on_click=select_subset,
                kwargs={"method": "hist"},
                disabled=(st.session_state.active_view == "hist"),
                use_container_width=True,
            )
        else:
            if st.session_state.active_view == "hist":
                reset_view("hist")

    with col2:
        # set slide bar
        base_idx = MONTH.index(selected_time)
        start_idx = max(0, base_idx - 6)
        end_idx = min(len(MONTH) - 1, base_idx + 6)
        default_range = (MONTH[start_idx], MONTH[end_idx])

        st.markdown(
            "<p style='font-size:17px; font-weight:bold;'>Select Time Range</p>",
            unsafe_allow_html=True,
        )
        slide_bar_min, slide_bar_max = st.select_slider(
            "Select Time Range",
            options=MONTH,
            value=default_range,
            label_visibility="collapsed",
        )
        start_idx = MONTH.index(slide_bar_min)
        end_idx = MONTH.index(slide_bar_max)
        selected_months = MONTH[start_idx : end_idx + 1]

        # subset data
        if selected_area == "Whole NYC":
            df = water_quality[water_quality["year_month"].isin(selected_months)].copy()
        else:
            df = water_quality[
                (water_quality["year_month"].isin(selected_months))
                & (water_quality["Neighbourhood"] == selected_area)
            ].copy()

        df["datetime"] = pd.to_datetime(df["year_month"], format="%Y-%m")

        # LOWESS smoothing
        x = df["datetime"].map(datetime.toordinal).values
        y = df[selected_param].values
        lowess_frac = 0.2  # adjust smoothing fraction as needed
        smoothed = lowess(y, x, frac=lowess_frac, return_sorted=True)
        x_smooth_ord = smoothed[:, 0]
        y_smooth = smoothed[:, 1]
        x_smooth = [datetime.fromordinal(int(xi)) for xi in x_smooth_ord]

        # Create ticks for x-axis
        start_date = datetime.strptime(slide_bar_min, "%Y-%m")
        end_date = datetime.strptime(slide_bar_max, "%Y-%m")
        ticks = pd.date_range(start_date, end_date, periods=6)
        tick_vals = list(ticks)
        tick_text = [dt.strftime("%Y-%m") for dt in ticks]

        # create hover text
        df_grouped = df.groupby("year_month")[selected_param].mean().reset_index()
        hover_text = df_grouped.apply(
            lambda row: (
                f"Sample Time: {row['year_month']}<br>"
                f"Neighbourhood: {selected_area}<br>"
                f"Mean {NAME_MAPPING[selected_param]}: {row[selected_param]:.2f}"
            ),
            axis=1,
        )

        # Create figure
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=df_grouped["year_month"],
                y=df_grouped[selected_param],
                mode="markers",
                name="Real Measure",
                marker=dict(color="royalblue", size=8),
                hovertext=hover_text,
                hoverinfo="text",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=x_smooth,
                y=y_smooth,
                mode="lines",
                name="LOWESS Fit",
            )
        )
        fig.update_layout(
            title=f"{NAME_MAPPING[selected_param]} Change from {slide_bar_min} to {slide_bar_max}<br>in {selected_area}",
            xaxis=dict(tickmode="array", tickvals=tick_vals, ticktext=tick_text),
            yaxis_title=NAME_MAPPING[selected_param],
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
            criteria = {
                "year_month": df_grouped.iloc[event.selection.point_indices]["year_month"].unique().tolist(),
                "Neighbourhood": ([selected_area] if selected_area != "Whole NYC" else NEIGHBOUR_NAME),
            }
            st.session_state.selection_criteria["trend"] = criteria
            st.button(
                "View in Raw Data",
                key="view_trend",
                on_click=select_subset,
                kwargs={"method": "trend"},
                disabled=(st.session_state.active_view == "trend"),
                use_container_width=True,
            )
        else:
            if st.session_state.active_view == "trend":
                reset_view("trend")

    ########################################
    # Preview raw data
    ########################################
    st.subheader("Explore Raw Data")

    columns_to_display = ["year_month", "Residual_Chlorine", "Turbidity", "Neighbourhood"]

    if st.session_state.view_subset:
        st.button(
            "View all data",
            key="view_all",
            on_click=reset_view,
            kwargs={"reset_key": st.session_state.active_view},
            disabled=not st.session_state.view_subset,
        )

    display_df = water_quality[columns_to_display].copy()
    if st.session_state.view_subset:
        for col, vals in st.session_state.selection_criteria[st.session_state.active_view].items():
            display_df = display_df[display_df[col].isin(vals)]

    display_df.rename(columns={k: v for k, v in NAME_MAPPING.items() if k in df.columns}, inplace=True)

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
            st.write(
                {k: list(v) for k, v in st.session_state.selection_criteria[st.session_state.active_view].items()}
            )
