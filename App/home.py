import streamlit as st


def render_home():
    # title
    st.title("Project Name")

    col1, col2 = st.columns([3, 1])
    with col1:
        st.header("Objective")
        st.write("Project overview")

    with col2:
        st.subheader("Developer")
        st.write("- Aziz Zafar (az2798)\n- Naufa Amirani (nfa2120)\n- Di Liu (dl3738)")

    st.divider()
    st.header("Data source")
    st.markdown(
        """
    - Water Quality Data
    
    We get the raw water quality data from [NYC OpenData](https://data.cityofnewyork.us/Environment/Drinking-Water-Quality-Distribution-Monitoring-Dat/bkwf-xfky/about_data). For detailed data curation, please refer to our [GitHub](https://github.com/QMSS-G5063-2025/Group_F_TBD/tree/main/scripts/01_water_quality_data).

    - Neighboorhhod Health Data

    We get the raw neighboorhhod health data from [NYC Health Atlas](https://public.tableau.com/app/profile/nyc.health/viz/NewYorkCityNeighborhoodHealthAtlas/Home). For detailed data curation, please refer to our [GitHub](https://github.com/QMSS-G5063-2025/Group_F_TBD/tree/main/scripts/02_health_atlas). We follow the neighboorhhod definition of [2010 NYC City Planning](https://www.nyc.gov/content/planning/pages/resources/datasets/neighborhood-tabulation).

    **You can download our curated data from our [GitHub](https://github.com/QMSS-G5063-2025/Group_F_TBD/tree/main/data)**
    """
    )

    st.divider()
    st.header("Sections")
    cols = st.columns(3)
    sections = ["Water Quality Change over Time", "Section2", "Section3"]
    for col, section in zip(cols, sections):
        with col:
            if st.button(f"Go to {section}"):
                st.session_state.current_section = section
