import pydeck as pdk

NYC_BOUND = [[-74.2591, 40.4774], [-73.7004, 40.9176]]
MIN_ZOOM = 9
MAX_ZOOM = 13

def get_view_state(gdf, selected_area):

    nyc_view = pdk.ViewState(
        latitude=40.7128,
        longitude=-74.0060,
        zoom=9,
        pitch=0,
        min_zoom=MIN_ZOOM,
        max_zoom=MAX_ZOOM,
        bounds=NYC_BOUND,
        bearing=0,
    )

    if selected_area == "Whole NYC":
        return nyc_view

    area_data = gdf[gdf["NTAName"] == selected_area]
    if not area_data.empty:
        bounds = area_data.geometry.total_bounds  # [minx, miny, maxx, maxy]
        return pdk.ViewState(
            longitude=(bounds[0] + bounds[2]) / 2,
            latitude=(bounds[1] + bounds[3]) / 2,
            zoom=13,
            pitch=0,
            min_zoom=MIN_ZOOM,
            max_zoom=MAX_ZOOM,
            bounds=NYC_BOUND,
            bearing=0,
        )
    return nyc_view
