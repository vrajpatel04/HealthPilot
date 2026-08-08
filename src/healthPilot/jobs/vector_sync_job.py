from apscheduler.schedulers.asyncio import AsyncIOScheduler

from healthPilot.core.config import get_settings
from healthPilot.core.database import AsyncSessionLocal
from healthPilot.services.vector_sync_service import VectorSyncService

_scheduler: AsyncIOScheduler | None = None


async def _run_vector_sync_job() -> None:
    async with AsyncSessionLocal() as session:
        await VectorSyncService(session).sweep_pending()


def start_vector_sync_scheduler() -> AsyncIOScheduler:
    global _scheduler
    settings = get_settings()
    _scheduler = AsyncIOScheduler()
    _scheduler.add_job(
        _run_vector_sync_job,
        "interval",
        seconds=settings.VECTOR_SYNC_INTERVAL_SECONDS,
        id="vector_sync_sweep",
        replace_existing=True,
    )
    _scheduler.start()
    return _scheduler


def stop_vector_sync_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
