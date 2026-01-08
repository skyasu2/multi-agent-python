"""
Input & Controls Tab - ChatGPT 스타일 채팅 입력 UI

ChatGPT와 유사한 UX를 제공합니다:
- 입력창 좌측 + 버튼으로 파일 업로드
- 파일 선택 시 입력창 위에 미리보기 표시
- 키보드 접근성 및 aria-label 지원
"""
import streamlit as st
from typing import List, Dict, Any
import base64


# =============================================================================
# CSS 스타일 정의 - ChatGPT 스타일
# =============================================================================
CHAT_INPUT_CSS = """
<style>
/* ===== ChatGPT 스타일 + 버튼 ===== */
.chat-plus-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 36px;
    height: 36px;
    border-radius: 50%;
    border: 1px solid #e5e7eb;
    background: #ffffff;
    color: #6b7280;
    cursor: pointer;
    transition: all 0.2s ease;
    font-size: 1.25rem;
    font-weight: 300;
    flex-shrink: 0;
}
.chat-plus-btn:hover {
    background: #f3f4f6;
    color: #374151;
    border-color: #d1d5db;
}
.chat-plus-btn:focus {
    outline: 2px solid #3b82f6;
    outline-offset: 2px;
}
.chat-plus-btn.has-files {
    background: #dbeafe;
    color: #2563eb;
    border-color: #93c5fd;
}

/* ===== 파일 첨부 카드 스타일 (ChatGPT 스타일) ===== */
.file-chip {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 6px 12px;
    background: #f9fafb;
    border: 1px solid #e5e7eb;
    border-radius: 20px;
    font-size: 0.85rem;
    color: #374151;
    max-width: 180px;
    transition: all 0.15s ease;
}
.file-chip:hover {
    background: #f3f4f6;
    border-color: #d1d5db;
}

.file-chip-icon {
    font-size: 1rem;
    flex-shrink: 0;
}

.file-chip-name {
    flex: 1;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    font-weight: 500;
}

.file-chip-remove {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 18px;
    height: 18px;
    border-radius: 50%;
    background: transparent;
    color: #9ca3af;
    cursor: pointer;
    transition: all 0.15s ease;
    border: none;
    font-size: 12px;
    padding: 0;
    line-height: 1;
}
.file-chip-remove:hover {
    background: #fee2e2;
    color: #ef4444;
}
.file-chip-remove:focus {
    outline: 2px solid #ef4444;
    outline-offset: 1px;
}

/* ===== 파일 미리보기 컨테이너 (입력창 위) ===== */
.files-preview-bar {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    padding: 10px 14px;
    background: linear-gradient(to bottom, rgba(255,255,255,0.95), rgba(249,250,251,0.95));
    border-radius: 12px 12px 0 0;
    border: 1px solid #e5e7eb;
    border-bottom: none;
    margin-bottom: -2px;
    backdrop-filter: blur(8px);
}

/* ===== 툴바 버튼 스타일 ===== */
.toolbar-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 36px;
    height: 36px;
    border-radius: 50%;
    border: none;
    background: #f3f4f6;
    color: #6b7280;
    cursor: pointer;
    transition: all 0.2s;
    font-size: 1.1rem;
}
.toolbar-btn:hover {
    background: #e5e7eb;
    color: #374151;
}
.toolbar-btn.active {
    background: #dbeafe;
    color: #2563eb;
}

/* ===== 모드 버튼 스타일 ===== */
div[data-testid="stButton"] button {
    border: none !important;
    background: transparent !important;
    padding: 6px 10px !important;
    box-shadow: none !important;
    color: #6b7280 !important;
    transition: all 0.15s !important;
    border-radius: 8px !important;
}
div[data-testid="stButton"] button:hover {
    background: #f3f4f6 !important;
    color: #374151 !important;
}
div[data-testid="stButton"] button[kind="primary"] {
    color: #2563eb !important;
    background: #dbeafe !important;
}

/* ===== 업로드 패널 스타일 (개선) ===== */
.upload-panel {
    background: white;
    border-radius: 16px;
    padding: 20px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.12);
    border: 1px solid #e5e7eb;
}

.upload-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
}

.upload-title {
    font-size: 1rem;
    font-weight: 600;
    color: #111827;
}

/* ===== 드래그 앤 드롭 영역 ===== */
.drop-zone {
    border: 2px dashed #d1d5db;
    border-radius: 12px;
    padding: 32px;
    text-align: center;
    background: #fafafa;
    transition: all 0.2s;
}
.drop-zone:hover {
    border-color: #9ca3af;
    background: #f3f4f6;
}
.drop-zone.drag-over {
    border-color: #3b82f6;
    background: #eff6ff;
}
.drop-zone-icon {
    font-size: 2.5rem;
    margin-bottom: 8px;
}
.drop-zone-text {
    color: #6b7280;
    font-size: 0.9rem;
}
.drop-zone-hint {
    color: #9ca3af;
    font-size: 0.75rem;
    margin-top: 4px;
}

/* ===== 입력 영역 래퍼 (+ 버튼 통합) ===== */
.chat-input-wrapper {
    display: flex;
    align-items: flex-end;
    gap: 10px;
    padding: 8px;
    background: white;
    border-radius: 24px;
    border: 1px solid #e5e7eb;
    box-shadow: 0 2px 12px rgba(0,0,0,0.08);
}

/* ===== 숨겨진 파일 입력 ===== */
.hidden-file-input {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    border: 0;
}
</style>
"""


# =============================================================================
# 파일 타입별 아이콘 매핑
# =============================================================================
FILE_ICONS = {
    "pdf": "📄",
    "txt": "📝",
    "md": "📑",
    "docx": "📃",
    "doc": "📃",
    "png": "🖼️",
    "jpg": "🖼️",
    "jpeg": "🖼️",
    "gif": "🖼️",
    "default": "📎"
}

# 사용자 요구사항: 텍스트(.txt, .md), PDF(.pdf), 이미지(.png, .jpg)
ALLOWED_EXTENSIONS = {"txt", "md", "pdf", "png", "jpg", "jpeg"}
MAX_FILE_SIZE_MB = 10
MAX_FILES = 5

# 파일 타입별 MIME 타입 매핑 (file input accept 속성용)
MIME_TYPES = {
    "txt": "text/plain",
    "md": "text/markdown",
    "pdf": "application/pdf",
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg"
}


def get_file_icon(filename: str) -> str:
    """파일 확장자에 따른 아이콘 반환"""
    ext = filename.split(".")[-1].lower() if "." in filename else ""
    return FILE_ICONS.get(ext, FILE_ICONS["default"])


def format_file_size(size_bytes: int) -> str:
    """파일 크기를 읽기 쉬운 형식으로 변환"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


def init_file_state():
    """파일 업로드 관련 세션 상태 초기화"""
    if "attached_files" not in st.session_state:
        st.session_state.attached_files = []  # [{name, size, type, content}, ...]
    if "show_upload_panel" not in st.session_state:
        st.session_state.show_upload_panel = False


def render_file_preview_card(file_info: Dict[str, Any], index: int) -> bool:
    """
    개별 파일 미리보기 카드 렌더링
    Returns: True if file should be removed
    """
    icon = get_file_icon(file_info["name"])
    size_str = format_file_size(file_info["size"])

    col1, col2 = st.columns([5, 1])
    with col1:
        st.markdown(f"""
        <div class="file-card">
            <span class="file-icon">{icon}</span>
            <div class="file-info">
                <div class="file-name" title="{file_info['name']}">{file_info['name']}</div>
                <div class="file-meta">{size_str}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        if st.button("✕", key=f"remove_file_{index}", help="파일 제거"):
            return True
    return False


def render_attached_files_preview():
    """첨부된 파일들 미리보기 영역"""
    if not st.session_state.attached_files:
        return

    st.markdown('<div class="files-preview-container">', unsafe_allow_html=True)

    files_to_remove = []
    cols = st.columns(min(len(st.session_state.attached_files), 3))

    for idx, file_info in enumerate(st.session_state.attached_files):
        col_idx = idx % 3
        with cols[col_idx]:
            icon = get_file_icon(file_info["name"])
            size_str = format_file_size(file_info["size"])

            # 파일 카드와 삭제 버튼
            c1, c2 = st.columns([4, 1])
            with c1:
                st.markdown(f"**{icon} {file_info['name'][:15]}{'...' if len(file_info['name']) > 15 else ''}**")
                st.caption(size_str)
            with c2:
                if st.button("✕", key=f"rm_{idx}"):
                    files_to_remove.append(idx)

    st.markdown('</div>', unsafe_allow_html=True)

    # 삭제 처리
    if files_to_remove:
        for idx in sorted(files_to_remove, reverse=True):
            st.session_state.attached_files.pop(idx)
        # uploaded_content 업데이트
        _update_uploaded_content()
        st.rerun()


def _update_uploaded_content():
    """attached_files를 기반으로 uploaded_content 업데이트"""
    if not st.session_state.attached_files:
        st.session_state.uploaded_content = None
        return

    # 텍스트 파일들의 내용을 결합
    contents = []
    for f in st.session_state.attached_files:
        if f.get("content"):
            contents.append(f"[파일: {f['name']}]\n{f['content']}")

    st.session_state.uploaded_content = "\n\n---\n\n".join(contents) if contents else None


def render_upload_panel():
    """파일 업로드 패널 (ChatGPT 스타일)"""
    st.markdown('<div id="upload-panel-target"></div>', unsafe_allow_html=True)

    # 헤더
    col_title, col_close = st.columns([4, 1])
    with col_title:
        st.markdown("##### 📁 파일 첨부")
    with col_close:
        if st.button("✕", key="close_panel"):
            st.session_state.show_upload_panel = False
            st.rerun()

    # 파일 업로더 (다중 파일)
    uploaded_files = st.file_uploader(
        "파일을 드래그하거나 클릭하여 선택",
        type=list(ALLOWED_EXTENSIONS),
        accept_multiple_files=True,
        key="multi_file_uploader",
        label_visibility="collapsed"
    )

    # 안내 문구
    st.caption(f"📌 지원 형식: {', '.join(ALLOWED_EXTENSIONS).upper()} | 최대 {MAX_FILE_SIZE_MB}MB, {MAX_FILES}개")

    if uploaded_files:
        new_files_added = False

        for uploaded_file in uploaded_files:
            # 중복 체크
            existing_names = [f["name"] for f in st.session_state.attached_files]
            if uploaded_file.name in existing_names:
                continue

            # 파일 수 제한
            if len(st.session_state.attached_files) >= MAX_FILES:
                st.warning(f"최대 {MAX_FILES}개 파일까지 첨부 가능합니다.")
                break

            # 크기 체크
            file_size = len(uploaded_file.getbuffer())
            if file_size > MAX_FILE_SIZE_MB * 1024 * 1024:
                st.error(f"'{uploaded_file.name}' 파일이 너무 큽니다.")
                continue

            # 파일 읽기
            ext = uploaded_file.name.split(".")[-1].lower()
            content = None

            if ext in {"txt", "md"}:
                content = uploaded_file.read().decode("utf-8", errors="ignore")[:50000]
            elif ext == "pdf":
                # PDF는 내용 추출 불가 시 메타데이터만
                content = f"[PDF 파일: {uploaded_file.name}]"
            elif ext in {"png", "jpg", "jpeg", "gif"}:
                # 이미지는 base64 인코딩 (향후 멀티모달용)
                content = f"[이미지 파일: {uploaded_file.name}]"
            elif ext == "docx":
                content = f"[DOCX 파일: {uploaded_file.name}]"

            # 파일 정보 저장
            st.session_state.attached_files.append({
                "name": uploaded_file.name,
                "size": file_size,
                "type": ext,
                "content": content
            })
            new_files_added = True

        if new_files_added:
            _update_uploaded_content()
            st.success(f"✅ {len(uploaded_files)}개 파일이 추가되었습니다.")

    # 첨부된 파일 목록 표시
    if st.session_state.attached_files:
        st.markdown("---")
        st.markdown("**첨부된 파일:**")

        for idx, f in enumerate(st.session_state.attached_files):
            icon = get_file_icon(f["name"])
            c1, c2, c3 = st.columns([1, 4, 1])
            with c1:
                st.markdown(f"<span style='font-size:1.5rem'>{icon}</span>", unsafe_allow_html=True)
            with c2:
                st.markdown(f"**{f['name']}**")
                st.caption(format_file_size(f["size"]))
            with c3:
                if st.button("🗑️", key=f"del_{idx}", help="삭제"):
                    st.session_state.attached_files.pop(idx)
                    _update_uploaded_content()
                    st.rerun()

        # 모두 삭제 버튼
        if st.button("🗑️ 모두 삭제", key="clear_all_files"):
            st.session_state.attached_files = []
            st.session_state.uploaded_content = None
            st.rerun()


def render_file_upload():
    """
    파일 업로드 영역 렌더링 (호환성 유지용)

    Note: 파일 업로드 UI가 render_input_area() 내에 통합되었습니다.
    이 함수는 기존 app.py와의 호환성을 위해 유지됩니다.
    """
    # 파일 업로드 기능이 render_input_area()의 + 버튼으로 통합됨
    # 별도 렌더링 불필요
    pass


def render_file_chips():
    """
    ChatGPT 스타일 파일 칩 미리보기 렌더링
    입력창 바로 위에 첨부된 파일들을 칩 형태로 표시
    """
    if not st.session_state.attached_files:
        return

    # 파일 칩 컨테이너
    st.markdown('<div id="file-chips-container" class="files-preview-bar">', unsafe_allow_html=True)

    files_to_remove = []
    cols = st.columns(min(len(st.session_state.attached_files), 4))

    for idx, f in enumerate(st.session_state.attached_files):
        with cols[idx % 4]:
            icon = get_file_icon(f["name"])
            short_name = f["name"][:15] + "..." if len(f["name"]) > 15 else f["name"]
            size_str = format_file_size(f["size"])

            # ChatGPT 스타일 파일 칩
            st.markdown(f"""
            <div class="file-chip" title="{f['name']} ({size_str})" role="listitem">
                <span class="file-chip-icon" aria-hidden="true">{icon}</span>
                <span class="file-chip-name">{short_name}</span>
            </div>
            """, unsafe_allow_html=True)

            # 삭제 버튼 (접근성 포함)
            if st.button(
                "✕",
                key=f"chip_rm_{idx}",
                help=f"{f['name']} 파일 제거",
            ):
                files_to_remove.append(idx)

    st.markdown('</div>', unsafe_allow_html=True)

    # 삭제 처리
    if files_to_remove:
        for idx in sorted(files_to_remove, reverse=True):
            st.session_state.attached_files.pop(idx)
        _update_uploaded_content()
        st.rerun()


def render_input_area():
    """
    채팅 입력 영역 렌더링 (ChatGPT 스타일)

    레이아웃:
    ┌─────────────────────────────────────────────────┐
    │  📎 file1.txt  📄 doc.pdf  🖼️ image.png  [x]   │  ← 파일 미리보기 (조건부)
    ├─────────────────────────────────────────────────┤
    │ [+]  │  [메시지를 입력하세요...]          [↵]  │  ← 입력 영역
    └─────────────────────────────────────────────────┘
    │ ⚡ ⚖️ 💎                                        │  ← 모드 선택
    └─────────────────────────────────────────────────┘

    접근성:
    - + 버튼: aria-label="파일 첨부", tabindex 지원
    - 파일 칩: role="listitem", 삭제 버튼에 aria-label
    - 키보드 네비게이션 지원
    """
    # CSS 적용
    st.markdown(CHAT_INPUT_CSS, unsafe_allow_html=True)

    # 상태 초기화
    init_file_state()

    # 상태 표시 Placeholder
    status_placeholder = st.empty()

    # ==========================================================================
    # 첨부 파일 미리보기 (입력창 위, ChatGPT 스타일 칩)
    # ==========================================================================
    render_file_chips()

    # ==========================================================================
    # 업로드 패널 (토글 - Streamlit file_uploader 사용)
    # ==========================================================================
    if st.session_state.show_upload_panel:
        with st.container():
            render_upload_panel()

    # ==========================================================================
    # 입력 영역: + 버튼 + 채팅 입력창
    # ==========================================================================
    # 마커 (JavaScript에서 참조)
    st.markdown('<span id="input-wrapper-target" style="display:none;"></span>', unsafe_allow_html=True)

    col_plus, col_input = st.columns([0.08, 0.92])

    # [+] 버튼 (ChatGPT 스타일)
    with col_plus:
        file_count = len(st.session_state.attached_files)
        btn_class = "has-files" if file_count > 0 else ""
        btn_icon = "✕" if st.session_state.show_upload_panel else "+"
        btn_label = "파일 패널 닫기" if st.session_state.show_upload_panel else "파일 첨부"

        # 버튼 + 접근성
        if st.button(
            btn_icon,
            key="btn_attach_plus",
            help=btn_label,
            type="secondary"
        ):
            st.session_state.show_upload_panel = not st.session_state.show_upload_panel
            st.rerun()

        # 파일 개수 배지
        if file_count > 0 and not st.session_state.show_upload_panel:
            st.markdown(
                f'<span style="position:absolute;top:-4px;right:-4px;background:#2563eb;color:white;'
                f'border-radius:50%;width:16px;height:16px;font-size:10px;display:flex;'
                f'align-items:center;justify-content:center;">{file_count}</span>',
                unsafe_allow_html=True
            )

    # 채팅 입력창
    with col_input:
        placeholder = "메시지를 입력하세요..."
        if (st.session_state.get("current_state") or {}).get("need_more_info"):
            placeholder = "답변을 입력하세요..."

        user_input = st.chat_input(
            placeholder,
            key=f"chat_input_{st.session_state.input_key}"
        )

    # ==========================================================================
    # 모드 선택 툴바
    # ==========================================================================
    st.markdown('<span id="mode-toolbar-target" style="display:none;"></span>', unsafe_allow_html=True)
    col_spacer, col_m1, col_m2, col_m3, col_spacer2 = st.columns([3, 0.6, 0.6, 0.6, 3])

    MODE_CONFIG = {
        "speed": ("⚡", "Speed", "빠른 응답 (gpt-4o-mini)"),
        "balanced": ("⚖️", "Balanced", "균형 모드 (gpt-4o)"),
        "quality": ("💎", "Quality", "고품질 분석 (gpt-4o + RAG)")
    }

    current_mode = st.session_state.get("generation_preset", "balanced")

    for col, mode in zip([col_m1, col_m2, col_m3], ["speed", "balanced", "quality"]):
        icon, label, desc = MODE_CONFIG[mode]
        with col:
            is_active = (current_mode == mode)
            btn_type = "primary" if is_active else "secondary"
            if st.button(
                icon,
                key=f"mode_{mode}",
                type=btn_type,
                help=f"{label}: {desc}"
            ):
                st.session_state.generation_preset = mode
                st.rerun()

    # ==========================================================================
    # JavaScript: ChatGPT 스타일 레이아웃 적용
    # ==========================================================================
    import streamlit.components.v1 as components

    js_code = """
    <script>
    (function() {
        // ChatGPT 스타일: 입력창 좌측에 + 버튼 배치
        const inputWrapperStyle = {
            display: 'flex',
            alignItems: 'flex-end',
            gap: '8px',
            position: 'fixed',
            bottom: '20px',
            left: '50%',
            transform: 'translateX(-50%)',
            width: '720px',
            maxWidth: '92%',
            zIndex: '999',
            padding: '0 8px'
        };

        // + 버튼 스타일
        const plusBtnStyle = {
            width: '40px',
            height: '40px',
            borderRadius: '50%',
            border: '1px solid #e5e7eb',
            background: '#ffffff',
            color: '#6b7280',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '1.5rem',
            fontWeight: '300',
            flexShrink: '0',
            transition: 'all 0.2s ease',
            marginBottom: '8px'
        };

        // 파일 미리보기 바 스타일
        const fileChipsStyle = {
            position: 'fixed',
            bottom: '80px',
            left: '50%',
            transform: 'translateX(-50%)',
            width: '680px',
            maxWidth: '88%',
            zIndex: '998'
        };

        // 모드 툴바 스타일
        const modeToolbarStyle = {
            position: 'fixed',
            bottom: '75px',
            left: '50%',
            transform: 'translateX(-50%)',
            display: 'flex',
            gap: '8px',
            zIndex: '997'
        };

        // 업로드 패널 스타일
        const uploadPanelStyle = {
            position: 'fixed',
            bottom: '120px',
            left: '50%',
            transform: 'translateX(-50%)',
            width: '680px',
            maxWidth: '88%',
            background: 'white',
            padding: '20px',
            borderRadius: '16px',
            boxShadow: '0 8px 32px rgba(0,0,0,0.18)',
            zIndex: '1000',
            border: '1px solid #e5e7eb'
        };

        function applyStyles() {
            const doc = window.parent.document;

            // 입력 영역 래퍼
            const inputWrapper = doc.getElementById('input-wrapper-target');
            if (inputWrapper) {
                const container = inputWrapper.closest('[data-testid="stHorizontalBlock"]');
                if (container && !container.dataset.inputStyled) {
                    Object.assign(container.style, inputWrapperStyle);
                    container.dataset.inputStyled = 'true';

                    // + 버튼 스타일 적용
                    const plusBtn = container.querySelector('button');
                    if (plusBtn) {
                        Object.assign(plusBtn.style, plusBtnStyle);
                        plusBtn.setAttribute('aria-label', '파일 첨부');
                        plusBtn.setAttribute('tabindex', '0');
                    }
                }
            }

            // 파일 칩 컨테이너
            const fileChips = doc.getElementById('file-chips-container');
            if (fileChips) {
                const container = fileChips.closest('[data-testid="stVerticalBlock"]');
                if (container) {
                    Object.assign(container.style, fileChipsStyle);
                }
            }

            // 모드 툴바
            const modeToolbar = doc.getElementById('mode-toolbar-target');
            if (modeToolbar) {
                const container = modeToolbar.closest('[data-testid="stHorizontalBlock"]');
                if (container && !container.dataset.modeStyled) {
                    Object.assign(container.style, modeToolbarStyle);
                    container.dataset.modeStyled = 'true';
                }
            }

            // 업로드 패널
            const uploadPanel = doc.getElementById('upload-panel-target');
            if (uploadPanel) {
                const container = uploadPanel.closest('[data-testid="stVerticalBlock"]');
                if (container) {
                    Object.assign(container.style, uploadPanelStyle);
                }
            }

            // 채팅 입력창 자동 포커스
            const input = doc.querySelector('textarea[data-testid="stChatInputTextArea"]');
            if (input && !input.dataset.focused) {
                input.focus();
                input.dataset.focused = 'true';
            }

            // 접근성: + 버튼 키보드 이벤트
            const allPlusBtns = doc.querySelectorAll('button[aria-label="파일 첨부"]');
            allPlusBtns.forEach(btn => {
                if (!btn.dataset.keyHandler) {
                    btn.addEventListener('keydown', (e) => {
                        if (e.key === 'Enter' || e.key === ' ') {
                            e.preventDefault();
                            btn.click();
                        }
                    });
                    btn.dataset.keyHandler = 'true';
                }
            });
        }

        // 초기 적용 및 주기적 업데이트
        setTimeout(applyStyles, 100);
        setInterval(applyStyles, 500);
    })();
    </script>
    """
    components.html(js_code, height=0)

    # ==========================================================================
    # 입력 처리
    # ==========================================================================
    if user_input:
        # 파일 첨부 정보와 함께 메시지 구성
        message_content = user_input
        message_type = "text"

        if st.session_state.attached_files:
            file_names = [f["name"] for f in st.session_state.attached_files]
            message_type = "text_with_files"

        # 채팅 히스토리에 추가
        st.session_state.chat_history.append({
            "role": "user",
            "content": message_content,
            "type": message_type,
            "files": [f["name"] for f in st.session_state.attached_files] if st.session_state.attached_files else None
        })

        # 상태 초기화
        st.session_state.show_upload_panel = False
        st.session_state.prefill_prompt = None
        st.session_state.input_key += 1
        st.session_state.pending_input = user_input

        # 파일은 메시지 전송 후 초기화
        st.session_state.attached_files = []

        # Thread ID 갱신 (새 대화)
        if not (st.session_state.get("current_state") or {}).get("need_more_info"):
            import uuid
            st.session_state.thread_id = str(uuid.uuid4())

        st.rerun()

    return status_placeholder
