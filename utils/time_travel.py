"""
PlanCraft Time-Travel Utility

LangGraph Checkpointer를 활용한 상태 스냅샷 및 롤백 기능을 제공합니다.

기능:
    - get_state_history: 전체 실행 이력 조회
    - get_state_at_step: 특정 단계의 상태 조회
    - rollback_to_step: 특정 단계로 롤백
    - replay_from_step: 특정 단계부터 재실행
    - compare_states: 두 상태 비교

사용 예시:
    from utils.time_travel import TimeTravel

    tt = TimeTravel(app, thread_id="my_thread")

    # 실행 이력 조회
    history = tt.get_state_history()

    # 특정 단계로 롤백
    tt.rollback_to_step(step_index=2)

    # 상태 비교
    diff = tt.compare_states(step1=1, step2=3)
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime


@dataclass
class StateSnapshot:
    """상태 스냅샷 데이터 클래스"""
    checkpoint_id: str
    step_name: str
    timestamp: str
    state: Dict[str, Any]
    metadata: Dict[str, Any]


class TimeTravel:
    """
    LangGraph 워크플로우의 Time-Travel 기능을 제공하는 클래스

    Checkpointer를 통해 저장된 상태 이력을 조회하고,
    특정 시점으로 롤백하거나 재실행할 수 있습니다.
    """

    def __init__(self, app, thread_id: str = "default_thread"):
        """
        Args:
            app: 컴파일된 LangGraph 워크플로우 (compile() 결과)
            thread_id: 스레드 식별자
        """
        self.app = app
        self.thread_id = thread_id
        self.config = {"configurable": {"thread_id": thread_id}}

    def get_current_state(self) -> Optional[Dict[str, Any]]:
        """
        현재 상태 조회

        Returns:
            현재 워크플로우 상태 (없으면 None)
        """
        try:
            snapshot = self.app.get_state(self.config)
            if snapshot and snapshot.values:
                return dict(snapshot.values)
            return None
        except Exception as e:
            print(f"[TimeTravel] 현재 상태 조회 실패: {e}")
            return None

    def get_state_history(self, limit: int = 50) -> List[StateSnapshot]:
        """
        전체 실행 이력 조회

        Args:
            limit: 최대 조회 개수

        Returns:
            StateSnapshot 리스트 (최신순)
        """
        snapshots = []
        try:
            # LangGraph의 get_state_history 사용
            for i, state_snapshot in enumerate(self.app.get_state_history(self.config)):
                if i >= limit:
                    break

                state = dict(state_snapshot.values) if state_snapshot.values else {}
                step_name = state.get("current_step", "unknown")

                # step_history에서 타임스탬프 추출
                step_history = state.get("step_history", [])
                timestamp = ""
                if step_history:
                    last_step = step_history[-1] if step_history else {}
                    timestamp = last_step.get("timestamp", "")

                snapshots.append(StateSnapshot(
                    checkpoint_id=state_snapshot.config.get("configurable", {}).get("checkpoint_id", f"step_{i}"),
                    step_name=step_name,
                    timestamp=timestamp or datetime.now().isoformat(),
                    state=state,
                    metadata={
                        "next": list(state_snapshot.next) if state_snapshot.next else [],
                        "tasks": len(state_snapshot.tasks) if state_snapshot.tasks else 0
                    }
                ))

        except Exception as e:
            print(f"[TimeTravel] 이력 조회 실패: {e}")

        return snapshots

    def get_state_at_step(self, step_index: int) -> Optional[StateSnapshot]:
        """
        특정 단계의 상태 조회

        Args:
            step_index: 단계 인덱스 (0부터 시작, 0이 가장 최신)

        Returns:
            해당 단계의 StateSnapshot (없으면 None)
        """
        history = self.get_state_history(limit=step_index + 1)
        if step_index < len(history):
            return history[step_index]
        return None

    def get_state_by_checkpoint_id(self, checkpoint_id: str) -> Optional[StateSnapshot]:
        """
        체크포인트 ID로 상태 조회

        Args:
            checkpoint_id: 체크포인트 식별자

        Returns:
            해당 체크포인트의 StateSnapshot (없으면 None)
        """
        try:
            config_with_checkpoint = {
                "configurable": {
                    "thread_id": self.thread_id,
                    "checkpoint_id": checkpoint_id
                }
            }
            snapshot = self.app.get_state(config_with_checkpoint)
            if snapshot and snapshot.values:
                state = dict(snapshot.values)
                return StateSnapshot(
                    checkpoint_id=checkpoint_id,
                    step_name=state.get("current_step", "unknown"),
                    timestamp=datetime.now().isoformat(),
                    state=state,
                    metadata={}
                )
        except Exception as e:
            print(f"[TimeTravel] 체크포인트 조회 실패: {e}")
        return None

    def rollback_to_step(self, step_index: int) -> bool:
        """
        특정 단계로 롤백

        해당 단계의 상태를 복원하고, 이후 상태를 무효화합니다.

        Args:
            step_index: 롤백할 단계 인덱스

        Returns:
            성공 여부
        """
        try:
            history = self.get_state_history(limit=step_index + 1)
            if step_index >= len(history):
                print(f"[TimeTravel] 유효하지 않은 step_index: {step_index}")
                return False

            target_snapshot = history[step_index]

            # LangGraph의 update_state를 사용하여 상태 복원
            # 참고: 실제 롤백은 checkpoint_id 기반으로 수행
            config_with_checkpoint = {
                "configurable": {
                    "thread_id": self.thread_id,
                    "checkpoint_id": target_snapshot.checkpoint_id
                }
            }

            # 상태 업데이트 (롤백 마커 추가)
            rollback_marker = {
                "step": "rollback",
                "status": "ROLLBACK",
                "summary": f"Rolled back to step: {target_snapshot.step_name}",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "target_checkpoint": target_snapshot.checkpoint_id
            }

            current_history = target_snapshot.state.get("step_history", [])
            updated_history = current_history + [rollback_marker]

            self.app.update_state(
                config_with_checkpoint,
                {"step_history": updated_history}
            )

            print(f"[TimeTravel] 롤백 완료: {target_snapshot.step_name} (checkpoint: {target_snapshot.checkpoint_id})")
            return True

        except Exception as e:
            print(f"[TimeTravel] 롤백 실패: {e}")
            return False

    def replay_from_step(
        self,
        step_index: int,
        modified_input: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        특정 단계부터 재실행

        Args:
            step_index: 시작할 단계 인덱스
            modified_input: 수정된 입력 (선택적)

        Returns:
            최종 실행 결과 (실패 시 None)
        """
        try:
            history = self.get_state_history(limit=step_index + 1)
            if step_index >= len(history):
                print(f"[TimeTravel] 유효하지 않은 step_index: {step_index}")
                return None

            target_snapshot = history[step_index]

            # 체크포인트 기반 config 설정
            replay_config = {
                "configurable": {
                    "thread_id": self.thread_id,
                    "checkpoint_id": target_snapshot.checkpoint_id
                }
            }

            # 수정된 입력이 있으면 상태 업데이트
            if modified_input:
                self.app.update_state(replay_config, modified_input)

            # 재실행 (None 입력으로 현재 상태에서 계속)
            result = self.app.invoke(None, config=replay_config)

            print(f"[TimeTravel] 재실행 완료: {target_snapshot.step_name}부터")
            return result

        except Exception as e:
            print(f"[TimeTravel] 재실행 실패: {e}")
            return None

    def compare_states(
        self,
        step1: int,
        step2: int
    ) -> Dict[str, Any]:
        """
        두 상태 비교

        Args:
            step1: 첫 번째 단계 인덱스
            step2: 두 번째 단계 인덱스

        Returns:
            차이점 딕셔너리 {field: {"before": ..., "after": ...}}
        """
        snapshot1 = self.get_state_at_step(step1)
        snapshot2 = self.get_state_at_step(step2)

        if not snapshot1 or not snapshot2:
            return {"error": "하나 이상의 스냅샷을 찾을 수 없습니다"}

        diff = {}
        state1 = snapshot1.state
        state2 = snapshot2.state

        # 모든 키 수집
        all_keys = set(state1.keys()) | set(state2.keys())

        for key in all_keys:
            val1 = state1.get(key)
            val2 = state2.get(key)

            # 값이 다른 경우만 기록
            if val1 != val2:
                diff[key] = {
                    "step1_value": self._summarize_value(val1),
                    "step2_value": self._summarize_value(val2),
                    "step1_name": snapshot1.step_name,
                    "step2_name": snapshot2.step_name
                }

        return diff

    def _summarize_value(self, value: Any, max_length: int = 100) -> str:
        """값을 요약 문자열로 변환"""
        if value is None:
            return "None"
        if isinstance(value, str):
            if len(value) > max_length:
                return f"{value[:max_length]}... ({len(value)} chars)"
            return value
        if isinstance(value, (list, tuple)):
            return f"[{len(value)} items]"
        if isinstance(value, dict):
            return f"{{...}} ({len(value)} keys)"
        return str(value)[:max_length]

    def get_step_summary(self) -> List[Dict[str, Any]]:
        """
        실행 단계 요약 조회 (UI 표시용)

        Returns:
            단계별 요약 리스트
        """
        history = self.get_state_history()
        summaries = []

        for i, snapshot in enumerate(history):
            step_history = snapshot.state.get("step_history", [])
            last_step_info = step_history[-1] if step_history else {}

            summaries.append({
                "index": i,
                "checkpoint_id": snapshot.checkpoint_id,
                "step_name": snapshot.step_name,
                "timestamp": snapshot.timestamp,
                "status": last_step_info.get("status", "UNKNOWN"),
                "summary": last_step_info.get("summary", ""),
                "can_rollback": True,
                "can_replay": True
            })

        return summaries


# =============================================================================
# 편의 함수
# =============================================================================

def create_time_travel(thread_id: str = "default_thread") -> TimeTravel:
    """
    TimeTravel 인스턴스 생성 헬퍼

    Args:
        thread_id: 스레드 식별자

    Returns:
        TimeTravel 인스턴스
    """
    from graph.workflow import app
    return TimeTravel(app, thread_id)


def get_execution_timeline(thread_id: str = "default_thread") -> List[Dict[str, Any]]:
    """
    실행 타임라인 조회 (간편 함수)

    Args:
        thread_id: 스레드 식별자

    Returns:
        타임라인 데이터 리스트
    """
    tt = create_time_travel(thread_id)
    return tt.get_step_summary()


def rollback_workflow(thread_id: str, step_index: int) -> bool:
    """
    워크플로우 롤백 (간편 함수)

    Args:
        thread_id: 스레드 식별자
        step_index: 롤백할 단계 인덱스

    Returns:
        성공 여부
    """
    tt = create_time_travel(thread_id)
    return tt.rollback_to_step(step_index)
