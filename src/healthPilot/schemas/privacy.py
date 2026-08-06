from pydantic import BaseModel, Field


class CoachRequest(BaseModel):
    message: str = Field(min_length=1, description="User message to the wellness coach")
    biomarkers: dict[str, float | int | str] = Field(
        default_factory=dict,
        description="Structured biomarkers (never raw report text)",
    )
    user_facing: bool = Field(
        default=True,
        description="When false, skips NeMo output rail (internal agents)",
    )


class CoachResponse(BaseModel):
    response: str
    deidentified_input: str
    blocked: bool = False
    error: str | None = None


class PrivacyHealthResponse(BaseModel):
    presidio: bool
    nemo_guardrails: bool
    ready: bool
