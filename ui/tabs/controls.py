"""
Input & Controls Tab - ChatGPT 스타일 채팅 입력 UI

Features:
- [+] 버튼으로 파일 첨부 (ChatGPT 스타일)
- 파일 칩 미리보기
- 아이콘 버튼 모드 선택 (⚡⚖️💎)
- 키보드 접근성 지원
"""
import streamlit as st
from typing import Dict, Any
import uuid


# =============================================================================
# 상수 정의
# =============================================================================
FILE_ICONS = {
    "pdf": "📄", "txt": "📝", "md": "📑", "docx": "📃",
    "png": "🖼️", "jpg": "🖼️", "jpeg": "🖼️", "gif": "🖼️",
    "default": "📎"
}

ALLOWED_EXTENSIONS = {"txt", "md", "pdf", "png", "jpg", "jpeg"}
MAX_FILE_SIZE_MB = 10
MAX_FILES = 5

MODE_CONFIG = {
    "speed": {"icon": "⚡", "label": "Speed", "desc": "빠른 응답 (gpt-4o-mini)"},
    "balanced": {"icon": "⚖️", "label": "Balanced", "desc": "균형 모드 (gpt-4o)"},
    "quality": {"icon": "💎", "label": "Quality", "desc": "고품질 분석 (gpt-4o + RAG)"}
}


# =============================================================================
# CSS 스타일
# =============================================================================
CONTROLS_CSS = """
<style>
/* ===== 툴바 (채팅 입력창 위) ===== */
.chat-toolbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 12px;
    background: linear-gradient(to bottom, rgba(255,255,255,0.98), rgba(248,250,252,0.95));
    border-radius: 16px;
    border: 1px solid #e2e8f0;
    margin-bottom: 8px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}

/* ===== 좌측 그룹 (+ 버튼 + 파일 개수) ===== */
.toolbar-left {
    display: flex;
    align-items: center;
    gap: 8px;
}

/* ===== 우측 그룹 (모드 버튼들) ===== */
.toolbar-right {
    display: flex;
    align-items: center;
    gap: 4px;
}

/* ===== 파일 칩 스타일 ===== */
.file-chip {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 6px 12px;
    background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
    border: 1px solid #cbd5e1;
    border-radius: 20px;
    font-size: 0.85rem;
    color: #334155;
    max-width: 160px;
    transition: all 0.15s ease;
}
.file-chip:hover {
    background: linear-gradient(135deg, #e2e8f0 0%, #cbd5e1 100%);
    border-color: #94a3b8;
}
.file-chip-icon { font-size: 1rem; }
.file-chip-name {
    flex: 1;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    font-weight: 500;
}

/* ===== 파일 미리보기 바 ===== */
.files-preview-bar {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    padding: 12px 16px;
    background: linear-gradient(to bottom, rgba(255,255,255,0.98), rgba(248,250,252,0.95));
    border-radius: 16px 16px 0 0;
    border: 1px solid #e2e8f0;
    border-bottom: none;
    margin-bottom: -4px;
}

/* ===== + 버튼 스타일 ===== */
.plus-btn button {
    width: 40px !important;
    height: 40px !important;
    min-width: 40px !important;
    border-radius: 50% !important;
    border: 1.5px solid #e2e8f0 !important;
    background: white !important;
    color: #64748b !important;
    font-size: 1.5rem !important;
    font-weight: 300 !important;
    padding: 0 !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04) !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}
.plus-btn button:hover {
    background: #f1f5f9 !important;
    border-color: #94a3b8 !important;
    color: #475569 !important;
    transform: scale(1.08) !important;
}
.plus-btn.has-files button {
    background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%) !important;
    border-color: #60a5fa !important;
    color: #2563eb !important;
}

/* ===== 모드 버튼 스타일 (가로 배치) ===== */
.mode-btn button {
    width: 44px !important;
    height: 44px !important;
    min-width: 44px !important;
    border-radius: 12px !important;
    border: 1.5px solid #e2e8f0 !important;
    background: white !important;
    font-size: 1.4rem !important;
    padding: 0 !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 2px 6px rgba(0,0,0,0.04) !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}
.mode-btn button:hover {
    background: #f8fafc !important;
    border-color: #94a3b8 !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08) !important;
}
.mode-btn.active button {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    border: none !important;
    color: white !important;
    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.35) !important;
}
.mode-btn.active button:hover {
    transform: translateY(-2px) scale(1.02) !important;
    box-shadow: 0 6px 20px rgba(102, 126, 234, 0.45) !important;
}

/* ===== 파일 개수 배지 ===== */
.file-count-badge {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    font-size: 0.7rem;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 12px;
    margin-left: -4px;
}

/* ===== 업로드 패널 ===== */
.upload-panel {
    background: white;
    border-radius: 16px;
    padding: 20px;
    margin-bottom: 12px;
    border: 1px solid #e2e8f0;
    box-shadow: 0 4px 20px rgba(0,0,0,0.08);
}

/* ===== Prefill 확인 박스 ===== */
.prefill-box {
    background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
    border: 1px solid #93c5fd;
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 16px;
}
.prefill-text {
    font-size: 0.95rem;
    color: #1e40af;
    margin-bottom: 12px;
}
</style>
"""


# =============================================================================
# 헬퍼 함수
# =============================================================================
def get_file_icon(filename: str) -> str:
    """파일 확장자에 따른 아이콘 반환"""
    ext = filename.split(".")[-1].lower() if "." in filename else ""
    return FILE_ICONS.get(ext, FILE_ICONS["default"])


def format_file_size(size_bytes: int) -> str:
    """파일 크기를 읽기 쉬운 형식으로 변환"""
    if size_bytes < 1024:
        return f"{size_bytes}B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f}KB"
    return f"{size_bytes / (1024 * 1024):.1f}MB"


def init_file_state():
    """파일 업로드 관련 세션 상태 초기화"""
    if "attached_files" not in st.session_state:
        st.session_state.attached_files = []
    if "show_upload_panel" not in st.session_state:
        st.session_state.show_upload_panel = False


def update_uploaded_content():
    """attached_files를 기반으로 uploaded_content 업데이트"""
    if not st.session_state.attached_files:
        st.session_state.uploaded_content = None
        return

    contents = []
    for f in st.session_state.attached_files:
        if f.get("content"):
            contents.append(f"[파일: {f['name']}]\n{f['content']}")

    st.session_state.uploaded_content = "\n\n---\n\n".join(contents) if contents else None


# =============================================================================
# 파일 업로드 UI
# =============================================================================
def render_file_upload():
    """파일 업로드 영역 (호환성 유지)"""
    pass  # render_input_area()에 통합됨


def render_file_chips():
    """첨부된 파일 칩 미리보기"""
    if not st.session_state.attached_files:
        return

    st.markdown('<div class="files-preview-bar">', unsafe_allow_html=True)

    cols = st.columns(min(len(st.session_state.attached_files) + 1, 5))
    files_to_remove = []

    for idx, f in enumerate(st.session_state.attached_files):
        with cols[idx]:
            icon = get_file_icon(f["name"])
            short_name = f["name"][:12] + "..." if len(f["name"]) > 12 else f["name"]

            st.markdown(f"""
            <div class="file-chip" title="{f['name']} ({format_file_size(f['size'])})">
                <span class="file-chip-icon">{icon}</span>
                <span class="file-chip-name">{short_name}</span>
            </div>
            """, unsafe_allow_html=True)

            if st.button("✕", key=f"rm_chip_{idx}", help=f"{f['name']} 제거"):
                files_to_remove.append(idx)

    st.markdown('</div>', unsafe_allow_html=True)

    if files_to_remove:
        for idx in sorted(files_to_remove, reverse=True):
            st.session_state.attached_files.pop(idx)
        update_uploaded_content()
        st.rerun()


def render_upload_panel():
    """파일 업로드 패널"""
    st.markdown('<div class="upload-panel">', unsafe_allow_html=True)

    # 헤더
    col_title, col_close = st.columns([5, 1])
    with col_title:
        st.markdown("##### 📁 파일 첨부")
    with col_close:
        if st.button("✕", key="close_upload_panel", help="닫기"):
            st.session_state.show_upload_panel = False
            st.rerun()

    # 파일 업로더
    uploaded_files = st.file_uploader(
        "파일을 드래그하거나 클릭하여 선택",
        type=list(ALLOWED_EXTENSIONS),
        accept_multiple_files=True,
        key="file_uploader_main",
        label_visibility="collapsed"
    )

    st.caption(f"📌 {', '.join(ALLOWED_EXTENSIONS).upper()} | 최대 {MAX_FILE_SIZE_MB}MB, {MAX_FILES}개")

    if uploaded_files:
        for uploaded_file in uploaded_files:
            # 중복 체크
            existing_names = [f["name"] for f in st.session_state.attached_files]
            if uploaded_file.name in existing_names:
                continue

            # 파일 수 제한
            if len(st.session_state.attached_files) >= MAX_FILES:
                st.warning(f"최대 {MAX_FILES}개까지 첨부 가능합니다.")
                break

            # 크기 체크
            file_size = len(uploaded_file.getbuffer())
            if file_size > MAX_FILE_SIZE_MB * 1024 * 1024:
                st.error(f"'{uploaded_file.name}'이(가) 너무 큽니다.")
                continue

            # 파일 읽기
            ext = uploaded_file.name.split(".")[-1].lower()
            content = None

            if ext in {"txt", "md"}:
                content = uploaded_file.read().decode("utf-8", errors="ignore")[:50000]
            elif ext == "pdf":
                content = f"[PDF 파일: {uploaded_file.name}]"
            elif ext in {"png", "jpg", "jpeg", "gif"}:
                content = f"[이미지: {uploaded_file.name}]"

            st.session_state.attached_files.append({
                "name": uploaded_file.name,
                "size": file_size,
                "type": ext,
                "content": content
            })

        update_uploaded_content()
        st.success(f"✅ 파일 추가됨")

    # 첨부된 파일 목록
    if st.session_state.attached_files:
        st.markdown("---")
        for idx, f in enumerate(st.session_state.attached_files):
            col1, col2, col3 = st.columns([1, 5, 1])
            with col1:
                st.markdown(f"<span style='font-size:1.3rem'>{get_file_icon(f['name'])}</span>", unsafe_allow_html=True)
            with col2:
                st.markdown(f"**{f['name']}** ({format_file_size(f['size'])})")
            with col3:
                if st.button("🗑️", key=f"del_file_{idx}"):
                    st.session_state.attached_files.pop(idx)
                    update_uploaded_content()
                    st.rerun()

        if len(st.session_state.attached_files) > 1:
            if st.button("🗑️ 모두 삭제", key="clear_all"):
                st.session_state.attached_files = []
                st.session_state.uploaded_content = None
                st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)


# =============================================================================
# 메인 입력 영역
# =============================================================================
def render_input_area():
    """
    채팅 입력 영역 렌더링 (ChatGPT 스타일)

    레이아웃:
    ┌─────────────────────────────────────────────┐
    │ 📎 file1.txt  📄 doc.pdf  [x]              │  ← 파일 칩 (조건부)
    ├─────────────────────────────────────────────┤
    │ [업로드 패널]                               │  ← 토글 (조건부)
    ├─────────────────────────────────────────────┤
    │ [+] │ 메시지 입력...                  [↵]  │  ← 입력 영역
    │     │ ⚡  ⚖️  💎                           │  ← 모드 선택
    └─────────────────────────────────────────────┘
    """
    # CSS 적용
    st.markdown(CONTROLS_CSS, unsafe_allow_html=True)

    # 상태 초기화
    init_file_state()

    # Prefill 확인 UI
    if st.session_state.get("prefill_prompt") and not st.session_state.get("pending_input"):
        st.markdown(f"""
        <div class="prefill-box">
            <div class="prefill-text">📝 <strong>선택된 예시:</strong> {st.session_state.prefill_prompt}</div>
        </div>
        """, unsafe_allow_html=True)

        col_ok, col_no = st.columns(2)
        with col_ok:
            if st.button("✅ 이대로 시작", use_container_width=True, type="primary"):
                user_msg = st.session_state.prefill_prompt
                st.session_state.prefill_prompt = None
                st.session_state.chat_history.append({"role": "user", "content": user_msg, "type": "text"})
                st.session_state.pending_input = user_msg
                st.rerun()
        with col_no:
            if st.button("❌ 취소", use_container_width=True):
                st.session_state.prefill_prompt = None
                st.rerun()

    # 상태 표시 Placeholder
    status_placeholder = st.empty()

    # 파일 칩 미리보기
    render_file_chips()

    # 업로드 패널 (토글)
    if st.session_state.show_upload_panel:
        render_upload_panel()

    # =========================================================================
    # 툴바: [+] 버튼 (좌측) + 모드 선택 버튼들 (우측) - 가로 한 줄 배치
    # =========================================================================
    col_plus, col_spacer, col_mode1, col_mode2, col_mode3 = st.columns([0.6, 5, 0.7, 0.7, 0.7])

    file_count = len(st.session_state.attached_files)
    current_mode = st.session_state.get("generation_preset", "balanced")

    # [+] 버튼 (좌측)
    with col_plus:
        btn_class = "has-files" if file_count > 0 else ""
        st.markdown(f'<div class="plus-btn {btn_class}">', unsafe_allow_html=True)
        
        btn_icon = "✕" if st.session_state.show_upload_panel else "+"
        if st.button(btn_icon, key="btn_plus", help="파일 첨부" if not st.session_state.show_upload_panel else "닫기"):
            st.session_state.show_upload_panel = not st.session_state.show_upload_panel
            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 파일 개수 배지
        if file_count > 0 and not st.session_state.show_upload_panel:
            st.markdown(f'<span class="file-count-badge">{file_count}</span>', unsafe_allow_html=True)

    # 모드 버튼들 (우측, 가로 배치)
    mode_keys = list(MODE_CONFIG.keys())
    mode_columns = [col_mode1, col_mode2, col_mode3]
    
    for col, mode_key in zip(mode_columns, mode_keys):
        mode_info = MODE_CONFIG[mode_key]
        is_active = (current_mode == mode_key)
        
        with col:
            active_class = "active" if is_active else ""
            st.markdown(f'<div class="mode-btn {active_class}">', unsafe_allow_html=True)
            
            if st.button(
                mode_info["icon"],
                key=f"mode_{mode_key}",
                help=f"{mode_info['label']}: {mode_info['desc']}"
            ):
                st.session_state.generation_preset = mode_key
                st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)

    # 채팅 입력창
    placeholder_text = "💬 메시지를 입력하세요..."
    current_state = st.session_state.get("current_state")
    if current_state and current_state.get("need_more_info"):
        placeholder_text = "💬 답변을 입력하세요..."

    user_input = st.chat_input(placeholder_text, key=f"chat_input_{st.session_state.input_key}")

    # 입력 처리
    if user_input:
        # 메시지 타입 결정
        message_type = "text"
        if st.session_state.attached_files:
            message_type = "text_with_files"

        # 채팅 히스토리에 추가
        st.session_state.chat_history.append({
            "role": "user",
            "content": user_input,
            "type": message_type,
            "files": [f["name"] for f in st.session_state.attached_files] if st.session_state.attached_files else None
        })

        # 상태 초기화
        st.session_state.prefill_prompt = None
        st.session_state.show_upload_panel = False
        st.session_state.input_key += 1
        st.session_state.pending_input = user_input
        st.session_state.attached_files = []

        # Thread ID 갱신 (새 대화)
        if not current_state or not current_state.get("need_more_info"):
            st.session_state.thread_id = str(uuid.uuid4())

        st.rerun()

    return status_placeholder
