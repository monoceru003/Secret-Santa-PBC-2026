import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import random
import time
import streamlit.components.v1 as components

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Secret Santa Christmas Lunch",
    page_icon="🎄",
    layout="centered"
)

# --- KONEKSI GOOGLE SHEETS ---
@st.cache_resource
def init_connection():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scopes
    )
    client = gspread.authorize(creds)
    return client

def get_sheets():
    client = init_connection()
    sh = client.open_by_url(st.secrets["sheet_url"])
    return sh.worksheet("PESERTA"), sh.worksheet("CONFIG")

@st.cache_data(ttl=15)
def load_data():
    ws_peserta, ws_config = get_sheets()
    
    # Load Config
    config_records = ws_config.get_all_records()
    config = {str(row["KEY"]).strip(): str(row["VALUE"]).strip() for row in config_records}
    
    # Load Peserta
    peserta_records = ws_peserta.get_all_records()
    df = pd.DataFrame(peserta_records)
    if df.empty:
        df = pd.DataFrame(columns=["NAMA", "WISHLIST_LINK", "CATATAN", "WISHLIST_LOCKED", "SUDAH_SPIN", "GIFTEE"])
