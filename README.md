# Basic Information

## Team Member

- Aziz Zafar (az2798)
- Naufa Amirani (nfa2120)
- Di Liu (dl3738)

# Installation

## Publicly Available Website

We host our website [here](https://groupftbd-bntxpudsxzmibfu3iayopw.streamlit.app/) for your easy access.

## Local Installation

To run the website on your local machine **for better performance**, please follow the instruction

1. Clone the repo, run

```bash
git clone https://github.com/QMSS-G5063-2025/Group_F_TBD.git
cd Group_F_TBD
```

2. Setup the environment, run 

```bash
pip install -r requirements.txt
```

or manually install the required packages

```bash
pip install streamlit==1.44.1 plotly==6.0.1 geopandas==1.0.1 matplotlib==3.10.1 streamlit-aggrid==1.1.3 statsmodels==0.14.4
```

Note that the website is tested under `python 3.11.12`.

3. Launch the app

```bash
streamlit run App/main.py
```

# Repo Organization

- App: source code for website
- data: source data for visualization
- Documents: procedural documents, including [project proposal](./Documents/Data_Visualization_Proposal.pdf).
- scripts: data processing scripts

# Data Source

- [Water Quality Data in NYC](https://data.cityofnewyork.us/Environment/Drinking-Water-Quality-Distribution-Monitoring-Dat/bkwf-xfky/about_data)
- [Neighboorhood Health Data](https://public.tableau.com/app/profile/nyc.health/viz/NewYorkCityNeighborhoodHealthAtlas/Home)