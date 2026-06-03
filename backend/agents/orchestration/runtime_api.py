"""Session lifecycle and API-facing orchestration helpers."""

from __future__ import annotations

import uuid
from typing import Any

from app.core.logging import AgentLogger
from app.models.agent import (
    AgentEventResponse,
    AgentProjectLatestSessionResponse,
    AgentProjectSummary,
    AgentSessionResponse,
    AgentSessionStateResponse,
    AgentTurnRequest,
)


ANONYMOUS_MAX_PROJECTS = 1
ANONYMOUS_MAX_USER_MESSAGES = 30


class RuntimeApiMixin:
    async def create_session(self, *, user_id: str, query: str, learning_style: str | None = None, is_anonymous: bool = False) -> AgentSessionResponse:
        if is_anonymous:
            existing = await self.store.list_projects(user_id)
            if len(existing) >= ANONYMOUS_MAX_PROJECTS:
                raise ValueError(
                    "Guest accounts are limited to one learning path. Create a free account to start additional topics."
                )

        roadmap = await self.roadmap_agent.generate(query=query)
        project_id = str(uuid.uuid4())
        session_id = str(uuid.uuid4())
        state = self._initial_state(roadmap=roadmap, learning_style=learning_style)

        project = await self.store.create_project(
            {
                "id": project_id,
                "user_id": user_id,
                "title": self._roadmap_label(roadmap.model_dump(), query),
                "goal": query,
                "roadmap_json": roadmap.model_dump(),
                "status": "active",
                "latest_session_id": None,
            }
        )
        session = await self.store.create_session(
            {
                "id": session_id,
                "project_id": project_id,
                "user_id": user_id,
                "query": query,
                "status": "awaiting_start_mode",
                "active_agent": "orchestrator",
                "roadmap_json": roadmap.model_dump(),
                "state": state,
            }
        )
        await self.knowledge_store.seed_project_skill_states(
            user_id=user_id,
            project_id=project_id,
            ordered_skills=self._ordered_skills(roadmap.model_dump()),
        )
        await self.store.append_event(
            {
                "session_id": session_id,
                "role": "system",
                "agent": "orchestrator",
                "event_type": "session_created",
                "content": f"Created project '{project['title']}' and initialized the learning session.",
                "payload": {"query": query, "project_id": project_id},
            }
        )
        await self.store.append_event(
            {
                "session_id": session_id,
                "role": "user",
                "agent": "orchestrator",
                "event_type": "initial_query",
                "content": query,
                "payload": {"query": query},
            }
        )

        response = self._session_response(
            session,
            message="Roadmap generated. Choose whether to start from the beginning or take a placement test.",
        )
        await self._persist_assistant_response(session, response)
        AgentLogger.info(event="session_created", component="orchestrator", session_id=session_id, project_id=project_id, user_id=user_id)
        return response

    async def get_session(self, session_id: str) -> AgentSessionStateResponse:
        session = await self.store.get_session(session_id)
        pending_questions = await self._pending_questions_for_session(session)
        return self._session_state_response(session, pending_questions=pending_questions)

    async def list_projects(self, user_id: str) -> list[AgentProjectSummary]:
        rows = await self.store.list_projects(user_id)
        if not rows:
            return []

        # Batch-fetch all latest sessions in one query instead of one per project
        session_ids = [str(row["latest_session_id"]) for row in rows if row.get("latest_session_id")]
        session_status_map: dict[str, str] = {}
        if session_ids:
            sessions = await self.store.get_sessions_by_ids(session_ids)
            session_status_map = {str(s["id"]): str(s.get("status") or "") for s in sessions}

        summaries: list[AgentProjectSummary] = []
        for row in rows:
            sid = str(row["latest_session_id"]) if row.get("latest_session_id") else None
            latest_session_status = session_status_map.get(sid) if sid else None
            summaries.append(self._project_summary(row, latest_session_status=latest_session_status))
        return summaries

    async def get_project_latest_session(self, *, project_id: str, user_id: str) -> AgentProjectLatestSessionResponse:
        project = await self.store.get_project(project_id)
        if str(project["user_id"]) != user_id:
            raise ValueError("Project does not belong to the current user")
        latest_session = await self.store.get_latest_session_for_project(project_id)
        latest_session_status = latest_session.get("status") if latest_session else None
        session_response = None
        if latest_session:
            pending_questions = await self._pending_questions_for_session(latest_session)
            session_response = self._session_state_response(latest_session, pending_questions=pending_questions)
        return AgentProjectLatestSessionResponse(
            project=self._project_summary(project, latest_session_status=latest_session_status),
            session=session_response,
        )

    async def get_project_summary(self, *, project_id: str, user_id: str) -> AgentProjectSummary:
        project = await self.store.get_project(project_id)
        if str(project["user_id"]) != user_id:
            raise ValueError("Project does not belong to the current user")
        latest_session = await self.store.get_latest_session_for_project(project_id)
        latest_session_status = latest_session.get("status") if latest_session else None
        return self._project_summary(project, latest_session_status=latest_session_status)

    async def delete_project(self, *, project_id: str, user_id: str) -> None:
        project = await self.store.get_project(project_id)
        if str(project["user_id"]) != user_id:
            raise ValueError("Project does not belong to the current user")
        deleted = await self.store.delete_project(project_id, user_id)
        if not deleted:
            raise ValueError("Project could not be deleted")

    async def list_session_events(self, *, session_id: str, user_id: str) -> list[AgentEventResponse]:
        session = await self.store.get_session(session_id)
        if str(session["user_id"]) != user_id:
            raise ValueError("Session does not belong to the current user")
        events = await self.store.list_events(session_id)
        return [self._event_response(event) for event in events]

    async def handle_user_message(self, *, session_id: str, turn: AgentTurnRequest, is_anonymous: bool = False) -> AgentSessionResponse:
        session = await self.store.get_session(session_id)
        if str(session["user_id"]) != turn.user_id:
            raise ValueError("User does not match the active session")

        if is_anonymous:
            prior_messages = await self.store.count_user_message_events(turn.user_id)
            if prior_messages >= ANONYMOUS_MAX_USER_MESSAGES:
                raise ValueError(
                    "Guest accounts are limited to 30 messages. Create a free account to continue the conversation."
                )

        user_content = turn.message
        if turn.input_mode == "quiz_ready":
            user_content = user_content or "[Start quiz]"
        if turn.input_mode == "dungeon_start":
            user_content = user_content or "[Dungeon]"
        if turn.input_mode == "dungeon_abort":
            user_content = user_content or "[Leave dungeon]"
        if turn.input_mode == "dungeon_dismiss":
            user_content = user_content or "[Dungeon complete]"
        await self.store.append_event(
            {
                "session_id": session_id,
                "role": "user",
                "agent": session["active_agent"],
                "event_type": "user_message",
                "content": user_content,
                "payload": {
                    "message": turn.message,
                    "input_mode": turn.input_mode,
                    "question_id": turn.question_id,
                    "selected_option_id": turn.selected_option_id,
                    "selected_option_index": turn.selected_option_index,
                    "dungeon_transcript": session["status"] == "awaiting_topic_dungeon" and turn.input_mode == "text",
                },
            }
        )

        status = session["status"]
        if status == "awaiting_start_mode":
            response = await self._handle_start_mode(session, turn)
        elif status == "awaiting_knowledge_answer":
            response = await self._handle_knowledge_turn(session, turn)
        elif status == "awaiting_focus_confirm":
            response = await self._handle_focus_confirm(session)
        elif status in {
            "awaiting_topic_followup",
            "awaiting_topic_quiz",
            "awaiting_topic_dungeon",
            "awaiting_skill_quiz",
            "reviewing_topic",
            "awaiting_domain_quiz",
            "reviewing_domain",
        }:
            response = await self._handle_conversation_turn(session, turn)
        else:
            response = await self._respond_from_terminal_state(session)

        await self._persist_assistant_response(session, response)
        return response

    async def _handle_start_mode(self, session: dict[str, Any], turn: AgentTurnRequest) -> AgentSessionResponse:
        state = session["state"]
        choice = str(turn.selected_option_id or "").strip()
        if choice not in {"beginning", "placement"}:
            raise ValueError("Start mode must be either 'beginning' or 'placement'")

        state["learning_path_mode"] = choice

        if choice == "beginning":
            return await self._start_guided_skill(
                session=session,
                state=state,
                intro=None,
            )

        return await self._start_placement_flow(
            session=session,
            state=state,
            intro="Starting placement calibration.",
        )

    async def _start_placement_flow(
        self,
        *,
        session: dict[str, Any],
        state: dict[str, Any],
        intro: str,
    ) -> AgentSessionResponse:
        self._initialize_binary_placement(state, session["roadmap_json"])
        await self._refresh_project_knowledge_state(session=session, state=state)
        target_skill = self._placement_current_skill(state, session["roadmap_json"])
        quiz_bundle = await self._create_placement_quiz(
            session=session,
            state=state,
            target_skill=target_skill,
            prior_question=None,
            attempt_number=1,
        )
        updated = await self.store.update_session(
            session["id"],
            {"status": "awaiting_knowledge_answer", "active_agent": "quiz_agent", "state": quiz_bundle["state"]},
        )
        return self._session_response(
            updated,
            message=f"{intro}\n\n{quiz_bundle['message']}",
            pending_questions=[quiz_bundle["question"]],
        )

    async def _handle_focus_confirm(self, session: dict[str, Any]) -> AgentSessionResponse:
        state = session["state"]
        if "focus_reveal" in state:
            state.pop("focus_reveal", None)
        session["state"] = state
        return await self._deliver_current_topic(session, intro="Great. Let’s get started.")
