import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
import re
import time

# Konfiguracja strony
st.set_page_config(page_title="SQM Logistics Retro Terminal", layout="wide")

# --- STYLIZACJA RETRO ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Abril+Fatface&family=Courier+Prime:wght@400;700&display=swap');
    .stApp { background-color: #f4e9d8; }
    .retro-title {
        font-family: 'Abril Fatface', serif;
        color: #e61e2a; 
        text-align: center;
        font-size: 50px;
        text-shadow: 2px 2px 0px #ffffff;
        margin: 0;
    }
    .retro-subtitle {
        font-family: 'Courier Prime', monospace;
        color: #333;
        text-align: center;
        font-weight: bold;
        border-bottom: 2px solid #e61e2a;
        margin-bottom: 20px;
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
    geolocator = Nominatim(user_agent="sqm_logistics_final")
    
    # --- PROCES CZYSZCZENIA NAZWY ---
    text = str(fair_name).upper()
    
    # 1. Usuń rok (np. 2026)
    text = re.sub(r'\d{4}', '', text)
    
    # 2. Jeśli jest ukośnik, bierzemy to co po ukośniku (często tam jest miasto)
    if '/' in text:
        text = text.split('/')[-1]
    
    # 3. Usuń popularne nazwy targów, które mylą geokoder
    blacklist = ['EUROSHOP', 'BTL', 'ITB', 'ECR', 'JEC WORLD', 'PROWEIN', 'KUBECON', 'XPONENTIAL', 'EBCC', 'STOM', 'DMEA', 'ESCMID', 'IFAT', 'DTW', 'SALONE DEL MOBILE']
    for word in blacklist:
        text = text.replace(word, '')
    
    # 4. Wyczyść białe znaki
    city_candidate = text.strip()
    
    if not city_candidate:
        return None, None

    try:
        # Próba geokodowania czystego miasta
        location = geolocator.geocode(city_candidate, timeout=10)
        if location:
            return location.latitude, location.longitude
        
        # Próba ostatniej szansy: samo ostatnie słowo
        last_word = city_candidate.split()[-1]
        location = geolocator.geocode(last_word, timeout=10)
        if location:
            return location.latitude, location.longitude
            
        return None, None
    except:
        return None, None

# --- GŁÓWNA LOGIKA ---

st.markdown('<p class="retro-title">SQM MULTIMEDIA SOLUTIONS</p>', unsafe_allow_html=True)
st.markdown('<p class="retro-subtitle">LOGISTYKA TRANSPORTOWA - MONITORING TARGÓW</p>', unsafe_allow_html=True)

df1 = load_data("targi_DUKIEL")
df2 = load_data("targi_KACZMAREK")
full_df = pd.concat([df1, df2], ignore_index=True)

# Mapa
m = folium.Map(location=[50.0, 15.0], zoom_start=4, tiles="cartodbpositron")

locations_found = 0
status_colors = {
    "W TRAKCIE": "red",
    "OCZEKUJE": "orange",
    "ZAKOŃCZONE": "lightgray"
}

# Iteracja i nakładanie punktów
for idx, row in full_df.iterrows():
    lat, lon = get_coordinates(row['Nazwa Targów'])
    
    if lat and lon:
        locations_found += 1
        status = str(row['Status']).upper()
        marker_color = status_colors.get(status, "blue")
        
        popup_content = f"""
        <div style="font-family: 'Courier New'; width: 160px; font-size: 12px;">
            <b style="color: #e61e2a;">{row['Nazwa Targów']}</b><br>
            <hr style="margin: 5px 0;">
            <b>Status:</b> {status}<br>
            <b>Logistyk:</b> {row['Logistyk']}<br>
            <b>Auto:</b> {row['Auta']}
        </div>
        """
        
        folium.Marker(
            [lat, lon],
            popup=folium.Popup(popup_content, max_width=200),
            icon=folium.Icon(color=marker_color, icon='truck', prefix='fa'),
            tooltip=row['Nazwa Targów']
        ).add_to(m)
    # Krótka pauza, by nie zablokować geokodera przy starcie
    if idx % 5 == 0:
        time.sleep(0.1)

# --- LAYOUT ---
col_map, col_info = st.columns([3, 1])

with col_map:
    st_folium(m, width="100%", height=600, key="main_map")

with col_info:
    st.markdown("### LEGENDA")
    st.markdown("🔴 **W TRAKCIE**")
    st.markdown("🟡 **OCZEKUJE**")
    st.divider()
    st.metric("Wszystkie wpisy", len(full_df))
    st.metric("Zlokalizowane", locations_found)
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/ce/Coca-Cola_logo.svg/512px-Coca-Cola_logo.svg.png", width=120)

st.markdown("### 📋 PEŁNA LISTA OPERACYJNA")
st.dataframe(full_df, use_container_width=True)
