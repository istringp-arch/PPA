import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import io

# ==========================================
# 1. Page Configuration & Dark Theme CSS
# ==========================================
st.set_page_config(page_title="RE100 Strategy Dashboard", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Arial&display=swap');
    
    html, body, [class*="css"], .stMarkdown, p, h1, h2, h3, h4, h5, h6, label, span {
        font-family: 'Arial', sans-serif !important;
        color: #F8FAFC !important;
    }
    
    .stApp {
        background-color: #121212 !important;
    }
    
    [data-testid="stSidebar"] {
        background-color: #1A1C23 !important;
        border-right: 1px solid #2D3748 !important;
    }
    
    .stSlider div[data-testid="stThumbValue"], .stSlider label, .stSelectbox label, .stNumberInput label {
        color: #FFFFFF !important;
        font-weight: bold !important;
    }
    div[data-baseweb="slider"] div[data-testid="stTickBar"] {
        background-color: #3DCD58 !important; 
    }
    
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
    
    # 1. 누락되었던 Input Setting 섹션 복구
    st.markdown("### 📝 Contract Settings")
    voltage_type = st.selectbox("Voltage Type", ["High Voltage A", "High Voltage B", "High Voltage C"])
    rate_option = st.selectbox("Rate Plan", ["Option I", "Option II", "Option III"])
    contract_type = st.selectbox("Network Usage Type", [
        "Transmission Gen - Transmission User",
        "Transmission Gen - Distribution User",
        "Distribution Gen - Distribution User (Same Substation)"
    ])
    
    col_a, col_b = st.columns(2)
    with col_a:
        contract_power = st.number_input("Contract Power (kW)", value=15200, step=100)
    with col_b:
        applied_power = st.number_input("Applied Power (kW)", value=8000, step=100)

    st.markdown("---")
    
    # 2. 시장 단가 파라미터 섹션
    st.markdown("### ⚙️ Market Pricing (KRW/kWh)")
    kepco_price = st.slider("KEPCO Base Rate", min_value=100, max_value=250, value=150, step=1)
    ppa_price = st.slider("Direct PPA Rate", min_value=100, max_value=250, value=165, step=1)
    rec_price = st.slider("REC Market Price", min_value=10, max_value=100, value=50, step=1)
    gp_price = st.slider("Green Premium (GP)", min_value=5, max_value=30, value=10, step=1)
    
    st.markdown("---")
    
    # 3. 변동률 파라미터 섹션
    st.markdown("### 📈 Escalation Rates (%)")
    kepco_escalation = st.slider("Annual Tariff Increase", min_value=0.0, max_value=10.0, value=2.0, step=0.1)
    usage_growth = st.slider("Annual Consumption Growth", min_value=0.0, max_value=5.0, value=1.0, step=0.1)

# ==========================================
# 3. Core Calculations (20-Year Loop)
# ==========================================
base_usage = 10000000 # 10,000 MWh 가정 (웹 시뮬레이션용)

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
    
    # 그래프를 그리기 위해 억원 단위(KRW Billion)로 미리 환산하여 저장
    yearly_data.append({
        "Year": 2027 + i,
        "KEPCO_Cost_Bn": yearly_kepco / 100000000,
        "PPA_Cost_Bn": yearly_ppa / 100000000,
        "REC_Cost_Bn": yearly_rec / 100000000,
        "GP_Cost_Bn": yearly_gp / 100000000
    })

df_results = pd.DataFrame(yearly_data)

# 누적 비용 억원(KRW Billion) 단위
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

# 공통 차트 레이아웃 설정
chart_layout = dict(
    template="plotly_dark",
    margin=dict(l=20, r=20, t=50, b=20),
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Arial", color="#F8FAFC", size=14),
    showlegend=True,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
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
            width=0.4,
            showlegend=False
        )
    ])
    fig1.update_layout(**chart_layout, title="1. Power Procurement (Raw Energy Cost)")
    fig1.update_layout(showlegend=False)
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
            width=0.5,
            showlegend=False
        )
    ])
    fig2.update_layout(**chart_layout, title="2. RE100 Procurement (Energy + REC)")
    fig2.update_layout(showlegend=False)
    st.plotly_chart(fig2, use_container_width=True)

# --- SECTION 2: 20-Year Long-Term Analysis ---
st.markdown('<div class="section-title">📈 Section 2: 20-Year Long-Term Analysis</div>', unsafe_allow_html=True)

tab1, tab2 = st.tabs(["Line Chart (Annual Trend)", "Bar Chart (Cumulative Total)"])

# 누락되었던 20년 추이 선 그래프 복구
with tab1:
    fig_line = go.Figure()
    fig_line.add_trace(go.Scatter(x=df_results['Year'], y=df_results['KEPCO_Cost_Bn'], mode='lines+markers', name='KEPCO 100%', line=dict(color='#64748B', width=3)))
    fig_line.add_trace(go.Scatter(x=df_results['Year'], y=df_results['PPA_Cost_Bn'], mode='lines+markers', name='Direct PPA', line=dict(color='#3DCD58', width=4)))
    fig_line.add_trace(go.Scatter(x=df_results['Year'], y=df_results['REC_Cost_Bn'], mode='lines+markers', name='KEPCO + REC', line=dict(color='#0F766E', width=2, dash='dash')))
    fig_line.add_trace(go.Scatter(x=df_results['Year'], y=df_results['GP_Cost_Bn'], mode='lines+markers', name='KEPCO + GP', line=dict(color='#059669', width=2, dash='dot')))
    
    fig_line.update_layout(
        **chart_layout,
        title="Annual Cost Trend Over 20 Years",
        xaxis_title="Year",
        yaxis_title="Annual Cost (KRW Billion)",
        height=550,
        xaxis=dict(tickmode="linear", tick0=2027, dtick=2)
    )
    st.plotly_chart(fig_line, use_container_width=True)

# 누적 막대그래프
with tab2:
    fig_bar = go.Figure(data=[
        go.Bar(
            x=['KEPCO 100%', 'Direct PPA', 'KEPCO + REC', 'KEPCO + GP'],
            y=[cum_kepco_bn, cum_ppa_bn, cum_rec_bn, cum_gp_bn],
            text=[f"{val:,.1f} Bn" for val in [cum_kepco_bn, cum_ppa_bn, cum_rec_bn, cum_gp_bn]],
            textposition='auto',
            textfont=dict(size=16, color="white", family="Arial"),
            marker_color=['#64748B', '#3DCD58', '#0F766E', '#059669'],
            width=0.4,
            showlegend=False
        )
    ])
    fig_bar.update_layout(
        **chart_layout,
        title="20-Year Total Cumulative Cost Comparison",
        yaxis_title="Total Cost (KRW Billion)",
        height=550
    )
    fig_bar.update_layout(showlegend=False)
    st.plotly_chart(fig_bar, use_container_width=True)

# ==========================================
# 5. Export / Download Section (오류 완벽 수정)
# ==========================================
st.markdown("---")
st.markdown("### 💾 Export Data")

# 에러 없는 안정적인 Buffer 방식 적용
excel_buffer = io.BytesIO()

try:
    # openpyxl 엔진을 사용하여 호환성 오류 방지
    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
        df_results.to_excel(writer, index=False, sheet_name='20-Year_Simulation')
    excel_data = excel_buffer.getvalue()
    
    st.download_button(
        label="⬇️ Download Excel File (.xlsx)",
        data=excel_data,
        file_name="RE100_Simulation_Results.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
except Exception as e:
    # 엑셀 엔진이 없는 환경을 대비한 CSV 다운로드 폴백(Fallback) 제공
    st.warning("Excel Engine(openpyxl) is not installed in this environment. Providing CSV download instead.")
    csv_data = df_results.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="⬇️ Download CSV File (.csv)",
        data=csv_data,
        file_name="RE100_Simulation_Results.csv",
        mime="text/csv"
    )

st.info("💡 **Tip for PDF Export:** To generate a clean PDF report of this dashboard, press `Ctrl + P` (or `Cmd + P` on Mac) and select 'Save as PDF' in your browser's print dialog.")
