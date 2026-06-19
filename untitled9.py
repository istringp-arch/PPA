import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# 화면 넓게 쓰기 설정
st.set_page_config(layout="wide", page_title="PPA 경제성 분석 대시보드")

# 다크 모드, 프리텐다드 폰트 및 투명 대시보드판 효과 적용
st.markdown("""
    <style>
    @import url("https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css");
    
    * {
        font-family: "Pretendard", sans-serif !important;
    }
    
    /* 전체 배경을 고급스러운 다크 네이비로 설정 */
    .stApp {
        background-color: #0B1121;
    }
    
    /* 사이드바 배경 설정 */
    [data-testid="stSidebar"] {
        background-color: #0F172A;
    }

    /* 기본 텍스트 색상을 밝은 회색으로 변경 */
    h1, h2, h3, h4, p, label {
        color: #F8FAFC !important;
    }

    /* 투명 느낌의 대시보드 카드 디자인 */
    .metric-card {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.4);
        text-align: center;
    }
    .metric-label {
        font-size: 15px;
        color: #94A3B8;
        font-weight: 500;
        margin-bottom: 8px;
    }
    .metric-value {
        font-size: 32px;
        color: #F1F5F9;
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    .metric-delta-up {
        font-size: 14px;
        margin-top: 8px;
        font-weight: 600;
        color: #EF4444;
    }
    .metric-delta-down {
        font-size: 14px;
        margin-top: 8px;
        font-weight: 600;
        color: #10B981;
    }
    .metric-delta-neutral {
        font-size: 14px;
        margin-top: 8px;
        font-weight: 600;
        color: #94A3B8;
    }
    </style>
""", unsafe_allow_html=True)

@st.cache_data
def generate_virtual_data(annual_usage, solar_capacity, target_year=2027):
    date_rng = pd.date_range(start=f"{target_year}-01-01", end=f"{target_year}-12-31 23:00", freq="h")
    df = pd.DataFrame({"Datetime": date_rng})
    df["Hour"] = df["Datetime"].dt.hour

    base_hourly = annual_usage / 8760
    df["기업전력사용량(kWh)"] = np.where((df["Hour"] >= 9) & (df["Hour"] <= 18), base_hourly * 1.4, base_hourly * 0.6)
    
    efficiency = 0.15
    df["발전량(kWh)"] = np.where((df["Hour"] >= 8) & (df["Hour"] <= 18), 
                                 solar_capacity * efficiency * np.sin(np.pi * (df["Hour"] - 8) / 10), 0)
    df["한전_시간대별_단가"] = np.where((df["Hour"] >= 9) & (df["Hour"] <= 18), 175.0, 115.0)
    return df

def run_simulation(df, ppa_price, rec_price, smp_price, discount_rate=0.05):
    contract_years = 20
    yearly_summary_data = []
    
    for year_idx in range(contract_years):
        target_year = 2027 + year_idx
        t = year_idx
        
        temp_df = df.copy()
        temp_df["발전량(kWh)"] = temp_df["발전량(kWh)"] * ((1 - 0.005) ** t)
        temp_df["기업전력사용량(kWh)"] = temp_df["기업전력사용량(kWh)"] * ((1 + 0.01) ** t)
        temp_df["한전_시간대별_단가"] = temp_df["한전_시간대별_단가"] * ((1 + 0.02) ** t)
        
        current_smp = smp_price * ((1 + 0.015) ** t)
        current_rec = rec_price * ((1 + 0.015) ** t)
        
        annual_usage = temp_df["기업전력사용량(kWh)"].sum()
        
        baseline_final_cost = annual_usage * temp_df["한전_시간대별_단가"].mean()
        total_dppa_cost = annual_usage * ppa_price * 0.92
        rec_final_cost = baseline_final_cost + (annual_usage * current_rec)
        
        discount_factor = (1 + discount_rate) ** t
        
        yearly_summary_data.append({
            "연도": target_year,
            "DPPA 현재가치(PV)": total_dppa_cost / discount_factor,
            "한전100% 현재가치(PV)": baseline_final_cost / discount_factor,
            "REC 현재가치(PV)": rec_final_cost / discount_factor,
            "DPPA 연평균단가(원/kWh)": total_dppa_cost / annual_usage,
            "한전100% 연평균단가(원/kWh)": baseline_final_cost / annual_usage,
            "REC 연평균단가(원/kWh)": rec_final_cost / annual_usage,
        })
    return pd.DataFrame(yearly_summary_data)

st.title("RE100 이행 대안별 장기 경제성 시뮬레이션")
st.caption("제안된 시나리오별 비용 및 단가 비교 분석 대시보드")
st.markdown("---")

with st.sidebar:
    st.header("분석 조건 설정")
    annual_usage = st.number_input("연간 총 전력사용량 (kWh):", value=6000000, step=500000)
    solar_capacity = st.number_input("태양광 설비용량 (kW):", value=1500, step=100)
    st.markdown("---")
    ppa_price = st.slider("PPA 계약 단가 (원/kWh):", 120, 220, 175)
    rec_price = st.slider("REC 예상 단가 (원/kWh):", 40, 140, 70)
    smp_price = st.slider("SMP 기준 단가 (원/kWh):", 80, 180, 135)

base_df = generate_virtual_data(annual_usage, solar_capacity)
result_df = run_simulation(base_df, ppa_price, rec_price, smp_price)

npc_kepco = result_df["한전100% 현재가치(PV)"].sum() / 1e8
npc_ppa = result_df["DPPA 현재가치(PV)"].sum() / 1e8
npc_rec = result_df["REC 현재가치(PV)"].sum() / 1e8
saved_money = npc_kepco - npc_ppa

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">한전 100% 유지 시 총비용</div>
            <div class="metric-value">{npc_kepco:,.1f} 억원</div>
            <div class="metric-delta-neutral">기준 시나리오</div>
        </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">직접 PPA 도입 시 총비용</div>
            <div class="metric-value" style="color: #38BDF8;">{npc_ppa:,.1f} 억원</div>
            <div class="metric-delta-down">▼ {saved_money:,.1f} 억원 절감 장점</div>
        </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">한전 + REC 구매 시 총비용</div>
            <div class="metric-value">{npc_rec:,.1f} 억원</div>
            <div class="metric-delta-up">▲ {npc_rec - npc_kepco:,.1f} 억원 추가 부담</div>
        </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

col_graph1, col_graph2 = st.columns(2)

with col_graph1:
    st.markdown("### 1. 20년 누적 총비용 비교")
    
    fig_total = go.Figure(data=[
        go.Bar(
            x=["한전 100% 유지", "직접 PPA 도입", "한전 + REC 구매"],
            y=[npc_kepco, npc_ppa, npc_rec],
            text=[f"{npc_kepco:,.1f}억", f"{npc_ppa:,.1f}억", f"{npc_rec:,.1f}억"],
            textposition="auto",
            marker_color=["#64748B", "#38BDF8", "#34D399"],
            width=0.5
        )
    ])
    fig_total.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        yaxis_title="20년 누적 현재가치 비용 (억원)",
        margin=dict(l=20, r=20, t=20, b=20),
        height=400,
        font=dict(family="Pretendard", color="#F8FAFC")
    )
    st.plotly_chart(fig_total, use_container_width=True)

with col_graph2:
    st.markdown("### 2. 연도별 대안별 연평균 단가 추이")
    
    fig_years = go.Figure()
    fig_years.add_trace(go.Scatter(x=result_df["연도"], y=result_df["한전100% 연평균단가(원/kWh)"], mode="lines+markers", name="한전 100%", line=dict(color="#64748B", width=2)))
    fig_years.add_trace(go.Scatter(x=result_df["연도"], y=result_df["DPPA 연평균단가(원/kWh)"], mode="lines+markers", name="직접 PPA", line=dict(color="#38BDF8", width=3)))
    fig_years.add_trace(go.Scatter(x=result_df["연도"], y=result_df["REC 연평균단가(원/kWh)"], mode="lines+markers", name="REC 구매", line=dict(color="#34D399", width=2, dash="dot")))
    
    fig_years.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis_title="분석 기준 연도",
        yaxis_title="실질 평균 단가 (원/kWh)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, r=20, t=20, b=20),
        height=400,
        font=dict(family="Pretendard", color="#F8FAFC")
    )
    st.plotly_chart(fig_years, use_container_width=True)

st.markdown("---")
csv = result_df.to_csv(index=False).encode("utf-8-sig")
st.download_button(label="시뮬레이션 결과 데이터 다운로드", data=csv, file_name="ppa_simulation_result.csv", mime="text/csv")
