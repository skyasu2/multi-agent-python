"""Workflow Service - Business logic layer wrapping run_plancraft"""
import uuid
import asyncio
from typing import Optional, Dict, Any

from api.schemas.workflow import (
    WorkflowRunResponse,
    WorkflowStatus,
    WorkflowStatusResponse,
)


class WorkflowService:
    """Workflow business logic service"""

    async def run(
        self,
        user_input: str,
        file_content: Optional[str] = None,
        generation_preset: str = "balanced",
        thread_id: Optional[str] = None,
        refine_count: int = 0,
        previous_plan: Optional[str] = None,
    ) -> WorkflowRunResponse:
        """Execute workflow"""
        from graph.workflow import run_plancraft

        if not thread_id:
            thread_id = str(uuid.uuid4())

        # run_plancraft is synchronous, use asyncio.to_thread
        result = await asyncio.to_thread(
            run_plancraft,
            user_input=user_input,
            file_content=file_content,
            generation_preset=generation_preset,
            thread_id=thread_id,
            refine_count=refine_count,
            previous_plan=previous_plan,
        )

        return self._convert_to_response(thread_id, result)

    async def resume(
        self,
        thread_id: str,
        resume_data: Dict[str, Any],
    ) -> WorkflowRunResponse:
        """Resume HITL interrupt"""
        from graph.workflow import run_plancraft

        result = await asyncio.to_thread(
            run_plancraft,
            user_input="",  # Not needed for resume
            thread_id=thread_id,
            resume_command={"resume": resume_data},
        )

        return self._convert_to_response(thread_id, result)

    async def get_status(self, thread_id: str) -> Optional[WorkflowStatusResponse]:
        """Get workflow status"""
        from graph.workflow import app

        config = {"configurable": {"thread_id": thread_id}}

        try:
            snapshot = app.get_state(config)
        except Exception:
            return None

        if not snapshot or not snapshot.values:
            return None

        state = snapshot.values
        has_interrupt = bool(snapshot.next and snapshot.tasks)

        return WorkflowStatusResponse(
            thread_id=thread_id,
            status=self._determine_status(state, has_interrupt),
            current_step=state.get("current_step"),
            step_history=state.get("step_history", []),
            has_pending_interrupt=has_interrupt,
        )

    def _convert_to_response(self, thread_id: str, result: dict) -> WorkflowRunResponse:
        """Convert result dict to WorkflowRunResponse"""
        interrupt = result.get("__interrupt__")

        if interrupt:
            status = WorkflowStatus.INTERRUPTED
        elif result.get("error"):
            status = WorkflowStatus.FAILED
        elif result.get("final_output"):
            status = WorkflowStatus.COMPLETED
        else:
            status = WorkflowStatus.RUNNING

        return WorkflowRunResponse(
            thread_id=thread_id,
            status=status,
            final_output=result.get("final_output"),
            chat_summary=result.get("chat_summary"),
            interrupt=interrupt,
            analysis=result.get("analysis"),
            step_history=result.get("step_history", []),
            error=result.get("error"),
        )

    def _determine_status(self, state: dict, has_interrupt: bool) -> WorkflowStatus:
        """Determine workflow status from state"""
        if has_interrupt:
            return WorkflowStatus.INTERRUPTED
        if state.get("error"):
            return WorkflowStatus.FAILED
        if state.get("final_output"):
            return WorkflowStatus.COMPLETED
        return WorkflowStatus.RUNNING
