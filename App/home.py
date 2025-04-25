import streamlit as st


def render_home():
    # title
    st.title("What is in our water?")

    col1, col2 = st.columns([3, 1])
    with col1:
        
        st.image("https://i.ytimg.com/vi/oCiagTL2K-Q/hqdefault.jpg")
        st.markdown("""[Image Source](https://www.google.com/url?sa=i&url=https%3A%2F%2Fwww.youtube.com%2Fwatch%3Fv%3DoCiagTL2K-Q&psig=AOvVaw0UenNNRz_2Kmiz8iL9c_BG&ust=1745697773717000&source=images&cd=vfe&opi=89978449&ved=0CBcQjhxqGAoTCIC1sI_984wDFQAAAAAdAAAAABDyAQ)""")
        st.header("Visualization of demographic patterns of water quality and health outcomes in New York.")
        st.markdown("""The New York City Mayor's office recognizes the deep and structural 
            history of [environmental injustice in New York](https://climate.cityofnewyork.us/ejnyc-report/history-of-environmental-injustice-and-racism-in-nyc/). To this day, there is strong evidence
             for [water inequality throughout the United States](https://www.nature.com/articles/s41467-021-23898-z). We focus on New York since             it is a large and heterogenous city with  
            complex plumbing and water infrastructure, and a diversity of neighborhoods with varying geographical and demographic characteristics. In the three sections
            presented, you may find maps and plots illustrating changes in water quality measurements over time, and how they
            correlate with health outcomes and neighborhood demographics.""")

    with col2:
        st.subheader("Developer")
        st.write("- Aziz Zafar (az2798)\n- Naufa Amirani (nfa2120)\n- Di Liu (dl3738)")

    st.divider()
    st.header("Data sources")
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
    sections = ["Water Quality Change over Time", "Water Quality and Health", "Water Quality and Demographics"]
    for col, section in zip(cols, sections):
        with col:
            if st.button(f"Go to {section}"):
                st.session_state.current_section = section
