import matplotlib.pyplot as plt
import numpy as np
import streamlit as st
from matplotlib.colors import to_hex
from streamlit.components.v1 import html

NAME_MAPPING = {
    "Residual_Chlorine": "Residual Chlorine Content (mg/L)",
    "Turbidity": "Turbidity (NTU)",
    "year_month": "Sample Time",
    "Sample.Number": "Sample ID",
}


def get_color_map(vals, selected_param, cmap="OrRd", n_stops=5, max_clip=None):
    min_val = vals.min()
    raw_max = vals.max()
    if max_clip is None:
        max_clip = raw_max
    clipped = np.clip(vals, min_val, max_clip)
    norm = plt.Normalize(vmin=min_val, vmax=max_clip)

    cmap = plt.get_cmap(cmap)
    colors = (cmap(norm(clipped)) * 255).astype(int)

    stops = np.linspace(min_val, max_clip, n_stops)
    hex_colors = [to_hex(cmap(norm(v)), keep_alpha=True) for v in stops]
    gradient_css = ", ".join(hex_colors)

    css = (
        f"background: linear-gradient(to right, {gradient_css});"
        "border-radius: 5px;"
        "height: 20px;"
        "width: 300px;"
    )
    text_style = (
        "font-size:0.9em; font-weight:600; color:#FFF; "
        "background-color: rgba(0,0,0,0.6); padding:2px 6px; "
        "border-radius:3px; text-shadow:1px 1px 2px rgba(0,0,0,0.7);"
    )

    if max_clip < raw_max:
        val_label = f"{min_val:.2f} → ≥{max_clip:.2f}"
    else:
        val_label = f"{min_val:.2f} → {max_clip:.2f}"

    html = f"""
    <div style="display:flex; align-items:center; margin-top:20px;">
      <div style="{css}"></div>
      <div style="margin-left:12px; display:flex; flex-direction:column; gap:4px;">
        <div style="{text_style}">{selected_param}</div>
        <div style="{text_style}">{val_label}</div>
      </div>
    </div>
    """

    return colors, html


def select_subset(method, criteria):
    st.session_state.view_subset = True
    st.session_state.selection_criteria = criteria
    st.session_state.active_view = method


def reset_view():
    st.session_state.view_subset = False
    st.session_state.selection_criteria = {}
    st.session_state.active_view = None
