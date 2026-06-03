-- Performance indexes: speed up the three most common query patterns
-- that were running sequential scans.

-- agent_sessions: looked up by project_id in get_latest_session_for_project
CREATE INDEX IF NOT EXISTS idx_agent_sessions_project_id
    ON agent_sessions (project_id);

-- agent_events: looked up and ordered by session_id on every message
CREATE INDEX IF NOT EXISTS idx_agent_events_session_id_created
    ON agent_events (session_id, created_at DESC);

-- projects: listed and ordered by updated_at for each user
CREATE INDEX IF NOT EXISTS idx_projects_user_id_updated
    ON projects (user_id, updated_at DESC);
