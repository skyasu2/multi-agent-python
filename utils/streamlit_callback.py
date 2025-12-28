from typing import Any, Dict, List, Optional
from uuid import UUID
from langchain_core.callbacks import BaseCallbackHandler
import streamlit as st

class StreamlitStatusCallback(BaseCallbackHandler):
    """
    LangChain/LangGraph 실행 과정을 Streamlit의 st.status 컨테이너에 실시간으로 출력하는 콜백 핸들러
    """
    def __init__(self, status_container):
        self.status = status_container
        self.last_tool = None

    def on_chain_start(
        self, serialized: Dict[str, Any], inputs: Dict[str, Any], **kwargs: Any
    ) -> None:
        """체인(Workflow) 시작 시"""
        # 최상위 체인보다는 내부 노드 진입을 감지하는 것이 더 중요하므로 여기서는 패스
        pass

    def on_llm_start(
        self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any
    ) -> None:
        """LLM 생성 시작 시"""
        self.status.write("🧠 AI가 생각하고 있습니다...")

    def on_tool_start(
        self, serialized: Dict[str, Any], input_str: str, **kwargs: Any
    ) -> None:
        """도구(Tool) 실행 시작 시"""
        tool_name = serialized.get("name", "Unknown Tool")
        self.last_tool = tool_name
        
        icon = "🔧"
        if "search" in tool_name.lower():
            icon = "🌐"
        elif "read" in tool_name.lower():
            icon = "📖"
            
        self.status.write(f"{icon} **{tool_name}** 도구를 사용 중입니다...")

    def on_tool_end(self, output: str, **kwargs: Any) -> None:
        """도구 실행 완료 시"""
        if self.last_tool:
            self.status.write(f"✅ {self.last_tool} 완료")
            self.last_tool = None

    def on_agent_action(self, action: Any, **kwargs: Any) -> Any:
        """에이전트가 행동을 결정했을 때"""
        self.status.write(f"🤔 에이전트 결정: `{action.tool}`")

    def custom_log(self, message: str, icon: str = "ℹ️"):
        """사용자 정의 로그 출력 (워크플로우 노드에서 직접 호출용)"""
        self.status.write(f"{icon} {message}")
