"""
UI Components Module

재사용 가능한 UI 컴포넌트들을 정의합니다.
"""

import streamlit as st


def render_progress_steps(current_step: str = None):
    """진행 상태 표시"""
    steps = ["📥 분석", "🏗️ 구조", "✍️ 작성", "🔍 검토", "✨ 개선", "📋 완료"]
    step_keys = ["analyze", "structure", "write", "review", "refine", "format"]
    step_descriptions = {
        "analyze": "사용자의 요구사항을 분석하고 있습니다...",
        "structure": "기획서의 구조를 설계하고 있습니다...",
        "write": "섹션별 내용을 작성하고 있습니다...",
        "review": "품질을 검토하고 있습니다...",
        "refine": "피드백을 반영하여 개선하고 있습니다...",
        "format": "최종 문서를 정리하고 있습니다..."
    }
    
    current_idx = -1
    if current_step:
        for i, key in enumerate(step_keys):
            if key in current_step.lower():
                current_idx = i
                break
    
    cols = st.columns(len(steps))
    for i, (step, key) in enumerate(zip(steps, step_keys)):
        with cols[i]:
            icon = step.split()[0]  # 이모지 추출
            if i < current_idx:
                # 완료된 단계
                st.markdown(f"<div style='text-align:center; color:#28a745; margin-bottom:5px;'>{icon}<br><small>✅</small></div>", unsafe_allow_html=True)
            elif i == current_idx:
                # 현재 단계
                st.markdown(f"<div style='text-align:center; color:#007bff; font-weight:bold; margin-bottom:5px;'>{icon}<br><small>▶️</small></div>", unsafe_allow_html=True)
            else:
                # 대기 단계
                st.markdown(f"<div style='text-align:center; color:#ddd; margin-bottom:5px;'>{icon}</div>", unsafe_allow_html=True)
    
    # 현재 단계 설명
    if current_step and current_step in step_descriptions:
        st.markdown(f"<div style='text-align:center; color:#666; font-size:0.9rem; margin-top:1rem; background-color:#f8f9fa; padding:0.5rem; border-radius:8px;'>{step_descriptions[current_step]}</div>", unsafe_allow_html=True)


def render_timeline(step_history: list):
    """LangGraph 실행 이력 타임라인 렌더링"""
    if not step_history:
        return

    st.markdown("##### ⏱️ 실행 타임라인")
    with st.expander("상세 실행 이력 보기", expanded=False):
        for i, item in enumerate(step_history):
            # 상태 아이콘
            status = item.get("status", "UNKNOWN")
            icon = "🟢" if status == "SUCCESS" else "🔴" if status == "FAILED" else "⚪"
            
            # 시간 포맷 (HH:MM:SS)
            ts = item.get("timestamp", "")
            time_str = ts.split("T")[1][:8] if "T" in ts else ts
            
            # 단계 이름 (첫 글자 대문자)
            step_name = item.get("step", "").upper()
            
            # 요약 및 에러
            summary = item.get("summary", "")
            error = item.get("error")
            
            # Markdown 렌더링
            col1, col2 = st.columns([0.1, 0.9])
            with col1:
                st.markdown(f"<div style='font-size:1.2em; text-align:center;'>{icon}</div>", unsafe_allow_html=True)
            with col2:
                st.markdown(f"**{step_name}** <small style='color:gray'>({time_str})</small>", unsafe_allow_html=True)
                if summary:
                    st.caption(f"└ {summary}")
                if error:
                    st.error(f"Error: {error}")
            
            if i < len(step_history) - 1:
                st.divider()


def render_chat_message(role: str, content: str, msg_type: str = "text"):
    """채팅 메시지 렌더링"""
    if role == "user":
        with st.chat_message("user"):
            st.markdown(content)
    else:  # assistant
        with st.chat_message("assistant"):
            st.markdown(content)
