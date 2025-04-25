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
from matplotlib.colors import TwoSlopeNorm, to_hex
import numpy as np
from shapely.geometry import mapping

########################################
# global setting
########################################
# load local modules
BASE_DIR = Path(__file__).parent
sys.path.append(BASE_DIR)

from utils.data import load_data, load_shapefile
from utils.map import get_view_state
from utils.utils import COLOR_BAR_SETTING, COLOR_BAR_HEALTH, COLOR_BAR_DEMO, HEALTH_MAPPING, DEMO_MAPPING, NAME_MAPPING, get_color_map, reset_view, select_subset

DATA_BASE = BASE_DIR.parent / "data"


def render_sec3():
    # title
    st.title("Water Quality Change over Time")

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
    
    # ***** CHANGED: START Preprocessing *****
    
    neighbourhood = load_shapefile(DATA_BASE / "raw_data/nynta2010_25a/nynta2010.shp")
    nta_health_demo = load_data(DATA_BASE / "nta_health_demographic_NAUFA.csv")
    # Get sets of neighborhood names from both datasets
    neighborhoods_in_health = set(nta_health_demo["NTA_Name"].unique())
    neighborhoods_in_water = set(water_quality["Neighbourhood"].unique())
    neighborhood_health_merged = pd.merge(left= nta_health_demo, right= neighbourhood,
                                          left_on="NTA_Code", right_on= "NTACode",
                                          how = "left")
    neighborhood_health_merged.dropna(inplace=True)
    
#    # Find missing neighborhoods
#    missing_neighborhoods = neighborhoods_in_health - neighborhoods_in_water
#    st.write(f"Number of neighborhoods in health data but missing in water data: {len(missing_neighborhoods)}")
#    if missing_neighborhoods:
#        st.write("Missing neighborhoods:")
#        for name in sorted(missing_neighborhoods):
#            st.write("-", name)

    # Subset water quality data to 2015 only
    water_quality_2015 = water_quality[water_quality["year_month"].str.startswith("2015")]
    # Take average of all numeric cols in 2015 water quality data by Neighbourhood
    avg_water_quality = water_quality_2015.groupby("Neighbourhood", as_index=False).mean(numeric_only=True)
    
    # Merge with nta_health_demo
    merged_df = avg_water_quality.merge(neighborhood_health_merged, left_on="Neighbourhood", right_on="NTA_Name", how="inner")
    
    merged_df["geometry"] = merged_df["geometry"].apply(mapping)
    
#    st.write(f"Original water quality records: {len(water_quality)}")
#    st.write(f"Health/demographic records: {len(nta_health_demo)}")
#    st.write(f"Water quality records from 2015: {len(water_quality_2015)}")
#    st.write(f"Averaged water quality rows (1 per neighborhood): {len(avg_water_quality)}")
#    st.write(f"After merge: {len(merged_df)} rows")
    
#    # Identify missing neighborhoods after merge
#    merged_neighborhoods = set(merged_df["Neighbourhood"])
#    all_water_neighborhoods = set(avg_water_quality["Neighbourhood"])
#    missing_neighborhoods = all_water_neighborhoods - merged_neighborhoods
#    if missing_neighborhoods:
#        for n in sorted(missing_neighborhoods):
#            st.write(f"- {n}")
    
    demo_2015 = merged_df.copy()
    
    # ***** CHANGED: END Preprocessing *****


    MONTH = [
        f"{year}-{month:02d}"
        for year in range(2015, 2025)
        for month in range(1, 13)
        if not (year == 2024 and month > 12)
    ]
    NEIGHBOUR_NAME = ["Whole NYC"] + sorted(water_quality["Neighbourhood"].unique().tolist())

    ########################################
    # plot map (demographics as base color)
    ########################################
    st.subheader("NYC Health Outcomes by Demographic Characteristics")

    # Demographic categories
    demo_options = {
        "Hispanic": "Hispanic",
        "White (Non-Hispanic)": "WhiteNonHisp",
        "Black (Non-Hispanic)": "BlackNonHisp",
        "Asian / Pacific Islander": "AsianPI",
        "Other Race": "OtherRace"
    }
    
    # Add control components
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            "<p style='font-size:17px; font-weight:bold;'>Demographic Group</p>",
            unsafe_allow_html=True,
        )
        selected_param_demo = st.selectbox(
            "Demographic Variable",
            options=list(demo_options.values()),
            format_func=lambda x: DEMO_MAPPING[x],
            index=0,
            label_visibility="collapsed",
        )

    with col2:
        st.markdown(
            "<p style='font-size:17px; font-weight:bold;'>Health Outcomes</p>",
            unsafe_allow_html=True,
        )
        selected_param_health = st.selectbox(
            "Health Outcomes",
            options=["PrematureMortality", "PretermBirths", "SMM", "HepB", "HepC", "TB"],
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

    subset = merged_df.copy()
    subset = subset[subset.geometry.notnull()]

    # Polygon color by demographics
    rgba_demo, colorbar_demo = get_color_map(
        subset[selected_param_demo],
        DEMO_MAPPING[selected_param_demo],
        **COLOR_BAR_DEMO[selected_param_demo]
    )
    subset["demo_color"] = rgba_demo.tolist()
    subset["tooltip_demo"] = subset.apply(
        lambda row: f"<b>{DEMO_MAPPING[selected_param_demo]}:</b> {row[selected_param_demo]:.2f}<br/><b>Neighbourhood:</b> {row['Neighbourhood']}",
        axis=1,
    )

    # Point color by health outcomes
    rgba_health, colorbar_health = get_color_map(
        subset[selected_param_health],
        HEALTH_MAPPING[selected_param_health],
        **COLOR_BAR_HEALTH[selected_param_health]
    )
    subset["health_color"] = rgba_health.tolist()
    subset["tooltip_health"] = subset.apply(
        lambda row: f"<b>{HEALTH_MAPPING[selected_param_health]}:</b> {row[selected_param_health]}<br/><b>Neighbourhood:</b> {row['NTA_Name']}",
        axis=1,
    )

    view_state = get_view_state(neighbourhood, selected_area)
    
    # Polygons
    neighbourhood_json = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": row["geometry"],
                "properties": {
                    "fill_color": row["demo_color"],
                    "tooltip": row["tooltip_demo"]
                }
            }
            for _, row in subset.iterrows()
        ]
    }

    # Polygon layer w demographic coloring
    polygon_layer = pdk.Layer(
        "GeoJsonLayer",
        neighbourhood_json,
        stroked=True,
        filled=True,
        extruded=False,
        opacity=0.6,
        get_fill_color="properties.fill_color",
        get_line_color=[100, 100, 100, 200],
        get_line_width=2,
        line_width_units="pixels",
        line_width_min_pixels=1,
        line_width_max_pixels=4,
        pickable=True,
        auto_highlight=True,
        highlight_color=[200, 200, 200, 150]
    )

    # Point layer w health outcome
    point_layer = pdk.Layer(
        "ScatterplotLayer",
        data=subset,
        get_position=["longitude", "latitude"],
        get_radius=150,
        get_fill_color="health_color",
        pickable=True,
        auto_highlight=True,
        get_tooltip="tooltip_health"
    )

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

    st.markdown(colorbar_demo, unsafe_allow_html=True)
    st.markdown(colorbar_health, unsafe_allow_html=True)


    ########################################
    # plot summary plot
    ########################################

    # ***** CHANGED: START Radar + Bar chart toggle for demographics *****

    st.subheader("Demographic Breakdown for Selected Neighborhood")
    
    display_labels = list(demo_options.keys())
    column_keys = list(demo_options.values())
    # Find the demographic row for selected neighborhood
    demo_row = nta_health_demo[nta_health_demo["NTA_Name"] == selected_area]
    if not demo_row.empty:
        demo_values = demo_row.iloc[0][column_keys].tolist()
        total_percent = sum(demo_values)
        if not total_percent == 100.00:
            st.warning(f"Total demographic percentage = {total_percent:.2f}%, but should be 100%")

        # Add radar/bar chart toggle
        chart_type = st.radio("Display as:", ["Radar Chart", "Bar Chart"], horizontal=True)
        if chart_type == "Radar Chart":
            radar_values = demo_values + [demo_values[0]]
            radar_labels = display_labels + [display_labels[0]]
            radar_fig = go.Figure()
            radar_fig.add_trace(go.Scatterpolar(
                r=radar_values,
                theta=radar_labels,
                fill='toself',
                name="Demographic %",
                line=dict(color="rgba(255, 105, 180, 0.7)", width=3),
                marker=dict(size=12),
                hovertemplate="%{theta}: %{r:.1f}%<extra></extra>"
            ))
            radar_fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, max(demo_values) + 5],
                        tickfont=dict(size=14)
                    ),
                    angularaxis=dict(
                        tickfont=dict(size=20),
                    ),
                ),
                showlegend=False,
                title=f"Demographics in {selected_area}",
                width=1000,
                height=800
            )
            st.plotly_chart(radar_fig, use_container_width=True)
        elif chart_type == "Bar Chart":
            bar_colors = {
                "WhiteNonHisp": "#2CA02C",   # green
                "BlackNonHisp": "#9467BD",   # purple
                "AsianPI": "#FF7F0E",        # orange
                "Hispanic": "#D62728",       # red
                "OtherRace": "#7F7F7F"       # gray
            }
            # Match display_label to color w column name
            colors = [bar_colors.get(demo_options[label], "gray") for label in display_labels]
            bar_fig = go.Figure(go.Bar(
                x=display_labels,
                y=demo_values,
                marker_color=colors,
                text=[f"{val:.1f}%" for val in demo_values],
                textposition="outside",
                textfont=dict(size=18)
            ))
            bar_fig.update_layout(
                xaxis=dict(
                    tickfont=dict(size=20),
                    title="Demographic Subcategories"
                ),
                yaxis=dict(title="Percent", range=[0, max(demo_values) + 10]),
                title=dict(
                    text=f"Demographics in {selected_area} (Bar Chart)",
                    font=dict(size=28)
                ),
                showlegend=False,
                width=800,
                height=600
            )
            st.plotly_chart(bar_fig, use_container_width=True)

    # *****CHANGED: END Radar + Bar chart toggle for demographics *****

    # *****CHANGED: START Two scatterplots with custom color mapping *****

    st.subheader("Demographic Groups vs. Poverty and Education (Colored by Water Quality)")
    
    selected_x_label = st.selectbox(
        "Demographic group",
        options=list(demo_options.keys())
    )
    selected_x = demo_options[selected_x_label]

    y_axis_options = {
        "Poverty (%)": "Poverty",
        "Less than HS Education (25+) (%)": "EduLessThanHS"
    }
    color_options = {
        "Turbidity": "Turbidity",
        "Residual Chlorine": "Residual_Chlorine"
    }

    # Get water quality metric
    color_metric_label = st.selectbox("Color by Water Quality Metric", list(color_options.keys()), key="color_metric")
    color_metric = color_options[color_metric_label]

    # Get color settings for the selected color metric
    colorbar_title = NAME_MAPPING.get(color_metric, color_metric)
    color_settings = COLOR_BAR_SETTING.get(color_metric, {})
    cmap = color_settings.get("cmap", "OrRd")
    min_clip = color_settings.get("min_clip")
    max_clip = color_settings.get("max_clip")
    log_scale_mapping = color_settings.get("log_scale_mapping", False)

    # Colors for the selected color metric
    selected_vals = demo_2015[color_metric]
    colors, colorbar_html = get_color_map(
        vals=selected_vals,
        selected_param=colorbar_title,
        cmap=cmap,
        n_stops=6,
        min_clip=min_clip,
        max_clip=max_clip,
        log_scale_mapping=log_scale_mapping
    )
    hex_colors = [to_hex(c / 255) for c in colors]

    col1, col2 = st.columns(2)

    # Plot 1: always Poverty on y-axis
    with col1:
        st.write("#### Plot 1: % of Population Under Federal Poverty Level")
        y1 = "Poverty"

        hovertext1 = [
            f"{row['Neighbourhood']}<br>{selected_x_label}: {row[selected_x]:.1f}%<br>Poverty: {row[y1]:.1f}%<br>{colorbar_title}: {row[color_metric]:.2f}"
            for _, row in demo_2015.iterrows()
        ]
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(
            x=demo_2015[selected_x],
            y=demo_2015[y1],
            mode="markers",
            marker=dict(
                size=10,
                color=hex_colors,
                opacity=0.85
            ),
            text=hovertext1,
            hoverinfo="text"
        ))
        fig1.update_layout(
            xaxis_title=f"{selected_x_label} (%)",
            yaxis_title="Poverty (%)",
            title=f"Poverty vs {selected_x_label}",
            dragmode="zoom"
        )
        st.plotly_chart(fig1, use_container_width=True, key="plot_left")

    # Plot 2: always Education on y-axis
    with col2:
        st.write("#### Plot 2: % of >=25 y/o Population with Less Than High School Level Education")
        y2 = "EduLessThanHS"

        hovertext2 = [
            f"{row['Neighbourhood']}<br>{selected_x_label}: {row[selected_x]:.1f}%<br>Less than HS: {row[y2]:.1f}%<br>{colorbar_title}: {row[color_metric]:.2f}"
            for _, row in demo_2015.iterrows()
        ]
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=demo_2015[selected_x],
            y=demo_2015[y2],
            mode="markers",
            marker=dict(
                size=10,
                color=hex_colors,
                opacity=0.85
            ),
            text=hovertext2,
            hoverinfo="text"
        ))
        fig2.update_layout(
            xaxis_title=f"{selected_x_label} (%)",
            yaxis_title="Less than HS Education (%)",
            title=f"Education vs {selected_x_label}",
            dragmode="zoom"
        )
        st.plotly_chart(fig2, use_container_width=True, key="plot_right")

    # Centered colorbar
    colorbar_container = st.container()
    with colorbar_container:
        _, center_col, _ = st.columns([1, 4, 1])
        with center_col:
            st.markdown(
                f"<div style='display: flex; justify-content: center;'>{colorbar_html}</div>",
                unsafe_allow_html=True
            )

    # *****CHANGED: END Two scatterplots with custom color mapping *****


    ########################################
    # Preview raw data
    ########################################
    st.subheader("Explore Raw Data")

    columns_to_display = ["Hispanic", "WhiteNonHisp", "BlackNonHisp", "AsianPI", "OtherRace",
                        "Poverty", "EduLessThanHS"]

    if st.session_state.view_subset:
        st.button(
            "View all data",
            key="view_all",
            on_click=reset_view,
            disabled=not st.session_state.view_subset,
        )

    display_df = merged_df[columns_to_display].copy()
    if st.session_state.view_subset:
        for col, vals in st.session_state.selection_criteria.items():
            display_df = display_df[display_df[col].isin(vals)]

    display_df.rename(columns={k: v for k, v in NAME_MAPPING.items() if k in display_df.columns}, inplace=True)

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
