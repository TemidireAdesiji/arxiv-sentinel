"""GET /api/v1/health — per-service health check."""

from __future__ import annotations

from fastapi import APIRouter

from sentinel.api.deps import (
    DbDep,
    LlmDep,
    SearchDep,
    SettingsDep,
)
from sentinel.api.schemas import (
    HealthPayload,
    ServiceInfo,
)

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    response_model=HealthPayload,
)
async def health_check(
    cfg: SettingsDep,
    db: DbDep,
    search: SearchDep,
    llm: LlmDep,
) -> HealthPayload:
    """Report service health for every dependency."""
    services: dict[str, ServiceInfo] = {}

    if db.verify_connection():
        services["database"] = ServiceInfo(
            status="healthy",
            message="Connected",
        )
    else:
        services["database"] = ServiceInfo(
            status="unhealthy",
            message="Unreachable",
        )

    os_health = search.check_health()
    services["opensearch"] = ServiceInfo(
        status=os_health.get("status", "unknown"),
        message=(f"docs={os_health.get('documents', '?')}"),
    )

    llm_health = await llm.check_health()
    services["ollama"] = ServiceInfo(
        status=llm_health.get("status", "unknown"),
        message=llm_health.get(
            "version",
            llm_health.get("error", ""),
        ),
    )

    all_ok = all(s.status == "healthy" for s in services.values())
    return HealthPayload(
        status="ok" if all_ok else "degraded",
        version=cfg.app_version,
        environment=cfg.environment,
        service_name=cfg.service_name,
        services=services,
    )
