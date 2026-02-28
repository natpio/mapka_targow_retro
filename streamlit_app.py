import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
import re
import time

# Konfiguracja strony
st.set_page_config(page_title="SQM Retro Logistics Hub", layout="wide")

# --- ROZBUDOWANA STYLIZACJA RETRO ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Abril+Fatface&family=Bungee+Shade&family=Courier+Prime:wght@400;700&display=swap');

    /* Tło z teksturą starego papieru */
    .stApp {
        background-color: #f4e9d8;
        background-image: url("https://www.transparenttextures.com/patterns/paper-fibers.png");
    }

    /* Nagłówek Coca-Cola Style */
    .retro-title {
        font-family: 'Abril Fatface', serif;
        color: #e61e2a; 
        text-align: center;
        font-size: 65px;
        line-height: 1;
        text-shadow: 3px 3px 0px #ffffff, 6px 6px 0px rgba(0,0,0,0.1);
        margin-bottom: 0px;
    }

    .retro-subtitle {
        font-family: 'Courier Prime', monospace;
        color: #2b2b2b;
        text-align: center;
        font-weight: bold;
        font-size: 18px;
        letter-spacing: 3px;
        text-transform: uppercase;
        border-top: 3px double #e61e2a;
        border-bottom: 3px double #e61e2a;
        padding: 5px 0;
        margin: 10px auto 30px auto;
        width: 80%;
    }

    /* Stylizacja Sidebar (Panel Sterowania) */
    section[data-testid="stSidebar"] {
        background-color: #2b2b2b !important;
        border-right: 5px solid #e61e2a;
    }
    
    section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] label {
        color: #f4e9d8 !important;
        font-family: 'Abril Fatface', serif !important;
        font-size: 24px !important;
    }

    /* Stylizacja tabel i ekspanderów */
    .stExpander {
        background-color: rgba(255, 255, 255, 0.5);
        border: 2px solid #e61e2a !important;
        border-radius: 0px !important;
    }

    /* Karty statystyk (Metrics) */
    div[data-testid="stMetricValue"] {
        font-family: 'Bungee Shade', cursive;
        color: #e61e2a !important;
    }
    
    /* Przyciski */
    .stButton>button {
        border-radius: 0px;
        background-color: #e61e2a;
        color: white;
        font-family: 'Courier Prime', monospace;
        font-weight: bold;
        border: 2px solid #2b2b2b;
    }
    </style>
    """, unsafe_allow_html=True)

# --- FUNKCJE DANYCH ---

def load_data(sheet_name):
    base_url = "https://docs.google.com/spreadsheets/d/1DiYcP2P8AbZqq-FDxcLAoPRa9ffsyDf1jO31Bil8t_A/gviz/tq?tqx=out:csv&sheet="
    url = f"{base_url}{sheet_name}"
    try:
        df = pd.read_csv(url)
        return df
    except:
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def get_coordinates(fair_name):
    geolocator = Nominatim(user_agent="sqm_logistics_v4")
    text = str(fair_name).upper()
    text = re.sub(r'\d{4}', '', text) # Usuń rok
    if '/' in text: text = text.split('/')[-1] # Miasto po /
    
    # Usuwanie zbędnych słów branżowych
    for word in ['EUROSHOP', 'BTL', 'ITB', 'ECR', 'JEC', 'PROWEIN', 'KUBECON', 'STOM', 'IFAT', 'DTW']:
        text = text.replace(word, '')
    
    city = text.strip()
    try:
        location = geolocator.geocode(city, timeout=5)
        if location: return location.latitude, location.longitude
        return None, None
    except:
        return None, None

# --- LOGIKA FILTROWANIA (SIDEBAR) ---

st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/ce/Coca-Cola_logo.svg/512px-Coca-Cola_logo.svg.png", width=200)
st.sidebar.markdown("---")
st.sidebar.header("PANEL STEROWANIA")

# Checkboxy do filtrowania statusów
show_w_trakcie = st.sidebar.checkbox("🔴 POKAŻ: W TRAKCIE", value=True)
show_oczekuje = st.sidebar.checkbox("🟡 POKAŻ: OCZEKUJE", value=True)

# Pobieranie i łączenie danych
df1 = load_data("targi_DUKIEL")
df2 = load_data("targi_KACZMAREK")
full_df = pd.concat([df1, df2], ignore_index=True)

# Aplikowanie filtrów statusu
allowed_statuses = []
if show_w_trakcie: allowed_statuses.append("W TRAKCIE")
if show_oczekuje: allowed_statuses.append("OCZEKUJE")

filtered_df = full_df[full_df['Status'].str.upper().isin(allowed_statuses)]

# --- INTERFEJS GŁÓWNY ---

st.markdown('<p class="retro-title">SQM MULTIMEDIA</p>', unsafe_allow_html=True)
st.markdown('<p class="retro-subtitle">Dispatch & Logistics Division - 1950s Terminal</p>', unsafe_allow_html=True)

# Statystyki w stylu retro
c1, c2, c3 = st.columns(3)
with c1: st.metric("AKTYWNE TRASY", len(filtered_df))
with c2: st.metric("LOGISTYCY", "2")
with c3: st.metric("FLOTA", "SQM TRUCKS")

# Mapa
m = folium.Map(location=[50.0, 15.0], zoom_start=4, tiles="cartodbpositron")
locations_count = 0

for idx, row in filtered_df.iterrows():
    lat, lon = get_coordinates(row['Nazwa Targów'])
    if lat and lon:
        locations_count += 1
        color = "red" if row['Status'].upper() == "W TRAKCIE" else "orange"
        
        folium.Marker(
            [lat, lon],
            popup=folium.Popup(f"<b>{row['Nazwa Targów']}</b><br>Logistyk: {row['Logistyk']}", max_width=200),
            icon=folium.Icon(color=color, icon='truck', prefix='fa'),
            tooltip=row['Nazwa Targów']
        ).add_to(m)

# Wyświetlanie Mapy
st_folium(m, width="100%", height=550, key="logistics_map")

st.markdown("---")

# ZWIJALNA LISTA OPERACYJNA (Expander)
with st.expander("📂 KLIKNIJ, ABY ROZWINĄĆ PEŁNĄ LISTĘ OPERACYJNĄ"):
    st.markdown("### Raport bieżący")
    st.dataframe(
        filtered_df.style.set_properties(**{'background-color': '#ffffff', 'color': '#2b2b2b', 'border-color': '#e61e2a'}),
        use_container_width=True
    )

# Stopka Pin-up
st.sidebar.markdown("---")
st.sidebar.markdown("""
    <div style='text-align: center; color: #f4e9d8; font-family: Courier;'>
        <p>RELIABLE SERVICE</p>
        <img src='https://i.pinimg.com/originals/94/f0/2d/94f02d08a984489b331006a88b8f2d50.png' width='150'>
        <p>KEEP 'EM ROLLING!</p>
    </div>
    """, unsafe_allow_html=True)
