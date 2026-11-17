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
    else:
        for col in ["NAMA", "WISHLIST_LINK", "CATATAN", "WISHLIST_LOCKED", "SUDAH_SPIN", "GIFTEE"]:
            if col not in df.columns:
                df[col] = ""
            df[col] = df[col].astype(str).str.strip()
            
    return df, config

def is_true(val):
    return str(val).strip().upper() in ["TRUE", "1", "YES", "YA"]

# --- FUNGSI UPDATE DATABASE ---
def save_wishlist(nama, link, catatan):
    ws_peserta, _ = get_sheets()
    cell = ws_peserta.find(nama, in_column=1)
    if cell:
        row = cell.row
        ws_peserta.update_cell(row, 2, link)
        ws_peserta.update_cell(row, 3, catatan)
        ws_peserta.update_cell(row, 4, "TRUE")

def execute_spin(spinner_nama):
    ws_peserta, _ = get_sheets()
    df, _ = load_data()
    
    # Cek ulang di server apakah spinner sudah pernah spin
    spinner_row_data = df[df["NAMA"] == spinner_nama].iloc[0]
    if is_true(spinner_row_data["SUDAH_SPIN"]):
        return None, "ALREADY_SPUN"

    # Daftar orang yang sudah terpilih sebagai Giftee
    taken_giftees = set(df[df["GIFTEE"] != ""]["GIFTEE"].tolist())
    
    #
