# AI Tool Usage

I used AI coding assistance as a pair-programming tool during the build.

## Tools Used

- OpenAI Codex in the local development workspace.
- LLM-assisted debugging for backend/frontend implementation details.

## How It Was Used

- Translating product requirements into implementation tasks.
- Building FastAPI routers, services, SQLAlchemy models, and React pages.
- Refactoring large files into clearer backend and frontend modules.
- Debugging authentication, cookie/session restore, CORS, deployment, and RAG integration issues.
- Drafting documentation for setup, architecture, product decisions, and demo flow.

## Human Decisions

The main product and technical decisions were made intentionally for the ParcelPilot use case:

- Guided-first AI support rather than a blank chatbot.
- Strict account-level authorization for customers.
- Support-team portal as the additional client problem.
- Deterministic confidence labels based on available evidence.
- Ticket creation only after explicit customer confirmation.
- Hosted frontend on Vercel and backend on Render.

AI assistance was used to speed up implementation, but the final scope, trade-offs, and validation were directed around the assessment requirements.
