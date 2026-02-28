import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from datetime import datetime
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

# Konfiguracja strony
st.set_page_config(page_title="SQM Logistics Retro Terminal", layout="wide")

# --- STYLIZACJA RETRO (Coca-Cola / Pin-up) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Abril+Fatface&family=Courier+Prime:wght@400;700&display=swap');

    .stApp {
        background-color: #f4e9d8; 
    }

    .retro-title {
        font-family: 'Abril Fatface', serif;
        color: #e61e2a; 
        text-align: center;
        font-size: 50px;
        text-shadow: 3px 3px 0px #ffffff;
        margin-bottom: 0px;
        padding-top: 20px;
    }

    .retro-subtitle {
        font-family: 'Courier Prime', monospace;
        color: #333;
        text-align: center;
        font-weight: bold;
        letter-spacing: 2px;
        border-bottom: 2px solid #e61e2a;
        margin-bottom: 30px;
    }

    [data-testid="stSidebar"] {
        background-color: #2b2b2b;
    }
    [data-testid="stSidebar"] * {
        color: #f4e9d8 !important;
        font-family: 'Courier Prime', monospace;
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
    except Exception as e:
        st.error(f"Nie udało się pobrać danych z arkusza {sheet_name}")
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def get_coordinates(city_name):
    geolocator = Nominatim(user_agent="sqm_logistics_v2")
    try:
        location = geolocator.geocode(city_name)
        if location:
            return location.latitude, location.longitude
        return None, None
    except:
        return None, None

def extract_city(fair_name):
    words = str(fair_name).split()
    if len(words) > 1:
        return words[-1]
    return fair_name

# --- GŁÓWNA LOGIKA ---

st.markdown('<p class="retro-title">SQM MULTIMEDIA SOLUTIONS</p>', unsafe_allow_html=True)
st.markdown('<p class="retro-subtitle">LOGISTYKA TRANSPORTOWA - MONITORING TARGÓW</p>', unsafe_allow_html=True)

df1 = load_data("targi_DUKIEL")
df2 = load_data("targi_KACZMAREK")
full_df = pd.concat([df1, df2], ignore_index=True)

# Definicja mapy z poprawionym parametrem tiles
m = folium.Map(
    location=[52.0, 19.0], 
    zoom_start=5, 
    tiles="cartodbpositron" # Zmienione z "CartoDB style"
)

locations_found = 0
status_colors = {
    "W TRAKCIE": "red",
    "OCZEKUJE": "orange",
    "ZAKOŃCZONE": "gray"
}

for idx, row in full_df.iterrows():
    fair_name = row['Nazwa Targów']
    city = extract_city(fair_name)
    lat, lon = get_coordinates(city)
    
    if lat and lon:
        locations_found += 1
        status = str(row['Status']).upper()
        marker_color = status_colors.get(status, "blue")
        
        popup_html = f"""
        <div style="font-family: 'Courier New'; width: 180px; border: 2px solid #e61e2a; padding: 5px; background-color: #f4e9d8;">
            <b style="color: #e61e2a;">{fair_name}</b><br>
            <small>Logistyk: {row['Logistyk']}</small><br>
            <small>Status: {status}</small>
        </div>
        """
        
        folium.Marker(
            [lat, lon],
            popup=folium.Popup(popup_html, max_width=200),
            icon=folium.Icon(color=marker_color, icon='truck', prefix='fa')
        ).add_to(m)

# --- WYŚWIETLANIE ---

col_map, col_info = st.columns([3, 1])

with col_map:
    st_folium(m, width="100%", height=600)

with col_info:
    st.markdown("### LEGENDA")
    st.markdown("🔴 **W TRAKCIE**")
    st.markdown("🟡 **OCZEKUJE**")
    st.divider()
    st.metric("Suma Targów", len(full_df))
    st.metric("Zlokalizowane", locations_found)
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/ce/Coca-Cola_logo.svg/512px-Coca-Cola_logo.svg.png", width=120)

st.markdown("### 📋 SZCZEGÓŁY LOGISTYCZNE")
st.dataframe(full_df)
