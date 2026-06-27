"""Analytics plugin API schemas."""

from typing import Any

from pydantic import BaseModel, Field


class PluginInfo(BaseModel):
    """Registered analytics plugin metadata."""

    name: str
    display_name: str
    description: str
    applicable: bool
    reason: str | None = None


class PluginListResponse(BaseModel):
    """List of plugins with optional applicability for a file."""

    plugins: list[PluginInfo]


class PluginRunRequest(BaseModel):
    """Run a plugin against a dataset."""

    file_id: int
    params: dict[str, Any] = Field(default_factory=dict)


class PluginRunResponse(BaseModel):
    """Plugin execution result."""

    plugin_name: str
    file_id: int
    result_id: str
    summary: str
    metrics: dict[str, Any] = Field(default_factory=dict)
