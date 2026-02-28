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
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- PEŁNA STYLIZACJA RETRO (CSS) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Abril+Fatface&family=Bungee+Shade&family=Courier+Prime:wght@400;700&display=swap');

    /* Główny kontener z teksturą starego papieru */
    .stApp {
        background-color: #f4e9d8;
        background-image: url("https://www.transparenttextures.com/patterns/paper-fibers.png");
    }

    /* Nagłówek w stylu Vintage Coca-Cola */
    .retro-title {
        font-family: 'Abril Fatface', serif;
        color: #e61e2a; 
        text-align: center;
        font-size: 70px;
        line-height: 1.1;
        text-shadow: 3px 3px 0px #ffffff, 6px 6px 0px rgba(0,0,0,0.1);
        margin-top: 20px;
        margin-bottom: 0px;
    }

    .retro-subtitle {
        font-family: 'Courier Prime', monospace;
        color: #2b2b2b;
        text-align: center;
        font-weight: bold;
        font-size: 20px;
        letter-spacing: 4px;
        text-transform: uppercase;
        border-top: 4px double #e61e2a;
        border-bottom: 4px double #e61e2a;
        padding: 8px 0;
        margin: 15px auto 40px auto;
        width: 85%;
    }

    /* Sidebar stylizowany na tablicę rozdzielczą */
    section[data-testid="stSidebar"] {
        background-color: #2b2b2b !important;
        border-right: 6px solid #e61e2a;
    }
    
    section[data-testid="stSidebar"] .stMarkdown, section[data-testid="stSidebar"] label {
        color: #f4e9d8 !important;
        font-family: 'Courier Prime', monospace !important;
    }

    /* Stylizacja expandera (listy operacyjnej) */
    .stExpander {
        border: 2px solid #e61e2a !important;
        background-color: rgba(255, 255, 255, 0.4) !important;
        border-radius: 0px !important;
    }

    /* Nagłówki wewnątrz aplikacji */
    h1, h2, h3 {
        font-family: 'Abril Fatface', serif !important;
        color: #e61e2a !important;
    }

    /* Customowe metryki */
    div[data-testid="stMetricValue"] {
        font-family: 'Bungee Shade', cursive !important;
        color: #e61e2a !important;
        font-size: 40px !important;
    }
    
    /* Tabela danych */
    .stDataFrame {
        border: 1px solid #e61e2a;
    }
    </style>
    """, unsafe_allow_html=True)

# --- FUNKCJE POMOCNICZE ---

def load_data(sheet_name):
    """Pobiera dane z Google Sheets bez możliwości edycji."""
    base_url = "https://docs.google.com/spreadsheets/d/1DiYcP2P8AbZqq-FDxcLAoPRa9ffsyDf1jO31Bil8t_A/gviz/tq?tqx=out:csv&sheet="
    url = f"{base_url}{sheet_name}"
    try:
        df = pd.read_csv(url)
        return df
    except Exception as e:
        st.error(f"Krytyczny błąd połączenia z arkuszem {sheet_name}: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def get_coordinates(fair_name):
    """Zaawansowane wyodrębnianie miasta i geokodowanie."""
    geolocator = Nominatim(user_agent="sqm_logistics_final_system")
    
    # Czyszczenie nazwy w celu znalezienia miasta
    text = str(fair_name).upper()
    text = re.sub(r'\d{4}', '', text) # Usuń rok (2025, 2026 itp.)
    
    if '/' in text:
        # Priorytet dla tekstu po ukośniku (często miasto)
        text = text.split('/')[-1]
    
    # Lista słów do usunięcia, które nie są miastami
    junk_words = ['EUROSHOP', 'BTL', 'ITB', 'ECR', 'JEC WORLD', 'PROWEIN', 'KUBECON', 
                  'XPONENTIAL', 'EBCC', 'STOM', 'DMEA', 'ESCMID', 'IFAT', 'DTW', 
                  'SALONE DEL MOBILE', 'TARGI', 'EXHIBITION', 'SHOW']
    
    for word in junk_words:
        text = text.replace(word, '')
    
    city_candidate = text.strip()
    
    if not city_candidate:
        return None, None

    try:
        # Próba 1: Cała wyczyszczona nazwa
        location = geolocator.geocode(city_candidate, timeout=10)
        if location:
            return location.latitude, location.longitude
        
        # Próba 2: Tylko ostatnie słowo (najczęstsza lokalizacja miasta)
        last_word = city_candidate.split()[-1]
        location = geolocator.geocode(last_word, timeout=10)
        if location:
            return location.latitude, location.longitude
            
        return None, None
    except:
        return None, None

# --- SIDEBAR - PANEL STEROWANIA ---

st.sidebar.markdown("<br>", unsafe_allow_html=True)
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/ce/Coca-Cola_logo.svg/512px-Coca-Cola_logo.svg.png", width=220)
st.sidebar.markdown("<h2 style='text-align:center; color:white;'>CONTROL PANEL</h2>", unsafe_allow_html=True)
st.sidebar.markdown("---")

st.sidebar.subheader("FILTRY STATUSU")
filter_w_trakcie = st.sidebar.checkbox("🔴 POKAŻ: W TRAKCIE", value=True)
filter_oczekuje = st.sidebar.checkbox("🟡 POKAŻ: OCZEKUJE", value=True)

st.sidebar.markdown("---")
st.sidebar.subheader("INFO")
st.sidebar.info("Aplikacja odczytuje dane z arkuszy DUKIEL i KACZMAREK w czasie rzeczywistym.")

# --- POBIERANIE I ŁĄCZENIE DANYCH ---

with st.spinner('Ładowanie danych z terminali...'):
    df_d = load_data("targi_DUKIEL")
    df_k = load_data("targi_KACZMAREK")
    
    # Łączymy oba arkusze w jeden DataFrame
    full_df = pd.concat([df_d, df_k], ignore_index=True)

# Filtrowanie na podstawie checkboxów
active_filters = []
if filter_w_trakcie: active_filters.append("W TRAKCIE")
if filter_oczekuje: active_filters.append("OCZEKUJE")

# Filtracja (ignoruje wielkość liter dla bezpieczeństwa)
display_df = full_df[full_df['Status'].str.upper().isin(active_filters)].copy()

# --- GŁÓWNA SEKCJA WIZUALNA ---

st.markdown('<p class="retro-title">SQM MULTIMEDIA SOLUTIONS</p>', unsafe_allow_html=True)
st.markdown('<p class="retro-subtitle">Logistics & Dispatch Division • Road Map 2026</p>', unsafe_allow_html=True)

# Statystyki (Metrics)
m1, m2, m3 = st.columns(3)
with m1:
    st.metric("AKTYWNE OPERACJE", len(display_df))
with m2:
    st.metric("DOSTĘPNE AUTA", "AUTO-DETECT")
with m3:
    st.metric("REGION", "EUROPE")

# --- MAPA OPERACYJNA ---

# Inicjalizacja mapy (styl CartoDB Positron jest najbardziej czytelny dla retro pinezek)
m = folium.Map(location=[51.0, 10.0], zoom_start=5, tiles="cartodbpositron")

found_on_map = 0
status_colors = {
    "W TRAKCIE": "red",
    "OCZEKUJE": "orange"
}

for idx, row in display_df.iterrows():
    lat, lon = get_coordinates(row['Nazwa Targów'])
    
    if lat and lon:
        found_on_map += 1
        current_status = str(row['Status']).upper()
        m_color = status_colors.get(current_status, "blue")
        
        # Retro Popup
        popup_html = f"""
        <div style="font-family: 'Courier New'; width: 200px; border: 2px solid #e61e2a; padding: 10px; background-color: #f4e9d8;">
            <b style="color: #e61e2a; font-size: 14px;">{row['Nazwa Targów']}</b><br>
            <hr style="border: 0.5px solid #e61e2a;">
            <b>LOGISTYK:</b> {row['Logistyk']}<br>
            <b>WYJAZD:</b> {row['Pierwszy wyjazd']}<br>
            <b>STATUS:</b> {current_status}
        </div>
        """
        
        folium.Marker(
            [lat, lon],
            popup=folium.Popup(popup_html, max_width=250),
            icon=folium.Icon(color=m_color, icon='truck', prefix='fa'),
            tooltip=f"{row['Nazwa Targów']} ({row['Logistyk']})"
        ).add_to(m)
    
    # Krótki sleep, aby nie przekroczyć limitów darmowego geokodera przy dużym arkuszu
    if idx % 10 == 0:
        time.sleep(0.05)

# Wyświetlenie mapy na pełną szerokość
st_folium(m, width="100%", height=600, key="sqm_map_v1")

st.markdown("<br>", unsafe_allow_html=True)

# --- ZWIJALNA LISTA (EXPANDER) ---

with st.expander("📂 OTWÓRZ PEŁNĄ LISTĘ OPERACYJNĄ (TABELA DANYCH)"):
    st.markdown("### Raport szczegółowy z arkuszy Google")
    # Zastosowanie stylu do tabeli
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )

# --- STOPKA SIDEBARA (PIN-UP ACCENT) ---
st.sidebar.markdown("---")
st.sidebar.markdown("""
    <div style='text-align: center;'>
        <p style='font-family: Courier; font-size: 12px; color: #f4e9d8;'>SQM LOGISTICS DEPT.<br>EST. 2026</p>
        <img src='https://i.pinimg.com/originals/94/f0/2d/94f02d08a984489b331006a88b8f2d50.png' width='140' style='filter: sepia(100%) contrast(120%);'>
        <p style='font-family: Courier; font-size: 10px; color: #f4e9d8;'>KEEP 'EM ROLLING!</p>
    </div>
    """, unsafe_allow_html=True)
