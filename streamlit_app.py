import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
import re
import time

# --- KONFIGURACJA STRONY ---
st.set_page_config(
    page_title="SQM Logistics Retro Terminal",
    page_icon="🚛",
    layout="wide"
)

# --- STYLIZACJA CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Abril+Fatface&family=Bungee+Shade&family=Courier+Prime:wght@400;700&display=swap');
    .stApp { background-color: #f4e9d8; background-image: url("https://www.transparenttextures.com/patterns/paper-fibers.png"); }
    .retro-title { font-family: 'Abril Fatface', serif; color: #e61e2a; text-align: center; font-size: 60px; text-shadow: 2px 2px 0px #ffffff; margin: 0; }
    .retro-subtitle { font-family: 'Courier Prime', monospace; color: #2b2b2b; text-align: center; font-weight: bold; border-top: 3px double #e61e2a; border-bottom: 3px double #e61e2a; padding: 5px 0; margin-bottom: 20px; }
    section[data-testid="stSidebar"] { background-color: #2b2b2b !important; border-right: 5px solid #e61e2a; }
    section[data-testid="stSidebar"] * { color: #f4e9d8 !important; }
    .stMetric { background: rgba(255,255,255,0.2); padding: 10px; border: 1px solid #e61e2a; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNKCJE ---

def load_data(sheet_name):
    # Link do Twojego arkusza
    base_url = "https://docs.google.com/spreadsheets/d/1DiYcP2P8AbZqq-FDxcLAoPRa9ffsyDf1jO31Bil8t_A/gviz/tq?tqx=out:csv&sheet="
    url = f"{base_url}{sheet_name}"
    try:
        df = pd.read_csv(url)
        # USUWANIE PROBLEMÓW Z NAZWAMI KOLUMN:
        df.columns = df.columns.str.strip() # usuwa spacje na końcach
        return df
    except:
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def get_coordinates(fair_name):
    geolocator = Nominatim(user_agent="sqm_logistics_v5")
    text = str(fair_name).upper()
    text = re.sub(r'\d{4}', '', text)
    if '/' in text: text = text.split('/')[-1]
    
    # Lista słów do wycięcia przed szukaniem na mapie
    for word in ['EUROSHOP', 'BTL', 'ITB', 'ECR', 'JEC', 'PROWEIN', 'STOM', 'IFAT']:
        text = text.replace(word, '')
    
    city = text.strip()
    try:
        location = geolocator.geocode(city, timeout=5)
        if location: return location.latitude, location.longitude
        return None, None
    except:
        return None, None

# --- PANEL BOCZNY ---
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/ce/Coca-Cola_logo.svg/512px-Coca-Cola_logo.svg.png", width=180)
st.sidebar.title("FILTRY")
f_w_trakcie = st.sidebar.checkbox("🔴 POKAŻ: W TRAKCIE", value=True)
f_oczekuje = st.sidebar.checkbox("🟡 POKAŻ: OCZEKUJE", value=True)

# --- PRZETWARZANIE DANYCH ---

df_d = load_data("targi_DUKIEL")
df_k = load_data("targi_KACZMAREK")
full_df = pd.concat([df_d, df_k], ignore_index=True)

# Debugowanie - sprawdzanie czy dane w ogóle są (widoczne tylko dla Ciebie podczas testów)
if full_df.empty:
    st.error("BŁĄD: Arkusze są puste lub link jest nieaktywny.")
    st.stop()

# Filtrowanie (uodpornione na wielkość liter)
# Sprawdzamy czy kolumna 'Status' istnieje
if 'Status' in full_df.columns:
    mask = []
    if f_w_trakcie: mask.append("W TRAKCIE")
    if f_oczekuje: mask.append("OCZEKUJE")
    
    # Filtrujemy dane
    display_df = full_df[full_df['Status'].str.upper().isin(mask)]
else:
    st.warning("Nie znaleziono kolumny 'Status' w arkuszu.")
    display_df = full_df

# --- WIDOK GŁÓWNY ---

st.markdown('<p class="retro-title">SQM MULTIMEDIA</p>', unsafe_allow_html=True)
st.markdown('<p class="retro-subtitle">Logistics & Transport Terminal</p>', unsafe_allow_html=True)

# Metryki
c1, c2 = st.columns(2)
c1.metric("ŁADUNKI W TRASIE", len(display_df[display_df['Status'].str.upper() == "W TRAKCIE"]))
c2.metric("PLANOWANE (SLOTY)", len(display_df[display_df['Status'].str.upper() == "OCZEKUJE"]))

# MAPA
m = folium.Map(location=[51.0, 15.0], zoom_start=5, tiles="cartodbpositron")
points_count = 0

# Szukamy kolumny z nazwą (może nazywać się 'Nazwa Targów' lub 'Nazwa')
name_col = 'Nazwa Targów' if 'Nazwa Targów' in display_df.columns else display_df.columns[0]

for _, row in display_df.iterrows():
    lat, lon = get_coordinates(row[name_col])
    if lat and lon:
        points_count += 1
        stat = str(row['Status']).upper()
        color = "red" if stat == "W TRAKCIE" else "orange"
        
        folium.Marker(
            [lat, lon],
            popup=f"<b>{row[name_col]}</b><br>Logistyk: {row.get('Logistyk', 'N/A')}",
            icon=folium.Icon(color=color, icon='truck', prefix='fa')
        ).add_to(m)

# Wyświetlenie mapy
st_folium(m, width="100%", height=500, key="mapa_v5")

st.markdown("### 🔍 Zlokalizowano na mapie: " + str(points_count))

# ZWIJALNA TABELA
with st.expander("📂 PEŁNA LISTA OPERACYJNA (KLIKNIJ BY ROZWINĄĆ)"):
    st.table(display_df)
