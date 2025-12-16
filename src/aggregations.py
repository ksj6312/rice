"""
KPI 계산 및 집계 함수 모듈

기능:
- 피크 혼잡도/시간 계산
- 시간대별 평균 (출근/점심/퇴근/심야)
- TOP-N 역/호선 추출
- 방향별 비교
- 요일별 비교
- 혼잡도 분포 통계
"""

import pandas as pd
from typing import Optional, Literal


# ============================================================================
# 1. 상수 정의
# ============================================================================

TIME_PERIODS = {
    '출근': ('06:00', '10:00'),
    '점심': ('11:00', '14:00'),
    '퇴근': ('17:00', '21:00'),
    '심야': ('22:00', '24:30'),
}

WEEKDAY_CLASSIFICATION = {
    '평일': ['평일'],
    '주말': ['토요일', '일요일'],
}


# ============================================================================
# 2. 유틸리티 함수
# ============================================================================

def apply_filters(df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    """
    필터 딕셔너리를 기반으로 DataFrame 필터링
    
    Args:
        df: Long 포맷 DataFrame
        filters: 필터 딕셔너리
            - '요일': list or str
            - '호선': list or str
            - '역명': list or str
            - '방향': list or str
            - '시간대': str (TIME_PERIODS 키)
            
    Returns:
        필터링된 DataFrame
    """
    df_filtered = df.copy()
    
    # 요일 필터
    if '요일' in filters and filters['요일']:
        if isinstance(filters['요일'], list):
            df_filtered = df_filtered[df_filtered['요일'].isin(filters['요일'])]
        else:
            df_filtered = df_filtered[df_filtered['요일'] == filters['요일']]
    
    # 호선 필터
    if '호선' in filters and filters['호선']:
        if isinstance(filters['호선'], list):
            df_filtered = df_filtered[df_filtered['호선'].isin(filters['호선'])]
        else:
            df_filtered = df_filtered[df_filtered['호선'] == filters['호선']]
    
    # 역명 필터
    if '역명' in filters and filters['역명']:
        if isinstance(filters['역명'], list):
            df_filtered = df_filtered[df_filtered['역명'].isin(filters['역명'])]
        else:
            df_filtered = df_filtered[df_filtered['역명'] == filters['역명']]
    
    # 방향 필터
    if '방향' in filters and filters['방향']:
        if isinstance(filters['방향'], list):
            df_filtered = df_filtered[df_filtered['방향'].isin(filters['방향'])]
        else:
            df_filtered = df_filtered[df_filtered['방향'] == filters['방향']]
    
    # 시간대 필터
    if '시간대' in filters and filters['시간대']:
        time_period = filters['시간대']
        if time_period in TIME_PERIODS:
            start_time, end_time = TIME_PERIODS[time_period]
            df_filtered = df_filtered[
                (df_filtered['시간'] >= start_time) & 
                (df_filtered['시간'] <= end_time)
            ]
    
    return df_filtered


def get_time_period(time_str: str) -> Optional[str]:
    """
    시간 문자열을 시간대 구간으로 분류
    
    Args:
        time_str: 시간 문자열 (예: '07:30')
        
    Returns:
        시간대 구간명 (예: '출근') 또는 None
    """
    for period_name, (start_time, end_time) in TIME_PERIODS.items():
        if start_time <= time_str <= end_time:
            return period_name
    return None


def _time_to_minutes(time_str: str) -> int:
    """
    시간 문자열을 분 단위로 변환 (내부 유틸리티)
    
    Args:
        time_str: 'HH:MM' 형식
        
    Returns:
        분 단위 정수
    """
    try:
        hours, minutes = map(int, time_str.split(':'))
        return hours * 60 + minutes
    except:
        return 0


# ============================================================================
# 3. 핵심 함수
# ============================================================================

def compute_kpis(df: pd.DataFrame, filters: dict) -> dict:
    """
    필터 조건에 따른 KPI 계산
    
    Args:
        df: Long 포맷 DataFrame
        filters: 필터 딕셔너리
        
    Returns:
        KPI 딕셔너리:
            - peak_congestion: 최대 혼잡도
            - peak_time: 피크 시간대
            - avg_congestion: 평균 혼잡도
            - total_records: 필터 적용 후 레코드 수
    """
    # 필터 적용
    df_filtered = apply_filters(df, filters)
    
    # 데이터가 없는 경우
    if len(df_filtered) == 0:
        return {
            'peak_congestion': 0,
            'peak_time': 'N/A',
            'avg_congestion': 0,
            'total_records': 0
        }
    
    # KPI 계산
    peak_idx = df_filtered['혼잡도'].idxmax()
    peak_congestion = df_filtered.loc[peak_idx, '혼잡도']
    peak_time = df_filtered.loc[peak_idx, '시간']
    avg_congestion = df_filtered['혼잡도'].mean()
    total_records = len(df_filtered)
    
    return {
        'peak_congestion': round(peak_congestion, 1),
        'peak_time': peak_time,
        'avg_congestion': round(avg_congestion, 1),
        'total_records': total_records
    }


def aggregate_for_line(df: pd.DataFrame) -> pd.DataFrame:
    """
    호선별 집계
    
    Args:
        df: Long 포맷 DataFrame
        
    Returns:
        DataFrame[호선, 평균혼잡도, 최대혼잡도, 피크시간]
    """
    if len(df) == 0:
        return pd.DataFrame(columns=['호선', '평균혼잡도', '최대혼잡도', '피크시간'])
    
    # 호선별 집계
    agg_result = df.groupby('호선').agg({
        '혼잡도': ['mean', 'max']
    }).reset_index()
    
    # 컬럼명 평탄화
    agg_result.columns = ['호선', '평균혼잡도', '최대혼잡도']
    
    # 피크시간 계산 (각 호선별 최대 혼잡도 시간)
    peak_times = []
    for line in agg_result['호선']:
        line_df = df[df['호선'] == line]
        peak_idx = line_df['혼잡도'].idxmax()
        peak_time = line_df.loc[peak_idx, '시간']
        peak_times.append(peak_time)
    
    agg_result['피크시간'] = peak_times
    
    # 반올림
    agg_result['평균혼잡도'] = agg_result['평균혼잡도'].round(1)
    agg_result['최대혼잡도'] = agg_result['최대혼잡도'].round(1)
    
    # 평균혼잡도 기준 내림차순 정렬
    agg_result = agg_result.sort_values('평균혼잡도', ascending=False).reset_index(drop=True)
    
    return agg_result


def aggregate_for_heatmap(df: pd.DataFrame) -> pd.DataFrame:
    """
    히트맵용 집계 (시간 × 호선)
    
    Args:
        df: Long 포맷 DataFrame
        
    Returns:
        DataFrame[index=시간, columns=호선, values=평균혼잡도]
    """
    if len(df) == 0:
        return pd.DataFrame()
    
    # 피벗 테이블 생성
    heatmap_df = df.pivot_table(
        index='시간',
        columns='호선',
        values='혼잡도',
        aggfunc='mean'
    )
    
    # 시간 순서로 정렬 (문자열 기준이지만 HH:MM 포맷이므로 정렬 가능)
    heatmap_df = heatmap_df.sort_index()
    
    # 반올림
    heatmap_df = heatmap_df.round(1)
    
    return heatmap_df


def top_n_stations(
    df: pd.DataFrame, 
    n: int = 10, 
    by: Literal['max', 'avg'] = 'max'
) -> pd.DataFrame:
    """
    가장 혼잡한 역 TOP N
    
    Args:
        df: Long 포맷 DataFrame
        n: 상위 N개
        by: 'max' (최대값 기준) 또는 'avg' (평균 기준)
        
    Returns:
        DataFrame[역명, 호선, 혼잡도, 순위]
    """
    if len(df) == 0:
        return pd.DataFrame(columns=['역명', '호선', '혼잡도', '순위'])
    
    # 역명 + 호선별 집계
    if by == 'max':
        agg_df = df.groupby(['역명', '호선'])['혼잡도'].max().reset_index()
    else:  # avg
        agg_df = df.groupby(['역명', '호선'])['혼잡도'].mean().reset_index()
    
    # 혼잡도 기준 내림차순 정렬
    agg_df = agg_df.sort_values('혼잡도', ascending=False).reset_index(drop=True)
    
    # TOP N 추출
    top_df = agg_df.head(n).copy()
    
    # 순위 추가
    top_df['순위'] = range(1, len(top_df) + 1)
    
    # 혼잡도 반올림
    top_df['혼잡도'] = top_df['혼잡도'].round(1)
    
    # 컬럼 순서 조정
    top_df = top_df[['순위', '역명', '호선', '혼잡도']]
    
    return top_df


# ============================================================================
# 4. 추가 함수 (비교/통계)
# ============================================================================

def compare_by_weekday(df: pd.DataFrame) -> pd.DataFrame:
    """
    요일별 비교 (평일 vs 주말)
    
    Args:
        df: Long 포맷 DataFrame
        
    Returns:
        DataFrame[구분, 평균혼잡도, 최대혼잡도]
    """
    if len(df) == 0:
        return pd.DataFrame(columns=['구분', '평균혼잡도', '최대혼잡도'])
    
    results = []
    
    for classification, days in WEEKDAY_CLASSIFICATION.items():
        filtered_df = df[df['요일'].isin(days)]
        
        if len(filtered_df) > 0:
            avg_congestion = filtered_df['혼잡도'].mean()
            max_congestion = filtered_df['혼잡도'].max()
            
            results.append({
                '구분': classification,
                '평균혼잡도': round(avg_congestion, 1),
                '최대혼잡도': round(max_congestion, 1)
            })
    
    return pd.DataFrame(results)


def compare_by_direction(df: pd.DataFrame) -> pd.DataFrame:
    """
    방향별 비교 (상행/하행 또는 내선/외선)
    
    Args:
        df: Long 포맷 DataFrame
        
    Returns:
        DataFrame[방향, 평균혼잡도, 최대혼잡도, 피크시간]
    """
    if len(df) == 0:
        return pd.DataFrame(columns=['방향', '평균혼잡도', '최대혼잡도', '피크시간'])
    
    # 방향별 집계
    agg_result = df.groupby('방향').agg({
        '혼잡도': ['mean', 'max']
    }).reset_index()
    
    # 컬럼명 평탄화
    agg_result.columns = ['방향', '평균혼잡도', '최대혼잡도']
    
    # 피크시간 계산
    peak_times = []
    for direction in agg_result['방향']:
        dir_df = df[df['방향'] == direction]
        peak_idx = dir_df['혼잡도'].idxmax()
        peak_time = dir_df.loc[peak_idx, '시간']
        peak_times.append(peak_time)
    
    agg_result['피크시간'] = peak_times
    
    # 반올림
    agg_result['평균혼잡도'] = agg_result['평균혼잡도'].round(1)
    agg_result['최대혼잡도'] = agg_result['최대혼잡도'].round(1)
    
    return agg_result


def get_congestion_stats(df: pd.DataFrame) -> dict:
    """
    혼잡도 분포 통계
    
    Args:
        df: Long 포맷 DataFrame
        
    Returns:
        통계 딕셔너리:
            - mean: 평균
            - std: 표준편차
            - min: 최소값
            - max: 최대값
            - q25: 1사분위수
            - q50: 중앙값
            - q75: 3사분위수
    """
    if len(df) == 0:
        return {
            'mean': 0,
            'std': 0,
            'min': 0,
            'max': 0,
            'q25': 0,
            'q50': 0,
            'q75': 0,
        }
    
    congestion_series = df['혼잡도']
    
    return {
        'mean': round(congestion_series.mean(), 1),
        'std': round(congestion_series.std(), 1),
        'min': round(congestion_series.min(), 1),
        'max': round(congestion_series.max(), 1),
        'q25': round(congestion_series.quantile(0.25), 1),
        'q50': round(congestion_series.quantile(0.50), 1),
        'q75': round(congestion_series.quantile(0.75), 1),
    }
