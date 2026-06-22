import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import io
import holidays
import calendar

# ==========================================
# 1. 페이지 설정 및 다크모드 디자인
# ==========================================
st.set_page_config(page_title="RE100 Strategy Dashboard", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    * { font-family: "Arial", sans-serif !important; }
    .stApp { background-color: #121212 !important; }
    [data-testid="stSidebar"] { background-color: #1E1E1E !important; box-shadow: 2px 0 10px rgba(0,0,0,0.5); border-right: 1px solid #333; }
    h1, h2, h3, h4, h5, h6, p, label, .stMarkdown, .stText, span { color: #FFFFFF !important; }
    
    .gradient-header {
        background: linear-gradient(135deg, #009E4D 0%, #3DCD58 100%);
        padding: 2rem; border-radius: 15px; color: white !important;
        box-shadow: 0 10px 20px rgba(0, 0, 0, 0.4); margin-bottom: 2rem;
    }
    .gradient-header h1 { margin: 0; font-size: 2rem; font-weight: 800; color: white !important; }
    .gradient-header p { margin: 0; opacity: 0.9; font-size: 1.1rem; color: white !important; }
    
    .summary-card {
        background-color: #1E1E1E; padding: 1.5rem; border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.4); border: 1px solid #333;
        text-align: center; margin-bottom: 2rem;
    }
    .summary-value { font-size: 2.5rem; font-weight: 800; color: #3DCD58 !important; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 핵심 엔진: 8760시간 데이터 로딩 및 병합 (캐시 적용)
# ==========================================
# st.cache_data 데코레이터를 붙이면 CSV를 읽고 요금표를 만드는 무거운 작업을 딱 한 번만 실행합니다.
@st.cache_data
def load_and_prep_base_data():
    # 이곳에 질문자님이 코랩에서 작성하셨던 "시간별 요금표 생성" 및 "CSV 데이터 병합" 코드를 그대로 넣습니다.
    # 예시를 위해 구조만 잡아두었습니다. 실제로는 기존 판다스 코드를 복사해 넣으시면 됩니다.
    
    # 1. 파일 읽기
    uploaded = "기업 전력사용량 & 발전량 데이터_case 2.csv"
    user_data = pd.read_csv(uploaded, encoding="cp949", thousands=",")
    user_data.columns = user_data.columns.str.replace(" ", "")
    
    # 2. 8760시간 요금표 생성 및 병합 로직 (기존 코드와 동일)
    # merged_df = pd.merge(...)
    
    # 임시 테스트용 가짜 데이터 생성 (실제 적용 시 삭제하고 위 로직 사용)
    dates = pd.date_range(start="2027-01-01", periods=8760, freq="H")
    merged_df = pd.DataFrame({"Datetime": dates})
    merged_df["발전량(kWh)"] = np.random.uniform(500, 2000, 8760)
    merged_df["기업전력사용량(kWh)"] = np.random.uniform(1000, 3000, 8760)
    merged_df["한전_시간대별_단가"] = np.random.choice([120, 160, 230], 8760)
    
    return merged_df

# 무거운 원본 데이터를 한 번만 불러옵니다.
base_merged_df = load_and_prep_base_data()

# ==========================================
# 3. 사이드바 파라미터 입력
# ==========================================
with st.sidebar:
    st.markdown("### 🏢 Company Logo Here")
    st.markdown("---")
    st.header("⚙️ Simulation Parameters")
    
    st.subheader("Market Pricing (KRW/kWh)")
    ppa_price = st.slider("Direct PPA Rate", 100, 250, 165, 1)
    rec_price = st.slider("REC Market Price", 10, 100, 50, 1)
    gp_price = st.slider("Green Premium", 5, 30, 10, 1)
    smp_price = st.slider("SMP Rate", 50, 250, 140, 1)
    
    st.markdown("---")
    st.subheader("Growth & Escalation (%)")
    kepco_escalation = st.slider("Annual Tariff Increase", 0.0, 10.0, 2.0, 0.1)
    usage_growth = st.slider("Annual Power Consumption Growth", 0.0, 5.0, 1.0, 0.1)
    degradation_rate = st.slider("Solar Panel Degradation", 0.0, 2.0, 0.5, 0.1)
    
    # 고정 변수 세팅
    loss_rate = 0.03
    ppa_network_rate = 15.0 # PPA 송배전 사용요금 단가 등 필요한 변수 입력

# ==========================================
# 4. 20년 시간별 경제성 분석 시뮬레이션
# ==========================================
# 슬라이더가 움직일 때마다 17만 줄 데이터를 넘파이로 순식간에 재계산합니다.

total_kepco_cost = 0
total_ppa_cost = 0
total_rec_cost = 0
total_gp_cost = 0

# 넘파이 배열로 변환하여 계산 속도 극대화
base_gen = base_merged_df["발전량(kWh)"].values
base_usage = base_merged_df["기업전력사용량(kWh)"].values
base_tariff = base_merged_df["한전_시간대별_단가"].values

yearly_results = []

for year in range(20):
    t = year
    
    # 1. 인상률 및 열화율 반영
    current_gen = base_gen * ((1 - degradation_rate / 100) ** t)
    current_usage = base_usage * ((1 + usage_growth / 100) ** t)
    current_tariff = base_tariff * ((1 + kepco_escalation / 100) ** t)
    
    # 2. PPA 정산 로직 적용 (시간별 초과/부족 판별)
    is_shortage = current_gen <= current_usage
    
    ppa_supply = np.where(is_shortage, current_gen, current_usage / (1 - loss_rate))
    shortfall = np.where(is_shortage, current_usage - (current_gen - (current_gen * loss_rate)), 0)
    excess_gen = np.where(~is_shortage, current_gen - ppa_supply, 0)
    
    # 3. 비용 계산
    annual_usage_sum = np.sum(current_usage)
    
    # 한전 100% 사용 시
    yearly_kepco = np.sum(current_usage * current_tariff)
    
    # 직접 PPA 도입 시 (한전 부족전력 요금 + PPA 요금 - SMP 수익)
    kepco_shortfall_cost = np.sum(shortfall * current_tariff)
    ppa_energy_cost = np.sum(ppa_supply * (ppa_price + ppa_network_rate))
    smp_revenue = np.sum(excess_gen * smp_price)
    yearly_ppa = kepco_shortfall_cost + ppa_energy_cost - smp_revenue
    
    # 대안별 총비용
    yearly_rec = yearly_kepco + (annual_usage_sum * rec_price)
    yearly_gp = yearly_kepco + (annual_usage_sum * gp_price)
    
    total_kepco_cost += yearly_kepco
    total_ppa_cost += yearly_ppa
    total_rec_cost += yearly_rec
    total_gp_cost += yearly_gp
    
    # 1년차 단가 기록 (섹터 1 차트용)
    if year == 0:
        first_year_kepco_unit = yearly_kepco / annual_usage_sum
        first_year_ppa_unit = yearly_ppa / annual_usage_sum

# 단위 변환 (억원)
cum_kepco_bn = total_kepco_cost / 1e8
cum_ppa_bn = total_ppa_cost / 1e8
cum_rec_bn = total_rec_cost / 1e8
cum_gp_bn = total_gp_cost / 1e8
savings_bn = cum_kepco_bn - cum_ppa_bn

# ==========================================
# 5. 대시보드 화면 출력
# ==========================================
st.markdown("""
    <div class="gradient-header">
        <h1>RE100 Economic Feasibility Dashboard</h1>
        <p>Long-term simulation & cost-benefit analysis based on hourly data</p>
    </div>
""", unsafe_allow_html=True)

st.markdown(f"""
    <div class="summary-card">
        <h3 style="color: #A0AEC0; font-size: 1.1rem;">Expected 20-Year Cumulative Savings</h3>
        <div class="summary-value">{abs(savings_bn):,.1f} <span style="font-size: 1.5rem; color: #FFFFFF;">KRW Billion</span></div>
        <p style="color: #CBD5E1; font-size: 0.9rem;">Cost Reduction via Direct PPA Adoption</p>
    </div>
""", unsafe_allow_html=True)

chart_layout = dict(
    template="plotly_dark", margin=dict(l=0, r=0, t=40, b=0),
    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    showlegend=False, font=dict(family="Arial", color="white")
)

st.markdown("### 📊 Section 1: Summary of Alternatives (Year 1 Weighted Average)")
col1, col2 = st.columns(2)

with col1:
    st.markdown("**1. Power Procurement (Raw Energy Cost)**")
    fig1 = go.Figure(data=[
        go.Bar(
            x=["KEPCO Grid", "Direct PPA"],
            y=[first_year_kepco_unit, first_year_ppa_unit],
            text=[f"{first_year_kepco_unit:.1f} 원", f"{first_year_ppa_unit:.1f} 원"],
            textposition="auto", marker_color=["#94A3B8", "#3DCD58"]
        )
    ])
    fig1.update_layout(**chart_layout, yaxis_title="KRW / kWh")
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.markdown("**2. RE100 Procurement (Energy + REC)**")
    fig2 = go.Figure(data=[
        go.Bar(
            x=["Direct PPA", "KEPCO + REC", "KEPCO + GP"],
            y=[first_year_ppa_unit, first_year_kepco_unit + rec_price, first_year_kepco_unit + gp_price],
            text=[f"{first_year_ppa_unit:.1f} 원", f"{first_year_kepco_unit + rec_price:.1f} 원", f"{first_year_kepco_unit + gp_price:.1f} 원"],
            textposition="auto", marker_color=["#3DCD58", "#0F766E", "#059669"]
        )
    ])
    fig2.update_layout(**chart_layout, yaxis_title="KRW / kWh")
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")

st.markdown("### 📈 Section 2: 20-Year Long-Term Cumulative Analysis")
fig3 = go.Figure(data=[
    go.Bar(
        x=["KEPCO 100%", "Direct PPA", "KEPCO + REC", "KEPCO + GP"],
        y=[cum_kepco_bn, cum_ppa_bn, cum_rec_bn, cum_gp_bn],
        text=[f"{val:,.1f} Bn" for val in [cum_kepco_bn, cum_ppa_bn, cum_rec_bn, cum_gp_bn]],
        textposition="auto", marker_color=["#94A3B8", "#3DCD58", "#0F766E", "#059669"], width=0.5
    )
])
fig3.update_layout(**chart_layout, yaxis_title="Total Cost (KRW Billion)", height=500)
st.plotly_chart(fig3, use_container_width=True)
