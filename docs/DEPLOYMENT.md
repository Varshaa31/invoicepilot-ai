# Deployment

InvoicePilot AI is a split frontend/backend application.

The AI API key must stay on the backend. Do not put `GROQ_API_KEY` in the frontend or expose it through Vercel.

## Database

Use hosted PostgreSQL (Supabase, Neon, Railway, Render).

Set:

```text
DATABASE_URL=postgresql+pg8000://USER:PASSWORD@HOST:5432/DBNAME