# AI Language Agent

AI Language Agent is a full-stack language-learning platform with two complementary capabilities:

1. **Pronunciation analysis** — combines Azure Speech pronunciation assessment with an AI-generated coaching report so learners can practice reading aloud, upload recordings, and receive structured feedback on pronunciation, fluency, accuracy, and improvement opportunities.
2. **Live German speaking agent** — a real-time, spoken conversation partner powered by Azure VoiceLive. Learners talk into their microphone in the browser and hear a natural German voice reply, with support for interrupting the agent mid-sentence (barge-in).

The project includes a FastAPI backend, a React + Vite frontend, and Docker support for running the full stack locally with one command.

## Why this project stands out

- Real speech analysis powered by Azure Speech Pronunciation Assessment.
- Real-time, low-latency voice conversation powered by Azure VoiceLive.
- Human-friendly feedback generated from assessment results, not just raw scores.
- Audio upload, microphone recording, and live streaming conversation flows in the frontend.
- Dockerized backend and frontend for reproducible local runs.
- Clean separation between scoring, AI narrative generation, real-time audio relay, and UI presentation.

## What It Does

- Assess pronunciation from uploaded audio.
- Assess pronunciation from text-based practice input.
- Convert uploaded audio to a format suitable for speech analysis.
- Return structured assessment data and a readable AI coaching report.
- Support a real-time streaming assessment endpoint for interactive scenarios.
- Hold a live, two-way German voice conversation directly in the browser.

## Architecture

- Backend: FastAPI + Azure Speech (pronunciation) + Azure VoiceLive (live conversation) + optional Gemini-based report generation.
- Frontend: React, TypeScript, Vite, Axios, and a component-based UI, plus a Web Audio pipeline for real-time microphone capture and playback.
- Runtime: Docker Compose with an Nginx-served frontend and a Python backend.

## Repository Layout

```text
.
├── app/
│   ├── main.py                        # FastAPI application and API routes (incl. /api/voice/live)
│   ├── config.py                      # Environment-driven settings (Speech + VoiceLive)
│   ├── models/                        # Pydantic request/response models
│   ├── services/
│   │   ├── azure_pronunciation.py     # Azure Speech pronunciation assessment
│   │   ├── AI_service.py              # AI coaching report generation
│   │   ├── voicelive_bridge.py        # Browser <-> Azure VoiceLive relay (web app)
│   │   └── german_voice_agent.py      # Standalone terminal voice agent (CLI)
│   └── utils/                         # Shared helpers
├── frontend/
│   ├── src/
│   │   ├── components/GermanVoiceChat.tsx   # Live conversation UI
│   │   └── services/voiceLiveClient.ts      # Browser audio capture/playback client
│   ├── Dockerfile                     # Frontend container build
│   └── nginx.conf                     # Production frontend routing
├── Dockerfile                         # Backend container build
├── docker-compose.yml                 # Full-stack orchestration
└── pyproject.toml                     # Python dependencies and project metadata
```

## Prerequisites

- Python 3.12+
- Node.js 20+
- Docker Desktop if you want to run the full stack with Compose
- Azure Speech credentials (for pronunciation analysis)
- Azure VoiceLive credentials (for the live speaking agent)
- Optional: a Google Gemini API key for richer narrative feedback

## Environment Variables

Create a `.env` file in the repository root.

For pronunciation analysis:

```env
AZURE_SPEECH_KEY=your_azure_speech_key
AZURE_SPEECH_REGION=your_azure_region
```

For the live German speaking agent (web app):

```env
AZURE_VOICELIVE_API_KEY=your_voicelive_key
AZURE_VOICELIVE_ENDPOINT=https://your-resource-name.services.ai.azure.com/
AZURE_VOICELIVE_MODEL=gpt-realtime
AZURE_VOICELIVE_VOICE=de-DE-KatjaNeural
```

Optional:

```env
GOOGLE_API_KEY=your_google_api_key
# Override the default German coaching persona:
AZURE_VOICELIVE_INSTRUCTIONS=Du bist ein freundlicher deutscher Sprachcoach ...
```

If `AZURE_VOICELIVE_API_KEY` is omitted, the backend falls back to Azure AD (`DefaultAzureCredential`), which resolves credentials from the environment, a managed identity, or `az login`.

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

> **Microphone note:** Browsers only grant microphone access on `localhost` or over HTTPS. Local development on `localhost` works out of the box; a deployed instance must be served over HTTPS for the voice agent to capture audio.

## API Overview

Backend routes provided by FastAPI:

- `GET /health` - service health check
- `GET /api/config` - available modes, languages, and proficiency levels
- `POST /api/assess/text` - assess pronunciation from text input
- `POST /api/assess/audio` - assess pronunciation from an uploaded audio file
- `POST /analyze` - alternative audio analysis endpoint
- `POST /analyze-with-reference` - analyze learner audio against a reference file
- `WebSocket /api/assess/stream` - streaming pronunciation assessment
- `WebSocket /api/voice/live` - live German voice conversation (Azure VoiceLive relay)

## Frontend Flow

The frontend lets the user:

- choose a pronunciation mode
- enter or load reference text
- record audio from a microphone or upload a file
- view structured scoring and AI-generated coaching feedback
- start a live German voice conversation and speak with the coaching agent

It communicates with the backend through `frontend/src/services/api.ts` (REST) and `frontend/src/services/voiceLiveClient.ts` (WebSocket audio).

## Live German Speaking Agent

The live agent lets a learner have a natural, spoken back-and-forth conversation in German. It ships in two forms that share the same Azure VoiceLive session model: an in-browser experience (the main product feature) and a standalone terminal CLI (useful for quick local testing).

### How it works

```text
 Browser mic ─► PCM16 24kHz ─► WebSocket ─► FastAPI bridge ─► Azure VoiceLive
 Browser speaker ◄─ PCM16 24kHz ◄─ WebSocket ◄─ FastAPI bridge ◄─ Azure VoiceLive
```

- The browser captures the microphone with the Web Audio API, downsamples to **raw PCM16, mono, 24 kHz**, and streams it as binary WebSocket frames.
- The FastAPI bridge (`app/services/voicelive_bridge.py`) relays those frames to Azure VoiceLive and pumps the model's audio response back to the browser, which schedules it for gapless playback.
- **Turn-taking** uses Azure server-side voice activity detection (VAD). When the learner starts speaking while the agent is talking, the agent is interrupted and its queued audio is dropped — natural **barge-in** behavior.
- Audio is never persisted; the server is a stateless relay for the duration of the WebSocket connection.

The agent's persona defaults to a friendly German language coach that adapts to the learner's level and offers brief, helpful corrections. Override it with `AZURE_VOICELIVE_INSTRUCTIONS`.

### Using it in the web app

1. Set the VoiceLive environment variables above and start the backend and frontend.
2. Open the frontend and find the **🇩🇪 Deutsch sprechen** card.
3. Click **Gespräch starten**, allow microphone access, and begin speaking. Click **Gespräch beenden** to end the session.

Live status (`listening`, `processing`, `ready`) and any assistant transcript are shown in the card.

### Wire protocol

The browser client and server bridge exchange:

- **Browser → Server:** binary frames — raw PCM16 mono @ 24 kHz microphone audio.
- **Server → Browser:**
  - binary frames — raw PCM16 mono @ 24 kHz audio to play back.
  - text frames (JSON) — control/status events:
    - `{"type": "status", "state": "connected" | "ready" | "listening" | "processing"}`
    - `{"type": "speech_started"}` — barge-in signal; the client flushes queued playback.
    - `{"type": "transcript", "role": "assistant", "text": "..."}`
    - `{"type": "error", "message": "..."}`

### Standalone terminal agent (CLI)

For quick local testing without the frontend, the CLI in `app/services/german_voice_agent.py` captures and plays audio directly on the host machine with PyAudio.

> The CLI reads its own environment variables — `AZURE_VOICELIVE_API_KEY`, `AZURE_VOICELIVE_ENDPOINT`, `VOICELIVE_MODEL`, `VOICELIVE_VOICE`, and `VOICELIVE_INSTRUCTIONS` — and also accepts equivalent command-line flags. (These `VOICELIVE_*` names differ from the `AZURE_VOICELIVE_*` names used by the web app.)

Run it from the repository root:

```bash
uv run python -m app.services.german_voice_agent
```

Or with explicit flags (for example, to use a German voice):

```bash
uv run python -m app.services.german_voice_agent \
  --voice de-DE-KatjaNeural \
  --model gpt-realtime \
  --instructions "Du bist ein freundlicher deutscher Sprachcoach."
```

Press `Ctrl+C` to exit. Use `--use-token-credential` for Azure AD auth instead of an API key, and `--verbose` for debug logging.

## Design Notes

This codebase is intentionally structured for product-quality demos and portfolio use:

- backend logic is separated from presentation logic
- the real-time audio relay is isolated in a dedicated bridge module, decoupled from REST assessment logic
- environment variables control credentials and deployment behavior
- the frontend is container-ready for static hosting
- the API returns both machine-readable scores and human-readable coaching output

## Troubleshooting

- If Docker Compose fails, make sure Docker Desktop is running.
- If audio analysis fails, confirm `ffmpeg` is available in the backend container and your Azure credentials are valid.
- If the AI report is generic, set `GOOGLE_API_KEY` for Gemini-powered narrative feedback.
- If the voice agent connects but you hear nothing, check that the browser tab has audio output and that the page was reloaded after granting mic permission; playback runs through a Web Audio context that must be started by a user gesture (the **Gespräch starten** button).
- If the voice agent won't connect, verify the VoiceLive endpoint, key, and model, and confirm the backend log shows a `connected` → `ready` status for the session.

## Next Improvements

- Add a live demo link or screenshots.
- Add sample audio inputs for fast onboarding.
- Add a connection cap and on-screen mic-level indicator for the voice agent.
- Add CI checks for backend tests and frontend linting.
- Add deployment instructions for cloud hosting (with HTTPS for microphone access).
