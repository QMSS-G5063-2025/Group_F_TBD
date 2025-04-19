import pydeck as pdk

def get_view_state(gdf, selected_area):

    nyc_view = pdk.ViewState(latitude=40.7128, longitude=-74.0060, zoom=10, pitch=0)

    if selected_area == "Whole NYC":
        return nyc_view

    area_data = gdf[gdf["NTAName"] == selected_area]
    if not area_data.empty:
        bounds = area_data.geometry.total_bounds  # [minx, miny, maxx, maxy]
        return pdk.ViewState(
            longitude=(bounds[0] + bounds[2]) / 2, latitude=(bounds[1] + bounds[3]) / 2, zoom=13, pitch=0
        )
    return nyc_view
