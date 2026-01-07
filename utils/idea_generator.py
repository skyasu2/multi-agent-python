"""
PlanCraft Agent - 아이디어 생성기 (통합 버전)

기능:
1. 카테고리별 아이디어 제안 (IT, 금융, F&B, 헬스케어 등)
2. LLM 기반 창의적 아이디어 생성
3. 세션당 LLM 호출 제한 (10회 초과 시 Static Pool 사용)
4. 짧은 입력 증강 (Analyzer와 통합)
5. 시간 컨텍스트 반영 (시즌별 트렌드)
"""

import random
from typing import List, Tuple, Optional, Dict
from utils.llm import get_llm
from utils.schemas import CreativeIdeaList
from utils.prompt_examples import (
    CATEGORIES,
    CATEGORY_POOLS,
    ALL_EXAMPLES,
    WEB_APP_POOL,
    NON_IT_POOL,
    get_examples_by_category,
)
from utils.time_context import get_time_context


# =============================================================================
# LLM 호출 제한 관리 (세션 레벨)
# =============================================================================

MAX_LLM_CALLS_PER_SESSION = 10

# 세션 상태는 Streamlit에서 관리하므로, 여기서는 카운터만 제공
_llm_call_count = 0


def get_llm_call_count() -> int:
    """현재 LLM 호출 횟수 반환"""
    return _llm_call_count


def increment_llm_call_count() -> int:
    """LLM 호출 횟수 증가 및 반환"""
    global _llm_call_count
    _llm_call_count += 1
    return _llm_call_count


def reset_llm_call_count():
    """LLM 호출 횟수 초기화 (새 세션 시작 시)"""
    global _llm_call_count
    _llm_call_count = 0


def is_llm_available() -> bool:
    """LLM 호출 가능 여부 확인"""
    return _llm_call_count < MAX_LLM_CALLS_PER_SESSION


# =============================================================================
# 시스템 프롬프트 빌더
# =============================================================================

def _build_system_prompt(category: str = None) -> str:
    """시간 컨텍스트 + 카테고리를 포함한 시스템 프롬프트 생성"""
    time_context = get_time_context()

    category_hint = ""
    if category and category != "random":
        cat_info = CATEGORIES.get(category, {})
        category_hint = f"""
⚠️ **카테고리 제한**: {cat_info.get('label', category)} 분야의 아이디어만 제안하세요.
- 설명: {cat_info.get('description', '')}
"""

    return f"""{time_context}

당신은 실리콘밸리의 유니콘 스타트업 액셀러레이터입니다.
사람들이 "와우"할 만한 혁신적인 아이디어를 제안해야 합니다.
{category_hint}
조건:
1. 흔한 아이디어(예: 단순 쇼핑몰, 투두리스트)는 절대 제외하세요.
2. 구체적이고 실현 가능한 아이디어를 제안하세요.
3. '제목'은 이모지를 포함해 직관적이고 매력적으로 지으세요.
4. '설명'은 이 에이전트에게 그대로 기획 요청을 보낼 수 있도록 구체적인 프롬프트 형태여야 합니다.
5. 현재 연도와 분기에 맞는 현실적인 아이디어를 제안하세요.
"""


# =============================================================================
# 비IT 아이디어 검증
# =============================================================================

def _has_non_it_idea(ideas: list) -> bool:
    """아이디어 목록에 비IT 아이디어가 있는지 확인"""
    non_it_keywords = [
        "창업", "제조", "프랜차이즈", "카페", "공방", "오프라인", "공장",
        "정육점", "베이커리", "미용실", "학원", "배달", "렌탈", "공간",
        "서점", "캠핑", "웨딩", "비누", "숙성", "농장", "도시락"
    ]

    for _, desc in ideas:
        for keyword in non_it_keywords:
            if keyword in desc:
                return True
    return False


# =============================================================================
# 메인 함수: 아이디어 생성 (통합)
# =============================================================================

def generate_ideas(
    category: str = "random",
    count: int = 3,
    use_llm: bool = True,
    session_call_count: int = None
) -> Tuple[List[Tuple[str, str]], bool]:
    """
    아이디어를 생성합니다 (LLM 또는 Static Pool).

    Args:
        category: 카테고리 키 (random, it_tech, finance 등)
        count: 생성할 아이디어 수
        use_llm: LLM 사용 여부 (False면 Static Pool만 사용)
        session_call_count: 외부에서 전달받은 세션 호출 횟수 (Streamlit 연동용)

    Returns:
        Tuple[List[Tuple[str, str]], bool]:
            - 아이디어 리스트 [(제목, 프롬프트), ...]
            - LLM 사용 여부 (True: LLM 생성, False: Static Pool)
    """
    # 세션 호출 횟수 체크 (외부에서 전달받은 경우 사용)
    current_count = session_call_count if session_call_count is not None else _llm_call_count

    # LLM 호출 제한 체크
    if current_count >= MAX_LLM_CALLS_PER_SESSION:
        use_llm = False
        print(f"[INFO] LLM 호출 제한 도달 ({current_count}/{MAX_LLM_CALLS_PER_SESSION}). Static Pool 사용.")

    # Static Pool 사용
    if not use_llm:
        ideas = get_examples_by_category(category, count)
        return ideas, False

    # LLM 사용
    try:
        ideas = _generate_with_llm(category, count)
        increment_llm_call_count()
        return ideas, True
    except Exception as e:
        print(f"[WARN] LLM 아이디어 생성 실패 (Fallback): {e}")
        ideas = get_examples_by_category(category, count)
        return ideas, False


def _generate_with_llm(category: str, count: int) -> List[Tuple[str, str]]:
    """LLM을 사용하여 아이디어 생성"""
    llm = get_llm(temperature=0.9).with_structured_output(CreativeIdeaList)

    system_prompt = _build_system_prompt(category)

    # 카테고리별 힌트
    category_hint = ""
    if category and category != "random":
        cat_info = CATEGORIES.get(category, {})
        category_hint = f"**{cat_info.get('label', category)}** 분야에서 "

    user_msg = f"""{category_hint}기발하고 혁신적인 스타트업 아이디어 {count}개를 제안해줘.
한국어로 작성해."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_msg}
    ]

    result = llm.invoke(messages)

    if not result or not result.ideas:
        raise ValueError("Empty result from LLM")

    ideas = [(idea.title, idea.description) for idea in result.ideas]

    # 랜덤 카테고리인 경우 비IT 강제 포함
    if category == "random" and not _has_non_it_idea(ideas) and len(ideas) > 0:
        print("[INFO] 비IT 아이디어 누락 → 강제 추가")
        ideas.pop()
        ideas.append(random.choice(NON_IT_POOL))

    # 부족하면 Static에서 채움
    if len(ideas) < count:
        fallback = get_examples_by_category(category, count - len(ideas))
        ideas.extend(fallback)

    return ideas[:count]


# =============================================================================
# 짧은 입력 증강 (Analyzer 통합용)
# =============================================================================

def expand_short_input(
    short_input: str,
    category: str = None,
    session_call_count: int = None
) -> Optional[Dict]:
    """
    짧은 입력을 구체적인 기획 컨셉으로 증강합니다.

    이 함수는 Analyzer에서 짧은 입력 감지 시 호출되어,
    브레인스토밍 스타일의 구체적인 제안을 생성합니다.

    Args:
        short_input: 사용자의 짧은 입력 (예: "배달 앱", "카페 창업")
        category: 카테고리 힌트 (없으면 자동 감지)
        session_call_count: 세션 LLM 호출 횟수

    Returns:
        Optional[Dict]: 증강된 기획 컨셉 또는 None
            {
                "topic": "구체화된 서비스명",
                "purpose": "핵심 가치",
                "key_features": ["기능1", "기능2", ...],
                "target_users": "타겟 사용자",
                "expanded_prompt": "구체화된 프롬프트"
            }
    """
    # LLM 호출 제한 체크
    current_count = session_call_count if session_call_count is not None else _llm_call_count
    if current_count >= MAX_LLM_CALLS_PER_SESSION:
        print("[INFO] LLM 제한으로 입력 증강 스킵")
        return None

    try:
        from utils.schemas import AnalysisResult

        llm = get_llm(temperature=0.8).with_structured_output(AnalysisResult)

        time_context = get_time_context()

        system_prompt = f"""{time_context}

당신은 10년 경력의 시니어 기획 컨설턴트입니다.
사용자가 짧고 모호한 아이디어를 제시하면, 이를 구체적이고 매력적인 기획 컨셉으로 확장해야 합니다.

규칙:
1. 평범한 아이디어를 혁신적으로 재해석하세요.
2. 구체적인 차별화 포인트를 제시하세요.
3. 최신 트렌드(AI, 구독 경제, 지속가능성 등)를 접목하세요.
4. 타겟 사용자를 명확히 정의하세요.
5. 최소 5개의 핵심 기능을 제안하세요.

출력 예시:
- "배달 앱" → "EcoEats - 탄소중립 AI 배달 플랫폼: 친환경 포장재 사용 식당만 큐레이션하고, 배달 경로 최적화로 탄소 배출을 줄이는 ESG 배달 앱"
"""

        user_msg = f"""다음 짧은 아이디어를 구체적인 기획 컨셉으로 확장해주세요:

"{short_input}"

JSON 형식으로 응답하세요."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg}
        ]

        result = llm.invoke(messages)
        increment_llm_call_count()

        if hasattr(result, "model_dump"):
            return result.model_dump()
        return result

    except Exception as e:
        print(f"[WARN] 입력 증강 실패: {e}")
        return None


# =============================================================================
# 레거시 호환성
# =============================================================================

def generate_creative_ideas(count: int = 3) -> List[Tuple[str, str]]:
    """
    레거시 함수: LLM을 사용하여 창의적인 아이디어를 생성합니다.

    새 코드에서는 generate_ideas()를 사용하세요.
    """
    ideas, _ = generate_ideas(category="random", count=count, use_llm=True)
    return ideas


# 레거시 상수 (호환성)
SYSTEM_PROMPT = _build_system_prompt()
