import json
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.express as px
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
from utils.utils import NAME_MAPPING, get_color_map

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

    ########################################
    # read in data
    ########################################
    water_quality = load_data(DATA_BASE / "water_quality.csv")
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
        )
        selected_param = st.radio(
            "Water Quality Monitoring Indicators",
            options=["Residual_Chlorine", "Turbidity"],
            format_func=lambda x: NAME_MAPPING[x],
            index=0,
            label_visibility="collapsed",
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
    rgba_colors, colorbar_html = get_color_map(subset[selected_param], NAME_MAPPING[selected_param])
    subset["color"] = rgba_colors.tolist()
    subset["tooltip"] = subset.apply(
        lambda row: f"<b>Sample ID:</b> {row['Sample.Number']}<br/><b>{NAME_MAPPING[selected_param]}:</b> {row[selected_param]}<br/><b>Neighbourhood:</b> {row['Neighbourhood']}<br/><b>Sample Time:</b> {selected_time}",
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
            "Choose Bin Counts", min_value=5, max_value=100, value=20, step=1, label_visibility="collapsed"
        )

        fig = px.histogram(
            subset,
            x=selected_param,
            nbins=bin_count,
            title=f"Histogram of {NAME_MAPPING[selected_param]}<br>in NYC at {selected_time}",
            labels={selected_param: NAME_MAPPING[selected_param]},
            opacity=0.75,
        )
        fig.update_layout(dragmode="select", selectdirection="h")
        st.plotly_chart(fig, use_container_width=True)

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
        fig.add_trace(go.Scatter(x=x_smooth, y=y_smooth, mode="lines", name="LOWESS Fit"))

        fig.update_layout(
            title=f"{NAME_MAPPING[selected_param]} Change <br>from {slide_bar_min} to {slide_bar_max} in {selected_area}",
            xaxis=dict(tickmode="array", tickvals=tick_vals, ticktext=tick_text),
            yaxis_title=NAME_MAPPING[selected_param],
        )

        st.plotly_chart(fig, use_container_width=True)

    ########################################
    # Preview raw data
    ########################################
    st.subheader("Explore Raw Data")

    columns_to_display = ["Sample.Number", "year_month", "Residual_Chlorine", "Turbidity", "Neighbourhood"]
    df = water_quality[columns_to_display].copy()
    df.rename(columns=NAME_MAPPING, inplace=True)

    # build grid options
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=15)
    gb.configure_default_column(
        filter=True,
        sortable=True,
        cellStyle={"textAlign": "center"},
        headerClass="centered-header",
        wrapHeaderText=True,
        autoHeaderHeight=True,
    )
    grid_options = gb.build()
    st.markdown(
        """
        <style>
            .centered-header .ag-header-cell-label {
                justify-content: center !important;
                white-space: normal !important;
            }
        </style>
    """,
        unsafe_allow_html=True,
    )

    AgGrid(df, gridOptions=grid_options, height=400, fit_columns_on_grid_load=True)
