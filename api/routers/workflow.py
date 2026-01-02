"""Workflow API Router"""
from fastapi import APIRouter, HTTPException

from api.schemas.workflow import (
    WorkflowRunRequest,
    WorkflowResumeRequest,
    WorkflowRunResponse,
    WorkflowStatusResponse,
)
from api.services.workflow_service import WorkflowService

router = APIRouter(prefix="/api/workflow", tags=["workflow"])


@router.post("/run", response_model=WorkflowRunResponse)
async def run_workflow(request: WorkflowRunRequest):
    """
    Execute PlanCraft workflow

    - Start new session or reuse existing session
    - Returns interrupt payload in interrupt field when HITL is triggered
    """
    service = WorkflowService()
    result = await service.run(
        user_input=request.user_input,
        file_content=request.file_content,
        generation_preset=request.generation_preset,
        thread_id=request.thread_id,
        refine_count=request.refine_count,
        previous_plan=request.previous_plan,
    )
    return result


@router.post("/resume", response_model=WorkflowRunResponse)
async def resume_workflow(request: WorkflowResumeRequest):
    """
    Resume HITL interrupt

    - Continue workflow with user response
    """
    service = WorkflowService()
    result = await service.resume(
        thread_id=request.thread_id,
        resume_data=request.resume_data,
    )
    return result


@router.get("/status/{thread_id}", response_model=WorkflowStatusResponse)
async def get_workflow_status(thread_id: str):
    """
    Get workflow status

    - Current step, history, interrupt pending status
    """
    service = WorkflowService()
    result = await service.get_status(thread_id)
    if not result:
        raise HTTPException(status_code=404, detail="Thread not found")
    return result
