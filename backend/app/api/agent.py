"""API endpoints for the multi-agent coaching runtime."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from agents.orchestrator import LearningOrchestrator
from app.core.auth import CurrentUser, get_current_user
from app.models.agent import (
    AgentDeleteResponse,
    AgentEventResponse,
    AgentProjectLatestSessionResponse,
    AgentProjectSummary,
    AgentSessionCreateRequest,
    AgentSessionResponse,
    AgentSessionStateResponse,
    AgentTurnBody,
    AgentTurnRequest,
)


router = APIRouter(prefix="/api/agent", tags=["Agent"])
orchestrator = LearningOrchestrator()


def _quota_http(exc: Exception) -> HTTPException | None:
    msg = str(exc)
    if msg.startswith("Guest accounts"):
        return HTTPException(status_code=403, detail=msg)
    return None


@router.post("/sessions", response_model=AgentSessionResponse)
async def create_agent_session(
    request: AgentSessionCreateRequest,
    user: CurrentUser = Depends(get_current_user),
) -> AgentSessionResponse:
    try:
        return await orchestrator.create_session(
            user_id=user.id,
            query=request.query,
            learning_style=request.learning_style,
            is_anonymous=user.is_anonymous,
        )
    except ValueError as exc:
        if quota := _quota_http(exc):
            raise quota from exc
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/sessions/{session_id}", response_model=AgentSessionStateResponse)
async def get_agent_session(
    session_id: str,
    user: CurrentUser = Depends(get_current_user),
) -> AgentSessionStateResponse:
    try:
        data = await orchestrator.get_session(session_id)
        if str(data.user_id) != user.id:
            raise HTTPException(status_code=403, detail="Session does not belong to the current user")
        return data
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/projects", response_model=list[AgentProjectSummary])
async def list_agent_projects(user: CurrentUser = Depends(get_current_user)) -> list[AgentProjectSummary]:
    try:
        return await orchestrator.list_projects(user.id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/projects/{project_id}", response_model=AgentProjectSummary)
async def get_agent_project(
    project_id: str,
    user: CurrentUser = Depends(get_current_user),
) -> AgentProjectSummary:
    try:
        return await orchestrator.get_project_summary(project_id=project_id, user_id=user.id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/projects/{project_id}/latest-session", response_model=AgentProjectLatestSessionResponse)
async def get_project_latest_session(
    project_id: str,
    user: CurrentUser = Depends(get_current_user),
) -> AgentProjectLatestSessionResponse:
    try:
        return await orchestrator.get_project_latest_session(project_id=project_id, user_id=user.id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/sessions/{session_id}/events", response_model=list[AgentEventResponse])
async def list_agent_session_events(
    session_id: str,
    user: CurrentUser = Depends(get_current_user),
) -> list[AgentEventResponse]:
    try:
        return await orchestrator.list_session_events(session_id=session_id, user_id=user.id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.delete("/projects/{project_id}", response_model=AgentDeleteResponse)
async def delete_agent_project(
    project_id: str,
    user: CurrentUser = Depends(get_current_user),
) -> AgentDeleteResponse:
    try:
        await orchestrator.delete_project(project_id=project_id, user_id=user.id)
        return AgentDeleteResponse(deleted=True)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/sessions/{session_id}/message", response_model=AgentSessionResponse)
async def send_agent_message(
    session_id: str,
    body: AgentTurnBody,
    user: CurrentUser = Depends(get_current_user),
) -> AgentSessionResponse:
    try:
        turn = AgentTurnRequest(user_id=user.id, **body.model_dump())
        return await orchestrator.handle_user_message(
            session_id=session_id,
            turn=turn,
            is_anonymous=user.is_anonymous,
        )
    except ValueError as exc:
        if quota := _quota_http(exc):
            raise quota from exc
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc
