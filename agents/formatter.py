"""
PlanCraft Agent - Formatter Agent

최종 기획서를 사용자 친화적인 채팅 요약으로 변환하는 Agent입니다.
전체 기획서는 그대로 유지하면서, 핵심만 요약한 채팅 메시지를 생성합니다.

주요 기능:
    - 기획서 핵심 포인트 추출
    - 채팅 친화적 요약 생성
    - 검토 결과 하이라이트

입력:
    - final_output: 완성된 기획서 (마크다운)
    - analysis: 분석 결과
    - review: 검토 결과
    - structure: 구조 정보

출력:
    - chat_summary: 채팅용 요약 메시지
    - final_output: 기존 기획서 (유지)

Best Practice 적용:
    - PlanCraftState 타입 어노테이션: 명시적 입출력 타입
    - NOTE: Formatter는 자유형식 요약을 출력하므로 Structured Output 미적용
"""

from utils.llm import get_llm
from graph.state import PlanCraftState
from prompts.formatter_prompt import FORMATTER_SYSTEM_PROMPT, FORMATTER_USER_PROMPT


class FormatterAgent:
    """
    최종 출력을 사용자 친화적으로 포맷팅하는 Agent

    복잡한 기획서를 채팅에 적합한 요약 형태로 변환합니다.

    NOTE: Formatter는 자유형식 요약을 출력하므로 with_structured_output() 미적용

    Attributes:
        llm: AzureChatOpenAI 인스턴스

    Example:
        >>> agent = FormatterAgent()
        >>> state = {"final_output": "...", "analysis": {...}, "review": {...}}
        >>> result = agent.run(state)
        >>> print(result["chat_summary"])
    """

    def __init__(self, model_type: str = "gpt-4o-mini"):
        """
        Formatter Agent를 초기화합니다.

        Args:
            model_type: 사용할 LLM 모델 (요약은 빠른 모델로 충분)
        """
        self.llm = get_llm(model_type=model_type, temperature=0.5)

    def run(self, state: PlanCraftState) -> PlanCraftState:
        """
        기획서를 채팅 요약으로 변환합니다.

        Args:
            state: 현재 워크플로우 상태 (PlanCraftState)
                - final_output: 완성된 기획서
                - analysis: 분석 결과
                - review: 검토 결과
                - structure: 구조 정보

        Returns:
            PlanCraftState: chat_summary가 추가된 상태
        """
        # =====================================================================
        # 1. 입력 데이터 추출 (객체 접근)
        # =====================================================================
        analysis = state.analysis
        review = state.review
        structure = state.structure
        
        # Pydantic 객체 Optional 처리
        # analysis, review, structure가 None일 수 있으므로 safe access
        
        # 제목 추출
        # structure, analysis가 Pydantic 객체이므로 .title, .topic 접근
        title = "기획서"
        if structure and structure.title:
            title = structure.title
        elif analysis and analysis.topic:
            title = analysis.topic

        # 분석 정보
        topic = analysis.topic if analysis else ""
        purpose = analysis.purpose if analysis else ""
        target_users = analysis.target_users if analysis else ""
        key_features = analysis.key_features if analysis else []

        # 검토 정보 (내부용 - 점수는 사용자에게 노출하지 않음)
        strengths = review.strengths if review else []

        # =====================================================================
        # 2. 프롬프트 구성 및 LLM 호출
        # =====================================================================
        messages = [
            {"role": "system", "content": FORMATTER_SYSTEM_PROMPT},
            {"role": "user", "content": FORMATTER_USER_PROMPT.format(
                title=title,
                topic=topic,
                purpose=purpose,
                target_users=target_users,
                key_features=", ".join(key_features) if key_features else "정보 없음",
                strengths=", ".join(strengths[:2]) if strengths else "우수한 구조와 명확한 목표"
            )}
        ]

        try:
            response = self.llm.invoke(messages)
            chat_summary = response.content
        except Exception as e:
            # 실패 시 기본 요약 생성
            chat_summary = self._generate_fallback_summary(
                title, topic, purpose, key_features
            )
            state.error = f"포맷팅 오류: {str(e)}"

        # =====================================================================
        # 3. 웹 검색 출처 추가 (참고 자료 섹션)
        # =====================================================================
        final_output = state.final_output or ""
        web_urls = state.web_urls or []
        web_context = state.web_context
        
        # 웹 검색 결과가 있으면 출처 섹션 추가
        if web_urls or web_context:
            references_section = self._generate_references_section(web_urls, web_context)
            if references_section and references_section not in final_output:
                final_output = final_output + "\n\n" + references_section

        # =====================================================================
        # 4. 상태 업데이트 (Pydantic 모델 복사)
        # =====================================================================
        new_state = state.model_copy(update={
            "chat_summary": chat_summary,
            "final_output": final_output,
            "current_step": "format"
        })

        return new_state
    
    def _generate_references_section(self, web_urls: list, web_context: str = None) -> str:
        """
        웹 검색 출처 섹션을 생성합니다.
        
        Args:
            web_urls: 참조한 URL 목록
            web_context: 웹 검색 결과 컨텍스트
            
        Returns:
            str: 참고 자료 섹션 마크다운
        """
        if not web_urls and not web_context:
            return ""
        
        lines = []
        lines.append("---")
        lines.append("")
        lines.append("## 📚 참고 자료")
        lines.append("")
        lines.append("> 본 기획서는 다음 자료를 참고하여 작성되었습니다.")
        lines.append("")
        
        # URL 목록이 있으면 출력
        if web_urls:
            for i, url in enumerate(web_urls[:5], 1):  # 최대 5개
                lines.append(f"- [{url}]({url})")
        
        # URL은 없지만 웹 검색 결과가 있으면 표시
        if not web_urls and web_context:
            # 웹 검색 출처 표시 (Tavily MCP)
            lines.append("- 웹 검색 결과 (Tavily AI Search)")
        
        lines.append("")
        
        return "\n".join(lines)

    def _generate_fallback_summary(
        self,
        title: str,
        topic: str,
        purpose: str,
        key_features: list
    ) -> str:
        """
        LLM 실패 시 기본 요약을 생성합니다.

        Args:
            title: 기획서 제목
            topic: 주제
            purpose: 목적
            key_features: 핵심 기능 목록

        Returns:
            str: 기본 요약 메시지
        """
        features_text = ""
        for i, feature in enumerate(key_features[:3], 1):
            features_text += f"{i}. **{feature}**\n"

        return f"""## {title} 기획서 완성!

### 핵심 콘셉트
> {purpose}

### 주요 기능
{features_text}
---
상세 기획서는 아래에서 확인하세요!
"""


def run(state: PlanCraftState) -> PlanCraftState:
    """
    LangGraph 노드용 함수

    LangGraph에서 노드로 등록할 때 사용하는 래퍼 함수입니다.

    Args:
        state: 워크플로우 상태 (PlanCraftState)

    Returns:
        PlanCraftState: 업데이트된 상태
    """
    agent = FormatterAgent()
    return agent.run(state)
