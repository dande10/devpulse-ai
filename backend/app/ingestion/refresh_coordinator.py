from datetime import datetime, timedelta, timezone
from threading import Lock, Thread

from sqlalchemy import func

from app.core.config import settings
from app.database.session import SessionLocal
from app.ingestion.pipeline import IngestionPipeline
from app.models import DeveloperUpdate, IngestionRun, Technology


class RefreshCoordinator:
    """Controls background Tavily refresh jobs.

    The coordinator prevents duplicate refreshes, remembers the current status
    for the frontend, and applies a cooldown to user-triggered refreshes.
    """

    def __init__(self) -> None:
        self._lock = Lock()
        self._running = False
        self._last_user_refresh_at: datetime | None = None
        self._last_completed_at: datetime | None = None
        self._last_started_at: datetime | None = None
        self._last_status = "idle"
        self._last_error: str | None = None

    def status(self) -> dict:
        with self._lock:
            cooldown_until = None
            if self._last_user_refresh_at:
                cooldown_until = self._last_user_refresh_at + timedelta(seconds=settings.user_refresh_cooldown_seconds)
            return {
                "running": self._running,
                "last_started_at": self._last_started_at,
                "last_completed_at": self._last_completed_at,
                "last_status": self._last_status,
                "last_error": self._last_error,
                "cooldown_until": cooldown_until,
            }

    def is_stale(self, technology_slugs: list[str] | None = None) -> bool:
        """Return True when saved updates are older than the configured interval."""
        with SessionLocal() as db:
            query = db.query(func.max(DeveloperUpdate.updated_at))
            if technology_slugs:
                query = query.join(DeveloperUpdate.technologies).filter(Technology.slug.in_(technology_slugs))
            last_update = query.scalar()
            if not last_update:
                return True
            return last_update < datetime.now(timezone.utc) - timedelta(hours=settings.feed_stale_after_hours)

    def start_if_stale(self, technology_slugs: list[str] | None = None) -> bool:
        """Start background ingestion only when the saved feed is stale."""
        if not self.is_stale(technology_slugs):
            return False
        return self.start_background(technology_slugs, reason="stale-feed")

    def request_user_refresh(self, technology_slugs: list[str] | None = None) -> tuple[bool, str]:
        """Handle the user's 'Check for latest updates' button."""
        now = datetime.now(timezone.utc)
        with self._lock:
            if self._running:
                return False, "Refresh already running."
            if self._last_user_refresh_at:
                cooldown_until = self._last_user_refresh_at + timedelta(seconds=settings.user_refresh_cooldown_seconds)
                if now < cooldown_until:
                    seconds = int((cooldown_until - now).total_seconds())
                    return False, f"Please wait {seconds} seconds before checking again."
            self._last_user_refresh_at = now
        self.start_background(technology_slugs, reason="user-request")
        return True, "Refresh started."

    def start_background(self, technology_slugs: list[str] | None = None, reason: str = "scheduled") -> bool:
        """Run ingestion in a daemon thread so API responses do not block."""
        with self._lock:
            if self._running:
                return False
            self._running = True
            self._last_started_at = datetime.now(timezone.utc)
            self._last_status = "running"
            self._last_error = None
        thread = Thread(target=self._run, args=(technology_slugs, reason), daemon=True)
        thread.start()
        return True

    def _run(self, technology_slugs: list[str] | None, reason: str) -> None:
        """Open a database session and execute the Tavily ingestion pipeline."""
        try:
            with SessionLocal() as db:
                IngestionPipeline(db).refresh(technology_slugs, reason=reason)
            status = "completed"
            error = None
        except Exception as exc:
            status = "failed"
            error = str(exc)
            with SessionLocal() as db:
                db.add(
                    IngestionRun(
                        tavily_endpoint="search/extract/crawl",
                        status="failed",
                        completed_at=datetime.now(timezone.utc),
                        error_message=str(exc),
                    )
                )
                db.commit()
        with self._lock:
            self._running = False
            self._last_completed_at = datetime.now(timezone.utc)
            self._last_status = status
            self._last_error = error


refresh_coordinator = RefreshCoordinator()
