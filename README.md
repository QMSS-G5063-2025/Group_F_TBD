# Basic Information

## Team Member

- Aziz Zafar (az2798@cumc.columbia.edu)
- Naufa Amirani (nfa2120@cumc.columbia.edu)
- Di Liu (dl3738@cumc.columbia.edu)

# Installation

## Publicly Available Website

We host our website here.

## Local Installation

To run the website on your local machine, please follow the instruction

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
pip install streamlit==1.44.1
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