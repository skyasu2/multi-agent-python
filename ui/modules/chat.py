"""
Chat Module - 채팅 메시지 렌더링

Features:
- 파일 첨부 표시
- 타임스탬프
- 메시지 타입별 스타일링
"""
import streamlit as st
from datetime import datetime
from typing import List, Optional


# =============================================================================
# CSS 스타일
# =============================================================================
CHAT_CSS = """
<style>
/* ===== 메시지 메타 정보 ===== */
.msg-meta {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 8px;
    font-size: 0.75rem;
    color: #94a3b8;
}
.msg-time {
    font-weight: 500;
}

/* ===== 파일 첨부 표시 ===== */
.msg-files {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-top: 10px;
    padding-top: 10px;
    border-top: 1px solid rgba(0,0,0,0.06);
}
.msg-file-chip {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 4px 10px;
    background: rgba(99, 102, 241, 0.08);
    border: 1px solid rgba(99, 102, 241, 0.2);
    border-radius: 12px;
    font-size: 0.75rem;
    color: #4f46e5;
    font-weight: 500;
}
.msg-file-chip-icon {
    font-size: 0.85rem;
}

/* ===== 사용자 메시지 스타일 ===== */
.user-msg-content {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 12px 16px;
    border-radius: 18px 18px 4px 18px;
    margin-left: auto;
    max-width: 85%;
}

/* ===== 어시스턴트 메시지 타입별 ===== */
.msg-type-plan {
    background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
    border: 1px solid #6ee7b7;
    border-radius: 12px;
    padding: 16px;
}
.msg-type-guide {
    background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
    border: 1px solid #93c5fd;
    border-radius: 12px;
    padding: 16px;
}
.msg-type-summary {
    background: linear-gradient(135deg, #fefce8 0%, #fef3c7 100%);
    border: 1px solid #fcd34d;
    border-radius: 12px;
    padding: 16px;
}
.msg-type-error {
    background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
    border: 1px solid #fca5a5;
    border-radius: 12px;
    padding: 16px;
}

/* ===== 기획서 전문 Expander ===== */
.plan-expander {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    overflow: hidden;
}
.plan-expander summary {
    padding: 12px 16px;
    background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
    cursor: pointer;
    font-weight: 600;
    color: #334155;
}
.plan-expander summary:hover {
    background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
}
</style>
"""

# 파일 아이콘 매핑
FILE_ICONS = {
    "pdf": "📄", "txt": "📝", "md": "📑", "docx": "📃",
    "png": "🖼️", "jpg": "🖼️", "jpeg": "🖼️", "gif": "🖼️",
    "default": "📎"
}


def get_file_icon(filename: str) -> str:
    """파일 확장자에 따른 아이콘 반환"""
    ext = filename.split(".")[-1].lower() if "." in filename else ""
    return FILE_ICONS.get(ext, FILE_ICONS["default"])


def format_timestamp(timestamp: Optional[str] = None) -> str:
    """타임스탬프 포맷팅"""
    if timestamp:
        try:
            dt = datetime.fromisoformat(timestamp)
            return dt.strftime("%H:%M")
        except (ValueError, TypeError):
            pass
    return datetime.now().strftime("%H:%M")


def render_file_chips(files: List[str]) -> str:
    """파일 칩 HTML 생성"""
    if not files:
        return ""

    chips_html = '<div class="msg-files">'
    for filename in files:
        icon = get_file_icon(filename)
        short_name = filename[:15] + "..." if len(filename) > 15 else filename
        chips_html += f'''
        <span class="msg-file-chip" title="{filename}">
            <span class="msg-file-chip-icon">{icon}</span>
            {short_name}
        </span>
        '''
    chips_html += '</div>'
    return chips_html


def render_chat_message(
    role: str,
    content: str,
    msg_type: str = "text",
    files: Optional[List[str]] = None,
    timestamp: Optional[str] = None
):
    """
    채팅 메시지 렌더링 (개선된 버전)

    Args:
        role: "user" or "assistant"
        content: 메시지 내용
        msg_type: 메시지 유형
            - "text": 일반 텍스트 (기본값)
            - "text_with_files": 파일 첨부된 텍스트
            - "plan": 기획서 완료 알림
            - "plan_content": 기획서 전문 (접힌 상태로 표시)
            - "guide": 후속 액션 안내
            - "summary": 채팅 요약
            - "options": 옵션 선택
            - "error": 에러 메시지
        files: 첨부된 파일 이름 목록
        timestamp: 메시지 타임스탬프
    """
    # CSS 한 번만 적용
    if "chat_css_applied" not in st.session_state:
        st.markdown(CHAT_CSS, unsafe_allow_html=True)
        st.session_state.chat_css_applied = True

    time_str = format_timestamp(timestamp)

    if role == "user":
        with st.chat_message("user"):
            # 메시지 내용
            st.markdown(content)

            # 파일 첨부 표시
            if files:
                st.markdown(render_file_chips(files), unsafe_allow_html=True)

    else:  # assistant
        with st.chat_message("assistant"):
            if msg_type == "plan_content":
                # 기획서 전문은 접힌 상태로 표시
                with st.expander("📄 **생성된 기획서 전문** (클릭하여 펼치기)", expanded=False):
                    st.markdown(content)

            elif msg_type == "error":
                st.markdown(f"""
                <div class="msg-type-error">
                    ⚠️ {content}
                </div>
                """, unsafe_allow_html=True)

            elif msg_type == "plan":
                st.markdown(f"""
                <div class="msg-type-plan">
                    ✅ {content}
                </div>
                """, unsafe_allow_html=True)

            elif msg_type == "guide":
                st.markdown(f"""
                <div class="msg-type-guide">
                    💡 {content}
                </div>
                """, unsafe_allow_html=True)

            elif msg_type == "summary":
                st.markdown(f"""
                <div class="msg-type-summary">
                    📋 {content}
                </div>
                """, unsafe_allow_html=True)

            else:
                # 일반 텍스트
                st.markdown(content)


def render_chat_history(chat_history: list):
    """
    채팅 히스토리 전체 렌더링

    Args:
        chat_history: 채팅 메시지 목록
            각 메시지는 {"role", "content", "type", "files", "timestamp"} 형식
    """
    for msg in chat_history:
        render_chat_message(
            role=msg.get("role", "user"),
            content=msg.get("content", ""),
            msg_type=msg.get("type", "text"),
            files=msg.get("files"),
            timestamp=msg.get("timestamp")
        )
