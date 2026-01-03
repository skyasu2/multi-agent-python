"""
PlanCraft Agent - Writer Helper Functions

Writer Agent의 비즈니스 로직을 보조하는 헬퍼 함수 모음입니다.
- 컨텍스트 구성
- 웹 검색 실행
- 전문 에이전트 연동
- 시각화 지침 생성 및 피드백
- 초안 검증
"""

from graph.state import PlanCraftState, update_state, ensure_dict
from utils.file_logger import get_file_logger
from utils.settings import settings
from prompts.writer_prompt import WRITER_SYSTEM_PROMPT, WRITER_USER_PROMPT
from prompts.business_plan_prompt import BUSINESS_PLAN_SYSTEM_PROMPT, BUSINESS_PLAN_USER_PROMPT

def get_prompts_by_doc_type(state: PlanCraftState) -> tuple:
    """
    doc_type에 따라 적절한 프롬프트 반환

    Args:
        state: 현재 워크플로우 상태

    Returns:
        Tuple[str, str]: (system_prompt, user_prompt_template)
    """
    logger = get_file_logger()
    analysis = state.get("analysis")
    analysis_dict = ensure_dict(analysis)
    doc_type = analysis_dict.get("doc_type", "web_app_plan")

    if doc_type == "business_plan":
        logger.info("[Writer] 비IT 사업 기획서 모드로 작성합니다.")
        return BUSINESS_PLAN_SYSTEM_PROMPT, BUSINESS_PLAN_USER_PROMPT
    else:
        logger.info("[Writer] IT/Tech 기획서 모드로 작성합니다.")
        return WRITER_SYSTEM_PROMPT, WRITER_USER_PROMPT


def build_review_context(state: PlanCraftState, refine_count: int) -> str:
    """
    Reviewer 피드백을 컨텍스트 문자열로 변환

    Args:
        state: 현재 상태
        refine_count: 개선 횟수

    Returns:
        str: 리뷰 피드백 메시지 (없으면 빈 문자열)
    """
    if refine_count == 0:
        return ""

    review_data = state.get("review")
    if not review_data:
        return ""

    review_dict = ensure_dict(review_data)
    verdict = review_dict.get("verdict", "")
    feedback_summary = review_dict.get("feedback_summary", "")
    critical_issues = review_dict.get("critical_issues", [])
    action_items = review_dict.get("action_items", [])

    return f"""
=====================================================================
🚨 [REVISION REQUIRED] 이전 버전에 대한 심사 피드백 (반드시 반영할 것) 🚨
판정: {verdict}
지적 사항: {feedback_summary}
치명적 문제: {', '.join(critical_issues) if critical_issues else '없음'}
Action Items (실행 지침):
{chr(10).join([f'- {item}' for item in action_items])}
=====================================================================
"""


def build_refinement_context(refine_count: int, min_sections: int) -> str:
    """
    개선 모드용 컨텍스트 생성

    Args:
        refine_count: 현재 개선 횟수
        min_sections: 최소 섹션 수

    Returns:
        str: 개선 모드 지침 메시지
    """
    if refine_count == 0:
        return ""

    return f"""
=====================================================================
🔄 [REFINEMENT MODE] 개선 라운드 {refine_count} - 완전히 새로 작성하세요!
=====================================================================

⚠️ 이번은 {refine_count}번째 개선 시도입니다.
⚠️ 이전 버전의 피드백을 반영하여 **처음부터 완전히 새로 작성**하세요.
⚠️ 이전 버전을 참조하지 마세요. 아래 structure를 따라 **모든 {min_sections}개 섹션**을 작성하세요!

🎯 필수 요구사항:
1. sections 배열에 **정확히 {min_sections}개 이상**의 섹션 포함
2. 각 섹션은 **최소 300자 이상** 상세하게 작성
3. structure에 정의된 **모든 섹션**을 빠짐없이 작성
4. 부분 출력 절대 금지 - 완전한 기획서 출력 필수

=====================================================================
"""


def execute_web_search(user_input: str, rag_context: str, web_context: str, logger) -> str:
    """
    실시간 웹 검색 수행

    Args:
        user_input: 사용자 입력
        rag_context: RAG 컨텍스트
        web_context: 기존 웹 컨텍스트
        logger: 로거 인스턴스

    Returns:
        str: 업데이트된 웹 컨텍스트
    """
    try:
        from tools.web_search import should_search_web
        from tools.search_client import get_search_client

        search_decision = should_search_web(user_input, rag_context)

        if search_decision.get("should_search") and search_decision.get("search_query"):
            query = search_decision["search_query"]
            logger.info(f"[Writer] 실시간 웹 검색 수행: '{query}'")

            search_client = get_search_client()
            search_result = search_client.search(query)

            if "[Web Search Failed]" not in search_result:
                if not web_context:
                    web_context = ""
                web_context += f"\n\n[Writer Search Result]\nKeyword: {query}\n{search_result}"
                logger.info("[Writer] 웹 데이터가 컨텍스트에 추가되었습니다.")
            else:
                logger.warning(f"[Writer] 검색 실패 또는 스킵됨: {search_result}")

    except ImportError:
        logger.error("[Writer] 검색 모듈 로드 실패")
    except Exception as e:
        logger.error(f"[Writer] 웹 검색 중 오류 발생: {str(e)}")

    return web_context


def execute_specialist_agents(state: PlanCraftState, user_input: str,
                                web_context: str, refine_count: int, logger) -> tuple:
    """
    전문 에이전트(Supervisor) 실행

    Args:
        state: 현재 상태
        user_input: 사용자 입력
        web_context: 웹 컨텍스트
        refine_count: 개선 횟수
        logger: 로거 인스턴스

    Returns:
        Tuple[str, PlanCraftState]: (specialist_context, updated_state)
    """
    specialist_context = ""
    use_specialist_agents = state.get("use_specialist_agents", True)

    if use_specialist_agents and refine_count == 0:
        try:
            from agents.supervisor import PlanSupervisor

            logger.info("[Writer] 🤖 전문 에이전트 분석 시작 (Supervisor)...")

            analysis_dict = state.get("analysis", {})
            if hasattr(analysis_dict, "model_dump"):
                analysis_dict = analysis_dict.model_dump()
            elif not isinstance(analysis_dict, dict):
                analysis_dict = {}

            target_market = analysis_dict.get("target_market", "일반 시장")
            target_users = analysis_dict.get("target_user", "일반 사용자")
            tech_stack = analysis_dict.get("tech_stack", "React Native + Node.js + PostgreSQL")
            user_constraints = analysis_dict.get("user_constraints", [])

            web_search_list = []
            if web_context:
                for line in web_context.split("\n"):
                    if line.strip():
                        web_search_list.append({"title": "", "content": line[:500]})

            supervisor = PlanSupervisor()
            # [NEW] 프리셋의 deep_analysis_mode 확인
            deep_mode = False
            if hasattr(settings, "quality_preset") and hasattr(state, "get"):
                 # 상태에서 preset 이름을 확인하거나, 여기서는 간단히 preset 객체를 전달받았다고 가정하지 못하므로
                 # state나 global settings에서 추론해야 함. 
                 # 하지만 execute_specialist_agents 인그니처 변경 없이 내부 로직으로 처리.
                 # 호출부인 writer.py에서 preset을 넘겨주지 않으므로, 여기서 settings를 직접 참조하기엔 한계가 있음.
                 # 대신 web_app_plan 등 doc_type에 따라 판단하거나, refine_count 등으로 유추 가능.
                 # 가장 정확한건 execute_specialist_agents 인자에 preset을 추가하는 것임.
                 pass

            # 호출 시그니처 변경 없이 state에서 가져오거나 기본값 사용
            # * writer.py에서 execute_specialist_agents 호출 시 preset을 넘기도록 수정 필요.
            # * 일단 여기서는 supervisor.run에 임의의 키워드 인자로 전달하면 supervisor가 **kwargs로 받지 않으면 에러남.
            # * Supervisor.run 정의: run(self, service_overview, ... **kwargs) 형태여야 함.
            # * Supervisor 코드 확인 결과 run은 명시적 인자만 받음. run(self, service_overview: str, ...)
            
            # 전략 수정: Supervisor.run 메서드 시그니처를 먼저 유연하게 수정해야 함.
            # 하지만 Supervisor.run은 Pydantic validate를 사용하지 않고 직접 인자를 받음.
            
            # 여기서는 Supervisor.run에 deep_analysis_mode를 전달할 수 있도록
            # supervisor.py의 run 메서드 정의도 함께 수정해야 함.
            
            specialist_results = supervisor.run(
                service_overview=user_input,
                target_market=target_market,
                target_users=target_users,
                tech_stack=tech_stack,
                development_scope="MVP 3개월",
                web_search_results=web_search_list,
                user_constraints=user_constraints,
                deep_analysis_mode=state.get("deep_analysis_mode", False) # [NEW]
            )

            specialist_context = specialist_results.get("integrated_context", "")

            if specialist_context:
                logger.info("[Writer] ✓ 전문 에이전트 분석 완료!")

            state = update_state(state, specialist_analysis=specialist_results)

        except ImportError as e:
            logger.warning(f"[Writer] Supervisor 모듈 로드 실패: {e}")
        except Exception as e:
            logger.error(f"[Writer] 전문 에이전트 분석 중 오류: {e}")

    elif refine_count > 0:
        previous_specialist = state.get("specialist_analysis")
        if previous_specialist:
            from agents.supervisor import PlanSupervisor
            supervisor = PlanSupervisor()
            specialist_context = supervisor._integrate_results(previous_specialist)
            logger.info("[Writer] 이전 전문 에이전트 분석 결과 재사용")

    return specialist_context, state


def build_visual_instruction(preset, logger) -> str:
    """
    프리셋 기반 시각적 요소 지침 생성

    Args:
        preset: 생성 프리셋 설정
        logger: 로거 인스턴스

    Returns:
        str: 시각화 지침 문자열
    """
    if preset.include_diagrams == 0 and preset.include_charts == 0:
        return ""

    visual_instruction = """

=====================================================================
📊 **[필수] 시각적 요소 요구사항** - 반드시 포함할 것!
=====================================================================
"""

    if preset.include_diagrams > 0:
        # Mermaid 커스텀 옵션 적용
        diagram_types = getattr(preset, 'diagram_types', ['flowchart', 'sequenceDiagram'])
        direction = getattr(preset, 'diagram_direction', 'TB')
        theme = getattr(preset, 'diagram_theme', 'default')

        # 다이어그램 유형별 예시 생성
        type_examples = {
            "flowchart": f"""```mermaid
%%{{init: {{'theme': '{theme}'}}}}%%
flowchart {direction}
    A[사용자 접속] --> B[로그인/회원가입]
    B --> C{{서비스 선택}}
    C -->|기능A| D[기능A 처리]
    C -->|기능B| E[기능B 처리]
    D --> F[결과 표시]
    E --> F
```""",
            "sequenceDiagram": f"""```mermaid
%%{{init: {{'theme': '{theme}'}}}}%%
sequenceDiagram
    actor User as 사용자
    participant API as 백엔드
    participant DB as 데이터베이스
    User->>API: 요청 전송
    API->>DB: 데이터 조회
    DB-->>API: 결과 반환
    API-->>User: 응답 표시
```""",
            "classDiagram": f"""```mermaid
%%{{init: {{'theme': '{theme}'}}}}%%
classDiagram
    class User {{
        +String name
        +login()
    }}
    class Service {{
        +process()
    }}
    User --> Service
```""",
            "erDiagram": f"""```mermaid
%%{{init: {{'theme': '{theme}'}}}}%%
erDiagram
    USER ||--o{{ ORDER : places
    ORDER ||--|{{ ITEM : contains
```""",
        }

        # 선호 다이어그램 유형에서 첫 번째 예시 선택
        primary_type = diagram_types[0] if diagram_types else "flowchart"
        example_diagram = type_examples.get(primary_type, type_examples["flowchart"])

        visual_instruction += f"""
### Mermaid 다이어그램 ({preset.include_diagrams}개 이상 필수)
**권장 삽입 위치**: "시스템 아키텍처", "사용자 플로우", 또는 "서비스 구조" 섹션
**선호 다이어그램 유형**: {', '.join(diagram_types)}
**방향**: {direction} | **테마**: {theme}

아래 형식을 **정확히** 사용하세요 (백틱 3개 + mermaid):
{example_diagram}
"""

    if preset.include_charts > 0:
        visual_instruction += f"""
### ASCII 막대 그래프 ({preset.include_charts}개 이상 필수)
**권장 삽입 위치**: "수익 모델", "성장 전략", 또는 "마일스톤" 섹션

아래 형식을 사용하세요 (▓와 ░ 문자 사용):
| 구분 | 수치 | 그래프 |
|------|-----:|--------|
| 1분기 | 1,000명 | ▓▓░░░░░░░░ 20% |
| 2분기 | 2,500명 | ▓▓▓▓▓░░░░░ 50% |
| 3분기 | 4,000명 | ▓▓▓▓▓▓▓▓░░ 80% |
| 4분기 | 5,000명 | ▓▓▓▓▓▓▓▓▓▓ 100% |
"""

    visual_instruction += """
🚨 **경고**: 위 시각적 요소가 포함되지 않으면 검증 실패로 재작성 요청됩니다!
=====================================================================
"""
    logger.info(f"[Writer] 시각적 요소 요청: 다이어그램 {preset.include_diagrams}개, 차트 {preset.include_charts}개")

    return visual_instruction


def build_visual_feedback(validation_issues: list, preset) -> str:
    """
    시각적 요소 누락 시 구체적인 생성 예시가 포함된 피드백 생성

    Args:
        validation_issues: 검증 실패 항목 목록
        preset: 프리셋 설정

    Returns:
        str: 구체적인 시각적 요소 생성 지침
    """
    feedback_parts = []

    if "Mermaid 다이어그램 누락" in validation_issues:
        feedback_parts.append("""
⚠️ **Mermaid 다이어그램 필수**: 아래 형식으로 섹션에 포함하세요!
```mermaid
graph TB
    A[사용자 요청] --> B[서비스 처리]
    B --> C{결과 확인}
    C -->|성공| D[응답 반환]
    C -->|실패| E[에러 처리]
```
다이어그램을 '시스템 아키텍처' 또는 '사용자 플로우' 섹션에 추가하세요.
""")

    if "ASCII 차트 누락" in validation_issues:
        feedback_parts.append("""
⚠️ **ASCII 차트 필수**: 아래 형식으로 섹션에 포함하세요!
| 구분 | 수치 | 그래프 |
|------|-----:|--------|
| 1분기 | 1,000 | ▓▓░░░░░░░░ 20% |
| 2분기 | 2,500 | ▓▓▓▓▓░░░░░ 50% |
| 3분기 | 4,000 | ▓▓▓▓▓▓▓▓░░ 80% |
| 4분기 | 5,000 | ▓▓▓▓▓▓▓▓▓▓ 100% |
차트를 '수익 모델' 또는 '성장 전략' 섹션에 추가하세요.
""")

    return "\n".join(feedback_parts) if feedback_parts else ""


def validate_draft(draft_dict: dict, preset, specialist_context: str,
                    refine_count: int, logger) -> list:
    """
    생성된 초안 검증 (Self-Reflection)

    Args:
        draft_dict: 생성된 초안
        preset: 프리셋 설정
        specialist_context: 전문 에이전트 컨텍스트
        refine_count: 개선 횟수
        logger: 로거

    Returns:
        List[str]: 검증 실패 항목 목록 (빈 리스트면 통과)
    """
    sections = draft_dict.get("sections", [])
    section_count = len(sections)
    validation_issues = []

    MIN_SECTIONS = preset.min_sections
    MIN_CONTENT_LENGTH = 100

    # 검증 1: 섹션 개수
    if section_count < MIN_SECTIONS:
        validation_issues.append(f"섹션 개수 부족 ({section_count}/{MIN_SECTIONS}개)")

    # 검증 2: 섹션별 최소 길이
    short_sections = []
    for sec in sections:
        sec_name = sec.get("name", "") if isinstance(sec, dict) else getattr(sec, "name", "")
        sec_content = sec.get("content", "") if isinstance(sec, dict) else getattr(sec, "content", "")
        if len(sec_content) < MIN_CONTENT_LENGTH:
            short_sections.append(sec_name)

    if short_sections and len(short_sections) >= 3:
        validation_issues.append(f"부실 섹션 다수 ({', '.join(short_sections[:3])}...)")

    # 검증 3: Mermaid 다이어그램
    if preset.include_diagrams > 0:
        has_mermaid = any(
            "```mermaid" in (sec.get("content", "") if isinstance(sec, dict) else getattr(sec, "content", ""))
            for sec in sections
        )
        if not has_mermaid:
            validation_issues.append(f"Mermaid 다이어그램 누락")

    # 검증 4: ASCII 차트
    if preset.include_charts > 0:
        chart_indicators = ["▓", "░", "█", "■", "□", "●", "○"]
        has_chart = any(
            any(ind in (sec.get("content", "") if isinstance(sec, dict) else getattr(sec, "content", "")) for ind in chart_indicators)
            for sec in sections
        )
        if not has_chart:
            validation_issues.append(f"ASCII 차트 누락")

    # 검증 5: Specialist 분석 반영
    if specialist_context and refine_count == 0:
        all_content = " ".join(
            sec.get("content", "") if isinstance(sec, dict) else getattr(sec, "content", "")
            for sec in sections
        )
        specialist_checks = {
            "TAM/SAM/SOM": any(kw in all_content for kw in ["TAM", "SAM", "SOM", "시장 규모"]),
            "경쟁사 분석": any(kw in all_content for kw in ["경쟁사", "Competitor", "차별점"]),
            "BEP/손익분기": any(kw in all_content for kw in ["BEP", "손익분기", "손익 분기"]),
            "리스크": any(kw in all_content for kw in ["리스크", "Risk", "대응 방안", "위험"]),
        }
        missing = [k for k, v in specialist_checks.items() if not v]
        if missing:
            validation_issues.append(f"Specialist 데이터 누락: {', '.join(missing)}")

    return validation_issues
