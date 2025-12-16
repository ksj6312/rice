"""
서울 지하철 혼잡도 대시보드
메인 엔트리포인트
"""

import streamlit as st
import pandas as pd
from src.data_loader import load_data, to_long_format, get_csv_info

# 페이지 설정
st.set_page_config(
    page_title="서울 지하철 혼잡도 대시보드",
    page_icon="🚇",
    layout="wide"
)

# 타이틀
st.title("🚇 서울 지하철 혼잡도 대시보드")

# 데이터 로딩
try:
    with st.spinner("데이터 로딩 중..."):
        # Wide 포맷 로딩
        df_wide = load_data()
        
        # Long 포맷 변환
        df_long = to_long_format(df_wide)
        
        # 파일 정보
        file_info = get_csv_info()
    
    # 성공 메시지
    st.success("✅ 데이터 로딩 완료!")
    
    # 데이터 요약
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("총 레코드 수", f"{len(df_long):,}")
    
    with col2:
        st.metric("역 수", df_long['역명'].nunique())
    
    with col3:
        st.metric("호선 수", df_long['호선'].nunique())
    
    with col4:
        st.metric("시간대 수", df_long['시간'].nunique())
    
    # 페이즈 1 완료 안내
    st.info("""
    ✅ **페이즈 1 완료**: 데이터 로딩 및 정제 모듈 구현 완료
    - CSV 인코딩 처리 (CP949) ✓
    - 컬럼 표준화 ✓
    - Wide → Long 포맷 변환 ✓
    - Streamlit 캐싱 적용 ✓
    
    **다음 단계 (페이즈 2)**: KPI/집계 함수 구축
    """)

    # 데이터 미리보기
    with st.expander("📊 데이터 미리보기 (Long 포맷)"):
        st.dataframe(df_long.head(20), width='stretch')
        
        st.subheader("컬럼 정보")
        col_info = pd.DataFrame({
            '컬럼명': df_long.columns,
            '타입': df_long.dtypes.values,
            'Null 개수': df_long.isnull().sum().values,
            '고유값 개수': [df_long[col].nunique() for col in df_long.columns]
        })
        st.dataframe(col_info, width='stretch')
    
    # 파일 정보
    with st.expander("📁 파일 정보"):
        if file_info:
            st.write(f"**파일명**: {file_info.get('file_name', 'N/A')}")
            st.write(f"**파일 크기**: {file_info.get('file_size_mb', 0)} MB")
            st.write(f"**경로**: {file_info.get('file_path', 'N/A')}")
    
    # 프로젝트 구조 안내
    with st.expander("🗂️ 프로젝트 구조"):
        st.code("""
rice-1/
├── app.py                 # 메인 엔트리포인트 (현재 파일)
├── pages/                 # 멀티페이지용 (페이즈 4)
├── src/                   # 데이터 로딩/집계 모듈
│   ├── data_loader.py     # 데이터 로딩/정제 ✅
│   └── aggregations.py    # KPI/집계 함수 (페이즈 2)
├── data/                  # CSV 데이터 저장
│   └── 서울교통공사_지하철혼잡도정보_20250930.csv
└── requirements.txt       # 의존성 패키지
        """, language="text")

except FileNotFoundError as e:
    st.error(f"❌ 파일을 찾을 수 없습니다: {e}")
except Exception as e:
    st.error(f"❌ 데이터 로딩 중 오류 발생: {e}")
    st.exception(e)

import pandas as pd

st.divider()

# 개발 로드맵
st.subheader("📋 개발 로드맵")
col1, col2, col3 = st.columns(3)

with col1:
    st.success("✅ **페이즈 0**: 프로젝트 뼈대")
    st.caption("폴더 구조, requirements.txt")

with col2:
    st.success("✅ **페이즈 1**: 데이터 로딩/정제")
    st.caption("CSV 로딩, Long 포맷 변환")

with col3:
    st.warning("⏳ **페이즈 2**: KPI/집계")
    st.caption("피크 혼잡도, TOP-N 역")
