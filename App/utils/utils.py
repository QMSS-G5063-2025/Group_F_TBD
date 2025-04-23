import matplotlib.pyplot as plt
import numpy as np
import streamlit as st
from matplotlib.colors import TwoSlopeNorm, to_hex

NAME_MAPPING = {
    "Residual_Chlorine": "Residual Chlorine Content (mg/L)",
    "Turbidity": "Turbidity (NTU)",
    "year_month": "Sample Time",
    "Sample.Number": "Sample ID",
}

COLOR_BAR_SETTING = {
    "Residual_Chlorine": {"cmap": "bwr", "min_clip": None, "max_clip": None, "log_scale_mapping": False},
    "Turbidity": {"cmap": "bwr", "min_clip": 0.1, "max_clip": 1.5, "log_scale_mapping": False},
}


def get_color_map(
    vals,
    selected_param,
    cmap="OrRd",
    n_stops=5,
    min_clip=None,
    max_clip=None,
    median=None,
    log_scale_mapping=False,
    force_median=True
):
    raw_min = vals.min()
    raw_max = vals.max()
    raw_median = np.median(vals)

    max_label = f"≥ {max_clip:.2f}" if not max_clip is None else f"{raw_max:.2f}"
    min_label = f"{min_clip:.2f} ≤" if not min_clip is None else f"{raw_min:.2f}"
    val_label = f"{min_label} → {max_label}"

    if max_clip is None:
        max_clip = raw_max
    if min_clip is None:
        min_clip = raw_min
    if median is None:
        median = raw_median

    if log_scale_mapping:
        mapped = np.log(vals)
        clip_min_mapped = np.log(min_clip)
        clip_max_mapped = np.log(max_clip)
        median_mapped = np.log(median)
    else:
        mapped = vals.copy()
        clip_min_mapped = min_clip
        clip_max_mapped = max_clip
        median_mapped = median

    clipped = np.clip(mapped, clip_min_mapped, clip_max_mapped)
    if force_median:
        norm = TwoSlopeNorm(vmin=clip_min_mapped, vcenter=median_mapped, vmax=clip_max_mapped)
    else:
        norm = plt.Normalize(vmin=clip_min_mapped, vmax=clip_max_mapped)

    cmap = plt.get_cmap(cmap)
    colors = (cmap(norm(clipped)) * 255).astype(int)

    stops = np.linspace(clip_min_mapped, clip_max_mapped, n_stops)
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
