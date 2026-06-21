import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import io

# ==========================================
# 1. Page Configuration & Custom CSS
# ==========================================
st.set_page_config(page_title="RE100 Strategy Dashboard", layout="wide", initial_sidebar_state="expanded")

# 슈나이더 감성의 커스텀 CSS (부드러운 그림자, 그라데이션)
st.markdown("""
    <style>
    /* 전체 배경색 */
    .stApp {
        background-color: #F8FAFC;
    }
    
    /* 사이드바 스타일링 */
    [data-testid="stSidebar"] {
        background-color: #FFFFFF;
        box-shadow: 2px 0 10px rgba(0,0,0,0.05);
    }
    
    /* 메인 헤더 그라데이션 카드 */
    .gradient-header {
        background: linear-gradient(135deg, #009E4D 0%, #3DCD58 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        box-shadow: 0 10px 20px rgba(61, 205, 88, 0.2);
        margin-bottom: 2rem;
    }
    .gradient-header h1 {
        margin: 0;
        font-size: 2rem;
        font-weight: 800;
        color: white;
    }
    .gradient-header p {
        margin: 0;
        opacity: 0.9;
        font-size: 1.1rem;
    }
    
    /* 하이라이트 요약 카드 */
    .summary-card {
        background-color: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.04);
        border: 1px solid #E2E8F0;
        text-align: center;
        margin-bottom: 2rem;
    }
    .summary-value {
        font-size: 2.5rem;
        font-weight: 800;
        color: #009E4D;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. Sidebar Parameters (왼쪽 패널)
# ==========================================
with st.sidebar:
    # 로고 삽입 부분 (나중에 'logo.png' 파일 경로만 맞춰주시면 됩니다)
    # st.image("logo.png", use_column_width=True)
    st.markdown("### 🏢 Company Logo Here")
    st.markdown("---")
    
    st.header("⚙️ Simulation Parameters")
    
    st.subheader("Market Pricing (KRW/kWh)")
    kepco_price = st.slider("KEPCO Base Rate", min_value=100, max_value=250, value=150, step=1)
    ppa_price = st.slider("Direct PPA Rate", min_value=100, max_value=250, value=165, step=1)
    rec_price = st.slider("REC Market Price", min_value=10, max_value=100, value=50, step=1)
    gp_price = st.slider("Green Premium (GP)", min_value=5, max_value=30, value=10, step=1)
    
    st.markdown("---")
    st.subheader("Growth & Escalation (%)")
    kepco_escalation = st.slider("Annual Tariff Increase", min_value=0.0, max_value=10.0, value=2.0, step=0.1)
    usage_growth = st.slider("Annual Power Consumption Growth", min_value=0.0, max_value=5.0, value=1.0, step=0.1)

# ==========================================
# 3. Core Calculations (20-Year Loop)
# ==========================================
# 임의의 기준 사용량 (10,000 MWh 가정)
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

# 단위 변환 (KRW Billion - 억원)
cum_kepco_bn = total_kepco / 100000000
cum_ppa_bn = total_ppa / 100000000
cum_rec_bn = total_rec / 100000000
cum_gp_bn = total_gp / 100000000
savings_bn = cum_kepco_bn - cum_ppa_bn

# ==========================================
# 4. Main Dashboard UI
# ==========================================
# 메인 헤더
st.markdown("""
    <div class="gradient-header">
        <h1>RE100 Economic Feasibility Dashboard</h1>
        <p>Long-term simulation & cost-benefit analysis for corporate renewable energy procurement</p>
    </div>
""", unsafe_allow_html=True)

# 하이라이트 요약
st.markdown(f"""
    <div class="summary-card">
        <h3 style="color: #64748B; font-size: 1.1rem;">Expected 20-Year Cumulative Savings (vs KEPCO 100%)</h3>
        <div class="summary-value">{abs(savings_bn):,.1f} <span style="font-size: 1.5rem; color: #1E293B;">KRW Billion</span></div>
        <p style="color: #94A3B8; font-size: 0.9rem;">{ "Cost Reduction" if savings_bn > 0 else "Additional Cost" } via Direct PPA Adoption</p>
    </div>
""", unsafe_allow_html=True)


# --- SECTION 1: Alternative Summary ---
st.markdown("### 📊 Section 1: Summary of Alternatives (Current Year)")
col1, col2 = st.columns(2)

# 공통 차트 레이아웃 설정
chart_layout = dict(
    template="plotly_white",
    margin=dict(l=0, r=0, t=40, b=0),
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    showlegend=False
)

with col1:
    st.markdown("**1. Power Procurement (Raw Energy Cost)**")
    fig1 = go.Figure(data=[
        go.Bar(
            x=['KEPCO Grid', 'Direct PPA'],
            y=[kepco_price, ppa_price],
            text=[f"{kepco_price} KRW/kWh", f"{ppa_price} KRW/kWh"],
            textposition='auto',
            marker_color=['#94A3B8', '#3DCD58']
        )
    ])
    fig1.update_layout(**chart_layout, yaxis_title="KRW / kWh")
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.markdown("**2. RE100 Procurement (Energy + REC)**")
    fig2 = go.Figure(data=[
        go.Bar(
            x=['Direct PPA', 'KEPCO + REC', 'KEPCO + GP'],
            y=[ppa_price, kepco_price + rec_price, kepco_price + gp_price],
            text=[f"{ppa_price} KRW/kWh", f"{kepco_price + rec_price} KRW/kWh", f"{kepco_price + gp_price} KRW/kWh"],
            textposition='auto',
            marker_color=['#3DCD58', '#0F766E', '#059669']
        )
    ])
    fig2.update_layout(**chart_layout, yaxis_title="KRW / kWh")
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")

# --- SECTION 2: 20-Year Long-Term Analysis ---
st.markdown("### 📈 Section 2: 20-Year Long-Term Cumulative Analysis")

fig3 = go.Figure(data=[
    go.Bar(
        x=['KEPCO 100%', 'Direct PPA', 'KEPCO + REC', 'KEPCO + GP'],
        y=[cum_kepco_bn, cum_ppa_bn, cum_rec_bn, cum_gp_bn],
        text=[f"{val:,.1f} Bn" for val in [cum_kepco_bn, cum_ppa_bn, cum_rec_bn, cum_gp_bn]],
        textposition='auto',
        marker_color=['#94A3B8', '#3DCD58', '#0F766E', '#059669'],
        width=0.5
    )
])
fig3.update_layout(
    **chart_layout,
    yaxis_title="Total Cost (KRW Billion)",
    height=500
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

st.info("💡 **Tip for PDF Export:** To generate a clean PDF report of this dashboard, press `Ctrl + P` (or `Cmd + P` on Mac) and select 'Save as PDF' in your browser's print dialog. Streamlit's layout is automatically optimized for printing.")
