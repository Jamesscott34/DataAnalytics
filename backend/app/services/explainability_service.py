"""Explainability helpers for stored model results."""

from sqlalchemy.orm import Session

from app.schemas.explainability import (
    ConfidenceSummary,
    ExplainabilityResponse,
    ShapResponse,
)
from app.schemas.models import ClassificationResult, RegressionResult
from app.services.classification_service import (
    ClassificationError,
    classification_service,
)
from app.services.regression_service import RegressionError, regression_service


class ExplainabilityError(ValueError):
    """Raised when explainability cannot find a model result."""


class ExplainabilityService:
    """Build lightweight explainability summaries from stored model results."""

    def explain_result(
        self,
        result_id: str,
        db: Session | None = None,
    ) -> ExplainabilityResponse:
        """Return explainability data for a regression or classification result."""
        regression_result = result_persistence_service_load_regression(
            result_id,
            db,
        )
        if regression_result is not None:
            return ExplainabilityResponse(
                result_id=result_id,
                model_type=regression_result.model_type,
                feature_importance=regression_result.feature_importance,
                shap_values=None,
                confidence_scores=None,
                summary_text=(
                    "Feature importance is based on model coefficients or tree impurity "
                    "importance. SHAP is not computed in this lightweight runtime."
                ),
            )

        classification_result = result_persistence_service_load_classification(
            result_id,
            db,
        )
        if classification_result is not None:
            confidence_values = [
                prediction.confidence
                for prediction in classification_result.predictions
                if prediction.confidence is not None
            ]
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
                model_type=classification_result.model_type,
                confidence_scores=confidence,
                summary_text=(
                    "Classification explainability includes prediction confidence where "
                    "the selected estimator exposes probabilities."
                ),
            )

        raise ExplainabilityError("Model result not found")

    def shap_values(self, result_id: str, db: Session | None = None) -> ShapResponse:
        """Return a SHAP fallback for supported result IDs."""
        self.explain_result(result_id, db)
        return ShapResponse(
            supported=False,
            shap_summary=(
                "SHAP values are not available in this local build. Use feature "
                "importance and confidence summaries as the fallback explanation."
            ),
            shap_values_sample=[],
        )


def result_persistence_service_load_regression(
    result_id: str,
    db: Session | None,
) -> RegressionResult | None:
    """Load a regression result without raising when missing."""
    try:
        return regression_service.get_result(result_id, db)
    except RegressionError:
        return None


def result_persistence_service_load_classification(
    result_id: str,
    db: Session | None,
) -> ClassificationResult | None:
    """Load a classification result without raising when missing."""
    try:
        return classification_service.get_result(result_id, db)
    except ClassificationError:
        return None


explainability_service = ExplainabilityService()
