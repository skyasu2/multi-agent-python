"""
PlanCraft Agent - 컨텍스트 빌더 유틸리티

에이전트 프롬프트에 주입할 컨텍스트를 일관되게 구성합니다.
각 에이전트에서 반복되던 컨텍스트 조합 로직을 중앙화합니다.

Usage:
    from utils.context_builder import build_context, ContextBuilder

    # 간단한 사용
    context = build_context(state)

    # 빌더 패턴 사용
    context = (ContextBuilder(state)
        .add_rag()
        .add_web()
        .add_file(max_length=5000)
        .add_analysis()
        .build())
"""

from typing import Optional, Dict, Any, List
import json


def build_context(
    state: Dict[str, Any],
    include_rag: bool = True,
    include_web: bool = True,
    include_file: bool = True,
    include_analysis: bool = False,
    include_structure: bool = False,
    include_review: bool = False,
    max_file_length: int = 10000,
) -> str:
    """
    상태에서 컨텍스트 문자열을 구성합니다.

    Args:
        state: PlanCraftState 딕셔너리
        include_rag: RAG 컨텍스트 포함 여부
        include_web: 웹 검색 컨텍스트 포함 여부
        include_file: 파일 컨텍스트 포함 여부
        include_analysis: 분석 결과 포함 여부
        include_structure: 구조 결과 포함 여부
        include_review: 리뷰 결과 포함 여부
        max_file_length: 파일 내용 최대 길이

    Returns:
        조합된 컨텍스트 문자열 (없으면 빈 문자열)
    """
    builder = ContextBuilder(state)

    if include_rag:
        builder.add_rag()
    if include_web:
        builder.add_web()
    if include_file:
        builder.add_file(max_length=max_file_length)
    if include_analysis:
        builder.add_analysis()
    if include_structure:
        builder.add_structure()
    if include_review:
        builder.add_review()

    return builder.build()


class ContextBuilder:
    """
    컨텍스트 빌더 (Fluent API)

    체이닝 방식으로 필요한 컨텍스트만 선택적으로 추가할 수 있습니다.

    Example:
        context = (ContextBuilder(state)
            .add_rag()
            .add_web()
            .add_custom("추가 정보", "커스텀 내용")
            .build())
    """

    def __init__(self, state: Dict[str, Any]):
        self.state = state
        self.parts: List[str] = []

    def add_rag(self, label: str = "참고 자료") -> "ContextBuilder":
        """RAG 컨텍스트 추가"""
        rag_context = self.state.get("rag_context", "")
        if rag_context and rag_context.strip():
            self.parts.append(f"[{label}]\n{rag_context.strip()}")
        return self

    def add_web(self, label: str = "웹 검색 결과") -> "ContextBuilder":
        """웹 검색 컨텍스트 추가"""
        web_context = self.state.get("web_context", "")
        if web_context and web_context.strip():
            self.parts.append(f"[{label}]\n{web_context.strip()}")
        return self

    def add_file(self, label: str = "첨부 파일", max_length: int = 10000) -> "ContextBuilder":
        """파일 컨텍스트 추가 (길이 제한 포함)"""
        file_content = self.state.get("file_content", "")
        if file_content and file_content.strip():
            content = file_content.strip()
            if len(content) > max_length:
                content = content[:max_length] + f"\n... (총 {len(file_content):,}자 중 {max_length:,}자만 표시)"
            self.parts.append(f"[{label}]\n{content}")
        return self

    def add_analysis(self, label: str = "분석 결과") -> "ContextBuilder":
        """분석 결과 추가"""
        analysis = self.state.get("analysis")
        if analysis:
            analysis_str = self._to_json_str(analysis)
            self.parts.append(f"[{label}]\n{analysis_str}")
        return self

    def add_structure(self, label: str = "기획서 구조") -> "ContextBuilder":
        """구조 결과 추가"""
        structure = self.state.get("structure")
        if structure:
            structure_str = self._to_json_str(structure)
            self.parts.append(f"[{label}]\n{structure_str}")
        return self

    def add_review(self, label: str = "검토 의견") -> "ContextBuilder":
        """리뷰 결과 추가"""
        review = self.state.get("review")
        if review:
            review_str = self._to_json_str(review)
            self.parts.append(f"[{label}]\n{review_str}")
        return self

    def add_draft(self, label: str = "초안") -> "ContextBuilder":
        """초안 추가"""
        draft = self.state.get("draft")
        if draft:
            draft_str = self._to_json_str(draft)
            self.parts.append(f"[{label}]\n{draft_str}")
        return self

    def add_custom(self, label: str, content: str) -> "ContextBuilder":
        """커스텀 컨텍스트 추가"""
        if content and content.strip():
            self.parts.append(f"[{label}]\n{content.strip()}")
        return self

    def add_previous_plan(self, label: str = "이전 기획서") -> "ContextBuilder":
        """이전 기획서 추가"""
        previous_plan = self.state.get("previous_plan", "")
        if previous_plan and previous_plan.strip():
            self.parts.append(f"[{label}]\n{previous_plan.strip()}")
        return self

    def build(self, separator: str = "\n\n") -> str:
        """
        최종 컨텍스트 문자열 생성

        Args:
            separator: 각 파트 사이의 구분자

        Returns:
            조합된 컨텍스트 문자열
        """
        return separator.join(self.parts) if self.parts else ""

    def _to_json_str(self, obj: Any) -> str:
        """객체를 JSON 문자열로 변환 (Pydantic 모델 지원)"""
        if hasattr(obj, "model_dump"):
            # Pydantic v2
            return json.dumps(obj.model_dump(), ensure_ascii=False, indent=2)
        elif hasattr(obj, "dict"):
            # Pydantic v1
            return json.dumps(obj.dict(), ensure_ascii=False, indent=2)
        elif isinstance(obj, dict):
            return json.dumps(obj, ensure_ascii=False, indent=2)
        else:
            return str(obj)


def get_user_input_context(state: Dict[str, Any]) -> str:
    """
    사용자 입력 관련 컨텍스트만 추출

    Args:
        state: PlanCraftState 딕셔너리

    Returns:
        사용자 입력 + 파일 컨텍스트
    """
    parts = []

    user_input = state.get("user_input", "")
    if user_input:
        parts.append(f"[사용자 요청]\n{user_input}")

    file_content = state.get("file_content", "")
    if file_content:
        truncated = file_content[:5000] + "..." if len(file_content) > 5000 else file_content
        parts.append(f"[첨부 파일]\n{truncated}")

    return "\n\n".join(parts)


def get_generation_context(state: Dict[str, Any]) -> str:
    """
    생성 단계에 필요한 컨텍스트 (분석 + 구조)

    Writer, Refiner에서 사용
    """
    return (ContextBuilder(state)
        .add_analysis()
        .add_structure()
        .add_review()
        .build())


def get_full_context(state: Dict[str, Any], max_file_length: int = 10000) -> str:
    """
    전체 컨텍스트 (모든 소스 포함)

    Analyzer에서 사용
    """
    return (ContextBuilder(state)
        .add_rag()
        .add_web()
        .add_file(max_length=max_file_length)
        .add_previous_plan()
        .build())
