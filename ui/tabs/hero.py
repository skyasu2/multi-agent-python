"""
Hero Tab: Brainstorming UI (개선된 디자인)

Features:
- 카드 스타일 아이디어 버튼
- 아이콘 + 제목 + 설명
- 호버 효과 및 그라데이션
"""
import streamlit as st
from utils.prompt_examples import CATEGORIES, get_examples_by_category


# =============================================================================
# CSS 스타일
# =============================================================================
HERO_CSS = """
<style>
/* ===== 브레인스토밍 헤더 ===== */
.brainstorm-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 8px;
}
.brainstorm-title {
    font-size: 1.25rem;
    font-weight: 700;
    color: #1e293b;
    margin: 0;
}
.brainstorm-badge {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    font-size: 0.75rem;
    font-weight: 600;
    padding: 4px 10px;
    border-radius: 20px;
}

/* ===== 카테고리 드롭다운 ===== */
.category-select [data-testid="stSelectbox"] > div > div {
    border-radius: 20px !important;
    border: 1.5px solid #e2e8f0 !important;
    background: white !important;
}

/* ===== AI 생성 버튼 ===== */
.ai-gen-btn button {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 20px !important;
    font-weight: 600 !important;
    padding: 8px 20px !important;
    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3) !important;
    transition: all 0.2s ease !important;
}
.ai-gen-btn button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4) !important;
}

/* ===== 아이디어 카드 ===== */
.idea-card {
    background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
    border: 1.5px solid #e2e8f0;
    border-radius: 16px;
    padding: 20px;
    height: 100%;
    min-height: 120px;
    cursor: pointer;
    transition: all 0.25s ease;
    position: relative;
    overflow: hidden;
}
.idea-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    opacity: 0;
    transition: opacity 0.25s ease;
}
.idea-card:hover {
    border-color: #a5b4fc;
    transform: translateY(-4px);
    box-shadow: 0 12px 24px rgba(102, 126, 234, 0.15);
}
.idea-card:hover::before {
    opacity: 1;
}

.idea-card-icon {
    font-size: 2rem;
    margin-bottom: 8px;
    display: block;
}
.idea-card-title {
    font-size: 1rem;
    font-weight: 700;
    color: #1e293b;
    margin-bottom: 6px;
    line-height: 1.3;
}
.idea-card-desc {
    font-size: 0.8rem;
    color: #64748b;
    line-height: 1.4;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
}

/* ===== 아이디어 버튼 오버라이드 ===== */
.idea-cards-row [data-testid="stButton"] > button {
    background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%) !important;
    border: 1.5px solid #e2e8f0 !important;
    border-radius: 16px !important;
    padding: 16px !important;
    min-height: 100px !important;
    text-align: left !important;
    color: #1e293b !important;
    font-weight: 600 !important;
    transition: all 0.25s ease !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04) !important;
}
.idea-cards-row [data-testid="stButton"] > button:hover {
    border-color: #a5b4fc !important;
    transform: translateY(-4px) !important;
    box-shadow: 0 12px 24px rgba(102, 126, 234, 0.15) !important;
    background: linear-gradient(135deg, #f8fafc 0%, #eff6ff 100%) !important;
}

/* ===== 팁 박스 ===== */
.tip-box {
    background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
    border-left: 4px solid #667eea;
    border-radius: 12px;
    padding: 16px 20px;
    margin-top: 20px;
}
.tip-box-title {
    font-weight: 700;
    color: #1e293b;
    font-size: 0.95rem;
    margin-bottom: 8px;
}
.tip-box-content {
    color: #475569;
    font-size: 0.88rem;
    line-height: 1.6;
}
.tip-good {
    color: #059669;
    font-weight: 600;
}
.tip-bad {
    color: #dc2626;
    font-weight: 600;
}

/* ===== 카테고리 설명 ===== */
.category-desc {
    background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
    border-radius: 8px;
    padding: 8px 14px;
    font-size: 0.85rem;
    color: #3b82f6;
    display: inline-block;
    margin-bottom: 16px;
}
</style>
"""

# 아이디어 카드 아이콘 (순환 사용)
IDEA_ICONS = ["🚀", "💡", "🎯", "✨", "🔥", "💎"]


def render_brainstorming_hero():
    """시작 화면 브레인스토밍 UI (개선된 디자인)"""

    # CSS 적용
    st.markdown(HERO_CSS, unsafe_allow_html=True)

    st.markdown("<div class='animate-fade-in'>", unsafe_allow_html=True)

    # =========================================================================
    # 세션 상태 초기화
    # =========================================================================
    if "idea_category" not in st.session_state:
        st.session_state.idea_category = "random"
    if "idea_llm_count" not in st.session_state:
        st.session_state.idea_llm_count = 0
    if "random_examples" not in st.session_state or st.session_state.random_examples is None:
        st.session_state.random_examples = get_examples_by_category("random", 3)

    cat_keys = list(CATEGORIES.keys())

    def on_category_change():
        new_category = st.session_state.idea_category
        st.session_state.random_examples = get_examples_by_category(new_category, 3)

    # =========================================================================
    # 헤더: 타이틀 + 카테고리 + AI 생성 버튼
    # =========================================================================
    llm_remaining = max(0, 10 - st.session_state.idea_llm_count)

    col_title, col_dropdown, col_btn = st.columns([2.5, 1.5, 1.2])

    with col_title:
        st.markdown(f"""
        <div class="brainstorm-header">
            <span style="font-size: 1.5rem;">🎲</span>
            <span class="brainstorm-title">AI 브레인스토밍</span>
            <span class="brainstorm-badge">{llm_remaining}회 남음</span>
        </div>
        """, unsafe_allow_html=True)

    with col_dropdown:
        st.markdown('<div class="category-select">', unsafe_allow_html=True)
        st.selectbox(
            "카테고리",
            options=cat_keys,
            format_func=lambda k: f"{CATEGORIES[k]['icon']} {CATEGORIES[k]['label']}",
            key="idea_category",
            label_visibility="collapsed",
            on_change=on_category_change
        )
        st.markdown('</div>', unsafe_allow_html=True)

    with col_btn:
        st.markdown('<div class="ai-gen-btn">', unsafe_allow_html=True)
        if st.button("✨ AI 생성", key="refresh_hero_ex", use_container_width=True,
                     help="AI가 새로운 아이디어를 제안합니다"):
            from utils.idea_generator import generate_ideas
            with st.spinner("💡 아이디어를 떠올리는 중..."):
                ideas, used_llm = generate_ideas(
                    category=st.session_state.idea_category,
                    count=3,
                    use_llm=True,
                    session_call_count=st.session_state.idea_llm_count
                )
                st.session_state.random_examples = ideas
                if used_llm:
                    st.session_state.idea_llm_count += 1
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # 카테고리 설명
    current_cat = CATEGORIES.get(st.session_state.idea_category, {})
    cat_desc = current_cat.get('description', '다양한 분야에서 랜덤 추천')
    st.markdown(f'<div class="category-desc">💡 {cat_desc}</div>', unsafe_allow_html=True)

    # =========================================================================
    # 아이디어 카드 3개
    # =========================================================================
    st.markdown('<div class="idea-cards-row">', unsafe_allow_html=True)
    cols = st.columns(3)

    for i, (title, prompt) in enumerate(st.session_state.random_examples):
        icon = IDEA_ICONS[i % len(IDEA_ICONS)]

        with cols[i]:
            # 제목에서 설명 추출 (prompt의 앞부분 사용)
            desc = prompt[:50] + "..." if len(prompt) > 50 else prompt

            # 카드 형태 버튼
            btn_label = f"{icon} {title}"
            if st.button(btn_label, key=f"hero_ex_{i}", use_container_width=True, help=prompt):
                st.session_state.prefill_prompt = prompt

    st.markdown('</div>', unsafe_allow_html=True)

    # =========================================================================
    # 팁 박스
    # =========================================================================
    st.markdown("""
    <div class="tip-box animate-slide-up">
        <div class="tip-box-title">💡 Tip: 빠른 기획서 생성을 위한 입력 가이드</div>
        <div class="tip-box-content">
            <strong>명확한 입력</strong>(타겟, 목적 포함) 시 바로 기획서가 생성됩니다.<br/>
            <span class="tip-good">✅ "직장인을 위한 AI 식단 관리 앱"</span>
            &nbsp; vs &nbsp;
            <span class="tip-bad">❓ "다이어트 앱"</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
