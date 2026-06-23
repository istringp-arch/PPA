import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(layout="wide", page_title="PPA 경제성 분석 대시보드")

# 1. 가상 데이터 생성기 함수
@st.cache_data
def generate_virtual_data(annual_usage, solar_capacity, target_year=2027):
    # 1년 8760시간 데이터프레임 생성
    date_rng = pd.date_range(start=f"{target_year}-01-01", end=f"{target_year}-12-31 23:00", freq="h")
    df = pd.DataFrame({"Datetime": date_rng})
    df["Year"] = df["Datetime"].dt.year
    df["Month"] = df["Datetime"].dt.month
    df["Day"] = df["Datetime"].dt.day
    df["Hour"] = df["Datetime"].dt.hour

    # 기업 전력사용량 가상 패턴: 업무시간(9시~18시)에 집중, 나머지 시간은 절반 수준
    base_hourly = annual_usage / 8760
    df["기업전력사용량(kWh)"] = np.where(
        (df["Hour"] >= 9) & (df["Hour"] <= 18), 
        base_hourly * 1.5, 
        base_hourly * 0.5
    )

    # 태양광 발전량 가상 패턴: 일조시간(8시~18시)에 사인 곡선 형태로 발전, 최대 효율 15% 가정
    efficiency = 0.15
    df["발전량(kWh)"] = np.where(
        (df["Hour"] >= 8) & (df["Hour"] <= 18),
        solar_capacity * efficiency * np.sin(np.pi * (df["Hour"] - 8) / 10),
        0
    )
    
    # 임시 시간대별 한전 단가 생성 (실제 tariff_df 대체용)
    df["한전_시간대별_단가"] = np.where(
        (df["Hour"] >= 9) & (df["Hour"] <= 18), 180.0, 120.0
    )
    
    return df

# 2. 경제성 분석 메인 로직 함수
def run_simulation(df, ppa_price, rec_price, smp_price, discount_rate=0.05):
    contract_years = 20
    kepco_escalation = 0.02
    usage_growth = 0.01
    degradation_rate = -0.005
    smp_escalation = 0.015
    ppa_escalation = 0.0
    
    yearly_summary_data = []
    
    # 20년 시뮬레이션
    for year_idx in range(contract_years):
        target_year = 2027 + year_idx
        t = year_idx
        
        temp_df = df.copy()
        
        # 열화율 및 증가율 적용
        temp_df["발전량(kWh)"] = temp_df["발전량(kWh)"] * ((1 + degradation_rate) ** t)
        temp_df["기업전력사용량(kWh)"] = temp_df["기업전력사용량(kWh)"] * ((1 + usage_growth) ** t)
        
        # 단가 인상 적용
        temp_df["한전_시간대별_단가"] = temp_df["한전_시간대별_단가"] * ((1 + kepco_escalation) ** t)
        current_smp = smp_price * ((1 + smp_escalation) ** t)
        current_ppa = ppa_price * ((1 + ppa_escalation) ** t)
        current_rec = rec_price * ((1 + 0.015) ** t)
        
        # 전력 분배 로직
        is_shortage = temp_df["발전량(kWh)"] <= temp_df["기업전력사용량(kWh)"]
        loss_rate = 0.0352
        
        temp_df["PPA_공급량(kWh)"] = np.where(
            is_shortage,
            temp_df["발전량(kWh)"],
            temp_df["기업전력사용량(kWh)"] / (1 - loss_rate)
        )
        
        annual_usage = temp_df["기업전력사용량(kWh)"].sum()
        
        # 가상의 연간 총비용 계산 
        total_dppa_cost = annual_usage * current_ppa * 0.95 
        baseline_final_cost = annual_usage * temp_df["한전_시간대별_단가"].mean()
        rec_final_cost = baseline_final_cost + (annual_usage * current_rec)
        
        # 현재가치 할인
        discount_factor = (1 + discount_rate) ** t
        
        yearly_summary_data.append({
            "연도": target_year,
            "DPPA 총비용(명목, 원)": total_dppa_cost,
            "한전100% 총비용(명목, 원)": baseline_final_cost,
            "REC 총비용(명목, 원)": rec_final_cost,
            "DPPA 현재가치(PV)": total_dppa_cost / discount_factor,
            "한전100% 현재가치(PV)": baseline_final_cost / discount_factor,
            "REC 현재가치(PV)": rec_final_cost / discount_factor,
            "DPPA 연평균단가(원/kWh)": total_dppa_cost / annual_usage,
            "한전100% 연평균단가(원/kWh)": baseline_final_cost / annual_usage,
            "REC 연평균단가(원/kWh)": rec_final_cost / annual_usage,
        })
        
    return pd.DataFrame(yearly_summary_data)

# 3. 화면 UI 구성
st.title("기업용 PPA 도입 경제성 분석 대시보드")

with st.sidebar:
    st.header("사용자 입력 위젯")
    annual_usage = st.number_input("연간 총 전력사용량 (kWh):", value=5000000, step=100000)
    solar_capacity = st.number_input("태양광 설비용량 (kW):", value=1000, step=100)
    
    st.divider()
    ppa_price = st.slider("PPA 계약 단가 (원/kWh):", 100, 250, 180)
    rec_price = st.slider("REC 예상 단가 (원/kWh):", 30, 150, 75)
    smp_price = st.slider("SMP 기준 단가 (원/kWh):", 50, 200, 140)

# 가상 데이터 및 시뮬레이션 실행
base_df = generate_virtual_data(annual_usage, solar_capacity)
result_df = run_simulation(base_df, ppa_price, rec_price, smp_price)

# 상단 요약
st.subheader("20년 누적 현금흐름 요약 (현재가치 기준)")
col1, col2, col3 = st.columns(3)
npc_kepco = result_df["한전100% 현재가치(PV)"].sum() / 1e8
npc_ppa = result_df["DPPA 현재가치(PV)"].sum() / 1e8
npc_rec = result_df["REC 현재가치(PV)"].sum() / 1e8

col1.metric("한전 100% 유지 시", f"{npc_kepco:,.1f} 억원")
col2.metric("직접 PPA 도입 시", f"{npc_ppa:,.1f} 억원", f"{npc_kepco - npc_ppa:,.1f} 억원 절감")
col3.metric("한전 + REC 구매 시", f"{npc_rec:,.1f} 억원", f"{npc_kepco - npc_rec:,.1f} 억원 증가", delta_color="inverse")

st.divider()

# 그래프 시각화
col_g1, col_g2 = st.columns(2)

with col_g1:
    st.markdown("#### 연간 가중평균 단가 추이")
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=result_df["연도"], y=result_df["한전100% 연평균단가(원/kWh)"], name="한전 100%", line=dict(dash="dash", color="firebrick")))
    fig1.add_trace(go.Scatter(x=result_df["연도"], y=result_df["DPPA 연평균단가(원/kWh)"], name="직접 PPA", line=dict(width=3, color="royalblue")))
    fig1.add_trace(go.Scatter(x=result_df["연도"], y=result_df["REC 연평균단가(원/kWh)"], name="REC 구매", line=dict(dash="dot", color="forestgreen")))
    st.plotly_chart(fig1, use_container_width=True)

with col_g2:
    st.markdown("#### 연간 총비용 추이 (현재가치)")
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=result_df["연도"], y=result_df["한전100% 현재가치(PV)"] / 1e8, name="한전 100%", line=dict(dash="dash", color="firebrick")))
    fig2.add_trace(go.Scatter(x=result_df["연도"], y=result_df["DPPA 현재가치(PV)"] / 1e8, name="직접 PPA", line=dict(width=3, color="royalblue")))
    fig2.add_trace(go.Scatter(x=result_df["연도"], y=result_df["REC 현재가치(PV)"] / 1e8, name="REC 구매", line=dict(dash="dot", color="forestgreen")))
    st.plotly_chart(fig2, use_container_width=True)

st.divider()
st.markdown("#### 엑셀 데이터 다운로드")
csv = result_df.to_csv(index=False).encode("utf-8-sig")
st.download_button(label="20년 연간 요약 데이터 다운로드", data=csv, file_name="20yr_summary.csv", mime="text/csv")
