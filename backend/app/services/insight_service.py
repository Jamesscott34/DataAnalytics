"""Plain-English analysis insight generation."""

import json
from urllib import request as urllib_request

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.generated_insight import GeneratedInsight
from app.schemas.insights import InsightRequest, InsightResponse
from app.services.business_analytics_service import (
    BusinessAnalyticsError,
    business_analytics_service,
)
from app.services.classification_service import (
    ClassificationError,
    classification_service,
)
from app.services.recommendation_service import (
    RecommendationError,
    recommendation_service,
)
from app.services.regression_service import RegressionError, regression_service


class InsightError(ValueError):
    """Raised when an insight cannot be found or generated."""


class InsightService:
    """Generate and persist analysis summaries."""

    def generate(self, db: Session, payload: InsightRequest) -> InsightResponse:
        """Generate an insight using LLM config when available, otherwise fallback."""
        context = self._result_context(db, payload.result_id, payload.analysis_type)
        settings = get_settings()
        if settings.llm_api_key and settings.llm_api_base_url and settings.llm_model:
            summary = self._call_llm(context)
            source = "llm"
        else:
            summary = self._fallback_summary(context)
            source = "fallback"

        insight = GeneratedInsight(
            result_id=payload.result_id,
            job_id=payload.job_id,
            analysis_type=payload.analysis_type,
            source=source,
            summary=summary,
        )
        db.add(insight)
        db.commit()
        db.refresh(insight)
        return self._to_response(insight)

    def get(self, db: Session, insight_id: int) -> InsightResponse:
        """Return one stored insight."""
        insight = db.get(GeneratedInsight, insight_id)
        if insight is None:
            raise InsightError("Insight not found")
        return self._to_response(insight)

    def get_by_job(self, db: Session, job_id: str) -> InsightResponse:
        """Return the latest insight for a job id."""
        insight = (
            db.query(GeneratedInsight)
            .filter(GeneratedInsight.job_id == job_id)
            .order_by(GeneratedInsight.created_at.desc(), GeneratedInsight.id.desc())
            .first()
        )
        if insight is None:
            raise InsightError("Insight not found")
        return self._to_response(insight)

    def _result_context(
        self,
        db: Session,
        result_id: str,
        analysis_type: str,
    ) -> dict[str, object]:
        try:
            regression_result = regression_service.get_result(result_id, db)
            return {
                "analysis_type": analysis_type,
                "model_type": regression_result.model_type,
                "algorithm": regression_result.algorithm,
                "target": regression_result.target_column,
                "metrics": regression_result.metrics.model_dump(),
                "top_features": [
                    item.model_dump() for item in regression_result.feature_importance[:5]
                ],
            }
        except RegressionError:
            pass

        try:
            classification_result = classification_service.get_result(result_id, db)
            return {
                "analysis_type": analysis_type,
                "model_type": classification_result.model_type,
                "algorithm": classification_result.algorithm,
                "target": classification_result.target_column,
                "metrics": classification_result.metrics.model_dump(),
            }
        except ClassificationError:
            pass

        try:
            similarity_result = recommendation_service.get_result(result_id, db)
            return {
                "analysis_type": analysis_type,
                "model_type": similarity_result.model_type,
                "mode": similarity_result.mode,
                "suitable": similarity_result.suitable,
                "suitability_note": similarity_result.suitability_note,
                "top_pairs": [
                    item.model_dump() for item in similarity_result.top_pairs[:3]
                ],
            }
        except RecommendationError:
            pass

        try:
            business_result = business_analytics_service.get_result(result_id, db)
            return {
                "analysis_type": analysis_type,
                "model_type": "business",
                "kpis": [item.model_dump() for item in business_result.kpis],
                "suitability_note": business_result.suitability_note,
            }
        except BusinessAnalyticsError:
            pass

        return {
            "analysis_type": analysis_type,
            "model_type": "unknown",
            "result_id": result_id,
        }

    def _fallback_summary(self, context: dict[str, object]) -> str:
        model_type = str(context.get("model_type", "analysis"))
        analysis_type = str(context.get("analysis_type", model_type))
        metrics = context.get("metrics")
        if isinstance(metrics, dict) and metrics:
            metric_text = ", ".join(f"{key}: {value}" for key, value in metrics.items())
            return (
                f"Fallback insight for {analysis_type}: the {model_type} result was "
                f"generated successfully. Key metrics are {metric_text}."
            )
        note = context.get("suitability_note")
        if note:
            return f"Fallback insight for {analysis_type}: {note}"
        return (
            f"Fallback insight for {analysis_type}: analysis completed, but no detailed "
            "model metrics were available for summarization."
        )

    def _call_llm(self, context: dict[str, object]) -> str:
        settings = get_settings()
        payload = {
            "model": settings.llm_model,
            "messages": [
                {
                    "role": "system",
                    "content": "Summarize analytics results in concise plain English.",
                },
                {"role": "user", "content": json.dumps(context, default=str)},
            ],
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib_request.Request(
            settings.llm_api_base_url,
            data=data,
            headers={
                "Authorization": f"Bearer {settings.llm_api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib_request.urlopen(req, timeout=15) as response:  # noqa: S310
            body = json.loads(response.read().decode("utf-8"))
        try:
            return str(body["choices"][0]["message"]["content"]).strip()
        except (KeyError, IndexError, TypeError) as exc:
            raise InsightError("LLM response did not contain summary text") from exc

    def _to_response(self, insight: GeneratedInsight) -> InsightResponse:
        return InsightResponse(
            id=insight.id,
            result_id=insight.result_id,
            job_id=insight.job_id,
            analysis_type=insight.analysis_type,
            summary=insight.summary,
            source=insight.source,  # type: ignore[arg-type]
            generated_at=insight.created_at,
        )


insight_service = InsightService()
