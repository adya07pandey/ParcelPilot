# ParcelPilot

ParcelPilot is a logistics customer/support portal with an account-aware AI support agent. It combines structured operational data, document retrieval, role-based access control, and guided support workflows for shipment, cancellation, service-credit, ticket, product, and account questions.

## Submission Links

- Repository: https://github.com/adya07pandey/ParcelPilot
- Hosted frontend: https://parcelpilot-beta.vercel.app
- Hosted backend health: https://parcelpilot-m1ak.onrender.com/health
- Submission form: https://forms.gle/hLGBrDrNRmK7UAbv6

## Demo Accounts

Use the dataset password configured for the seeded demo users.

```text
Customer: aarav@northstar.example
Support:  rohit@parcelpilot.example
Admin:    admin@parcelpilot.example
Password: Demo@123
```

## What Is Implemented

- Customer portal: dashboard, orders, order detail, tickets, ticket detail, AI support.
- Support portal: dashboard, ticket queue/detail, customer directory/detail, orders/detail, policies and agreements, issues/incidents.
- Authentication: JWT access token, rotating HttpOnly refresh cookie, logout, session restore after refresh.
- Authorization: customer/support/admin RBAC and account-level tenant isolation.
- AI support: guided category/subcategory flow, persistent conversation state, account-aware structured tools, document retrieval, confidence labels, and ticket/cancellation-request confirmation flows.
- Data: Neon PostgreSQL schema and workbook import scripts for accounts, users, orders, shipment events, tickets, and ticket events.
- RAG stack: Voyage embeddings, Qdrant document retrieval, Groq chat completion.
- Deployment: Docker backend for Render, Vite frontend for Vercel, local Docker Compose.

## Documentation

- [Architecture Note](docs/ARCHITECTURE_NOTE.md)
- [Product Note](docs/PRODUCT_NOTE.md)
- [AI Tool Usage](docs/AI_TOOL_USAGE.md)
- [Demo Video Outline](docs/DEMO_VIDEO_OUTLINE.md)
- [Submission Checklist](docs/SUBMISSION_CHECKLIST.md)

## Tech Stack

- Frontend: React, Vite, CSS
- Backend: FastAPI, SQLAlchemy, PostgreSQL/Neon
- Agent/RAG: Groq, Voyage AI, Qdrant
- Auth: JWT access token plus HttpOnly refresh cookie
- Deployment: Vercel frontend, Render backend, Docker/Compose

## Local Backend Setup

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Set the required values in `backend/.env`:

```text
DATABASE_URL=postgresql+psycopg://...
JWT_SECRET_KEY=...
FRONTEND_ORIGIN=http://localhost:5173
BACKEND_ORIGIN=http://localhost:8000
VOYAGE_API_KEY=...
QDRANT_URL=...
QDRANT_API_KEY=...
GROQ_API_KEY=...
```

Import the dataset:

```powershell
python scripts/import_dataset.py
python scripts/backfill_ticket_categories.py
```

Ingest documents after Qdrant/Voyage are configured:

```powershell
python scripts/ingest_documents.py
```

Run the API:

```powershell
uvicorn app.main:app --reload
```

## Local Frontend Setup

```powershell
cd frontend
npm install
npm run dev
```

Set `frontend/.env`:

```text
VITE_BACKEND_ORIGIN=http://localhost:8000
VITE_API_BASE_URL=http://localhost:8000
```

## Docker Compose

Use Compose for local full-stack testing:

```powershell
docker compose up --build
```

Local URLs:

- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- Health: http://localhost:8000/health

## Deployment

### Render Backend

Use the root `Dockerfile` or configure Render with:

```text
Root Directory: backend
Dockerfile Path: ./Dockerfile
Docker Build Context Directory: .
Docker Command: empty
```

Required Render env vars:

```text
DATABASE_URL=postgresql+psycopg://...
JWT_SECRET_KEY=...
REFRESH_COOKIE_SECURE=true
FRONTEND_ORIGIN=https://parcelpilot-beta.vercel.app
BACKEND_ORIGIN=https://parcelpilot-m1ak.onrender.com
VOYAGE_API_KEY=...
QDRANT_URL=...
QDRANT_API_KEY=...
GROQ_API_KEY=...
```

### Vercel Frontend

Vercel settings:

```text
Root Directory: frontend
Install Command: npm ci
Build Command: npm run build
Output Directory: dist
```

Required Vercel env vars:

```text
VITE_BACKEND_ORIGIN=https://parcelpilot-m1ak.onrender.com
VITE_API_BASE_URL=https://parcelpilot-m1ak.onrender.com
```

## Repo Organization

```text
backend/app/auth          Authentication and refresh-token flow
backend/app/routers       API routers
backend/app/models        SQLAlchemy models
backend/app/ai            AI orchestration, providers, parsing, evidence, data access
backend/app/tickets       Ticket classification helpers
backend/scripts           Dataset import, document ingest, diagnostics
frontend/src/customer     Customer portal components/pages/utils
frontend/src/support      Support portal components/pages/utils
frontend/src/api          API client
frontend/src/auth         Auth provider/session restore
docs                      Submission notes
```

## Notes

Real `.env` files, API keys, local virtual environments, build output, and logs are intentionally ignored. The public repo should contain only examples and deployment instructions, not secrets.
