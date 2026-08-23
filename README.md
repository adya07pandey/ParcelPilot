# ParcelPilot

ParcelPilot is a FastAPI + React foundation for the AI support-agent assessment. This first slice sets up the database, authentication, refresh-cookie lifecycle, role checks, and tenant-scoped order/ticket APIs.

## Stack

- Backend: FastAPI, SQLAlchemy, PostgreSQL/Neon, JWT access tokens, HttpOnly refresh cookies
- Frontend: React + Vite + CSS
- Data source: `data/ParcelPilot_full_dataset.xlsx`

## Backend Setup

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Set `DATABASE_URL` in `backend/.env` to your Neon SQLAlchemy URL:

```text
postgresql+psycopg://neondb_owner:...@ep-solitary-resonance-axl8ez05-pooler.c-4.us-east-2.aws.neon.tech/neondb?sslmode=require
```

For the AI stack, add:

```text
VOYAGE_API_KEY=...
VOYAGE_EMBEDDING_MODEL=voyage-3-large
QDRANT_URL=...
QDRANT_API_KEY=...
QDRANT_COLLECTION=parcelpilot_documents
GROQ_API_KEY=...
GROQ_MODEL=openai/gpt-oss-120b
```

Import the workbook:

```powershell
python scripts/import_dataset.py
```

Run the API:

```powershell
uvicorn app.main:app --reload
```

The workbook stores `password_hash`, not plaintext passwords. At login, the backend hashes the submitted password and compares it to the stored hash. Role and account scope are checked only on the backend. In the current Neon development database, imported dataset users have been reset to the normal typed password `Demo@123`.

For local development, set a known password for any dataset user:

```powershell
python scripts/set_user_password.py aarav@northstar.example Demo@123
```

## Frontend Setup

```powershell
cd frontend
npm install
npm run dev
```

The app expects the API at `http://localhost:8000` by default. Override with `VITE_API_BASE_URL`.

## Docker Compose

Use Compose for local full-stack testing. The backend reads `backend/.env`; the frontend is built as static files and served by nginx.

```powershell
docker compose up --build
```

Local URLs:

- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000`
- Health: `http://localhost:8000/health`

Do not commit real `.env` files. Keep Neon, Voyage, Qdrant, and Groq credentials only in local/hosting environment variables.

## Deployment

### Backend on Render

This repo includes `render.yaml` for a Docker web service using `backend/Dockerfile`.

Set these Render environment variables:

```text
DATABASE_URL=postgresql+psycopg://...
JWT_SECRET_KEY=...
REFRESH_COOKIE_SECURE=true
FRONTEND_ORIGIN=https://your-vercel-app.vercel.app
BACKEND_ORIGIN=https://your-render-service.onrender.com
VOYAGE_API_KEY=...
QDRANT_URL=...
QDRANT_API_KEY=...
GROQ_API_KEY=...
```

Render injects `PORT`; the Dockerfile starts Uvicorn with `${PORT:-8000}`.

### Frontend on Vercel

This repo includes `vercel.json` for the Vite app in `frontend/`.

Set this Vercel environment variable:

```text
VITE_API_BASE_URL=https://your-render-service.onrender.com
VITE_BACKEND_ORIGIN=https://your-render-service.onrender.com
```

`VITE_API_BASE_URL` and `VITE_BACKEND_ORIGIN` can point to the same Render backend URL. The frontend client accepts either variable.

After the Vercel URL is known, update Render `FRONTEND_ORIGIN` to that exact Vercel origin so CORS and refresh cookies work.

## Implemented So Far

- PostgreSQL schema for accounts, users, refresh tokens, orders, tickets, events, and escalations
- Workbook import script for Neon/PostgreSQL
- JWT login with short-lived access tokens
- Rotating refresh token stored as a hashed DB record and raw HttpOnly cookie
- Logout and `/auth/me`
- Customer tenant isolation for order and ticket APIs
- Support/admin cross-account access
- Customer portal shell with Dashboard, Orders, and Tickets pages
- Order detail view with shipment event timeline
- Ticket creation and customer message posting
- AI Support navigation placeholder for the next build step
- AI provider adapters for Voyage embeddings, Qdrant document retrieval, and Groq chat completions
- Auth-protected `/api/v1/ai/providers` configuration status endpoint
- Persistent AI conversation/message tables with active order/ticket context
- Auth-protected `/api/v1/ai/chat` endpoint with customer account isolation
- Customer AI Support chat page connected to the backend endpoint
