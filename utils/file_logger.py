"""
PlanCraft - 구조적 JSONL 로깅 시스템

운영 환경에서의 모니터링, 장애 조기 탐지, 디버깅을 위한 구조화된 로그 시스템.

로그 구조:
{
    "timestamp": "ISO8601",
    "level": "INFO|WARNING|ERROR|DEBUG",
    "source": "module.function",
    "event_type": "workflow|agent|hitl|api|error",
    "step": "step_name",
    "data": {...},
    "context": {"thread_id": "...", "agent_id": "..."}
}
"""

import os
import json
import datetime
import traceback
from typing import Any, Optional, Dict

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")


class FileLogger:
    """구조적 JSONL 로깅 시스템"""

    MAX_LOG_FILES = 10  # 최대 로그 파일 개수

    def __init__(self):
        if not os.path.exists(LOG_DIR):
            os.makedirs(LOG_DIR)
        else:
            self._cleanup_old_logs()

        # 실행 시마다 새로운 로그 파일 생성 (시간별)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = os.path.join(LOG_DIR, f"execution_{timestamp}.jsonl")
        self.text_log_file = os.path.join(LOG_DIR, f"execution_{timestamp}.log") # [NEW] 가독성용 로그
        self._context: Dict[str, Any] = {}  # 글로벌 컨텍스트

    def _cleanup_old_logs(self):
        """
        로그 파일이 MAX_LOG_FILES개를 초과하지 않도록 오래된 파일 삭제
        """
        try:
            # .jsonl 및 .log 파일 모두 조회
            all_files = [
                f for f in os.listdir(LOG_DIR)
                if (f.endswith(".jsonl") or f.endswith(".log")) and os.path.isfile(os.path.join(LOG_DIR, f))
            ]

            if len(all_files) < self.MAX_LOG_FILES * 2: # 파일 종류가 2개이므로
                return

            # 수정 시간 기준 정렬
            files_with_time = [
                (f, os.path.getmtime(os.path.join(LOG_DIR, f)))
                for f in all_files
            ]
            files_with_time.sort(key=lambda x: x[1])

            # 삭제 대상 선정
            files_to_delete = len(all_files) - (self.MAX_LOG_FILES * 2)
            
            for i in range(max(0, files_to_delete)):
                file_to_delete = os.path.join(LOG_DIR, files_with_time[i][0])
                try:
                    os.unlink(file_to_delete)
                except Exception as e:
                    print(f"[FileLogger] Failed to delete {file_to_delete}: {e}")

        except Exception as e:
            print(f"[FileLogger] Log cleanup failed: {e}")
        
    def set_context(self, **kwargs):
        """글로벌 컨텍스트 설정 (thread_id, session_id 등)"""
        self._context.update(kwargs)

    def clear_context(self):
        """글로벌 컨텍스트 초기화"""
        self._context = {}

    def log(
        self,
        step: str,
        data: Any,
        level: str = "INFO",
        event_type: str = "workflow",
        source: Optional[str] = None,
        **extra_context
    ):
        """
        구조적 JSONL 로그 기록 + Plain Text 로그 기록
        """
        # 컨텍스트 병합
        context = {**self._context, **extra_context}
        ts_now = datetime.datetime.now()
        ts_iso = ts_now.isoformat()

        # [1] JSONL 기록
        log_entry = {
            "timestamp": ts_iso,
            "level": level,
            "event_type": event_type,
            "source": source,
            "step": step,
            "data": self._serialize(data),
            "context": context if context else None,
        }
        # None 값 제거
        log_entry = {k: v for k, v in log_entry.items() if v is not None}

        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"[FileLogger] JSON logging failed: {e}")

        # [2] Plain Text 기록 (가독성용)
        try:
            # 메시지 추출 (data가 문자열이면 그대로, dict면 message 필드, 아니면 serialize)
            msg_str = ""
            if isinstance(data, str):
                msg_str = data
            elif isinstance(data, dict) and "message" in data:
                msg_str = str(data["message"])
            else:
                msg_str = json.dumps(self._serialize(data), ensure_ascii=False)

            # 포맷: [YYYY-MM-DD HH:MM:SS] [LEVEL] [STEP] Message
            ts_readable = ts_now.strftime("%Y-%m-%d %H:%M:%S")
            text_line = f"[{ts_readable}] [{level:<5}] [{step}] {msg_str}\n"

            # "Service Execution Log" 같은 배너는 이미 포맷팅 되어 있으므로 raw하게 출력
            # (구분: 메시지 내에 개행문자가 있고 시작이 '='로 시작하면 raw 출력 고려)
            if isinstance(data, str) and ("\n" in data or data.strip().startswith("=")):
                text_line = f"{data}\n" # 타임스탬프 없이 원문 그대로 출력 (배너용)
            
            with open(self.text_log_file, "a", encoding="utf-8") as f:
                f.write(text_line)
                
        except Exception as e:
            print(f"[FileLogger] Text logging failed: {e}")

    def info(self, message: str, source: Optional[str] = None, **kwargs):
        """정보 로그 기록"""
        # [IMPROVEMENT] 단순 텍스트는 dict 래핑 없이 바로 저장
        self.log("info", message, level="INFO", source=source, **kwargs)

    def error(
        self,
        message: str,
        source: Optional[str] = None,
        exception: Optional[Exception] = None,
        **kwargs
    ):
        """에러 로그 기록 (스택 트레이스 포함)"""
        data = {"message": message}
        if exception:
            data["exception_type"] = type(exception).__name__
            data["exception_message"] = str(exception)
            data["traceback"] = traceback.format_exc()
        self.log("error", data, level="ERROR", event_type="error", source=source, **kwargs)

    def warning(self, message: str, source: Optional[str] = None, **kwargs):
        """경고 로그 기록"""
        # [IMPROVEMENT] 단순 텍스트는 dict 래핑 없이 바로 저장
        self.log("warning", message, level="WARNING", source=source, **kwargs)

    def debug(self, message: str, source: Optional[str] = None, **kwargs):
        """디버그 로그 기록"""
        # [IMPROVEMENT] 단순 텍스트는 dict 래핑 없이 바로 저장
        self.log("debug", message, level="DEBUG", source=source, **kwargs)

    def agent_start(self, agent_id: str, input_data: Any, **kwargs):
        """에이전트 시작 로그"""
        self.log(
            step=f"agent_{agent_id}_start",
            data={"agent_id": agent_id, "input": self._serialize(input_data)},
            level="INFO",
            event_type="agent",
            **kwargs
        )

    def agent_complete(self, agent_id: str, output_data: Any, duration_ms: int = 0, **kwargs):
        """에이전트 완료 로그"""
        self.log(
            step=f"agent_{agent_id}_complete",
            data={
                "agent_id": agent_id,
                "output_summary": str(output_data)[:500],
                "duration_ms": duration_ms
            },
            level="INFO",
            event_type="agent",
            **kwargs
        )

    def agent_error(self, agent_id: str, error: Exception, **kwargs):
        """에이전트 에러 로그"""
        self.log(
            step=f"agent_{agent_id}_error",
            data={
                "agent_id": agent_id,
                "error_type": type(error).__name__,
                "error_message": str(error),
                "traceback": traceback.format_exc()
            },
            level="ERROR",
            event_type="error",
            **kwargs
        )

    def hitl_interrupt(self, interrupt_id: str, question: str, options: list, **kwargs):
        """HITL 인터럽트 로그"""
        self.log(
            step="hitl_interrupt",
            data={
                "interrupt_id": interrupt_id,
                "question": question,
                "options_count": len(options)
            },
            level="INFO",
            event_type="hitl",
            **kwargs
        )

    def hitl_resume(self, interrupt_id: str, user_response: Any, **kwargs):
        """HITL 재개 로그"""
        self.log(
            step="hitl_resume",
            data={
                "interrupt_id": interrupt_id,
                "response_type": type(user_response).__name__
            },
            level="INFO",
            event_type="hitl",
            **kwargs
        )

    def workflow_start(self, thread_id: str, user_input: str, preset: str, **kwargs):
        """워크플로우 시작 로그"""
        self.set_context(thread_id=thread_id)
        self.log(
            step="workflow_start",
            data={
                "thread_id": thread_id,
                "input_length": len(user_input),
                "preset": preset
            },
            level="INFO",
            event_type="workflow",
            **kwargs
        )

    def workflow_complete(self, thread_id: str, status: str, duration_ms: int = 0, **kwargs):
        """워크플로우 완료 로그"""
        self.log(
            step="workflow_complete",
            data={
                "thread_id": thread_id,
                "status": status,
                "duration_ms": duration_ms
            },
            level="INFO",
            event_type="workflow",
            **kwargs
        )

    def _serialize(self, obj: Any) -> Any:
        """JSON 직렬화 불가능한 객체 처리"""
        if obj is None:
            return None
        if isinstance(obj, dict):
            return {k: self._serialize(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [self._serialize(item) for item in obj]
        if hasattr(obj, "model_dump"):
            return obj.model_dump()
        if hasattr(obj, "dict"):
            return obj.dict()
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()
        if isinstance(obj, Exception):
            return {"type": type(obj).__name__, "message": str(obj)}
        try:
            json.dumps(obj)
            return obj
        except (TypeError, ValueError):
            return str(obj)

# 전역 로거 인스턴스 (필요할 때마다 이 인스턴스를 사용하거나 새로 생성)
# 여기서는 싱글톤처럼 파일 하나에 계속 쓰기 위해 모듈 레벨에서 초기화하지 않고,
# 워크플로우 실행 시마다 생성하거나 관리하는 것이 좋지만,
# 편의상 모듈 로딩 시 파일이 생성되게 하거나, 
# 함수 호출 시 get_logger() 패턴을 사용할 수 있음.
# 간단하게 전역 인스턴스 제공.

_logger_instance = None

def get_file_logger():
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = FileLogger()
    return _logger_instance
