import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import io

# ==========================================
# 1. Page Configuration & Dark Theme CSS
# ==========================================
st.set_page_config(page_title="RE100 Strategy Dashboard", layout="wide", initial_sidebar_state="expanded")

# 다크 모드, Arial 폰트, 피그마 스타일 카드 UI를 완벽하게 강제하는 CSS
st.markdown("""
    <style>
    /* 전체 폰트 Arial 및 하얀색 텍스트 강제 */
    @import url('https://fonts.googleapis.com/css2?family=Arial&display=swap');
    
    html, body, [class*="css"], .stMarkdown, p, h1, h2, h3, h4, h5, h6, label, span {
        font-family: 'Arial', sans-serif !important;
        color: #F8FAFC !important;
    }
    
    /* 앱 전체 배경색 (다크 모드) */
    .stApp {
        background-color: #121212 !important;
    }
    
    /* 사이드바 스타일링 */
    [data-testid="stSidebar"] {
        background-color: #1A1C23 !important;
        border-right: 1px solid #2D3748 !important;
    }
    
    /* 슬라이더 값 텍스트 색상 및 막대 색상 */
    .stSlider div[data-testid="stThumbValue"], .stSlider label {
        color: #FFFFFF !important;
        font-weight: bold !important;
    }
    div[data-baseweb="slider"] div[data-testid="stTickBar"] {
        background-color: #3DCD58 !important; 
    }
    
    /* 메인 헤더 (슈나이더 그라데이션) */
    .gradient-header {
        background: linear-gradient(135deg, #009E4D 0%, #3DCD58 100%);
        padding: 2.5rem;
        border-radius: 16px;
        box-shadow: 0 10px 30px rgba(61, 205, 88, 0.15);
        margin-bottom: 2rem;
    }
    .gradient-header h1 {
        font-size: 2.2rem !important;
        font-weight: 900 !important;
        margin-bottom: 0.5rem;
        text-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    .gradient-header p {
        font-size: 1.1rem !important;
        opacity: 0.9;
    }
    
    /* 하이라이트 요약 카드 (피그마 디자인 반영) */
    .summary-card {
        background-color: #1E1E1E;
        padding: 2rem;
        border-radius: 16px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.4);
        border: 1px solid #333333;
        text-align: center;
        margin-bottom: 2.5rem;
    }
    .summary-title {
        color: #94A3B8 !important;
        font-size: 1.1rem !important;
        font-weight: bold;
        margin-bottom: 10px;
    }
    .summary-value {
        font-size: 3.5rem !important;
        font-weight: 900 !important;
        color: #3DCD58 !important;
        text-shadow: 0 0 20px rgba(61,205,88,0.2);
        margin: 10px 0;
    }
    
    /* 섹션 제목 스타일 */
    .section-title {
        font-size: 1.5rem !important;
        font-weight: bold !important;
        color: #FFFFFF !important;
        padding-bottom: 10px;
        border-bottom: 2px solid #2D3748;
        margin-top: 2rem;
        margin-bottom: 1.5rem;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. Sidebar Parameters (왼쪽 패널)
# ==========================================
with st.sidebar:
    st.markdown("### 🏢 Company Logo Here")
    st.markdown("---")
    
    st.markdown("### ⚙️ Simulation Parameters")
    st.markdown("<br>", unsafe_allow_html=True)
    
    kepco_price = st.slider("KEPCO Base Rate (KRW/kWh)", min_value=100, max_value=250, value=150, step=1)
    ppa_price = st.slider("Direct PPA Rate (KRW/kWh)", min_value=100, max_value=250, value=165, step=1)
    rec_price = st.slider("REC Market Price (KRW/kWh)", min_value=10, max_value=100, value=50, step=1)
    gp_price = st.slider("Green Premium (KRW/kWh)", min_value=5, max_value=30, value=10, step=1)
    
    st.markdown("---")
    kepco_escalation = st.slider("Annual Tariff Increase (%)", min_value=0.0, max_value=10.0, value=2.0, step=0.1)
    usage_growth = st.slider("Annual Consumption Growth (%)", min_value=0.0, max_value=5.0, value=1.0, step=0.1)

# ==========================================
# 3. Core Calculations (20-Year Loop)
# ==========================================
base_usage = 10000000 

total_kepco = 0
total_ppa = 0
total_rec = 0
total_gp = 0

yearly_data = []

for i in range(20):
    current_usage = base_usage * ((1 + usage_growth / 100) ** i)
    current_kepco_price = kepco_price * ((1 + kepco_escalation / 100) ** i)
    
    yearly_kepco = current_usage * current_kepco_price
    yearly_ppa = current_usage * ppa_price
    yearly_rec = yearly_kepco + (current_usage * rec_price)
    yearly_gp = yearly_kepco + (current_usage * gp_price)

    total_kepco += yearly_kepco
    total_ppa += yearly_ppa
    total_rec += yearly_rec
    total_gp += yearly_gp
    
    yearly_data.append({
        "Year": 2027 + i,
        "KEPCO_Cost": yearly_kepco,
        "PPA_Cost": yearly_ppa,
        "REC_Cost": yearly_rec,
        "GP_Cost": yearly_gp
    })

df_results = pd.DataFrame(yearly_data)

# 억원(KRW Billion) 단위 변환
cum_kepco_bn = total_kepco / 100000000
cum_ppa_bn = total_ppa / 100000000
cum_rec_bn = total_rec / 100000000
cum_gp_bn = total_gp / 100000000
savings_bn = cum_kepco_bn - cum_ppa_bn

# ==========================================
# 4. Main Dashboard UI
# ==========================================

# 상단 헤더
st.markdown("""
    <div class="gradient-header">
        <h1>RE100 Economic Feasibility Dashboard</h1>
        <p>Long-term simulation & cost-benefit analysis for corporate renewable energy procurement</p>
    </div>
""", unsafe_allow_html=True)

# 20년 누적 절감액 요약 보드
st.markdown(f"""
    <div class="summary-card">
        <div class="summary-title">Expected 20-Year Cumulative Savings (vs KEPCO 100%)</div>
        <div class="summary-value">{abs(savings_bn):,.1f} <span style="font-size: 1.5rem; color: #FFFFFF;">KRW Billion</span></div>
        <div style="color: #94A3B8; font-size: 0.95rem;">{ "Cost Reduction" if savings_bn > 0 else "Additional Cost" } via Direct PPA Adoption</div>
    </div>
""", unsafe_allow_html=True)


# 공통 차트 레이아웃 설정 (다크모드 완벽 호환, Arial 폰트)
chart_layout = dict(
    template="plotly_dark",
    margin=dict(l=20, r=20, t=50, b=20),
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Arial", color="#F8FAFC", size=14),
    showlegend=False,
    yaxis=dict(gridcolor="#333333", zerolinecolor="#333333")
)

# --- SECTION 1: Alternative Summary (Current Year) ---
st.markdown('<div class="section-title">📊 Section 1: Summary of Alternatives (Current Year)</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    fig1 = go.Figure(data=[
        go.Bar(
            x=['KEPCO Grid', 'Direct PPA'],
            y=[kepco_price, ppa_price],
            text=[f"{kepco_price} KRW", f"{ppa_price} KRW"],
            textposition='auto',
            textfont=dict(size=15, color="white", family="Arial"),
            marker_color=['#64748B', '#3DCD58'],
            width=0.4
        )
    ])
    fig1.update_layout(**chart_layout, title="1. Power Procurement (Raw Energy Cost)")
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    fig2 = go.Figure(data=[
        go.Bar(
            x=['Direct PPA', 'KEPCO + REC', 'KEPCO + GP'],
            y=[ppa_price, kepco_price + rec_price, kepco_price + gp_price],
            text=[f"{ppa_price} KRW", f"{kepco_price + rec_price} KRW", f"{kepco_price + gp_price} KRW"],
            textposition='auto',
            textfont=dict(size=15, color="white", family="Arial"),
            marker_color=['#3DCD58', '#0F766E', '#059669'],
            width=0.5
        )
    ])
    fig2.update_layout(**chart_layout, title="2. RE100 Procurement (Energy + REC)")
    st.plotly_chart(fig2, use_container_width=True)


# --- SECTION 2: 20-Year Long-Term Analysis ---
st.markdown('<div class="section-title">📈 Section 2: 20-Year Long-Term Cumulative Analysis</div>', unsafe_allow_html=True)

fig3 = go.Figure(data=[
    go.Bar(
        x=['KEPCO 100%', 'Direct PPA', 'KEPCO + REC', 'KEPCO + GP'],
        y=[cum_kepco_bn, cum_ppa_bn, cum_rec_bn, cum_gp_bn],
        text=[f"{val:,.1f} Bn" for val in [cum_kepco_bn, cum_ppa_bn, cum_rec_bn, cum_gp_bn]],
        textposition='auto',
        textfont=dict(size=16, color="white", family="Arial"),
        marker_color=['#64748B', '#3DCD58', '#0F766E', '#059669'],
        width=0.4
    )
])
fig3.update_layout(
    **chart_layout,
    title="20-Year Total Cumulative Cost Comparison",
    yaxis_title="Total Cost (KRW Billion)",
    height=550
)
st.plotly_chart(fig3, use_container_width=True)

# ==========================================
# 5. Export / Download Section
# ==========================================
st.markdown("---")
st.markdown("### 💾 Export Data")

# 엑셀 다운로드 로직
buffer = io.BytesIO()
with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
    df_results.to_excel(writer, sheet_name='20-Year_Simulation', index=False)
    
st.download_button(
    label="⬇️ Download Excel Data",
    data=buffer.getvalue(),
    file_name="RE100_Simulation_Results.xlsx",
    mime="application/vnd.ms-excel"
)

st.info("💡 **Tip for PDF Export:** To generate a clean PDF report of this dashboard, press `Ctrl + P` (or `Cmd + P` on Mac) and select 'Save as PDF' in your browser's print dialog.")
