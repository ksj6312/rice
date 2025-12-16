"""
KPI 계산 및 집계 함수 모듈

페이즈 2에서 구현 예정:
- 피크 혼잡도/시간 계산
- 시간대별 평균 (출근/퇴근/심야)
- TOP-N 역/호선 추출
- 방향별 비교
"""

import pandas as pd


def compute_kpis(df: pd.DataFrame, filters: dict) -> dict:
    """
    필터 조건에 따른 KPI 계산
    
    Args:
        df: Long 포맷 DataFrame
        filters: 필터 딕셔너리
        
    Returns:
        KPI 딕셔너리
    """
    # TODO: 페이즈 2에서 구현
    pass


def aggregate_for_line(df: pd.DataFrame) -> pd.DataFrame:
    """
    호선별 집계
    """
    # TODO: 페이즈 2에서 구현
    pass


def aggregate_for_heatmap(df: pd.DataFrame) -> pd.DataFrame:
    """
    히트맵용 집계 (시간 × 호선)
    """
    # TODO: 페이즈 2에서 구현
    pass


def top_n_stations(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """
    가장 혼잡한 역 TOP N
    """
    # TODO: 페이즈 2에서 구현
    pass

