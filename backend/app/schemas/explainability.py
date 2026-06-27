"""Explainability response schemas."""

from pydantic import BaseModel, Field

from app.schemas.models import FeatureImportanceItem


class ConfidenceSummary(BaseModel):
    """Summary of prediction confidence values."""

    available: bool
    average: float | None = None
    minimum: float | None = None
    maximum: float | None = None


class ExplainabilityResponse(BaseModel):
    """Plain explainability payload for a stored model result."""

    result_id: str
    model_type: str
    feature_importance: list[FeatureImportanceItem] = Field(default_factory=list)
    shap_values: list[dict[str, float]] | None = None
    confidence_scores: ConfidenceSummary | None = None
    summary_text: str


class ShapResponse(BaseModel):
    """SHAP calculation response or fallback."""

    supported: bool
    shap_summary: str
    shap_values_sample: list[dict[str, float]] = Field(default_factory=list)
