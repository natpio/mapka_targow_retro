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

    /* Tło i główny styl */
    .stApp {
        background-color: #f4e9d8; /* Postarzany papier / kremowy */
    }

    /* Nagłówek w stylu Coca-Cola */
    .retro-title {
        font-family: 'Abril Fatface', serif;
        color: #e61e2a; /* Czerwień klasyczna */
        text-align: center;
        font-size: 50px;
        text-shadow: 3px 3px 0px #ffffff, 5px 5px 0px rgba(0,0,0,0.1);
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

    /* Styl tabeli */
    .stDataFrame {
        border: 2px solid #e61e2a;
    }

    /* Sidebar stylizowany na starą tablicę ogłoszeń */
    [data-testid="stSidebar"] {
        background-color: #2b2b2b;
    }
    [data-testid="stSidebar"] * {
        color: #f4e9d8 !important;
        font-family: 'Courier Prime', monospace;
    }

    /* Przyciski i interakcje */
    button {
        background-color: #e61e2a !important;
        color: white !important;
        border-radius: 0px !important;
        border: 2px solid white !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- FUNKCJE DANYCH ---

def load_data(sheet_name):
    # Link do Twojego arkusza w formacie CSV
    base_url = "https://docs.google.com/spreadsheets/d/1DiYcP2P8AbZqq-FDxcLAoPRa9ffsyDf1jO31Bil8t_A/gviz/tq?tqx=out:csv&sheet="
    url = f"{base_url}{sheet_name}"
    try:
        # Odczytujemy arkusz (pomijając edycję)
        df = pd.read_csv(url)
        return df
    except Exception as e:
        st.error(f"Nie udało się pobrać danych z arkusza {sheet_name}: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=3600) # Cache na godzinę, by nie blokować geokodera
def get_coordinates(city_name):
    geolocator = Nominatim(user_agent="sqm_logistics_app")
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)
    try:
        location = geolocator.geocode(city_name)
        if location:
            return location.latitude, location.longitude
        return None, None
    except:
        return None, None

def extract_city(fair_name):
    # Próba wyciągnięcia ostatniego słowa (często miasto w Twoim arkuszu, np. "BTL LISBOA")
    words = str(fair_name).split()
    if len(words) > 1:
        return words[-1]
    return fair_name

# --- PROCESOWANIE DANYCH ---

st.markdown('<p class="retro-title">SQM MULTIMEDIA SOLUTIONS</p>', unsafe_allow_html=True)
st.markdown('<p class="retro-subtitle">LOGISTYKA TRANSPORTOWA - MONITORING TARGÓW</p>', unsafe_allow_html=True)

# Pobieranie danych
df1 = load_data("targi_DUKIEL")
df2 = load_data("targi_KACZMAREK")
full_df = pd.concat([df1, df2], ignore_index=True)

# Mapa kolorów statusu
status_colors = {
    "W TRAKCIE": "red",
    "OCZEKUJE": "orange",
    "ZAKOŃCZONE": "gray"
}

# Tworzenie mapy
m = folium.Map(location=[50.0, 15.0], zoom_start=4, tiles="CartoDB style", control_scale=True)

# Kontener na dane mapy
locations_found = 0

for idx, row in full_df.iterrows():
    fair_name = row['Nazwa Targów']
    city = extract_city(fair_name)
    lat, lon = get_coordinates(city)
    
    if lat and lon:
        locations_found += 1
        status = str(row['Status']).upper()
        marker_color = status_colors.get(status, "blue")
        
        # Treść dymka (Popup) w stylu retro
        popup_html = f"""
        <div style="font-family: 'Courier New'; width: 200px; border: 2px solid #e61e2a; padding: 10px; background-color: #f4e9d8;">
            <b style="color: #e61e2a; font-size: 14px;">{fair_name}</b><br>
            <hr style="border: 1px solid #e61e2a;">
            <b>LOGISTYK:</b> {row['Logistyk']}<br>
            <b>STATUS:</b> {status}<br>
            <b>WYJAZD:</b> {row['Pierwszy wyjazd']}<br>
            <b>POWRÓT:</b> {row['Data końca']}
        </div>
        """
        
        folium.Marker(
            [lat, lon],
            popup=folium.Popup(popup_html, max_width=250),
            icon=folium.Icon(color=marker_color, icon='truck', prefix='fa'),
            tooltip=f"{fair_name} - {status}"
        ).add_to(m)

# --- LAYOUT APLIKACJI ---

col_map, col_info = st.columns([3, 1])

with col_map:
    st_folium(m, width="100%", height=600)

with col_info:
    st.markdown("### LEGENDA")
    st.markdown("🔴 **W TRAKCIE** (Transport/Montaż)")
    st.markdown("🟡 **OCZEKUJE** (Planowanie)")
    st.markdown("⚪ **POZOSTAŁE**")
    st.divider()
    st.markdown("### STATYSTYKI")
    st.metric("Liczba targów", len(full_df))
    st.metric("Zlokalizowano na mapie", locations_found)
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/ce/Coca-Cola_logo.svg/512px-Coca-Cola_logo.svg.png", width=150)

st.markdown("### 📋 PEŁNA LISTA OPERACJI")
# Wyświetlamy tylko kluczowe kolumny dla logistyki
display_cols = ['Nazwa Targów', 'Pierwszy wyjazd', 'Data końca', 'Status', 'Logistyk', 'Auta', 'Zajętość auta']
st.table(full_df[display_cols])
