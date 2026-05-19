import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date

# Konfigurasi Halaman
st.set_page_config(page_title="Dashboard Bank Bogor Raya", page_icon="🏦", layout="wide")

# 1. Load Data
@st.cache_data
def load_data():
    # Menyesuaikan dengan file CSV yang dilampirkan (menggunakan pemisah ;)
    df = pd.read_csv("Streamlit Dashboard Team & Dataset(bank_timeseries_2025).csv", sep=";")
    
    # Konversi format tanggal agar terbaca dengan benar oleh Python
    df['Datetime'] = pd.to_datetime(df['Datetime'], format='%d/%m/%Y %H.%M', errors='coerce')
    return df

try:
    df = load_data()
except FileNotFoundError:
    st.error("File dataset tidak ditemukan. Pastikan file CSV ada di direktori/folder yang sama dengan file Python ini.")
    st.stop()

# Daftar 10 Touchpoints berdasarkan kolom dataset
touchpoints = [
    'Account Opening', 'ATM Service', 'Mobile Banking', 'Internet Banking', 
    'Customer Service', 'Loan Application', 'Complaint Handling', 
    'Branch Cleanliness', 'Staff Friendliness', 'Transaction Speed'
]

# 2. Sidebar - Filters
st.sidebar.title("📌 Menu Navigasi")
pilihan_halaman = st.sidebar.radio(
    "Pilih Halaman Analisis:",
    ["Overview", "Branch Analysis", "Touchpoint Analysis", "Insight & Recommendations"]
)

st.sidebar.divider()

st.sidebar.title("🏦 Filter Dashboard")

# Filter Time Series
# Menghapus nilai NaT (Not a Time) jika ada yang gagal dikonversi
valid_dates = df['Datetime'].dropna()
min_date = valid_dates.min().date()
max_date = valid_dates.max().date()

date_selection = st.sidebar.date_input("Rentang Waktu (Time Series)", [min_date, max_date])

# Handling date_input if user only selects one date
if len(date_selection) == 2:
    start_date, end_date = date_selection
else:
    start_date = end_date = date_selection[0]

# Filter Branch
branches = df['Branch'].dropna().unique()
selected_branches = st.sidebar.multiselect("Pilih Cabang (Branch/Area)", branches, default=branches)

# Filter Touchpoint
selected_touchpoint = st.sidebar.selectbox("Pilih Touchpoint untuk dianalisis", touchpoints)

# Terapkan Filter pada Dataframe
mask = (df['Datetime'].dt.date >= start_date) & \
       (df['Datetime'].dt.date <= end_date) & \
       (df['Branch'].isin(selected_branches))
filtered_df = df[mask]

# Jika data kosong setelah difilter
if filtered_df.empty:
    st.warning("Tidak ada data untuk kombinasi filter ini.")
    st.stop()

# ==========================================
# 3. KONTEN HALAMAN UTAMA (MAIN PAGE)
# ==========================================

if pilihan_halaman == "Overview":
    st.title("📊 Overview Dashboard")
    st.markdown("Ringkasan performa Customer Satisfaction (CSI) dan Net Promoter Score (NPS).")

    # --- Bagian A: KPI Cards (Angka Ringkasan) ---
    st.subheader("📊 Ringkasan Performa")
    
    # Menghitung metrik tambahan
    total_responden = len(filtered_df)
    promoters = len(filtered_df[filtered_df['NPS'] >= 9])
    detractors = len(filtered_df[filtered_df['NPS'] <= 6])
    nps_score = ((promoters - detractors) / total_responden) * 100 if total_responden > 0 else 0
    
    avg_csi = filtered_df['CSI'].mean()
    avg_loyalty = filtered_df['Loyalty'].mean()
    avg_ces = filtered_df['CES'].mean()
    
    # Menentukan Best & Worst Branch berdasarkan rata-rata NPS
    branch_stats = filtered_df.groupby('Branch')['NPS'].mean()
    best_branch = branch_stats.idxmax()
    worst_branch = branch_stats.idxmin()

    # Membuat layout 3x2 (3 kolom per baris)
    row1_col1, row1_col2, row1_col3 = st.columns(3)
    row2_col1, row2_col2, row2_col3 = st.columns(3)

    def display_kpi(col, label, value, color):
        with col:
            with st.container(border=True):
                st.markdown(f"**{label}**")
                st.markdown(f"<h3 style='color: {color}; margin-top: -10px;'>{value}</h3>", unsafe_allow_html=True)

    # Baris 1
    display_kpi(row1_col1, "NPS Score", f"{nps_score:.1f}", "#0068C9")
    display_kpi(row1_col2, "Avg. CSI", f"{avg_csi:.2f}", "#29B5E8")
    display_kpi(row1_col3, "Avg. Loyalty", f"{avg_loyalty:.2f}", "#82DD55")

    # Baris 2
    display_kpi(row2_col1, "Avg. CES", f"{avg_ces:.2f}", "#FF4B4B")
    display_kpi(row2_col2, "Best Branch", best_branch, "#09AB3B")
    display_kpi(row2_col3, "Worst Branch", worst_branch, "#FF9800")

    # --- Bagian B: Visualisasi Grafik ---
    col_kiri, col_kanan = st.columns(2)

    with col_kiri:
        st.subheader("📈 Tren NPS & CSI Harian")
        # Membuat agregasi rata-rata per hari
        trend_df = filtered_df.set_index('Datetime').resample('D').agg({'NPS': 'mean', 'CSI': 'mean'}).reset_index()
        # Membuat grafik garis (Line Chart)
        fig_trend = px.line(trend_df, x='Datetime', y=['NPS', 'CSI'], 
                            labels={'value': 'Skor Rata-rata', 'variable': 'Metrik'},
                            markers=True)
        st.plotly_chart(fig_trend, width='stretch')

    with col_kanan:
        st.subheader(f"🎯 Performa: {selected_touchpoint}")
        # Membandingkan skor touchpoint antar cabang
        tp_branch = filtered_df.groupby('Branch')[selected_touchpoint].mean().reset_index()
        tp_branch = tp_branch.sort_values(by=selected_touchpoint, ascending=True) # Sortir agar rapi
        # Membuat grafik batang horizontal
        fig_tp = px.bar(tp_branch, x=selected_touchpoint, y='Branch', orientation='h',
                        text_auto='.2f', color=selected_touchpoint, color_continuous_scale='Blues')
        st.plotly_chart(fig_tp, width='stretch')

    st.divider()
    
    # --- Bagian C: Perbandingan Semua Cabang ---
    st.subheader("🏢 Perbandingan Performa Antar Cabang")
    branch_perf = filtered_df.groupby('Branch').agg({
        'NPS': 'mean',
        'CSI': 'mean',
        'CES': 'mean'
    }).reset_index()
    
    # Grafik batang berkelompok (Grouped Bar Chart)
    fig_branch = px.bar(branch_perf, x='Branch', y=['NPS', 'CSI', 'CES'], barmode='group',
                        labels={'value': 'Skor Rata-rata', 'variable': 'Kategori'})
    st.plotly_chart(fig_branch, width='stretch')

# Placeholder untuk halaman lainnya
elif pilihan_halaman == "Branch Analysis":
    st.title("🏢 Branch Analysis")
    st.info("Kamu bisa menambahkan visualisasi detail yang spesifik membedah 1 cabang di sini.")

elif pilihan_halaman == "Touchpoint Analysis":
    st.title("🎯 Touchpoint Analysis")
    st.info("Halaman ini cocok diisi dengan grafik Radar/Spider Chart untuk membandingkan 10 layanan sekaligus.")

elif pilihan_halaman == "Insight & Recommendations":
    st.title("💡 Insight & Recommendations")
    st.dataframe(filtered_df[['Datetime', 'Branch', 'Improvement_Feedback']].dropna())
    st.info("Kamu bisa menampilkan tabel feedback dari pelanggan atau teks kesimpulan di halaman ini.")