import streamlit as st
import pandas as pd
import plotly.express as px
from wordcloud import WordCloud
import matplotlib.pyplot as plt

# Konfigurasi Halaman
st.set_page_config(page_title="Dashboard Bank Bogor Raya", page_icon="🏦", layout="wide")

# CSS Custom: Memaksa Latar Belakang Putih & Teks Gelap pada halaman utama 
# (Sidebar tidak disentuh agar tetap pada format bawaannya)
st.markdown("""
    <style>
    .stApp {
        background-color: #FFFFFF;
        color: #000000;
    }
    h1, h2, h3, h4, h5, h6, p, span, div, label {
        color: #212529 !important;
    }
    </style>
""", unsafe_allow_html=True)

# 1. Load Data
@st.cache_data
def load_data():
    # Menyesuaikan dengan file CSV yang dilampirkan
    df = pd.read_csv("Streamlit Dashboard Team & Dataset(bank_timeseries_2025).csv", sep=";")
    # Konversi format tanggal
    df['Datetime'] = pd.to_datetime(df['Datetime'], format='%d/%m/%Y %H.%M', errors='coerce')
    return df

try:
    df = load_data()
except FileNotFoundError:
    st.error("File dataset tidak ditemukan. Pastikan file CSV ada di direktori/folder yang sama.")
    st.stop()

# Daftar Touchpoints
touchpoints = [
    'Account Opening', 'ATM Service', 'Mobile Banking', 'Internet Banking', 
    'Customer Service', 'Loan Application', 'Complaint Handling', 
    'Branch Cleanliness', 'Staff Friendliness', 'Transaction Speed'
]

# ==========================================
# 2. SIDEBAR - FILTERS (TETAP SEPERTI ASLINYA)
# ==========================================
st.sidebar.title("📌 Menu Navigasi")
pilihan_halaman = st.sidebar.radio(
    "Pilih Halaman Analisis:",
    ["Overview", "Branch Analysis", "Touchpoint Analysis", "Insight & Recommendations"]
)

st.sidebar.divider()

st.sidebar.title("🏦 Filter Dashboard")

# Filter Time Series
valid_dates = df['Datetime'].dropna()
min_date = valid_dates.min().date()
max_date = valid_dates.max().date()

date_selection = st.sidebar.date_input("Rentang Waktu (Time Series)", [min_date, max_date])

if len(date_selection) == 2:
    start_date, end_date = date_selection
else:
    start_date = end_date = date_selection[0]

# Filter Branch
branches = df['Branch'].dropna().unique()
selected_branches = st.sidebar.multiselect("Pilih Cabang (Branch/Area)", branches, default=branches)

# Filter Touchpoint
selected_touchpoint = st.sidebar.selectbox("Pilih Touchpoint untuk dianalisis", touchpoints)

# Terapkan Filter
mask = (df['Datetime'].dt.date >= start_date) & \
       (df['Datetime'].dt.date <= end_date) & \
       (df['Branch'].isin(selected_branches))
filtered_df = df[mask]

if filtered_df.empty:
    st.warning("Tidak ada data untuk kombinasi filter ini.")
    st.stop()

# ==========================================
# 3. KONTEN HALAMAN UTAMA (MAIN PAGE)
# ==========================================

if pilihan_halaman == "Overview":
    st.title("📊 Overview Dashboard")
    st.markdown("Ringkasan performa Customer Satisfaction (CSI) dan Net Promoter Score (NPS).")

    # --- Bagian 1: KPI Cards ---
    st.subheader("📊 Ringkasan Performa")
    
    # Rata-rata NPS diperbaiki menggunakan skala 1-10 secara langsung
    avg_nps = filtered_df['NPS'].mean()
    avg_csi = filtered_df['CSI'].mean()
    avg_loyalty = filtered_df['Loyalty'].mean()
    avg_ces = filtered_df['CES'].mean()
    
    # Menentukan Best & Worst Branch berdasarkan rata-rata CSI 
    # (CSI digunakan karena paling adil untuk melihat murni pelayanan operasional)
    branch_stats = filtered_df.groupby('Branch')['CSI'].mean()
    best_branch = branch_stats.idxmax()
    worst_branch = branch_stats.idxmin()

    # Layout baris KPI
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.info(f"**Avg NPS (1-10):**\n### {avg_nps:.1f}")
    with col2:
        st.success(f"**Avg CSI:**\n### {avg_csi:.2f}")
    with col3:
        st.warning(f"**Avg Loyalty:**\n### {avg_loyalty:.2f}")
    with col4:
        st.error(f"**Avg CES:**\n### {avg_ces:.2f}")

    st.divider()

    # --- Bagian 2: Line Chart & Bar Chart Perbandingan ---
    col_kiri, col_kanan = st.columns(2)

    with col_kiri:
        st.subheader("📈 Tren Skor Bulanan")
        # ME = Month End untuk resampling data bulanan
        trend_df = filtered_df.set_index('Datetime').resample('ME')[['NPS', 'CSI', 'Loyalty', 'CES']].mean().reset_index()
        fig_line = px.line(trend_df, x='Datetime', y=['NPS', 'CSI', 'Loyalty', 'CES'], markers=True)
        fig_line.update_layout(paper_bgcolor="white", plot_bgcolor="white", font_color="black")
        st.plotly_chart(fig_line, width='stretch')

    with col_kanan:
        st.subheader("🏢 Perbandingan Performa Cabang")
        branch_perf = filtered_df.groupby('Branch')[['NPS', 'CSI', 'CES']].mean().reset_index()
        fig_branch = px.bar(branch_perf, x='Branch', y=['NPS', 'CSI', 'CES'], barmode='group')
        fig_branch.update_layout(paper_bgcolor="white", plot_bgcolor="white", font_color="black")
        st.plotly_chart(fig_branch, width='stretch')

    st.divider()

    # --- Bagian 3: Bar Chart Top/Bottom 5 & Donut Chart ---
    col_tb, col_pie = st.columns(2)

    with col_tb:
        st.subheader("🏆 Top 5 & Bottom 5 Cabang")
        st.caption("Alasan: Menggunakan metrik **CSI** karena metrik ini paling spesifik mengukur kinerja standar operasional (SOP) harian di lapangan.")
        
        sorted_branches = branch_stats.sort_values(ascending=False).reset_index()
        top_5 = sorted_branches.head(5)
        bottom_5 = sorted_branches.tail(5)
        
        # Menggabungkan data top dan bottom untuk visualisasi
        top_bot_df = pd.concat([top_5, bottom_5])
        top_bot_df['Kategori'] = ['Top 5'] * len(top_5) + ['Bottom 5'] * len(bottom_5)
        
        fig_topbot = px.bar(top_bot_df, x='CSI', y='Branch', color='Kategori', orientation='h',
                            color_discrete_map={'Top 5': '#28a745', 'Bottom 5': '#dc3545'})
        fig_topbot.update_layout(yaxis={'categoryorder':'total ascending'}, paper_bgcolor="white", plot_bgcolor="white", font_color="black")
        st.plotly_chart(fig_topbot, width='stretch')

    with col_pie:
        st.subheader("🎯 Proporsi Kinerja Touchpoint")
        st.caption("Alasan: Menampilkan Rata-rata Skor per **Touchpoint** untuk memetakan titik layanan mana yang paling memuaskan/mengecewakan secara keseluruhan.")
        
        tp_scores = filtered_df[touchpoints].mean().reset_index()
        tp_scores.columns = ['Touchpoint', 'Average Score']
        
        fig_pie = px.pie(tp_scores, values='Average Score', names='Touchpoint', hole=0.4)
        fig_pie.update_layout(paper_bgcolor="white", plot_bgcolor="white", font_color="black")
        st.plotly_chart(fig_pie, width='stretch')

    st.divider()

    # --- Bagian 4: Heatmap & WordCloud ---
    col_heat, col_word = st.columns(2)

    with col_heat:
        st.subheader("🔥 Heatmap Touchpoint per Cabang")
        heatmap_data = filtered_df.groupby('Branch')[touchpoints].mean()
        fig_heat = px.imshow(heatmap_data, text_auto=".1f", color_continuous_scale='Blues', aspect="auto")
        fig_heat.update_layout(paper_bgcolor="white", plot_bgcolor="white", font_color="black")
        st.plotly_chart(fig_heat, width='stretch')

    with col_word:
        st.subheader("☁️ Wordcloud Top Feedback")
        text_feedback = " ".join(filtered_df['Improvement_Feedback'].dropna().astype(str))
        if text_feedback.strip():
            wc = WordCloud(width=600, height=400, background_color="white", colormap="tab10").generate(text_feedback)
            fig_wc, ax = plt.subplots(figsize=(6, 4))
            ax.imshow(wc, interpolation='bilinear')
            ax.axis("off")
            fig_wc.patch.set_facecolor('white') # Pastikan background gambar putih
            st.pyplot(fig_wc)
        else:
            st.info("Tidak ada data feedback pada rentang waktu ini.")

    st.divider()

    # --- Bagian 5: Key Insights & Recommendations ---
    st.subheader("💡 Key Insights & Recommendations")
    
    # Kalkulasi Persentase NPS (Bulan pertama filter vs Bulan terakhir filter)
    nps_status = "stabil (data tidak cukup)"
    if len(trend_df) > 1:
        nps_start = trend_df['NPS'].iloc[0]
        nps_end = trend_df['NPS'].iloc[-1]
        if nps_start > 0:
            nps_trend_pct = ((nps_end - nps_start) / nps_start) * 100
            if nps_trend_pct > 0:
                nps_status = f"naik {nps_trend_pct:.1f}%"
            elif nps_trend_pct < 0:
                nps_status = f"turun {abs(nps_trend_pct):.1f}%"

    # Mendapatkan Touchpoint terendah (paling banyak masalah)
    worst_tp = tp_scores.loc[tp_scores['Average Score'].idxmin(), 'Touchpoint']
    
    col_ins, col_rec = st.columns(2)
    with col_ins:
        st.markdown("**🔑 Key Insight:**")
        st.markdown(f"1. NPS menunjukkan tren **{nps_status}** dibanding awal periode waktu yang dipilih.")
        st.markdown(f"2. Cabang **{best_branch}** memiliki performa operasional terbaik, sedangkan **{worst_branch}** adalah yang terendah.")
        st.markdown(f"3. **{worst_tp}** menjadi touchpoint dengan skor rata-rata terendah, indikasi titik keluhan terbanyak.")

    with col_rec:
        st.markdown("**✅ Recommendation:**")
        st.markdown(f"1. Tingkatkan kualitas layanan dan supervisi di Cabang **{worst_branch}** secara intensif.")
        st.markdown(f"2. Perbaiki performa di touchpoint **{worst_tp}**, terutama evaluasi sistem/SOP yang memperlambat layanan tersebut.")
        st.markdown("3. Tindak lanjuti kata kunci keluhan dari *Wordcloud feedback* pelanggan sebagai basis perbaikan kebijakan.")

# ==========================================
# PLACEHOLDER HALAMAN LAINNYA
# ==========================================
elif pilihan_halaman == "Branch Analysis":
    st.title("🏢 Branch Analysis")
    st.info("Halaman ini sudah disiapkan untuk visualisasi detail spesifik membedah 1 cabang.")

elif pilihan_halaman == "Touchpoint Analysis":
    st.title("🎯 Touchpoint Analysis")
    st.info("Halaman ini sudah disiapkan untuk membandingkan 10 layanan sekaligus.")

elif pilihan_halaman == "Insight & Recommendations":
    st.title("💡 Insight & Recommendations")
    st.dataframe(filtered_df[['Datetime', 'Branch', 'Improvement_Feedback']].dropna(), width=1000)
