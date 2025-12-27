"""
PlanCraft Agent - 웹 검색 판단 모듈

사용자 입력에 따라 웹 검색이 필요한지 판단하고 적절한 쿼리를 생성합니다.
"""

import re
from typing import Dict, Optional
from datetime import datetime


# =============================================================================
# 웹 검색 필요 여부 판단 키워드
# =============================================================================

# 내부 문서로 충분한 키워드 (웹 검색 불필요)
INTERNAL_KEYWORDS = [
    "규정", "매뉴얼", "절차", "프로세스", "내부",
    "사내", "우리", "당사", "회사",
]

def should_search_web(user_input: str, rag_context: str = "") -> Dict[str, any]:
    """
    웹 검색이 필요한지 판단합니다.

    변경된 로직 (v1.4.1):
    - RAG 컨텍스트가 있어도 웹 검색을 우선적으로 수행합니다.
    - URL이 포함된 경우에만 Fetch로 넘기기 위해 검색을 스킵합니다.
    - 그 외 대부분의 기획 관련 요청에 대해 검색을 수행합니다.

    Args:
        user_input: 사용자 입력 텍스트
        rag_context: RAG에서 검색된 컨텍스트 (참고용, 스킵 기준 아님)

    Returns:
        Dict: {
            "should_search": bool,
            "reason": str,
            "search_query": str (검색 필요시)
        }
    """
    # 1. URL이 이미 있으면 웹 검색 불필요 (URL fetch로 처리)
    if re.search(r'https?://', user_input):
        return {
            "should_search": False,
            "reason": "URL이 직접 제공됨",
            "search_query": None
        }

    # 2. 명시적인 내부 문서 질의인 경우만 스킵
    has_internal = any(kw in user_input for kw in INTERNAL_KEYWORDS)
    if has_internal:
        return {
            "should_search": False,
            "reason": "내부 문서 질의",
            "search_query": None
        }

    # 3. 그 외 모든 경우 웹 검색 수행 (RAG 컨텍스트 무시)
    query = _generate_search_query(user_input)
    return {
        "should_search": True,
        "reason": "최신/외부 정보 보강",
        "search_query": query
    }


def _generate_search_query(user_input: str) -> str:
    """
    검색 쿼리를 생성합니다.
    """
    # 불필요한 조사/어미 제거 등 간단한 정제
    clean_input = re.sub(r'[을를이가은는에서의로]', ' ', user_input)
    clean_input = re.sub(r'\s+', ' ', clean_input).strip()
    
    # 현재 연도 추가하여 최신성 확보
    current_year = datetime.now().year
    
    # 이미 연도가 없으면 추가
    if str(current_year) not in clean_input and str(current_year+1) not in clean_input:
        return f"{clean_input} {current_year} 트렌드 시장동향"
        
    return clean_input
