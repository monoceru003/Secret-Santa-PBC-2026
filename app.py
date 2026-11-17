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

# --- STYLING & HIASAN TEMA NATAL (CSS) ---
st.markdown("""
<style>
    /* Latar belakang bernuansa hangat & lembut */
    .stApp {
        background: linear-gradient(180deg, #FFFDF9 0%, #F7F2EA 100%);
    }

    /* Animasi Salju Halus (Pointer-events: none agar tidak menghalangi klik) */
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
    load_data.clear()

def execute_spin(spinner_nama):
    load_data.clear()
    ws_peserta, _ = get_sheets()
    df, _ = load_data()
    
    # Cek ulang di server apakah spinner sudah pernah spin
    spinner_row_data = df[df["NAMA"] == spinner_nama].iloc[0]
    if is_true(spinner_row_data["SUDAH_SPIN"]):
        return None, "ALREADY_SPUN"

    # Daftar orang yang sudah terpilih sebagai Giftee
    taken_giftees = set(df[df["GIFTEE"] != ""]["GIFTEE"].tolist())
    
    # Kandidat sah: belum terpilih & bukan diri sendiri
    all_names = df["NAMA"].tolist()
    available_targets = [n for n in all_names if n not in taken_giftees and n != spinner_nama]
    
    if not available_targets:
        return None, "NO_TARGETS"

    # Penjaga 2 Orang Terakhir (Anti-Deadlock)
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

    # Kunci hasil di Google Sheets
    cell = ws_peserta.find(spinner_nama, in_column=1)
    if cell:
        row = cell.row
        ws_peserta.update_cell(row, 5, "TRUE")
        ws_peserta.update_cell(row, 6, chosen_giftee)
    load_data.clear()
        
    return chosen_giftee, "OK"

# --- TRIK VISUAL RODA ROULETTE (HTML/CSS/JS) ---
def render_roulette_wheel(candidates, winner, spin_duration=4.5):
    slices = []
    if len(candidates) == 1:
        slices = [winner, "🎁 MYSTERY", winner, "🎄 SECRET", winner, "🎅 SANTA", winner, "✨ GIFT"]
    elif len(candidates) == 2:
        c1, c2 = candidates[0], candidates[1]
        slices = [c1, c2, c1, c2, c1, c2, c1, c2]
    elif len(candidates) in [3, 4]:
        slices = (candidates * 3)[:8]
    else:
        slices = candidates.copy()
        if winner not in slices:
            slices[0] = winner

    winner_indices = [i for i, x in enumerate(slices) if x == winner]
    target_idx = random.choice(winner_indices)
    
    num_slices = len(slices)
    arc = 360 / num_slices
    stop_angle = (360 * 6) + (270 - (target_idx * arc + arc / 2)) % 360

    colors = ["#D42426", "#165B33", "#BB2528", "#146B3A", "#EA4630", "#1E792C", "#C54B3C", "#0F5132"]
    
    slices_js = str(slices)
    colors_js = str([colors[i % len(colors)] for i in range(num_slices)])

    html_code = f"""
    <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; padding:10px;">
        <div style="position:relative; width:310px; height:310px;">
            <div style="position:absolute; top:-14px; left:50%; transform:translateX(-50%); width:0; height:0; 
                        border-left:16px solid transparent; border-right:16px solid transparent; 
                        border-top:28px solid #FFD700; z-index:10; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.4));"></div>
            <canvas id="wheel" width="310" height="310" style="border-radius:50%; box-shadow: 0 8px 20px rgba(0,0,0,0.3); border: 6px solid #FFD700;"></canvas>
        </div>
    </div>
    <script>
        const canvas = document.getElementById('wheel');
        const ctx = canvas.getContext('2d');
        const slices = {slices_js};
        const colors = {colors_js};
        const numSlices = slices.length;
        const arc = (2 * Math.PI) / numSlices;
        const radius = canvas.width / 2;

        function drawWheel() {{
            for (let i = 0; i < numSlices; i++) {{
                const angle = i * arc;
                ctx.beginPath();
                ctx.fillStyle = colors[i];
                ctx.moveTo(radius, radius);
                ctx.arc(radius, radius, radius, angle, angle + arc);
                ctx.lineTo(radius, radius);
                ctx.fill();

                ctx.save();
                ctx.translate(radius, radius);
                ctx.rotate(angle + arc / 2);
                ctx.textAlign = "right";
                ctx.fillStyle = "#FFFFFF";
                ctx.font = "bold 14px sans-serif";
                ctx.fillText(slices[i], radius - 18, 5);
                ctx.restore();
            }}
        }}
        drawWheel();

        setTimeout(() => {{
            canvas.style.transition = "transform {spin_duration}s cubic-bezier(0.15, 0.85, 0.25, 1)";
            canvas.style.transform = "rotate({stop_angle}deg)";
        }}, 100);
    </script>
    """
    components.html(html_code, height=340)

# --- DIALOG POP-UPS ---
@st.dialog("⚠️ Konfirmasi Simpan Wishlist")
def confirm_save_dialog(nama, link, catatan):
    st.markdown(f"Simpan wishlist atas nama **{nama}**?")
    st.warning(
        "Pengisian wishlist hanya dapat dilakukan **1 kali**. "
        "Setelah disimpan, data akan dikunci dan perubahan selanjutnya silakan hubungi **Andre & Regine**."
    )
    st.markdown(f"**Link:** {link}")
    if catatan:
        st.markdown(f"**Catatan:** {catatan}")
        
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Ya, Simpan & Kunci", type="primary", use_container_width=True):
            save_wishlist(nama, link, catatan)
            st.session_state.selected_user = None
            st.session_state.toast_msg = f"Wishlist {nama} berhasil disimpan dan dikunci!"
            st.rerun()
    with col2:
        if st.button("Cek Ulang", use_container_width=True):
            st.rerun()

@st.dialog("⚠️ Buang Perubahan?")
def confirm_discard_dialog(nama):
    st.write(f"Perubahan wishlist untuk **{nama}** belum disimpan. Yakin ingin kembali dan membuang perubahan?")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Ya, Buang Perubahan", type="primary", use_container_width=True):
            st.session_state.selected_user = None
            st.rerun()
    with col2:
        if st.button("Batal", use_container_width=True):
            st.rerun()

@st.dialog("🎅 Konfirmasi Identitas Undian")
def confirm_spin_dialog(nama):
    st.markdown(f"Kamu masuk sebagai **{nama}**.")
    st.warning(
        "Undian dan tampilan nama Giftee hanya muncul **1 kali** (pastikan segera di-screenshot setelah keluar). "
        "Jika lupa atau ingin melihat ulang, silakan hubungi **Andre & Regine**."
    )
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🎲 Ya, Ini Saya — Putar!", type="primary", use_container_width=True):
            st.session_state.spin_confirmed_user = nama
            st.rerun()
    with col2:
        if st.button("Bukan Saya (Kembali)", use_container_width=True):
            st.session_state.selected_user = None
            st.rerun()

# --- STATE MANAGEMENT ---
if "selected_user" not in st.session_state:
    st.session_state.selected_user = None
if "spin_confirmed_user" not in st.session_state:
    st.session_state.spin_confirmed_user = None
if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False
if "show_admin_login" not in st.session_state:
    st.session_state.show_admin_login = False
if "toast_msg" not in st.session_state:
    st.session_state.toast_msg = None

if st.session_state.toast_msg:
    st.success(st.session_state.toast_msg)
    st.session_state.toast_msg = None

# --- LOAD DATA ---
try:
    df, config = load_data()
except Exception as e:
    st.error(f"Gagal terhubung ke Google Sheets. Pastikan Secrets dan Share sudah benar. Detail: {e}")
    st.stop()

event_title = config.get("EVENT_TITLE", "Christmas Lunch Secret Santa")
budget_info = config.get("BUDGET_INFO", "Rp 100.000")
fase = config.get("FASE", "1")

# --- HEADER UTAMA BERHIAS NATAL ---
st.markdown(f"""
<div class="christmas-banner">
    <div class="christmas-ornaments">✨ 🎅 🎄 🦌 ✨</div>
    <h1>{event_title}</h1>
    <div style="font-size: 0.92rem; opacity: 0.92; margin-top: 4px;">Secret Santa Gift Exchange</div>
</div>
<div class="budget-card">
    🎁 <strong>Ketentuan Budget Hadiah:</strong> {budget_info}
</div>
""", unsafe_allow_html=True)

# ==========================================
# MODE ADMIN (KHUSUS ANDRE & REGINE)
# ==========================================
if st.session_state.admin_logged_in:
    st.subheader("⚙️ Panel Kontrol (Andre & Regine)", anchor=False)
    col_top1, col_top2 = st.columns(2)
    with col_top1:
        if st.button("⬅ Keluar dari Mode Admin", use_container_width=True):
            st.session_state.admin_logged_in = False
            st.session_state.show_admin_login = False
            st.rerun()
    with col_top2:
        if st.button("🔄 Refresh Data Terbaru", use_container_width=True):
            load_data.clear()
            st.rerun()
        
    st.divider()
    
    # 1. Kontrol Fase Acara
    st.markdown("### 1. Kontrol Fase Acara")
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        if st.button("📝 Set Fase 1: Isi Wishlist", type="primary" if fase == "1" else "secondary", use_container_width=True):
            _, ws_config = get_sheets()
            cell = ws_config.find("FASE", in_column=1)
            if cell:
                ws_config.update_cell(cell.row, 2, "1")
            load_data.clear()
            st.rerun()
    with col_f2:
        if st.button("🎲 Set Fase 2: Buka Roulette", type="primary" if fase == "2" else "secondary", use_container_width=True):
            _, ws_config = get_sheets()
            cell = ws_config.find("FASE", in_column=1)
            if cell:
                ws_config.update_cell(cell.row, 2, "2")
            load_data.clear()
            st.rerun()
    st.caption(f"Status saat ini: **Fase {fase}** ({'Pengisian Wishlist' if fase == '1' else 'Roulette Undian'})")

    st.divider()
    
    # 2. Monitoring & Edit Peserta
    st.markdown("### 2. Data Peserta, Wishlist & Giftee")
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    st.markdown("#### Edit Wishlist / Reset Status Peserta")
    edit_target = st.selectbox("Pilih nama peserta untuk diedit/reset:", df["NAMA"].tolist())
    if edit_target:
        row_data = df[df["NAMA"] == edit_target].iloc[0]
        new_link = st.text_input("Link Olshop:", value=row_data["WISHLIST_LINK"])
        new_catatan = st.text_area("Catatan:", value=row_data["CATATAN"])
        
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("💾 Simpan Perubahan Admin", use_container_width=True):
                ws_peserta, _ = get_sheets()
                cell = ws_peserta.find(edit_target, in_column=1)
                ws_peserta.update_cell(cell.row, 2, new_link)
                ws_peserta.update_cell(cell.row, 3, new_catatan)
                ws_peserta.update_cell(cell.row, 4, "TRUE" if new_link.strip() else "FALSE")
                load_data.clear()
                st.success(f"Data {edit_target} berhasil diperbarui!")
                time.sleep(1)
                st.rerun()
        with c2:
            if st.button("🔓 Buka Kunci Wishlist", use_container_width=True):
                ws_peserta, _ = get_sheets()
                cell = ws_peserta.find(edit_target, in_column=1)
                ws_peserta.update_cell(cell.row, 4, "FALSE")
                load_data.clear()
                st.success(f"Kunci wishlist {edit_target} dibuka (bisa isi ulang 1x).")
                time.sleep(1)
                st.rerun()
        with c3:
            if st.button("🔄 Reset Spin Undian", use_container_width=True):
                ws_peserta, _ = get_sheets()
                cell = ws_peserta.find(edit_target, in_column=1)
                ws_peserta.update_cell(cell.row, 5, "FALSE")
                ws_peserta.update_cell(cell.row, 6, "")
                load_data.clear()
                st.success(f"Status spin {edit_target} di-reset!")
                time.sleep(1)
                st.rerun()

    st.divider()
    # 3. Tambah Peserta Baru
    st.markdown("### 3. Tambah Peserta Baru")
    new_participant = st.text_input("Nama Peserta Baru:")
    if st.button("➕ Tambah ke Daftar"):
        if new_participant.strip() and new_participant.strip() not in df["NAMA"].tolist():
            ws_peserta, _ = get_sheets()
            ws_peserta.append_row([new_participant.strip(), "", "", "FALSE", "FALSE", ""])
            load_data.clear()
            st.success(f"{new_participant} ditambahkan!")
            time.sleep(1)
            st.rerun()
        else:
            st.warning("Nama kosong atau sudah terdaftar.")
    st.stop()

# ==========================================
# FASE 1: PENGISIAN WISHLIST
# ==========================================
if fase == "1":
    st.subheader("📝 Tahap 1: Pengisian Wishlist", anchor=False)
    
    if st.session_state.selected_user is None:
        options = ["-- Pilih Namamu --"]
        name_map = {}
        for _, row in df.iterrows():
            nama = row["NAMA"]
            locked = is_true(row["WISHLIST_LOCKED"])
            label = f"{nama} — (🔒 Wishlist sudah dikunci)" if locked else f"{nama} — (Belum mengisi)"
            options.append(label)
            name_map[label] = nama
            
        choice = st.selectbox("Pilih namamu dari daftar:", options)
        if choice != "-- Pilih Namamu --":
            chosen_name = name_map[choice]
            if st.button(f"Lanjut sebagai {chosen_name} ➔", type="primary", use_container_width=True):
                st.session_state.selected_user = chosen_name
                st.rerun()
    else:
        curr_user = st.session_state.selected_user
        user_row = df[df["NAMA"] == curr_user].iloc[0]
        
        st.markdown(f"### Halo, **{curr_user}**! 🎅")
        
        if is_true(user_row["WISHLIST_LOCKED"]):
            st.warning(
                f"Wishlist untuk **{curr_user}** sudah tersimpan dan dikunci.\n\n"
                "Jika ada perubahan link atau catatan, silakan hubungi **Andre & Regine**."
            )
            if st.button("⬅ Kembali / Ganti Nama"):
                st.session_state.selected_user = None
                st.rerun()
        else:
            st.caption("Pastikan ini benar namamu sebelum mengisi wishlist.")
            link_input = st.text_input("Link Olshop Barang yang Diinginkan (Tokopedia/Shopee/dll):", placeholder="https://...")
            catatan_input = st.text_area("Catatan Tambahan (Warna, Ukuran, Varian, dll):", placeholder="Contoh: Warna hitam, ukuran L...")
            
            col_back, col_save = st.columns(2)
            with col_back:
                if st.button("⬅ Kembali / Ganti Nama", use_container_width=True):
                    if link_input.strip() != "" or catatan_input.strip() != "":
                        confirm_discard_dialog(curr_user)
                    else:
                        st.session_state.selected_user = None
                        st.rerun()
            with col_save:
                if st.button("💾 Simpan Wishlist", type="primary", use_container_width=True):
                    if not link_input.strip():
                        st.error("Link olshop wajib diisi terlebih dahulu!")
                    else:
                        confirm_save_dialog(curr_user, link_input.strip(), catatan_input.strip())

# ==========================================
# FASE 2: ROULETTE UNDIAN
# ==========================================
elif fase == "2":
    st.subheader("🎲 Tahap 2: Undian Secret Santa", anchor=False)
    
    if st.session_state.spin_confirmed_user is not None:
        spinner = st.session_state.spin_confirmed_user
        
        taken_giftees = set(df[df["GIFTEE"] != ""]["GIFTEE"].tolist())
        candidates = [n for n in df["NAMA"].tolist() if n not in taken_giftees and n != spinner]
        
        giftee_name, status = execute_spin(spinner)
        
        if status == "ALREADY_SPUN":
            st.error(f"Undian atas nama **{spinner}** sudah pernah dilakukan. Hubungi **Andre & Regine** jika lupa hasilnya.")
            st.session_state.spin_confirmed_user = None
            st.session_state.selected_user = None
            if st.button("⬅ Kembali"):
                st.rerun()
        elif status == "OK":
            st.markdown(f"### Roda Undian untuk **{spinner}** 🎄")
            render_roulette_wheel(candidates, giftee_name, spin_duration=4.5)
            
            with st.spinner("Mengacak nama Giftee-mu..."):
                time.sleep(4.8)
                
            st.balloons()
            giftee_data = df[df["NAMA"] == giftee_name].iloc[0]
            
            st.markdown(f"""
            <div class="giftee-card">
                <div style="text-align:center; font-size:1.1rem; color:#165B33; font-weight:bold;">
                    🎅 Ho Ho Ho! Kamu adalah Secret Santa untuk:
                </div>
                <div style="text-align:center; font-size:2rem; font-weight:800; color:#9B1B1E; margin:10px 0;">
                    🎁 {giftee_name}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"**🔗 Link Wishlist:** {giftee_data['WISHLIST_LINK']}")
            if giftee_data['CATATAN']:
                st.markdown(f"**📝 Catatan:** {giftee_data['CATATAN']}")
                
            st.warning("📸 **PENTING:** Segera **SCREENSHOT** halaman ini sekarang! Hasil hanya ditampilkan **1 kali** dan akan terkunci setelah ditutup.")
            
            if st.button("✅ Selesai & Tutup (Sudah Screenshot)", type="primary", use_container_width=True):
                st.session_state.spin_confirmed_user = None
                st.session_state.selected_user = None
                st.rerun()
                
    else:
        options = ["-- Pilih Namamu --"]
        name_map = {}
        for _, row in df.iterrows():
            nama = row["NAMA"]
            spun = is_true(row["SUDAH_SPIN"])
            label = f"{nama} — (🔒 Sudah undian)" if spun else f"{nama} — (Belum undian)"
            options.append(label)
            name_map[label] = nama
            
        choice = st.selectbox("Pilih namamu untuk memutar roulette:", options)
        if choice != "-- Pilih Namamu --":
            chosen_name = name_map[choice]
            user_row = df[df["NAMA"] == chosen_name].iloc[0]
            
            if is_true(user_row["SUDAH_SPIN"]):
                st.warning(
                    f"Undian atas nama **{chosen_name}** sudah dilakukan dan hasil telah dikunci.\n\n"
                    "Jika lupa nama Giftee-mu atau belum sempat menyimpan link wishlist-nya, silakan hubungi **Andre & Regine**."
                )
            else:
                if st.button(f"Lanjut Undian sebagai {chosen_name} ➔", type="primary", use_container_width=True):
                    confirm_spin_dialog(chosen_name)

# --- FOOTER AKSES KHUSUS ADMIN ---
st.divider()
st.markdown("<div style='text-align:center; color:#8C7F70; font-size:0.85rem;'>🎄 Merry Christmas & Happy Gift Hunting! 🎁</div>", unsafe_allow_html=True)
col_empty, col_adm = st.columns([4, 1])
with col_adm:
    if st.button("⚙️ Admin", type="tertiary"):
        st.session_state.show_admin_login = not st.session_state.show_admin_login

if st.session_state.show_admin_login:
    pwd = st.text_input("Masukkan Password:", type="password")
    if st.button("Masuk"):
        if pwd == st.secrets["admin_password"]:
            st.session_state.admin_logged_in = True
            st.session_state.show_admin_login = False
            st.rerun()
        else:
            st.error("Password salah.")
