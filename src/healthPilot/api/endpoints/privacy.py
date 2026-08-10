from fastapi import APIRouter, HTTPException

from healthPilot.agents.graph import coach_graph
from healthPilot.privacy import (
    GuardrailsClient,
    PresidioClient,
    PrivacyPipelineBlockedError,
)
from healthPilot.schemas.privacy import CoachRequest, CoachResponse, PrivacyHealthResponse

router = APIRouter(tags=["privacy"])


@router.get("/health", response_model=PrivacyHealthResponse)
async def privacy_health() -> PrivacyHealthResponse:
    presidio = PresidioClient()
    guardrails = GuardrailsClient()
    presidio_ok = await presidio.health_ok()
    nemo_ok = await guardrails.health_ok()
    return PrivacyHealthResponse(
        presidio=presidio_ok,
        nemo_guardrails=nemo_ok,
        ready=presidio_ok and nemo_ok,
    )


@router.post("/coach", response_model=CoachResponse)
async def coach(request: CoachRequest) -> CoachResponse:
    """
    Run the privacy pipeline: Presidio → NeMo input → LLM → NeMo output → Presidio de-anonymize.
    """
    try:
        result = await coach_graph.ainvoke(
            {
                "raw_text": request.message,
                "biomarkers": request.biomarkers,
                "user_facing": request.user_facing,
                "messages": [],
            }
        )
    except PrivacyPipelineBlockedError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    if result.get("error"):
        raise HTTPException(status_code=503, detail=result["error"])

    return CoachResponse(
        response=result.get("final_response")
        or result.get("validated_response")
        or result.get("llm_response")
        or "",
        deidentified_input=result.get("deidentified_text") or "",
    )
