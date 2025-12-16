"""
서울 지하철 혼잡도 대시보드 - 페이즈 3 MVP
"""

import streamlit as st
import pandas as pd
import altair as alt
from src.data_loader import load_data, to_long_format
from src.aggregations import (
    compute_kpis, 
    apply_filters,
    top_n_stations,
    TIME_PERIODS
)

# ============================================================================
# 페이지 설정
# ============================================================================
st.set_page_config(
    page_title="서울 지하철 혼잡도 대시보드",
    page_icon="🚇",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# 데이터 로딩
# ============================================================================
@st.cache_data
def load_all_data():
    """데이터 로딩 및 변환"""
    df_wide = load_data()
    df_long = to_long_format(df_wide)
    return df_long

try:
    with st.spinner("🚇 데이터 로딩 중..."):
        df_long = load_all_data()
except Exception as e:
    st.error(f"❌ 데이터 로딩 실패: {e}")
    st.stop()

# ============================================================================
# 사이드바 필터
# ============================================================================
st.sidebar.header("🔍 필터")

# 요일 선택
요일_옵션 = sorted(df_long['요일'].unique().tolist())
선택_요일 = st.sidebar.multiselect(
    "📅 요일",
    options=요일_옵션,
    default=요일_옵션,
    help="분석할 요일을 선택하세요"
)

# 호선 선택
호선_옵션 = sorted(df_long['호선'].unique().tolist())
선택_호선 = st.sidebar.multiselect(
    "🚇 호선",
    options=호선_옵션,
    default=호선_옵션,
    help="분석할 호선을 선택하세요"
)

# 역 검색 (선택 사항)
역_옵션 = ['전체'] + sorted(df_long['역명'].unique().tolist())
선택_역 = st.sidebar.selectbox(
    "🏢 역 검색",
    options=역_옵션,
    help="특정 역을 선택하거나 전체를 선택하세요"
)

# 방향 선택
방향_옵션 = sorted(df_long['방향'].unique().tolist())
선택_방향 = st.sidebar.multiselect(
    "↔️ 방향",
    options=방향_옵션,
    default=방향_옵션,
    help="상행/하행 또는 내선/외선 선택"
)

# 시간대 선택
시간대_옵션 = ['전체'] + list(TIME_PERIODS.keys())
선택_시간대 = st.sidebar.selectbox(
    "⏰ 시간대",
    options=시간대_옵션,
    help="출근/점심/퇴근/심야 시간대 선택"
)

# 필터 딕셔너리 구성
filters = {}
if 선택_요일:
    filters['요일'] = 선택_요일
if 선택_호선:
    filters['호선'] = 선택_호선
if 선택_역 != '전체':
    filters['역명'] = [선택_역]
if 선택_방향:
    filters['방향'] = 선택_방향
if 선택_시간대 != '전체':
    filters['시간대'] = 선택_시간대

# 필터 적용
df_filtered = apply_filters(df_long, filters)

# 사이드바 하단 정보
st.sidebar.divider()
st.sidebar.caption(f"📊 필터링된 데이터: **{len(df_filtered):,}** 건")
st.sidebar.caption(f"📊 전체 데이터: **{len(df_long):,}** 건")

# ============================================================================
# 메인 헤더
# ============================================================================
st.title("🚇 서울 지하철 혼잡도 대시보드")
st.caption("서울교통공사 지하철 혼잡도 실시간 분석 (2025년 9월 기준)")

# ============================================================================
# KPI 카드 영역
# ============================================================================
kpis = compute_kpis(df_long, filters)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="🔥 피크 혼잡도",
        value=f"{kpis['peak_congestion']}%",
        help="선택된 조건에서 가장 높은 혼잡도"
    )

with col2:
    st.metric(
        label="📊 평균 혼잡도",
        value=f"{kpis['avg_congestion']}%",
        help="선택된 조건의 평균 혼잡도"
    )

with col3:
    st.metric(
        label="⏰ 피크 시간",
        value=kpis['peak_time'],
        help="혼잡도가 가장 높은 시간대"
    )

with col4:
    st.metric(
        label="📋 분석 건수",
        value=f"{kpis['total_records']:,}",
        help="필터링된 데이터 레코드 수"
    )

st.divider()

# ============================================================================
# 시각화 영역
# ============================================================================

# 차트 1: 시간대별 혼잡도 라인차트
st.subheader("📈 시간대별 혼잡도 추이")

if len(df_filtered) > 0:
    # 시간대별 평균 혼잡도 집계
    time_agg = df_filtered.groupby('시간', as_index=False)['혼잡도'].mean()
    time_agg['혼잡도'] = time_agg['혼잡도'].round(1)
    
    # Altair 라인차트
    line_chart = alt.Chart(time_agg).mark_line(
        point=alt.OverlayMarkDef(size=60, filled=True),
        strokeWidth=3,
        color='#FF6B6B'
    ).encode(
        x=alt.X('시간:O', 
                title='시간대',
                axis=alt.Axis(labelAngle=-45, labelFontSize=10)),
        y=alt.Y('혼잡도:Q', 
                title='평균 혼잡도 (%)',
                scale=alt.Scale(domain=[0, 100])),
        tooltip=[
            alt.Tooltip('시간:O', title='시간'),
            alt.Tooltip('혼잡도:Q', title='혼잡도 (%)', format='.1f')
        ]
    ).properties(
        height=400
    )
    
    # 피크 시간 강조
    peak_data = time_agg[time_agg['시간'] == kpis['peak_time']]
    if len(peak_data) > 0:
        peak_point = alt.Chart(peak_data).mark_point(
            size=300,
            color='#FF4444',
            filled=True,
            opacity=0.8
        ).encode(
            x='시간:O',
            y='혼잡도:Q',
            tooltip=[
                alt.Tooltip('시간:O', title='⭐ 피크 시간'),
                alt.Tooltip('혼잡도:Q', title='혼잡도 (%)', format='.1f')
            ]
        )
        
        final_chart = (line_chart + peak_point).configure_axis(
            labelFontSize=11,
            titleFontSize=13
        ).configure_view(
            strokeWidth=0
        )
    else:
        final_chart = line_chart.configure_axis(
            labelFontSize=11,
            titleFontSize=13
        ).configure_view(
            strokeWidth=0
        )
    
    st.altair_chart(final_chart, use_container_width=True)
    
    # 시간대별 통계 요약
    with st.expander("📊 시간대별 상세 데이터"):
        st.dataframe(
            time_agg.sort_values('혼잡도', ascending=False),
            hide_index=True,
            use_container_width=True,
            column_config={
                "시간": st.column_config.TextColumn("시간대", width="medium"),
                "혼잡도": st.column_config.NumberColumn("혼잡도 (%)", format="%.1f")
            }
        )
else:
    st.warning("⚠️ 선택한 필터 조건에 해당하는 데이터가 없습니다.")

st.divider()

# 차트 2: TOP 10 혼잡 역 막대차트
st.subheader("🏆 가장 혼잡한 역 TOP 10")

if len(df_filtered) > 0:
    # TOP 10 역 추출
    top_stations_df = top_n_stations(df_filtered, n=10, by='max')
    
    if len(top_stations_df) > 0:
        # Altair 막대차트
        bar_chart = alt.Chart(top_stations_df).mark_bar(
            cornerRadiusTopRight=8,
            cornerRadiusTopLeft=8
        ).encode(
            x=alt.X('혼잡도:Q', 
                    title='최대 혼잡도 (%)',
                    scale=alt.Scale(domain=[0, 100])),
            y=alt.Y('역명:N', 
                    title='역명',
                    sort='-x',
                    axis=alt.Axis(labelFontSize=12)),
            color=alt.Color('호선:N', 
                           title='호선',
                           scale=alt.Scale(scheme='tableau10')),
            tooltip=[
                alt.Tooltip('순위:Q', title='순위'),
                alt.Tooltip('역명:N', title='역명'),
                alt.Tooltip('호선:N', title='호선'),
                alt.Tooltip('혼잡도:Q', title='최대 혼잡도 (%)', format='.1f')
            ]
        ).properties(
            height=450
        ).configure_axis(
            labelFontSize=11,
            titleFontSize=13
        ).configure_legend(
            titleFontSize=12,
            labelFontSize=11
        ).configure_view(
            strokeWidth=0
        )
        
        st.altair_chart(bar_chart, use_container_width=True)
        
        # TOP 10 테이블
        with st.expander("📋 TOP 10 상세 정보"):
            st.dataframe(
                top_stations_df,
                hide_index=True,
                use_container_width=True,
                column_config={
                    "순위": st.column_config.NumberColumn("순위", width="small"),
                    "역명": st.column_config.TextColumn("역명", width="medium"),
                    "호선": st.column_config.TextColumn("호선", width="small"),
                    "혼잡도": st.column_config.NumberColumn("최대 혼잡도 (%)", format="%.1f")
                }
            )
    else:
        st.info("데이터가 충분하지 않습니다.")
else:
    st.warning("⚠️ 선택한 필터 조건에 해당하는 데이터가 없습니다.")

st.divider()

# ============================================================================
# 푸터
# ============================================================================
st.caption("💡 **사용 팁**: 왼쪽 사이드바에서 요일, 호선, 역, 방향, 시간대를 선택하여 데이터를 필터링할 수 있습니다.")
st.caption("📌 **데이터 출처**: 서울교통공사 지하철 혼잡도 정보 (2025년 9월 30일 기준)")
