"""
UI Validation Module

사용자 친화적인 입력 검증 및 에러 메시지를 제공합니다.

기능:
    - 입력 유효성 검증 (빈 값, 형식, 길이 등)
    - 친화적인 에러 메시지 포맷팅
    - 재시도 안내 및 도움말 제공
    - 다국어 지원 (한국어)

사용 예시:
    from ui.validation import validate_input, show_validation_error

    is_valid, error = validate_input(user_input, min_length=5)
    if not is_valid:
        show_validation_error(error)
"""

import streamlit as st
from typing import Optional, Tuple, List, Dict, Any
from enum import Enum


# =============================================================================
# Error Types and Messages
# =============================================================================

class ValidationErrorType(str, Enum):
    """검증 에러 유형"""
    EMPTY_INPUT = "empty_input"
    TOO_SHORT = "too_short"
    TOO_LONG = "too_long"
    INVALID_FORMAT = "invalid_format"
    MISSING_FIELD = "missing_field"
    NETWORK_ERROR = "network_error"
    LLM_ERROR = "llm_error"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"


# 사용자 친화적 에러 메시지 템플릿
ERROR_MESSAGES = {
    ValidationErrorType.EMPTY_INPUT: {
        "title": "입력이 비어있어요",
        "message": "기획서를 생성하려면 아이디어나 요구사항을 입력해주세요.",
        "hint": "💡 예: '반려동물 건강 관리 앱을 만들고 싶어요'",
        "icon": "📝"
    },
    ValidationErrorType.TOO_SHORT: {
        "title": "입력이 너무 짧아요",
        "message": "좀 더 구체적으로 설명해주시면 더 좋은 기획서를 만들 수 있어요.",
        "hint": "💡 목표, 대상 사용자, 주요 기능 등을 추가해보세요",
        "icon": "✏️"
    },
    ValidationErrorType.TOO_LONG: {
        "title": "입력이 너무 길어요",
        "message": "핵심 내용을 간추려서 다시 입력해주세요.",
        "hint": "💡 핵심 기능 3-5가지에 집중해보세요",
        "icon": "📏"
    },
    ValidationErrorType.INVALID_FORMAT: {
        "title": "형식이 올바르지 않아요",
        "message": "입력 형식을 확인해주세요.",
        "hint": "💡 도움이 필요하시면 예시를 참고해주세요",
        "icon": "⚠️"
    },
    ValidationErrorType.MISSING_FIELD: {
        "title": "필수 항목이 비어있어요",
        "message": "모든 필수 항목을 입력해주세요.",
        "hint": "💡 * 표시가 있는 항목은 필수입니다",
        "icon": "📋"
    },
    ValidationErrorType.NETWORK_ERROR: {
        "title": "네트워크 연결에 문제가 있어요",
        "message": "인터넷 연결을 확인하고 다시 시도해주세요.",
        "hint": "💡 잠시 후 다시 시도하거나, 페이지를 새로고침 해보세요",
        "icon": "🌐"
    },
    ValidationErrorType.LLM_ERROR: {
        "title": "AI 처리 중 문제가 발생했어요",
        "message": "잠시 후 다시 시도해주세요. 문제가 지속되면 관리자에게 문의해주세요.",
        "hint": "💡 입력을 조금 수정하거나 간략하게 줄여서 시도해보세요",
        "icon": "🤖"
    },
    ValidationErrorType.TIMEOUT: {
        "title": "응답 시간이 초과되었어요",
        "message": "서버가 바쁜 것 같아요. 잠시 후 다시 시도해주세요.",
        "hint": "💡 복잡한 요청은 시간이 더 걸릴 수 있어요",
        "icon": "⏰"
    },
    ValidationErrorType.UNKNOWN: {
        "title": "알 수 없는 오류가 발생했어요",
        "message": "예상치 못한 문제가 발생했어요. 다시 시도해주세요.",
        "hint": "💡 문제가 지속되면 새 대화를 시작해보세요",
        "icon": "❓"
    }
}


# =============================================================================
# Input Validation Functions
# =============================================================================

def validate_input(
    text: str,
    min_length: int = 1,
    max_length: int = 5000,
    required: bool = True
) -> Tuple[bool, Optional[ValidationErrorType], Optional[str]]:
    """
    사용자 입력 유효성 검증

    Args:
        text: 검증할 텍스트
        min_length: 최소 길이 (기본: 1)
        max_length: 최대 길이 (기본: 5000)
        required: 필수 여부 (기본: True)

    Returns:
        (is_valid, error_type, detail_message)
        - is_valid: 유효성 통과 여부
        - error_type: 에러 유형 (유효하면 None)
        - detail_message: 상세 메시지 (유효하면 None)
    """
    # 빈 입력 확인
    if not text or text.strip() == "":
        if required:
            return False, ValidationErrorType.EMPTY_INPUT, None
        return True, None, None

    text = text.strip()

    # 길이 확인
    if len(text) < min_length:
        return False, ValidationErrorType.TOO_SHORT, f"최소 {min_length}자 이상 입력해주세요 (현재: {len(text)}자)"

    if len(text) > max_length:
        return False, ValidationErrorType.TOO_LONG, f"최대 {max_length}자까지 입력 가능해요 (현재: {len(text)}자)"

    return True, None, None


def validate_form(
    form_data: Dict[str, Any],
    required_fields: List[str]
) -> Tuple[bool, List[str]]:
    """
    폼 데이터 유효성 검증

    Args:
        form_data: 폼 데이터 딕셔너리
        required_fields: 필수 필드 목록

    Returns:
        (is_valid, missing_fields)
    """
    missing = []
    for field in required_fields:
        value = form_data.get(field)
        if value is None or (isinstance(value, str) and value.strip() == ""):
            missing.append(field)

    return len(missing) == 0, missing


# =============================================================================
# Error Display Functions
# =============================================================================

def show_validation_error(
    error_type: ValidationErrorType,
    detail: Optional[str] = None,
    show_hint: bool = True
):
    """
    친화적인 에러 메시지 표시

    Args:
        error_type: 에러 유형
        detail: 추가 상세 메시지
        show_hint: 힌트 표시 여부
    """
    error_info = ERROR_MESSAGES.get(error_type, ERROR_MESSAGES[ValidationErrorType.UNKNOWN])

    with st.container():
        # 메인 에러 메시지
        st.error(f"{error_info['icon']} **{error_info['title']}**")

        # 설명 메시지
        st.markdown(f"<p style='color: #666; margin-top: -10px;'>{error_info['message']}</p>", unsafe_allow_html=True)

        # 상세 메시지 (있는 경우)
        if detail:
            st.caption(f"📌 {detail}")

        # 힌트 (선택적)
        if show_hint and error_info.get("hint"):
            st.info(error_info["hint"])


def show_input_warning(message: str, suggestion: Optional[str] = None):
    """
    입력 관련 경고 표시 (에러보다 가벼운 안내)

    Args:
        message: 경고 메시지
        suggestion: 제안 사항
    """
    warning_html = f"""
    <div style='
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 10px 15px;
        border-radius: 4px;
        margin: 10px 0;
    '>
        <strong>💡 알려드려요</strong><br>
        <span style='color: #856404;'>{message}</span>
        {f"<br><small style='color: #666;'>→ {suggestion}</small>" if suggestion else ""}
    </div>
    """
    st.markdown(warning_html, unsafe_allow_html=True)


def show_success_feedback(message: str, detail: Optional[str] = None):
    """
    성공 피드백 표시

    Args:
        message: 성공 메시지
        detail: 추가 상세 정보
    """
    st.success(f"✅ {message}")
    if detail:
        st.caption(detail)


def show_retry_prompt(
    error_type: ValidationErrorType,
    retry_count: int = 0,
    max_retries: int = 3
):
    """
    재시도 안내 표시

    Args:
        error_type: 발생한 에러 유형
        retry_count: 현재 재시도 횟수
        max_retries: 최대 재시도 횟수
    """
    remaining = max_retries - retry_count

    if remaining > 0:
        st.warning(f"🔄 다시 시도해주세요 (남은 시도: {remaining}회)")
    else:
        st.error("❌ 최대 시도 횟수를 초과했어요. 새 대화를 시작해주세요.")


# =============================================================================
# Error Type Detection (from Exception)
# =============================================================================

def detect_error_type(exception: Exception) -> ValidationErrorType:
    """
    예외에서 에러 유형 감지

    Args:
        exception: 발생한 예외

    Returns:
        ValidationErrorType
    """
    error_msg = str(exception).lower()
    error_type_name = type(exception).__name__

    # 네트워크 관련
    network_keywords = ["connection", "network", "http", "socket", "dns", "ssl", "timeout"]
    if any(kw in error_msg for kw in network_keywords):
        if "timeout" in error_msg:
            return ValidationErrorType.TIMEOUT
        return ValidationErrorType.NETWORK_ERROR

    # LLM 관련
    llm_keywords = ["openai", "azure", "api", "token", "rate limit", "model"]
    if any(kw in error_msg for kw in llm_keywords):
        return ValidationErrorType.LLM_ERROR

    # 검증 관련
    validation_keywords = ["validation", "invalid", "required", "missing"]
    if any(kw in error_msg for kw in validation_keywords):
        return ValidationErrorType.INVALID_FORMAT

    return ValidationErrorType.UNKNOWN


def handle_exception_friendly(exception: Exception, context: str = ""):
    """
    예외를 친화적인 UI로 표시

    Args:
        exception: 발생한 예외
        context: 에러 발생 컨텍스트 (예: "기획서 생성 중")
    """
    error_type = detect_error_type(exception)

    # 개발 모드에서만 상세 에러 표시
    import os
    is_dev = os.getenv("STREAMLIT_ENV", "").lower() == "development"

    show_validation_error(
        error_type,
        detail=f"{context}: {str(exception)[:100]}..." if context else None
    )

    if is_dev:
        with st.expander("🔧 개발자 정보 (Debug)", expanded=False):
            st.code(str(exception))
