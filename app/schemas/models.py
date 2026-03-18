from typing import Any

from pydantic import BaseModel


class ModelInfo(BaseModel):
    name: str
    size: int | None = None
    digest: str | None = None
    modified_at: str | None = None
    details: dict[str, Any] | None = None


class ModelsResponse(BaseModel):
    count: int
    models: list[ModelInfo]
