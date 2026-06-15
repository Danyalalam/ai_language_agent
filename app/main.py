"""FastAPI application for Pronunciation Analysis Agent."""
from __future__ import annotations

from fastapi import FastAPI

from app.api.gaming import router as gaming_router
from app.api.reading import router as reading_router
from app.config import settings

app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description="AI Language Agent for English Pronunciation Analysis",
)

app.include_router(reading_router)
app.include_router(gaming_router)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Pronunciation Analysis Agent"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)