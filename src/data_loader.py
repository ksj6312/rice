"""
데이터 로딩 및 정제 모듈

기능:
- CSV 인코딩 처리 (CP949)
- 컬럼 표준화
- Wide → Long 포맷 변환
- Streamlit 캐싱 적용
"""

import pandas as pd
import streamlit as st
from typing import Optional
import glob
import os


@st.cache_data
def load_data(file_path: Optional[str] = None) -> pd.DataFrame:
    """
    CSV 파일을 로딩하고 기본 정제 수행
    
    Args:
        file_path: CSV 파일 경로. None이면 data/ 폴더에서 자동 탐색
        
    Returns:
        정제된 DataFrame (Wide 포맷)
    """
    # 파일 경로 자동 탐색
    if file_path is None:
        csv_files = glob.glob('data/*.csv')
        if not csv_files:
            raise FileNotFoundError("data/ 폴더에 CSV 파일이 없습니다.")
        file_path = csv_files[0]
    
    # CSV 로딩 (CP949 인코딩)
    try:
        df = pd.read_csv(file_path, encoding='cp949')
    except UnicodeDecodeError:
        # CP949 실패 시 UTF-8 시도
        df = pd.read_csv(file_path, encoding='utf-8')
    
    # 컬럼명 정리 (공백 제거)
    df.columns = df.columns.str.strip()
    
    # 중복 컬럼 처리 (첫 번째와 다섯 번째가 같은 경우)
    if len(df.columns) > 4:
        expected_cols = ['요일구분', '호선', '역번호', '역명', '승하구분']
        time_cols = [col for col in df.columns if '시' in col or '00분' in col or '30분' in col]
        
        # 컬럼이 중복되면 앞 5개를 표준 이름으로 교체
        if len(df.columns) >= len(expected_cols) + len(time_cols):
            new_cols = expected_cols + time_cols
            df.columns = new_cols[:len(df.columns)]
    
    # 혼잡도 값 정제 (공백 제거, 숫자 변환)
    time_columns = [col for col in df.columns if col not in ['요일구분', '호선', '역번호', '역명', '승하구분']]
    for col in time_columns:
        # 공백 제거 후 숫자 변환
        df[col] = pd.to_numeric(df[col].astype(str).str.strip(), errors='coerce')
    
    # 결측치를 0으로 처리
    df[time_columns] = df[time_columns].fillna(0)
    
    return df


@st.cache_data
def to_long_format(df: pd.DataFrame) -> pd.DataFrame:
    """
    Wide 포맷을 Long 포맷으로 변환
    
    목표 스키마: 요일, 호선, 역번호, 역명, 방향, 시간, 혼잡도
    
    Args:
        df: Wide 포맷 DataFrame
        
    Returns:
        Long 포맷 DataFrame
    """
    # 식별 컬럼과 시간 컬럼 분리
    id_cols = ['요일구분', '호선', '역번호', '역명', '승하구분']
    time_cols = [col for col in df.columns if col not in id_cols]
    
    # Wide → Long 변환
    df_long = df.melt(
        id_vars=id_cols,
        value_vars=time_cols,
        var_name='시간',
        value_name='혼잡도'
    )
    
    # 컬럼명 표준화
    df_long = df_long.rename(columns={
        '요일구분': '요일',
        '승하구분': '방향'
    })
    
    # 시간 컬럼 정리 ('시', '분' 제거하고 HH:MM 포맷으로)
    df_long['시간'] = df_long['시간'].str.replace('시', ':').str.replace('분', '').str.strip()
    
    # 00:00, 00:30은 다음날로 처리하기 위해 24:00, 24:30으로 변환
    df_long['시간'] = df_long['시간'].replace({'00:00': '24:00', '00:30': '24:30'})
    
    # 정렬
    df_long = df_long.sort_values(['요일', '호선', '역번호', '방향', '시간']).reset_index(drop=True)
    
    return df_long


def get_csv_info(file_path: Optional[str] = None) -> dict:
    """
    CSV 파일 정보 반환
    
    Args:
        file_path: CSV 파일 경로
        
    Returns:
        파일 정보 딕셔너리
    """
    if file_path is None:
        csv_files = glob.glob('data/*.csv')
        if not csv_files:
            return {}
        file_path = csv_files[0]
    
    if not os.path.exists(file_path):
        return {}
    
    file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
    file_name = os.path.basename(file_path)
    
    return {
        'file_name': file_name,
        'file_size_mb': round(file_size, 2),
        'file_path': file_path
    }

