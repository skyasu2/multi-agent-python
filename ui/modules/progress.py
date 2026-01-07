"""
Progress UI Module
"""
import streamlit as st
import time

def render_visual_timeline(step_history: list):
    """
    실행 이력 시각화 (텍스트 타임라인)
    """
    if not step_history:
        return

    # 텍스트 기반 타임라인 (안정적)
    render_timeline(step_history)

    # (선택) 원본 데이터 보기
    with st.expander("📊 원본 JSON 데이터 (Debug)", expanded=False):
         st.json(step_history)


def render_progress_steps(current_step: str = None):
    """
    진행 상태 표시 (개선된 버전)

    - Streamlit 프로그레스 바 추가
    - CSS 변수 활용
    - 단계별 설명 표시
    """
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

    # 프로그레스 바 (0~1 사이 값)
    if current_idx >= 0:
        progress_value = (current_idx + 1) / len(steps)
        st.progress(progress_value, text=f"진행률: {int(progress_value * 100)}% ({current_idx + 1}/{len(steps)} 단계)")

    # 단계별 아이콘 표시
    cols = st.columns(len(steps))
    for i, (step, key) in enumerate(zip(steps, step_keys)):
        with cols[i]:
            icon = step.split()[0]  # 이모지 추출
            label = step.split()[1] if len(step.split()) > 1 else ""

            if i < current_idx:
                # 완료된 단계
                st.markdown(
                    f"<div style='text-align:center; color:var(--color-success, #28a745);'>"
                    f"<div style='font-size:1.5rem;'>{icon}</div>"
                    f"<small>✅ {label}</small></div>",
                    unsafe_allow_html=True
                )
            elif i == current_idx:
                # 현재 단계 (강조)
                st.markdown(
                    f"<div style='text-align:center; color:var(--color-primary, #667eea); font-weight:bold;'>"
                    f"<div style='font-size:1.8rem;'>{icon}</div>"
                    f"<small>▶️ {label}</small></div>",
                    unsafe_allow_html=True
                )
            else:
                # 대기 단계
                st.markdown(
                    f"<div style='text-align:center; color:var(--color-text-disabled, #ccc);'>"
                    f"<div style='font-size:1.2rem;'>{icon}</div>"
                    f"<small>{label}</small></div>",
                    unsafe_allow_html=True
                )

    # 현재 단계 설명
    if current_step and current_step in step_descriptions:
        st.markdown(
            f"<div style='text-align:center; color:var(--color-text-muted, #666); "
            f"font-size:0.9rem; margin-top:1rem; background-color:var(--color-bg-light, #f8f9fa); "
            f"padding:0.75rem; border-radius:var(--radius-sm, 8px); border-left:3px solid var(--color-primary, #667eea);'>"
            f"💬 {step_descriptions[current_step]}</div>",
            unsafe_allow_html=True
        )


def render_specialist_agents_status(specialist_analysis: dict = None, is_running: bool = False):
    """
    전문 에이전트 분석 상태 표시
    
    Multi-Agent Supervisor의 4개 전문 에이전트 진행/완료 상태를 시각화합니다.
    """
    agents = [
        {"key": "market_analysis", "name": "시장 분석", "icon": "📊", "desc": "TAM/SAM/SOM, 경쟁사"},
        {"key": "business_model", "name": "비즈니스 모델", "icon": "💰", "desc": "수익 모델, 가격 전략"},
        {"key": "tech_architecture", "name": "기술 아키텍처", "icon": "🏗️", "desc": "스택, 인프라, 로드맵"},
        {"key": "content_strategy", "name": "콘텐츠 전략", "icon": "📣", "desc": "브랜딩, 유입, 마케팅"},
        {"key": "financial_plan", "name": "재무 계획", "icon": "📈", "desc": "투자비, BEP, 손익"},
        {"key": "risk_analysis", "name": "리스크", "icon": "⚠️", "desc": "8가지 리스크 분석"},
    ]
    
    if is_running:
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 16px;
            border-radius: 12px;
            margin-bottom: 16px;
        ">
            <div style="display: flex; align-items: center; gap: 10px;">
                <span style="font-size: 1.5rem;">🤖</span>
                <div>
                    <strong>전문 에이전트 분석 중...</strong>
                    <p style="margin: 4px 0 0 0; font-size: 0.85rem; opacity: 0.9;">
                        4개의 전문 AI 에이전트가 병렬로 분석을 수행하고 있습니다
                    </p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # 진행 중 애니메이션 (3열 그리드 - Refactored)
        grid_cols = st.columns(3)
        grid_cols_2 = st.columns(3)
        
        for i, agent in enumerate(agents):
            target_col = grid_cols[i] if i < 3 else grid_cols_2[i-3]
            with target_col:
                st.markdown(f"""
                <div style="
                    text-align: center;
                    padding: 12px 8px;
                    background: #f8f9fa;
                    border-radius: 8px;
                    border: 2px dashed #667eea;
                ">
                    <div style="font-size: 1.5rem;">{agent['icon']}</div>
                    <div style="font-size: 0.8rem; font-weight: bold; margin: 4px 0;">{agent['name']}</div>
                    <div style="font-size: 0.7rem; color: #666;">⏳ 분석 중...</div>
                </div>
                """, unsafe_allow_html=True)
        return
    
    if not specialist_analysis:
        return
    
    # 분석 완료 상태 표시
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        color: white;
        padding: 16px;
        border-radius: 12px;
        margin-bottom: 16px;
    ">
        <div style="display: flex; align-items: center; gap: 10px;">
            <span style="font-size: 1.5rem;">✅</span>
            <div>
                <strong>전문 에이전트 분석 완료!</strong>
                <p style="margin: 4px 0 0 0; font-size: 0.85rem; opacity: 0.9;">
                    아래 분석 결과가 기획서 작성에 자동 반영됩니다
                </p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 완료된 에이전트 결과 표시 (3열 그리드)
    grid_cols = st.columns(3)
    grid_cols_2 = st.columns(3)
    
    for i, agent in enumerate(agents):
        target_col = grid_cols[i] if i < 3 else grid_cols_2[i-3]
        
        result = specialist_analysis.get(agent["key"])
        is_done = result is not None
        
        with target_col:
            if is_done:
                st.markdown(f"""
                <div style="
                    text-align: center;
                    padding: 12px 8px;
                    background: #e8f5e9;
                    border-radius: 8px;
                    border: 2px solid #4caf50;
                ">
                    <div style="font-size: 1.5rem;">{agent['icon']}</div>
                    <div style="font-size: 0.8rem; font-weight: bold; margin: 4px 0; color: #2e7d32;">{agent['name']}</div>
                    <div style="font-size: 0.7rem; color: #4caf50;">✓ 완료</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="
                    text-align: center;
                    padding: 12px 8px;
                    background: #ffebee;
                    border-radius: 8px;
                    border: 2px solid #ef5350;
                ">
                    <div style="font-size: 1.5rem;">{agent['icon']}</div>
                    <div style="font-size: 0.8rem; font-weight: bold; margin: 4px 0; color: #c62828;">{agent['name']}</div>
                    <div style="font-size: 0.7rem; color: #ef5350;">✗ 미완료</div>
                </div>
                """, unsafe_allow_html=True)
    
    # 상세 결과 Expander
    with st.expander("🔍 전문 에이전트 분석 상세 결과", expanded=False):
        stats = specialist_analysis.get("_execution_stats")
        
        tab_titles = []
        if stats:
            tab_titles.append("📊 시스템 통계")
            
        tab_titles.extend([f"{a['icon']} {a['name']}" for a in agents])
        tabs = st.tabs(tab_titles)
        
        current_tab_idx = 0
        
        # 1. 시스템 통계 렌더링
        if stats:
            with tabs[current_tab_idx]:
                st.markdown("#### ⚡ Multi-Agent Execution Stats")
                
                m1, m2, m3, m4 = st.columns(4)
                
                start = stats.get("started_at")
                end = stats.get("completed_at")
                duration = "N/A"
                if start and end:
                    from datetime import datetime
                    try:
                        s = datetime.fromisoformat(start)
                        e = datetime.fromisoformat(end)
                        duration = f"{(e-s).total_seconds():.2f}s"
                    except (ValueError, TypeError):
                        pass  # 날짜 파싱 실패 시 기본값 유지
                
                with m1:
                    st.metric("총 소요 시간", duration)
                with m2:
                    st.metric("성공/실패", f"{stats.get('successful_agents', 0)} / {stats.get('failed_agents', 0)}")
                with m3:
                    st.metric("재시도 횟수", f"{stats.get('retried_agents', 0)}")
                with m4:
                    st.metric("Fallback 사용", f"{stats.get('fallback_used_count', 0)}")
                
                st.divider()
                
                agent_stats = stats.get("agent_stats", {})
                if agent_stats:
                    st.markdown("##### 🕵️ 에이전트별 성능")
                    stat_data = []
                    for aid, a_stat in agent_stats.items():
                        stat_data.append({
                             "Agent": aid,
                             "Status": "✅ Success" if a_stat.get("success") else "❌ Failed",
                             "Time": f"{a_stat.get('execution_time_ms', 0):.0f}ms",
                             "Retries": a_stat.get("retry_count", 0),
                             "Fallback": "⚡ Yes" if a_stat.get("fallback_used") else "-",
                             "Error": a_stat.get("error_category", "-")
                        })
                    st.dataframe(stat_data, use_container_width=True)

            current_tab_idx += 1
        
        # 2. 각 에이전트 결과 렌더링
        for i, agent in enumerate(agents):
            try:
                with tabs[current_tab_idx + i]:
                    result = specialist_analysis.get(agent["key"])
                    if result:
                        if isinstance(result, dict) and "_fallback_reason" in result:
                            st.warning(f"⚠️ Fallback 사용됨: {result['_fallback_reason']}")
                        st.json(result)
                    else:
                        st.info("분석 결과 없음")
            except IndexError:
                # Tab index overflow protection
                pass


def render_timeline(step_history: list):
    """LangGraph 실행 이력 타임라인 렌더링"""
    if not step_history:
        return

    st.markdown("##### ⏱️ 실행 타임라인")
    with st.expander("상세 실행 이력 보기", expanded=False):
        for i, item in enumerate(step_history):
            status = item.get("status", "UNKNOWN")
            icon = "🟢" if status == "SUCCESS" else "🔴" if status == "FAILED" else "⚪"
            
            ts = item.get("timestamp", "")
            time_str = ts.split("T")[1][:8] if "T" in ts else ts
            
            step_name = item.get("step", "").upper()
            summary = item.get("summary", "")
            error = item.get("error")
            
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
