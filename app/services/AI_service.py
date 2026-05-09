from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Optional

from app.config import settings
from app.models.schemas import PronunciationReport


@dataclass
class AIReport:
    summary: str
    strengths: list[str]
    weaknesses: list[str]
    recommendations: list[str]
    full_report: str


class GeminiReportService:
    """
    Generates a human-readable pronunciation report from Azure pronunciation data.

    Azure remains the source of truth for scores.
    Gemini only turns those scores into readable feedback.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gemini-2.5-flash",
    ) -> None:
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY", "")
        self.model = model
        self._client = None

        if self.api_key:
            self._client = self._build_client()

    def _build_client(self):
        try:
            from google import genai
        except ImportError as exc:
            raise ImportError(
                "google-genai is not installed. Add it to pyproject.toml and run uv sync."
            ) from exc

        return genai.Client(api_key=self.api_key)

    def generate_report(
        self,
        azure_report: PronunciationReport | dict[str, Any],
        reference_text: str,
        language: str = "en-US",
        learner_name: str | None = None,
    ) -> dict[str, Any]:
        """
        Generate a structured AI report from Azure pronunciation results.

        Returns:
            {
                "ai_report": {
                    "summary": str,
                    "strengths": [...],
                    "weaknesses": [...],
                    "recommendations": [...],
                    "full_report": str,
                }
            }
        """
        report = self._normalize_report(azure_report)
        prompt = self._build_prompt(
            report=report,
            reference_text=reference_text,
            language=language,
            learner_name=learner_name,
        )

        if self._client is None:
            ai_report = self._fallback_report(report, learner_name=learner_name)
            return {"ai_report": ai_report}

        try:
            response = self._client.models.generate_content(
                model=self.model,
                contents=prompt,
                config={
                    "temperature": 0.4,
                    "response_mime_type": "application/json",
                },
            )
            text = getattr(response, "text", "") or ""
            parsed = self._safe_parse_json(text)
            if parsed is None:
                ai_report = self._fallback_report(report, learner_name=learner_name)
                return {"ai_report": ai_report}

            ai_report = self._normalize_ai_report(parsed, report, learner_name)
            return {"ai_report": ai_report}
        except Exception:
            ai_report = self._fallback_report(report, learner_name=learner_name)
            return {"ai_report": ai_report}

    def _build_prompt(
        self,
        report: dict[str, Any],
        reference_text: str,
        language: str,
        learner_name: str | None,
    ) -> str:
        learner_label = learner_name or "the learner"

        return f"""
You are a pronunciation coach. You must write a grounded feedback report using ONLY the Azure pronunciation data provided below.

Rules:
- Do not change or reinterpret the scores.
- Do not invent errors that are not supported by the data.
- Focus on pronunciation, fluency, completeness, and word-level feedback.
- Be concise, helpful, and teacher-like.
- Return valid JSON only.

Output JSON schema:
{{
  "summary": "string",
  "strengths": ["string"],
  "weaknesses": ["string"],
  "recommendations": ["string"],
  "full_report": "string"
}}

Context:
Learner: {learner_label}
Language: {language}
Reference text: {reference_text}

Azure pronunciation data:
{json.dumps(report, indent=2, ensure_ascii=False)}
""".strip()

    def _normalize_report(self, azure_report: PronunciationReport | dict[str, Any]) -> dict[str, Any]:
        if isinstance(azure_report, PronunciationReport):
            return azure_report.model_dump()

        return dict(azure_report)

    def _normalize_ai_report(
        self,
        parsed: dict[str, Any],
        report: dict[str, Any],
        learner_name: str | None,
    ) -> AIReport:
        summary = str(parsed.get("summary", "")).strip() or self._build_summary(report, learner_name)
        strengths = self._ensure_string_list(parsed.get("strengths")) or self._build_strengths(report)
        weaknesses = self._ensure_string_list(parsed.get("weaknesses")) or self._build_weaknesses(report)
        recommendations = self._ensure_string_list(parsed.get("recommendations")) or self._build_recommendations(report)
        full_report = str(parsed.get("full_report", "")).strip() or self._compose_full_report(
            summary,
            strengths,
            weaknesses,
            recommendations,
        )

        return AIReport(
            summary=summary,
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations,
            full_report=full_report,
        )

    def _fallback_report(
        self,
        report: dict[str, Any],
        learner_name: str | None = None,
    ) -> AIReport:
        summary = self._build_summary(report, learner_name)
        strengths = self._build_strengths(report)
        weaknesses = self._build_weaknesses(report)
        recommendations = self._build_recommendations(report)
        full_report = self._compose_full_report(summary, strengths, weaknesses, recommendations)

        return AIReport(
            summary=summary,
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations,
            full_report=full_report,
        )

    def _build_summary(self, report: dict[str, Any], learner_name: str | None = None) -> str:
        name_prefix = f"{learner_name}, " if learner_name else ""
        overall = report.get("overall_score", 0)
        accuracy = report.get("accuracy_score", 0)
        fluency = report.get("fluency_score", 0)
        completeness = report.get("completeness_score", 0)

        return (
            f"{name_prefix}your pronunciation is strong overall. "
            f"The overall score is {overall:.1f}, with accuracy at {accuracy:.1f}, "
            f"fluency at {fluency:.1f}, and completeness at {completeness:.1f}."
        )

    def _build_strengths(self, report: dict[str, Any]) -> list[str]:
        strengths: list[str] = []

        accuracy = float(report.get("accuracy_score", 0))
        fluency = float(report.get("fluency_score", 0))
        completeness = float(report.get("completeness_score", 0))

        if accuracy >= 90:
            strengths.append("Strong pronunciation accuracy across the spoken words.")
        if fluency >= 90:
            strengths.append("Speech flow and pacing are clear and natural.")
        if completeness >= 95:
            strengths.append("The spoken content matches the reference text very closely.")

        word_details = report.get("word_details", []) or []
        if word_details:
            good_words = [w.get("word", "") for w in word_details if float(w.get("accuracy_score", 0)) >= 95]
            if good_words:
                strengths.append(f"Excellent articulation on key words such as {', '.join(good_words[:4])}.")

        if not strengths:
            strengths.append("The response shows a solid baseline for pronunciation work.")

        return strengths

    def _build_weaknesses(self, report: dict[str, Any]) -> list[str]:
        weaknesses: list[str] = []

        accuracy = float(report.get("accuracy_score", 0))
        fluency = float(report.get("fluency_score", 0))
        completeness = float(report.get("completeness_score", 0))
        prosody = report.get("prosody_score", None)

        if accuracy < 85:
            weaknesses.append("Some words may need clearer articulation.")
        if fluency < 85:
            weaknesses.append("The rhythm or pacing could be smoother.")
        if completeness < 90:
            weaknesses.append("A few words may have been missed or misread.")
        if prosody is not None and float(prosody) < 70:
            weaknesses.append("Prosody, including stress and intonation, could be more expressive.")

        word_details = report.get("word_details", []) or []
        low_words = [w.get("word", "") for w in word_details if float(w.get("accuracy_score", 0)) < 90]
        if low_words:
            weaknesses.append(f"The following words may need practice: {', '.join(low_words[:5])}.")

        if not weaknesses:
            weaknesses.append("No major weaknesses are evident from the current Azure results.")

        return weaknesses

    def _build_recommendations(self, report: dict[str, Any]) -> list[str]:
        recommendations: list[str] = []

        overall = float(report.get("overall_score", 0))
        accuracy = float(report.get("accuracy_score", 0))
        fluency = float(report.get("fluency_score", 0))
        prosody = report.get("prosody_score", None)

        if accuracy < 95:
            recommendations.append("Repeat the sentence slowly and focus on crisp consonants and vowel clarity.")
        if fluency < 95:
            recommendations.append("Practice reading the sentence aloud several times to improve flow.")
        if prosody is not None and float(prosody) < 80:
            recommendations.append("Try varying stress and intonation to make the speech sound more natural.")
        if overall >= 90:
            recommendations.append("Keep practicing with longer sentences to build consistency.")
        else:
            recommendations.append("Break the sentence into smaller chunks and practice each chunk separately.")

        return recommendations

    def _compose_full_report(
        self,
        summary: str,
        strengths: list[str],
        weaknesses: list[str],
        recommendations: list[str],
    ) -> str:
        parts = [
            f"Summary: {summary}",
            "",
            "Strengths:",
            *[f"- {item}" for item in strengths],
            "",
            "Weaknesses:",
            *[f"- {item}" for item in weaknesses],
            "",
            "Recommendations:",
            *[f"- {item}" for item in recommendations],
        ]
        return "\n".join(parts)

    def _safe_parse_json(self, text: str) -> Optional[dict[str, Any]]:
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            return None

        return parsed if isinstance(parsed, dict) else None

    def _ensure_string_list(self, value: Any) -> list[str]:
        if not isinstance(value, list):
            return []
        return [str(item).strip() for item in value if str(item).strip()]


def generate_ai_report(
    azure_report: PronunciationReport | dict[str, Any],
    reference_text: str,
    language: str = "en-US",
    learner_name: str | None = None,
) -> dict[str, Any]:
    """
    Convenience wrapper for generating an AI report.
    """
    service = GeminiReportService()
    return service.generate_report(
        azure_report=azure_report,
        reference_text=reference_text,
        language=language,
        learner_name=learner_name,
    )