from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import settings
from app.ingestion.refresh_coordinator import refresh_coordinator

# main.py is the backend entry point.
# It creates the FastAPI app, connects all API routes, and starts the scheduler.
app = FastAPI(title="DevPulse AI API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)

scheduler = BackgroundScheduler(timezone="UTC")


@app.on_event("startup")
def start_scheduler() -> None:
    """Start scheduled Tavily refresh jobs when the API server boots."""
    if not scheduler.running:
        scheduler.add_job(
            refresh_coordinator.start_background,
            "interval",
            hours=settings.scheduled_refresh_hours,
            id="scheduled-tavily-ingestion",
            replace_existing=True,
            kwargs={"reason": "scheduled"},
        )
        scheduler.start()


@app.on_event("shutdown")
def stop_scheduler() -> None:
    """Stop background scheduling cleanly when the API server shuts down."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
