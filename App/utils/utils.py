import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import to_hex

NAME_MAPPING = {
    "Residual_Chlorine": "Residual Chlorine Content (mg/L)",
    "Turbidity": "Turbidity (NTU)",
}


def get_color_map(vals, selected_param, cmap="OrRd", n_stops=5):
    min_val = vals.min()
    max_val = vals.max()
    norm = plt.Normalize(vmin=min_val, vmax=max_val)

    cmap = plt.get_cmap(cmap)
    colors = (cmap(norm(vals)) * 255).astype(int)

    stops = np.linspace(min_val, max_val, n_stops)
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
        <div style="{text_style}">{min_val:.2f} → {max_val:.2f}</div>
      </div>
    </div>
    """

    return colors, html
