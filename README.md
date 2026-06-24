# AI Language Agent

AI Language Agent is a full-stack pronunciation analysis platform that combines Azure Speech pronunciation assessment with an AI-generated coaching report. It helps learners practice reading aloud, upload recordings, and receive structured feedback on pronunciation, fluency, accuracy, and improvement opportunities.

The project includes a FastAPI backend, a React + Vite frontend, and Docker support for running the full stack locally with one command.

## Why this project stands out

- Real speech analysis powered by Azure Speech Pronunciation Assessment.
- Human-friendly feedback generated from assessment results, not just raw scores.
- Audio upload and microphone recording flows in the frontend.
- Dockerized backend and frontend for reproducible local runs.
- Clean separation between scoring, AI narrative generation, and UI presentation.

## What It Does

- Assess pronunciation from uploaded audio.
- Assess pronunciation from text-based practice input.
- Convert uploaded audio to a format suitable for speech analysis.
- Return structured assessment data and a readable AI coaching report.
- Support a real-time streaming assessment endpoint for interactive scenarios.

## Architecture

- Backend: FastAPI + Azure Speech + optional Gemini-based report generation.
- Frontend: React, TypeScript, Vite, Axios, and a component-based UI.
- Runtime: Docker Compose with an Nginx-served frontend and a Python backend.

## Repository Layout

```text
.
├── app/
│   ├── main.py                # FastAPI application and API routes
│   ├── config.py              # Environment-driven settings
│   ├── models/                # Pydantic request/response models
│   ├── services/              # Azure pronunciation and AI report logic
│   └── utils/                 # Shared helpers
├── frontend/
│   ├── src/                   # React application source
│   ├── Dockerfile             # Frontend container build
│   └── nginx.conf             # Production frontend routing
├── Dockerfile                 # Backend container build
├── docker-compose.yml         # Full-stack orchestration
└── pyproject.toml             # Python dependencies and project metadata
```

## Prerequisites

- Python 3.12+
- Node.js 20+
- Docker Desktop if you want to run the full stack with Compose
- Azure Speech credentials
- Optional: a Google Gemini API key for richer narrative feedback

## Environment Variables

Create a `.env` file in the repository root with at least:

```env
AZURE_SPEECH_KEY=your_azure_speech_key
AZURE_SPEECH_REGION=your_azure_region
```

Optional:

```env
GOOGLE_API_KEY=your_google_api_key
```

## Quick Start With Docker

Run both services from the repository root:

```bash
docker compose up --build
```

After startup:

- Frontend: http://localhost:3000
- Backend health check: http://localhost:8000/health

## Local Development

### Backend

```bash
uv sync
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The Vite dev server runs on http://localhost:5173 by default.

## API Overview

Backend routes provided by FastAPI:

- `GET /health` - service health check
- `GET /api/config` - available modes, languages, and proficiency levels
- `POST /api/assess/text` - assess pronunciation from text input
- `POST /api/assess/audio` - assess pronunciation from an uploaded audio file
- `POST /analyze` - alternative audio analysis endpoint
- `POST /analyze-with-reference` - analyze learner audio against a reference file
- `WebSocket /api/assess/stream` - streaming pronunciation assessment

## Frontend Flow

The frontend lets the user:

- choose a pronunciation mode
- enter or load reference text
- record audio from a microphone or upload a file
- view structured scoring and AI-generated coaching feedback

It communicates with the backend through `frontend/src/services/api.ts`.

## Design Notes

This codebase is intentionally structured for product-quality demos and portfolio use:

- backend logic is separated from presentation logic
- environment variables control credentials and deployment behavior
- the frontend is container-ready for static hosting
- the API returns both machine-readable scores and human-readable coaching output

## Troubleshooting

- If Docker Compose fails, make sure Docker Desktop is running.
- If audio analysis fails, confirm `ffmpeg` is available in the backend container and your Azure credentials are valid.
- If the AI report is generic, set `GOOGLE_API_KEY` for Gemini-powered narrative feedback.

## Next Improvements

- Add a live demo link or screenshots.
- Add sample audio inputs for fast onboarding.
- Add CI checks for backend tests and frontend linting.
- Add deployment instructions for cloud hosting.

