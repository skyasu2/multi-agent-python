"""
UI Refinement Module

기획서 개선 요청 UI를 정의합니다.
"""

import streamlit as st
import uuid


def render_refinement_ui():
    """기획서 고도화 UI (개선 요청)"""
    if st.session_state.generated_plan and st.session_state.current_state:
        current_refine_count = st.session_state.current_state.get("refine_count", 0)
        
        st.divider()
        
        next_step = current_refine_count + 1
        label = f"🔧 기획서 추가 개선 ({next_step}/3단계) - 클릭하여 펼치기"
        
        with st.expander(label, expanded=False):
            if current_refine_count < 3:
                st.info(f"💡 AI에게 피드백을 전달하여 기획서를 고도화할 수 있습니다. (남은 기회: **{3 - current_refine_count}회**)")
                
                with st.form("refine_form"):
                    st.markdown("**1. 추가 요청사항 입력**")
                    feedback = st.text_area(
                        "요청사항",
                        placeholder="예: '수익 모델을 구독형으로 바꿔줘', '경쟁사 분석 데이터를 더 추가해줘', '초기 마케팅 전략을 구체화해줘'",
                        height=100,
                        label_visibility="collapsed"
                    )
                    
                    st.markdown("**2. 참고 자료 첨부 (선택)**")
                    refine_file = st.file_uploader(
                        "파일 업로드",
                        type=["txt", "md", "pdf", "docx"],
                        label_visibility="collapsed",
                        help="기획서에 반영할 추가 자료가 있다면 업로드하세요."
                    )
                    
                    st.markdown("")
                    col_submit, col_info = st.columns([1, 4])
                    with col_submit:
                        is_submitted = st.form_submit_button("🚀 개선 수행", use_container_width=True)
                    with col_info:
                        st.caption(f"현재 **{next_step}단계** 개선을 진행합니다. (최대 3단계)")
                    
                    if is_submitted and feedback:
                        # 입력 데이터 구성
                        original_input = st.session_state.current_state.get("user_input", "")
                        new_input = f"{original_input}\n\n--- [추가 요청 {current_refine_count + 1}] ---\n{feedback}"
                        
                        # 파일 내용 읽기
                        new_file_content = st.session_state.get("uploaded_content", "")
                        if refine_file:
                            try:
                                additional_content = refine_file.read().decode("utf-8")
                                new_file_content = (new_file_content + "\n\n" + additional_content) if new_file_content else additional_content
                                st.session_state.uploaded_content = new_file_content
                            except Exception as e:
                                st.error(f"파일 읽기 실패: {str(e)}")
                                
                        # 상태 업데이트 및 실행 예약
                        st.session_state.pending_input = new_input
                        
                        # 채팅창에 사용자 발화 추가
                        st.session_state.chat_history.append({
                            "role": "user",
                            "content": f"🛠 **추가 개선 요청 ({current_refine_count + 1}/3):**\n{feedback}",
                            "type": "text"
                        })
                        
                        st.session_state.next_refine_count = current_refine_count + 1
                        st.rerun()

            else:
                st.info("✅ 최대 개선 횟수(3회)를 모두 사용했습니다. 새로운 기획을 원하시면 '새 대화'를 시작하세요.")
        
        # 새 대화 시작 버튼 (개선 UI 아래)
        st.markdown("")  # 간격
        if st.button("🔄 새 대화 시작", key="new_chat_after_plan", use_container_width=True):
            # 세션 초기화
            st.session_state.chat_history = []
            st.session_state.current_state = None
            st.session_state.generated_plan = None
            st.session_state.input_key = st.session_state.get("input_key", 0) + 1
            st.session_state.thread_id = str(uuid.uuid4())
            st.session_state.prefill_prompt = None
            st.session_state.pending_input = None
            st.session_state.next_refine_count = 0
            st.rerun()
