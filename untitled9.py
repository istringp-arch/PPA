import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# 화면 넓게 쓰기 설정
st.set_page_config(layout="wide", page_title="PPA 경제성 분석 대시보드")

# 보내주신 이미지 느낌의 깔끔하고 고급스러운 디자인을 위한 CSS 스타일 적용
st.markdown("""
    <style>
    body {
        background-color: #F8FAFC;
    }
    .metric-card {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        text-align: center;
    }
    .metric-label {
        font-size: 14px;
        color: #64748B;
        font-weight: 600;
        margin-bottom: 8px;
    }
    .metric-value {
        font-size: 28px;
        color: #0F172A;
        font-weight: 700;
    }
    .metric-delta {
        font-size: 14px;
        margin-top: 6px;
        font-weight: 600;
    }
    </style>
""", unsafe_allow_html=True)

# 1. 가상 데이터 생성기 함수
@st.cache_data
def generate_virtual_data(annual_usage, solar_capacity, target_year=2027):
    date_rng = pd.date_range(start=f"{target_year}-01-01", end=f"{target_year}-12-31 23:00", freq="h")
    df = pd.DataFrame({"Datetime": date_rng})
    df["Hour"] = df["Datetime"].dt.hour

    # 전력사용량 및 발전량 가상 패턴 생성
    base_hourly = annual_usage / 8760
    df["기업전력사용량(kWh)"] = np.where((df["Hour"] >= 9) & (df["Hour"] <= 18), base_hourly * 1.4, base_hourly * 0.6)
    
    efficiency = 0.15
    df["발전량(kWh)"] = np.where((df["Hour"] >= 8) & (df["Hour"] <= 18), 
                                 solar_capacity * efficiency * np.sin(np.pi * (df["Hour"] - 8) / 10), 0)
    df["한전_시간대별_단가"] = np.where((df["Hour"] >= 9) & (df["Hour"] <= 18), 175.0, 115.0)
    return df

# 2. 경제성 분석 메인 로직 함수
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
        
        # 비용 정산 간소화 로직
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

# 타이틀 영역
st.title("RE100 이행 대안별 장기 경제성 시뮬레이션")
st.caption("제안된 시나리오별 비용 및 단가 비교 분석 대시보드")
st.markdown("---")

# 사이드바 설정
with st.sidebar:
    st.header("⚙️ 분석 조건 설정")
    annual_usage = st.number_input("연간 총 전력사용량 (kWh):", value=6000000, step=500000)
    solar_capacity = st.number_input("태양광 설비용량 (kW):", value=1500, step=100)
    st.markdown("---")
    ppa_price = st.slider("PPA 계약 단가 (원/kWh):", 120, 220, 175)
    rec_price = st.slider("REC 예상 단가 (원/kWh):", 40, 140, 70)
    smp_price = st.slider("SMP 기준 단가 (원/kWh):", 80, 180, 135)

# 시뮬레이션 계산 실행
base_df = generate_virtual_data(annual_usage, solar_capacity)
result_df = run_simulation(base_df, ppa_price, rec_price, smp_price)

# 누적 비용 산출
npc_kepco = result_df["한전100% 현재가치(PV)"].sum() / 1e8
npc_ppa = result_df["DPPA 현재가치(PV)"].sum() / 1e8
npc_rec = result_df["REC 현재가치(PV)"].sum() / 1e8
saved_money = npc_kepco - npc_ppa

# --- 상단 지표 카드 영역 (보내주신 이미지 디자인 구현) ---
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">한전 100% 유지 시 총비용</div>
            <div class="metric-value">{npc_kepco:,.1f} 억원</div>
            <div class="metric-delta" style="color: #64748B;">기준 시나리오</div>
        </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">직접 PPA 도입 시 총비용</div>
            <div class="metric-value" style="color: #0284c7;">{npc_ppa:,.1f} 억원</div>
            <div class="metric-delta" style="color: #16a34a;">▼ {saved_money:,.1f} 억원 절감 장점</div>
        </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">한전 + REC 구매 시 총비용</div>
            <div class="metric-value">{npc_rec:,.1f} 억원</div>
            <div class="metric-delta" style="color: #dc2626;">▲ {npc_rec - npc_kepco:,.1f} 억원 추가 부담</div>
        </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- 하단 막대그래프 시각화 영역 ---
col_graph1, col_graph2 = st.columns(2)

with col_graph1:
    st.markdown("### 1. 20년 누적 총비용 비교")
    
    fig_total = go.Figure(data=[
        go.Bar(
            x=["한전 100% 유지", "직접 PPA 도입", "한전 + REC 구매"],
            y=[npc_kepco, npc_ppa, npc_rec],
            text=[f"{npc_kepco:,.1f}억", f"{npc_ppa:,.1f}억", f"{npc_rec:,.1f}억"],
            textposition='auto',
            marker_color=['#94A3B8', '#0284C7', '#64748B'],
            width=0.5
        )
    ])
    fig_total.update_layout(
        template="plotly_white",
        yaxis_title="20년 누적 현재가치 비용 (억원)",
        margin=dict(l=20, r=20, t=20, b=20),
        height=400
    )
    st.plotly_chart(fig_total, use_container_width=True)

with col_graph2:
    st.markdown("### 2. 연도별 대안별 연평균 단가 추이")
    
    # 5년 단위로 샘플링하여 깔끔한 막대 그룹 생성
    sample_df = result_df[result_df["연도"].isin([2027, 2032, 2037, 2042, 2046])]
    
    fig_years = go.Figure()
    fig_years.add_trace(go.Bar(x=sample_df["연도"], y=sample_df["한전100% 연평균단가(원/kWh)"], name="한전 100%", marker_color='#94A3B8'))
    fig_years.add_trace(go.Bar(x=sample_df["연도"], y=sample_df["DPPA 연평균단가(원/kWh)"], name="직접 PPA", marker_color='#0284C7'))
    fig_years.add_trace(go.Bar(x=sample_df["연도"], y=sample_df["REC 연평균단가(원/kWh)"], name="REC 구매", marker_color='#64748B'))
    
    fig_years.update_layout(
        template="plotly_white",
        barmode='group',
        xaxis_title="분석 기준 연도",
        yaxis_title="실질 평균 단가 (원/kWh)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, r=20, t=20, b=20),
        height=400
    )
    st.plotly_chart(fig_years, use_container_width=True)

st.markdown("---")
# 데이터 다운로드 버튼 기능 유지
csv = result_df.to_csv(index=False).encode("utf-8-sig")
st.download_button(label="📊 시뮬레이션 결과 데이터(CSV) 다운로드", data=csv, file_name="ppa_simulation_result.csv", mime="text/csv")
