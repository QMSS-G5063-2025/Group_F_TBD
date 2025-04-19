import geopandas as gpd
import numpy as np
import pandas as pd
import streamlit as st

CACHE_TIME = 3600


@st.cache_data(ttl=CACHE_TIME)
def load_data(data_path):
    try:
        # Check if the files exist first
        if not data_path.exists():
            st.error(f"File not found: {data_path.absolute()}")
            return None

        data = pd.read_csv(data_path, index_col=0)

        return data

    except Exception as e:
        st.error(f"An error occurred during data loading: {str(e)}")
        return None


@st.cache_data(ttl=CACHE_TIME)
def load_shapefile(data_path):
    try:
        # Check if the files exist first
        if not data_path.exists():
            st.error(f"File not found: {data_path.absolute()}")
            return None

        data = gpd.read_file(data_path)
        data = data.to_crs(epsg=4326)
        # data["coordinates"] = data.geometry.apply(
        #     lambda geom: [np.array(poly.exterior.coords).tolist() for poly in geom.geoms]
        # )

        return data

    except Exception as e:
        st.error(f"An error occurred during data loading: {str(e)}")
        return None
