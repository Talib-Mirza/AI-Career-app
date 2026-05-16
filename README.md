# AI Career App

## Roadmap generation

Each roadmap is generated fresh with the LLM (domains, then skills). A short **learning-focus** label (snake_case) is produced for metadata; it can represent a career, course, concept, idea, project, skill, or similar — not only job titles.

The `roadmap_library` table and pgvector helpers remain in the database for optional admin cleanup (`DELETE /api/roadmap/cache`), but **generation no longer reads or writes that library**.

## Backend modules

- `backend/agents/roadmap/service.py`
- `backend/services/career_normalizer.py` (learning-focus normalization)
- `backend/services/roadmap_storage.py` (cache admin / legacy library)
- `backend/services/supabase_client.py`
- `backend/utils/embeddings.py`
- `supabase/migrations/003_roadmap_library_vector.sql` (schema only)

## Environment variables

Set in `backend/.env`:

- `OPENAI_API_KEY`
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`

## Supabase setup + local PostgreSQL cleanup

See:

- `POSTGRES_SETUP.md`

## Generate API response

`POST /api/roadmap/generate` returns `existing: false` for new generations. Domain JSON files are still written under `backend/roadmaps/` for the standalone roadmap page.
