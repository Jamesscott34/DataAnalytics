"""Explainability helpers for stored model results."""

from app.schemas.explainability import (
    ConfidenceSummary,
    ExplainabilityResponse,
    ShapResponse,
)
from app.services.classification_service import ClassificationError, classification_service
from app.services.regression_service import RegressionError, regression_service


class ExplainabilityError(ValueError):
    """Raised when explainability cannot find a model result."""


class ExplainabilityService:
    """Build lightweight explainability summaries from in-memory model results."""

    def explain_result(self, result_id: str) -> ExplainabilityResponse:
        """Return explainability data for a regression or classification result."""
        try:
            result = regression_service.get_result(result_id)
            return ExplainabilityResponse(
                result_id=result_id,
                model_type=result.model_type,
                feature_importance=result.feature_importance,
                shap_values=None,
                confidence_scores=None,
                summary_text=(
                    "Feature importance is based on model coefficients or tree impurity "
                    "importance. SHAP is not computed in this lightweight runtime."
                ),
            )
        except RegressionError:
            pass

        try:
            result = classification_service.get_result(result_id)
            confidence_values = [
                prediction.confidence
                for prediction in result.predictions
                if prediction.confidence is not None
            ]
            confidence = None
            if confidence_values:
                confidence = ConfidenceSummary(
                    available=True,
                    average=round(sum(confidence_values) / len(confidence_values), 4),
                    minimum=min(confidence_values),
                    maximum=max(confidence_values),
                )
            else:
                confidence = ConfidenceSummary(available=False)
            return ExplainabilityResponse(
                result_id=result_id,
                model_type=result.model_type,
                confidence_scores=confidence,
                summary_text=(
                    "Classification explainability includes prediction confidence where "
                    "the selected estimator exposes probabilities."
                ),
            )
        except ClassificationError as exc:
            raise ExplainabilityError("Model result not found") from exc

    def shap_values(self, result_id: str) -> ShapResponse:
        """Return a SHAP fallback for supported result IDs."""
        self.explain_result(result_id)
        return ShapResponse(
            supported=False,
            shap_summary=(
                "SHAP values are not available in this local build. Use feature "
                "importance and confidence summaries as the fallback explanation."
            ),
            shap_values_sample=[],
        )


explainability_service = ExplainabilityService()
