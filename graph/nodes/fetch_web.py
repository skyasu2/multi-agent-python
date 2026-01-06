"""
Fetch Web Context Node
"""
from graph.state import PlanCraftState, update_state
from graph.nodes.common import update_step_history
from tools.web_search_executor import execute_web_search
from utils.tracing import trace_node
from utils.error_handler import handle_node_error

@trace_node("context", tags=["web", "search", "tavily"])
@handle_node_error
def fetch_web_context(state: PlanCraftState) -> PlanCraftState:
    """
    조건부 웹 정보 수집 노드

    Side-Effect: 외부 웹 API 호출 (Tavily Search)
    - 실패 시 재시도 안전함 (조회 전용, 멱등성 보장)
    - 중복 호출 시 동일 결과 반환 (검색 결과 캐싱 없음)

    LangSmith: run_name="📚 컨텍스트 수집", tags=["rag", "retrieval", "web", "search", "tavily"]
    """
    import time
    start_time = time.time()
    
    user_input = state.get("user_input", "")
    rag_context = state.get("rag_context")
    
    # 1. 웹 검색 실행 (Executor 위임)
    result = execute_web_search(user_input, rag_context)

    # [DEBUG] 웹 검색 결과 상세 로그
    print(f"[FETCH_WEB DEBUG] urls={len(result.get('urls', []))}, sources={len(result.get('sources', []))}, context_len={len(result.get('context') or '')}, error={result.get('error')}")

    # 2. 상태 업데이트
    existing_context = state.get("web_context")
    existing_urls = state.get("web_urls") or []
    existing_sources = state.get("web_sources") or []

    new_context_str = result["context"]
    new_urls = result["urls"]
    new_sources = result["sources"]
    error = result["error"]

    final_context = existing_context
    if new_context_str:
        final_context = f"{final_context}\n\n{new_context_str}" if final_context else new_context_str

    final_urls = list(dict.fromkeys(existing_urls + new_urls))

    # web_sources 병합 (중복 URL 제거)
    final_sources = existing_sources.copy()
    for src in new_sources:
        if not any(s.get("url") == src.get("url") for s in final_sources):
            final_sources.append(src)

    if error:
        new_state = update_state(
            state,
            web_context=None,
            web_urls=[],
            error=f"웹 조회 오류: {error}"
        )
    else:
        new_state = update_state(
            state,
            web_context=final_context,
            web_urls=final_urls,
            web_sources=final_sources,
            current_step="fetch_web"
        )

    status = "FAILED" if new_state.get("error") else "SUCCESS"
    url_count = len(new_state.get("web_urls") or [])
    summary = f"웹 정보 수집: {url_count}개 URL 참조"
    
    return update_step_history(new_state, "fetch_web", status, summary, new_state.get("error"), start_time=start_time)
