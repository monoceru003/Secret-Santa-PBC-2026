import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import random
import time
import threading
from datetime import datetime
import streamlit.components.v1 as components

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Christmas Lunch PBC Veteran 2026",
    page_icon="🎄",
    layout="centered"
)

# --- STYLING & HIASAN TEMA NATAL (CSS) ---
st.markdown("""
<style>
    /* Latar belakang bernuansa hangat & lembut */
    .stApp {
        background: linear-gradient(180deg, #FFFDF9 0%, #F7F2EA 100%);
    }

    /* Animasi Salju Halus */
    @keyframes snowfall {
        0% { transform: translateY(-10vh) rotate(0deg); opacity: 0.85; }
        100% { transform: translateY(105vh) rotate(360deg); opacity: 0.2; }
    }
    .snowflake {
        position: fixed;
        top: -5%;
        color: #D4AF37;
        font-size: 1.1rem;
        user-select: none;
        pointer-events: none;
        z-index: 9999;
        animation: snowfall linear infinite;
    }

    /* Banner Header Natal */
    .christmas-banner {
        background: linear-gradient(135deg, #9B1B1E 0%, #165B33 100%);
        padding: 26px 20px;
        border-radius: 16px;
        text-align: center;
        color: #FFFFFF;
        box-shadow: 0 8px 20px rgba(155, 27, 30, 0.18);
        border: 2px solid #D4AF37;
        margin-bottom: 18px;
    }
    .christmas-banner h1 {
        color: #FFFFFF !important;
        font-size: 1.85rem !important;
        margin: 6px 0 !important;
        text-shadow: 1px 2px 4px rgba(0,0,0,0.3);
        letter-spacing: 0.5px;
    }
    .christmas-ornaments {
        font-size: 1.4rem;
        letter-spacing: 8px;
    }

    /* Kartu Ketentuan Budget */
    .budget-card {
        background-color: #FFFFFF;
        border-left: 5px solid #D42426;
        border-right: 5px solid #165B33;
        border-top: 1px solid #E8DFD1;
        border-bottom: 1px solid #E8DFD1;
        padding: 14px 18px;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.04);
        margin-bottom: 22px;
        font-size: 1.02rem;
        color: #2C2C2C;
    }

    /* Kartu Hasil Undian Giftee */
    .giftee-card {
        background: linear-gradient(135deg, #FFFDF7 0%, #FFF5E4 100%);
        border: 2px solid #D4AF37;
        border-radius: 16px;
        padding: 22px;
        margin: 15px 0;
        box-shadow: 0 6px 18px rgba(212, 175, 55, 0.2);
    }

    /* Kartu Kategori Awarding */
    .award-card {
        background-color: #FFFFFF;
        border: 1px solid #E6DEC8;
        border-left: 5px solid #165B33;
        border-radius: 12px;
        padding: 14px 16px 10px 16px;
        margin-top: 14px;
        margin-bottom: 4px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.03);
    }
    .award-title {
        font-size: 1.05rem;
        font-weight: 700;
        color: #9B1B1E;
        margin-bottom: 3px;
    }
    .award-desc {
        font-size: 0.84rem;
        color: #66605B;
        font-style: italic;
        line-height: 1.35;
    }

    /* Tombol Utama Merah Natal */
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #C82327 0%, #9B1B1E 100%) !important;
        border: 1px solid #D4AF37 !important;
        color: #FFFFFF !important;
        font-weight: 600 !important;
        border-radius: 10px !important;
        box-shadow: 0 4px 10px rgba(155, 27, 30, 0.2) !important;
        transition: transform 0.15s ease !important;
    }
    div.stButton > button[kind="primary"]:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 14px rgba(155, 27, 30, 0.3) !important;
    }
</style>

<!-- Hiasan Salju & Kilau Emas Halus -->
<div class="snowflake" style="left: 8%; animation-duration: 11s; animation-delay: 0s;">❄️</div>
<div class="snowflake" style="left: 22%; animation-duration: 14s; animation-delay: 2s;">✨</div>
<div class="snowflake" style="left: 38%; animation-duration: 10s; animation-delay: 4s;">❄️</div>
<div class="snowflake" style="left: 55%; animation-duration: 13s; animation-delay: 1s;">✨</div>
<div class="snowflake" style="left: 72%; animation-duration: 12s; animation-delay: 3s;">❄️</div>
<div class="snowflake" style="left: 88%; animation-duration: 15s; animation-delay: 5s;">✨</div>
""", unsafe_allow_html=True)

# --- DAFTAR KATEGORI AWARDING ---
AWARD_CATEGORIES = [
    {
        "key": "MINISTER_OF_LAST_MINUTE",
        "title": "1. ⏰ Minister of Last Minute",
        "desc": "Si paling kerjaan dan deadline di last minute"
    },
    {
        "key": "WALKING_BATTERY_LOW",
        "title": "2. 🔋 Walking Battery Low Award",
        "desc": "Energi 1% kerja tapi kerjaan tetep beres somehow"
    },
    {
        "key": "THE_WALKING_CALENDAR",
        "title": "3. 📅 The Walking Calendar",
        "desc": "Si paling tau semua jadwal kantor dll"
    },
    {
        "key": "CEO_OF_OVERTHINKING",
        "title": "4. 🤯 CEO of Overthinking",
        "desc": "Si paling gopoh overthinking"
    },
    {
        "key": "THE_WALKING_GREEN_FLAG",
        "title": "5. ✅ The Walking Green Flag",
        "desc": "Si paling green flag semuanya di kantor"
    }
]

# --- ANTREAN KUNCI SERVER (ANTI-BENTROK SAAT SPIN BERSAMAAN) ---
@st.cache_resource
def get_spin_lock():
    return threading.Lock()

# --- HELPER AUTO-RETRY API GOOGLE SHEETS ---
def api_call_with_retry(func, *args, max_retries=5, **kwargs):
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            err_str = str(e)
            if any(code in err_str for code in ["429", "500", "502", "503", "Quota", "Rate"]):
                if attempt < max_retries - 1:
                    time.sleep(1.5 * (attempt + 1) + random.uniform(0.2, 0.8))
                    continue
            raise e

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

@st.cache_resource
def get_spreadsheet():
    client = init_connection()
    return api_call_with_retry(client.open_by_url, st.secrets["sheet_url"])

def get_sheets():
    sh = get_spreadsheet()
    return (
        api_call_with_retry(sh.worksheet, "PESERTA"),
        api_call_with_retry(sh.worksheet, "CONFIG"),
        api_call_with_retry(sh.worksheet, "VOTING")
    )

def fetch_fresh_peserta_df():
    ws_peserta, _, _ = get_sheets()
    peserta_records = api_call_with_retry(ws_peserta.get_all_records)
    df = pd.DataFrame(peserta_records)
    cols_peserta = ["NAMA", "WISHLIST_LINK", "CATATAN", "WISHLIST_LOCKED", "SUDAH_SPIN", "GIFTEE", "SUDAH_VOTE"]
    if df.empty:
        df = pd.DataFrame(columns=cols_peserta)
    else:
        for col in cols_peserta:
            if col not in df.columns:
                df[col] = ""
            df[col] = df[col].astype(str).str.strip()
    return df, ws_peserta

@st.cache_data(ttl=30)
def load_data():
    ws_peserta, ws_config, ws_voting = get_sheets()
    
    config_records = api_call_with_retry(ws_config.get_all_records)
    config = {str(row["KEY"]).strip(): str(row["VALUE"]).strip() for row in config_records}
    
    peserta_records = api_call_with_retry(ws_peserta.get_all_records)
    df = pd.DataFrame(peserta_records)
    cols_peserta = ["NAMA", "WISHLIST_LINK", "CATATAN", "WISHLIST_LOCKED", "SUDAH_SPIN", "GIFTEE", "SUDAH_VOTE"]
    if df.empty:
        df = pd.DataFrame(columns=cols_peserta)
    else:
        for col in cols_peserta:
            if col not in df.columns:
                df[col] = ""
            df[col] = df[col].astype(str).str.strip()

    voting_records = api_call_with_retry(ws_voting.get_all_records)
    df_voting = pd.DataFrame(voting_records)
    cols_voting = ["TIMESTAMP", "VOTER", "MINISTER_OF_LAST_MINUTE", "WALKING_BATTERY_LOW",
                   "THE_WALKING_CALENDAR", "CEO_OF_OVERTHINKING", "THE_WALKING_GREEN_FLAG"]
    if df_voting.empty:
        df_voting = pd.DataFrame(columns=cols_voting)
    else:
        for col in cols_voting:
            if col not in df_voting.columns:
                df_voting[col] = ""
            df_voting[col] = df_voting[col].astype(str).str.strip()
            
    return df, config, df_voting

def is_true(val):
    return str(val).strip().upper() in ["TRUE", "1", "YES", "YA"]

# --- FUNGSI UPDATE DATABASE ---
def save_wishlist(nama, link, catatan):
    ws_peserta, _, _ = get_sheets()
    cell = api_call_with_retry(ws_peserta.find, nama, in_column=1)
    if cell:
        row = cell.row
        api_call_with_retry(ws_peserta.update, f"B{row}:D{row}", [[link, catatan, "TRUE"]])
    load_data.clear()

def execute_spin(spinner_nama):
    lock = get_spin_lock()
    with lock:
        df, ws_peserta = fetch_fresh_peserta_df()
        
        spinner_row_data = df[df["NAMA"] == spinner_nama].iloc[0]
        if is_true(spinner_row_data["SUDAH_SPIN"]):
            return None, "ALREADY_SPUN", []

        taken_giftees = set(df[df["GIFTEE"] != ""]["GIFTEE"].tolist())
        all_names = df["NAMA"].tolist()
        available_targets = [n for n in all_names if n not in taken_giftees and n != spinner_nama]
        
        if not available_targets:
            return None, "NO_TARGETS", []

        unspun_players = df[~df["SUDAH_SPIN"].apply(is_true)]["NAMA"].tolist()
        remaining_unspun = [n for n in unspun_players if n != spinner_nama]
        
        if len(remaining_unspun) == 1:
            last_player = remaining_unspun[0]
            if last_player in available_targets:
                chosen_giftee = last_player
            else:
                chosen_giftee = random.choice(available_targets)
        else:
            chosen_giftee = random.choice(available_targets)

        cell = api_call_with_retry(ws_peserta.find, spinner_nama, in_column=1)
        if cell:
            row = cell.row
            # Update kolom E & F sekaligus dalam 1 API request
            api_call_with_retry(ws_peserta.update, f"E{row}:F{row}", [["TRUE", chosen_giftee]])
        
        load_data.clear()
        return chosen_giftee, "OK", available_targets

def save_voting(voter_nama, votes_dict):
    lock = get_spin_lock()
    with lock:
        df, ws_peserta = fetch_fresh_peserta_df()
        _, _, ws_voting = get_sheets()

        voter_row = df[df["NAMA"] == voter_nama].iloc[0]
        if is_true(voter_row["SUDAH_VOTE"]):
            return False

        timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        api_call_with_retry(ws_voting.append_row, [
            timestamp_str,
            voter_nama,
            votes_dict["MINISTER_OF_LAST_
