# ... existing code ...
# ==========================================
# 1. Page Configuration & Custom CSS
# ==========================================
st.set_page_config(page_title="RE100 Strategy Dashboard", layout="wide", initial_sidebar_state="expanded")

# 슈나이더 감성의 커스텀 CSS (다크모드 적용, Arial 폰트 강제, 텍스트 화이트)
st.markdown("""
    <style>
    /* 폰트 Arial 강제 적용 */
    * {
        font-family: 'Arial', sans-serif !important;
    }
    
    /* 전체 배경색 - 다크 테마 */
    .stApp {
        background-color: #121212 !important;
    }
    
    /* 사이드바 스타일링 - 어두운 배경 */
    [data-testid="stSidebar"] {
        background-color: #1E1E1E !important;
        box-shadow: 2px 0 10px rgba(0,0,0,0.5);
        border-right: 1px solid #333;
    }
    
    /* 모든 기본 텍스트 하얀색으로 강제 변경 (안 보이는 글씨 밝히기) */
    h1, h2, h3, h4, h5, h6, p, label, .stMarkdown, .stText, span {
        color: #FFFFFF !important;
    }
    
    /* 메인 헤더 그라데이션 카드 */
    .gradient-header {
        background: linear-gradient(135deg, #009E4D 0%, #3DCD58 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white !important;
        box-shadow: 0 10px 20px rgba(0, 0, 0, 0.4);
        margin-bottom: 2rem;
    }
    .gradient-header h1 {
        margin: 0;
        font-size: 2rem;
        font-weight: 800;
        color: white !important;
    }
    .gradient-header p {
        margin: 0;
        opacity: 0.9;
        font-size: 1.1rem;
        color: white !important;
    }
    
    /* 하이라이트 요약 카드 */
    .summary-card {
        background-color: #1E1E1E;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.4);
        border: 1px solid #333;
        text-align: center;
        margin-bottom: 2rem;
    }
    .summary-value {
        font-size: 2.5rem;
        font-weight: 800;
        color: #3DCD58 !important; /* 포인트 컬러 유지 */
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. Sidebar Parameters (왼쪽 패널)
# ... existing code ...
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

# 하이라이트 요약 (인라인 스타일 글꼴색 어둡지 않게 수정)
st.markdown(f"""
    <div class="summary-card">
        <h3 style="color: #A0AEC0; font-size: 1.1rem;">Expected 20-Year Cumulative Savings (vs KEPCO 100%)</h3>
        <div class="summary-value">{abs(savings_bn):,.1f} <span style="font-size: 1.5rem; color: #FFFFFF;">KRW Billion</span></div>
        <p style="color: #CBD5E1; font-size: 0.9rem;">{ "Cost Reduction" if savings_bn > 0 else "Additional Cost" } via Direct PPA Adoption</p>
    </div>
""", unsafe_allow_html=True)


# --- SECTION 1: Alternative Summary ---
st.markdown("### 📊 Section 1: Summary of Alternatives (Current Year)")
col1, col2 = st.columns(2)

# 공통 차트 레이아웃 설정 (다크모드 및 Arial 폰트 적용)
chart_layout = dict(
    template="plotly_dark",
    margin=dict(l=0, r=0, t=40, b=0),
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    showlegend=False,
    font=dict(family="Arial", color="white")
)

with col1:
    st.markdown("**1. Power Procurement (Raw Energy Cost)**")
    fig1 = go.Figure(data=[
        go.Bar(
            x=['KEPCO Grid', 'Direct PPA'],
            y=[kepco_price, ppa_price],
            text=[f"{kepco_price} KRW/kWh", f"{ppa_price} KRW/kWh"],
            textposition='auto',
            textfont=dict(family="Arial", size=14),
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
            textfont=dict(family="Arial", size=14),
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
        textfont=dict(family="Arial", size=14),
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
# ... existing code ...
```eof

### 💡 주요 변경 사항
1. **전체 UI 다크 모드 (`#121212`)**: 바탕색을 짙은 회색/검정에 가까운 모던한 다크 모드로 변경했습니다.
2. **사이드바 음영 (`#1E1E1E`)**: 좌측 파라미터가 있는 사이드바도 어둡게 만들어 전체적인 일체감을 주었습니다.
3. **가시성 개선 (White Text)**: `color: #FFFFFF !important;` 속성을 모든 글씨 영역에 적용하여 배경에 묻히지 않고 눈에 확 띄도록 조정했습니다. (인라인 스타일 색상도 밝은 톤으로 올렸습니다.)
4. **폰트 변경 (Arial)**: 화면 전체 및 Plotly 차트 내부의 폰트까지 모두 `Arial`로 통일했습니다.
5. **차트 다크 테마 반영**: Plotly 차트 레이아웃에 `template="plotly_dark"`를 추가하여 그래프의 축이나 배경선도 어두운 테마에 알맞게 변경되었습니다.
