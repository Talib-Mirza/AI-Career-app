# Anonymous sign-ins (guest chat)

Guest chat uses [Supabase anonymous authentication](https://supabase.com/docs/guides/auth/auth-anonymous).

## Dashboard setup

1. Open your Supabase project → **Authentication** → **Providers**.
2. Enable **Anonymous sign-ins** and save.

Without this, `/chat` guest bootstrap will fail and the UI will show a retry error.

## Product limits (enforced in the API)

- One learning path (project) per anonymous user.
- Thirty `user_message` events total per anonymous user (counts quiz and dungeon turns as well as plain text).

Converting an anonymous user with email/password keeps the same user id so existing rows stay attached.
