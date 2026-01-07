"""
Interaction Module
"""
import streamlit as st
from ui.dynamic_form import render_pydantic_form

def render_error_state(current_state):
    """
    [개선] 에러 상태 UI 렌더링
    
    에러 메시지를 명확히 표시하고, 스마트한 복구 옵션을 제공합니다.
    """
    if not current_state:
        return

    error_msg = current_state.get("error_message") or current_state.get("error") or "알 수 없는 오류 발생"
    retry_count = current_state.get("retry_count", 0)

    st.error(f"### 🚫 오류 발생 (Retry: {retry_count})\n\n{error_msg}")
    
    with st.expander("상세 정보 보기", expanded=False):
        st.json(current_state)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 다시 시도", type="primary", use_container_width=True):
            # 상태 초기화 후 재시도 (재시도 카운트 증가)
            # 여기서는 단순히 세션 상태를 업데이트하고 rerun 합니다.
            # 실제 복구 로직은 App의 재실행 흐름에 맡깁니다.
            if st.session_state.current_state:
                st.session_state.current_state["retry_count"] = retry_count + 1
                st.session_state.current_state["error"] = None
                st.session_state.current_state["error_message"] = None
                st.session_state.current_state["step_status"] = "RUNNING"
            st.rerun()
            
    with col2:
        if st.button("✏️ 처음으로 돌아가기", use_container_width=True):
            st.session_state.chat_history = []
            st.session_state.current_state = None
            st.session_state.generated_plan = None
            st.rerun()


def render_human_interaction(current_state):
    """
    [통합] 휴먼 인터럽트 UI 렌더링
    
    1. 스키마 기반 폼 (input_schema가 있는 경우)
    2. 옵션 선택 버튼 (options가 있는 경우)
    3. 일반 텍스트 입력 (Fallback)
    """
    if not current_state:
        return

    # =========================================================================
    # [NEW] 에러 메시지 표시 개선 (HITL 재시도 시 명확한 피드백)
    # =========================================================================
    error_msg = current_state.get("error")
    retry_count = current_state.get("retry_count", 0)
    
    if error_msg:
        # 에러 유형에 따른 아이콘 및 안내 메시지
        error_icon = "⚠️"
        error_hint = "다시 시도해 주세요."
        
        if "필수" in str(error_msg) or "누락" in str(error_msg):
            error_icon = "📋"
            error_hint = "필수 항목을 모두 입력해 주세요."
        elif "형식" in str(error_msg) or "유효" in str(error_msg):
            error_icon = "📝"
            error_hint = "올바른 형식으로 입력해 주세요."
        elif "선택" in str(error_msg):
            error_icon = "👆"
            error_hint = "아래 옵션 중 하나를 선택해 주세요."
        
        # 재시도 횟수 표시 (최대 횟수 경고)
        MAX_RETRIES = 5
        retry_info = ""
        if retry_count > 0:
            remaining = MAX_RETRIES - retry_count
            if remaining <= 2:
                retry_info = f" 🔄 (남은 시도: {remaining}회)"
            else:
                retry_info = f" (시도 {retry_count}/{MAX_RETRIES})"
        
        # 에러 메시지 박스 렌더링
        st.markdown(f"""
        <div style="
            background-color: #fff3cd;
            border: 1px solid #ffc107;
            border-left: 4px solid #fd7e14;
            border-radius: 8px;
            padding: 12px 16px;
            margin-bottom: 16px;
        ">
            <strong>{error_icon} 입력 오류{retry_info}</strong>
            <p style="margin: 8px 0 0 0; color: #856404;">{error_msg}</p>
            <small style="color: #6c757d;">💡 {error_hint}</small>
        </div>
        """, unsafe_allow_html=True)

    # 1. Schema-driven Form (Priority)
    # PlanCraftState에 저장된 스키마 클래스명(Str)을 이용해 동적으로 폼 생성
    schema_name = current_state.get("input_schema_name")
    if schema_name:
        from utils import schemas
        model_cls = getattr(schemas, schema_name, None)
        
        if model_cls:
            st.markdown(f"##### 📝 추가 정보 입력 ({model_cls.__name__})")
            form_data = render_pydantic_form(model_cls, key_prefix="interrupt_form")
            
            if form_data:
                # 폼 제출 처리
                st.session_state.chat_history.append({
                    "role": "user", "content": f"[폼 입력 제출]\\n{form_data}", "type": "text"
                })
                # JSON 형태로 pending_input 저장
                import json
                st.session_state.current_state = None
                st.session_state.pending_input = f"FORM_DATA:{json.dumps(form_data, ensure_ascii=False)}"
                st.rerun()
            return

    # 2. Option Selector
    if current_state.get("options"):
        render_option_selector(current_state)
        return

    # 3. Fallback (If any other interrupt without options)
    st.info("사용자 입력 대기 중...")


def render_option_selector(current_state):
    """
    옵션 선택 UI 렌더링 (휴먼 인터럽트)
    
    Pydantic 스키마(OptionChoice) 기반의 옵션 목록을 렌더링하고,
    사용자 선택을 처리합니다.
    """
    if not current_state:
        return

    from graph.state import safe_get

    # TypedDict dict-access 방식으로 통일
    options = current_state.get("options", [])
    if not options:
        return

    cols = st.columns(len(options))
    for i, opt in enumerate(options):
        # dict 또는 Pydantic 객체 모두 지원
        title = safe_get(opt, "title", "")
        description = safe_get(opt, "description", "")
        opt_id = safe_get(opt, "id", "")

        with cols[i]:
            if st.button(f"{title}", key=f"opt_{i}", use_container_width=True, help=description):
                # [FIX] "수정" 옵션 선택 시 초기 화면으로 리셋
                # 사용자가 처음부터 다시 입력하고 파일 업로드할 수 있게 함
                is_retry_option = (
                    opt_id == "retry" or
                    "수정" in title or
                    "아니요" in title or
                    "취소" in title
                )

                if is_retry_option:
                    # 세션 상태 초기화 (처음 화면으로)
                    st.session_state.chat_history = []
                    st.session_state.current_state = None
                    st.session_state.generated_plan = None
                    st.session_state.uploaded_content = None
                    st.session_state.pending_input = None
                    st.session_state.prefill_prompt = None
                    st.session_state.input_key += 1
                    import uuid
                    st.session_state.thread_id = str(uuid.uuid4())
                    st.toast("🔄 처음 화면으로 돌아갑니다. 새로운 아이디어를 입력해주세요!")
                    st.rerun()
                    return

                # 일반 옵션 선택 처리 로직
                st.session_state.chat_history.append({
                    "role": "user", "content": f"'{title}' 선택", "type": "text"
                })

                # [FIX] OPTION: 프리픽스로 resume 명령 생성 (HITL Resume 패턴)
                # workflow_runner.py의 parse_resume_command()가 이를 인식
                import json
                option_payload = {"id": opt_id, "title": title, "description": description}

                # 상태 업데이트 및 재실행 준비
                st.session_state.current_state = None
                st.session_state.pending_input = f"OPTION:{json.dumps(option_payload, ensure_ascii=False)}"
                st.rerun()

    st.markdown("""
    <div style="display: flex; align-items: center; margin: 1.5rem 0 1rem 0;">
        <div style="flex: 1; height: 1px; background: #ddd;"></div>
        <span style="padding: 0 1rem; color: #888; font-size: 0.85rem;">또는 직접 입력</span>
        <div style="flex: 1; height: 1px; background: #ddd;"></div>
    </div>
    """, unsafe_allow_html=True)
    st.caption("⌨️ 위 옵션 외에 다른 의견이 있다면 아래 입력창에 자유롭게 작성하세요")
