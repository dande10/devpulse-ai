from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from app.core.config import settings
from app.database.session import get_db
from app.ingestion.pipeline import IngestionPipeline
from app.ingestion.refresh_coordinator import refresh_coordinator
from app.models import DeveloperUpdate, IngestionRun, Technology
from app.schemas.technology import TechnologyRead
from app.schemas.update import DeveloperUpdateRead, FeedResponse
from app.seed import seed_database

router = APIRouter(prefix="/api")


@router.get("/health")
def health(db: Session = Depends(get_db)) -> dict:
    """Simple backend status check used by local development and deployment monitors."""
    seed_database(db)
    return {"status": "ok", "tavily_configured": bool(settings.tavily_api_key)}


@router.get("/technologies", response_model=list[TechnologyRead])
def technologies(db: Session = Depends(get_db)) -> list[Technology]:
    """Return configurable technology stack options for the React UI."""
    seed_database(db)
    return db.query(Technology).filter(Technology.active.is_(True)).order_by(Technology.name).all()


def updates_query(db: Session):
    """Base PostgreSQL query for feed/search pages.

    Tavily is not called here. This keeps filtering, sorting, and pagination fast.
    """
    return (
        db.query(DeveloperUpdate)
        .options(joinedload(DeveloperUpdate.source), joinedload(DeveloperUpdate.technologies))
        .filter(~DeveloperUpdate.summary.ilike("%fallback because interactive scripts did not run%"))
        .filter(~DeveloperUpdate.summary.ilike("%Solutions & technology Security Ecosystem Industries%"))
        .filter(~DeveloperUpdate.summary.ilike("%Make Text Smaller%"))
        .filter(~DeveloperUpdate.title.ilike("%Gartner MQ%"))
        .filter(~DeveloperUpdate.title.ilike("%Certification%"))
    )


def apply_filters(query, technology_slugs, category, impact_level, date_from, date_to):
    if technology_slugs:
        query = query.join(DeveloperUpdate.technologies).filter(Technology.slug.in_(technology_slugs))
    if category and category != "All":
        query = query.filter(DeveloperUpdate.category == category)
    if impact_level:
        query = query.filter(DeveloperUpdate.impact_level == impact_level)
    if date_from:
        query = query.filter(DeveloperUpdate.published_at >= date_from)
    if date_to:
        query = query.filter(DeveloperUpdate.published_at <= date_to)
    return query


@router.get("/feed", response_model=FeedResponse)
def feed(
    technology_slugs: list[str] | None = Query(default=None),
    category: str | None = None,
    impact_level: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    sort: str = "newest",
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> FeedResponse:
    """Return saved PostgreSQL updates.

    Tavily is not called from this endpoint. New data is fetched only when the
    user clicks "Check for latest updates", which calls POST /api/refresh.
    """
    seed_database(db)
    refresh_status = refresh_coordinator.status()
    base = apply_filters(updates_query(db), technology_slugs, category, impact_level, date_from, date_to)
    total = base.count()
    order = DeveloperUpdate.published_at.asc() if sort == "oldest" else DeveloperUpdate.published_at.desc().nullslast()
    items = base.order_by(order).offset((page - 1) * page_size).limit(page_size).all()
    since = datetime.now(timezone.utc) - timedelta(days=7)
    return FeedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        new_updates=db.query(DeveloperUpdate).filter(DeveloperUpdate.discovered_at >= since).count(),
        requiring_action=db.query(DeveloperUpdate).filter(DeveloperUpdate.recommended_action.is_not(None)).count(),
        technologies_tracked=len(set(technology_slugs or [])) or db.query(Technology).filter(Technology.active.is_(True)).count(),
        last_updated_at=db.query(func.max(DeveloperUpdate.updated_at)).scalar(),
        refresh_running=refresh_status["running"],
        refresh_started=False,
        cooldown_until=refresh_status["cooldown_until"],
    )


@router.get("/updates", response_model=list[DeveloperUpdateRead])
def updates(page: int = 1, page_size: int = 20, db: Session = Depends(get_db)) -> list[DeveloperUpdate]:
    seed_database(db)
    return updates_query(db).order_by(DeveloperUpdate.published_at.desc().nullslast()).offset((page - 1) * page_size).limit(page_size).all()


@router.get("/updates/{update_id}", response_model=DeveloperUpdateRead)
def update_detail(update_id: int, db: Session = Depends(get_db)) -> DeveloperUpdate:
    seed_database(db)
    update = updates_query(db).filter(DeveloperUpdate.id == update_id).first()
    if not update:
        raise HTTPException(status_code=404, detail="Update not found")
    return update


@router.get("/search", response_model=FeedResponse)
def search(
    q: str,
    technology_slugs: list[str] | None = Query(default=None),
    category: str | None = None,
    impact_level: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> FeedResponse:
    """Search saved PostgreSQL updates without spending Tavily credits."""
    seed_database(db)
    text = f"%{q.lower()}%"
    query = updates_query(db).filter(
        or_(
            func.lower(DeveloperUpdate.title).like(text),
            func.lower(DeveloperUpdate.summary).like(text),
            func.lower(DeveloperUpdate.why_it_matters).like(text),
            func.lower(DeveloperUpdate.category).like(text),
            func.lower(DeveloperUpdate.impact_level).like(text),
        )
    )
    lowered = q.lower()
    inferred_slugs = [tech.slug for tech in db.query(Technology).all() if tech.name.lower() in lowered or tech.slug in lowered]
    slugs = technology_slugs or inferred_slugs
    if slugs:
        query = query.join(DeveloperUpdate.technologies).filter(Technology.slug.in_(slugs))
    if category and category != "All":
        query = query.filter(DeveloperUpdate.category == category)
    if impact_level:
        query = query.filter(DeveloperUpdate.impact_level == impact_level)
    if "this month" in lowered:
        query = query.filter(DeveloperUpdate.published_at >= datetime.now(timezone.utc) - timedelta(days=31))
    if "security" in lowered:
        query = query.filter(DeveloperUpdate.category == "Security")
    if "breaking" in lowered:
        query = query.filter(DeveloperUpdate.category == "Breaking")
    if "require action" in lowered or "requires action" in lowered:
        query = query.filter(DeveloperUpdate.recommended_action.is_not(None))

    total = query.count()
    items = query.order_by(DeveloperUpdate.published_at.desc().nullslast()).offset((page - 1) * page_size).limit(page_size).all()
    return FeedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        new_updates=total,
        requiring_action=sum(1 for item in items if item.recommended_action),
        technologies_tracked=len(set(technology_slugs or slugs)),
        last_updated_at=db.query(func.max(DeveloperUpdate.updated_at)).scalar(),
        refresh_running=refresh_coordinator.status()["running"],
        refresh_started=False,
        cooldown_until=refresh_coordinator.status()["cooldown_until"],
    )


@router.get("/refresh/status")
def refresh_status() -> dict:
    """Tell React whether a background Tavily refresh is currently running."""
    return refresh_coordinator.status()


@router.post("/refresh")
def request_refresh(technology_slugs: list[str] | None = Body(default=None)) -> dict:
    """User-facing 'Check for latest updates' endpoint.

    It starts Tavily ingestion in the background and uses a shared cooldown so
    repeated clicks do not burn API credits.
    """
    started, message = refresh_coordinator.request_user_refresh(technology_slugs)
    return {"started": started, "message": message, **refresh_coordinator.status()}


@router.post("/admin/refresh")
def admin_refresh(technology_slugs: list[str] | None = None, db: Session = Depends(get_db)) -> dict:
    """Manual refresh endpoint for debugging or operational use."""
    seed_database(db)
    runs = IngestionPipeline(db).refresh(technology_slugs)
    return {"runs": [{"id": run.id, "status": run.status, "error_message": run.error_message} for run in runs]}


@router.get("/admin/ingestion-runs")
def ingestion_runs(db: Session = Depends(get_db)) -> list[dict]:
    """Return recent ingestion history: saved count, duplicates, failures, timing."""
    seed_database(db)
    runs = db.query(IngestionRun).order_by(IngestionRun.started_at.desc()).limit(50).all()
    return [
        {
            "id": run.id,
            "technology_id": run.technology_id,
            "tavily_endpoint": run.tavily_endpoint,
            "started_at": run.started_at,
            "completed_at": run.completed_at,
            "status": run.status,
            "results_found": run.results_found,
            "results_saved": run.results_saved,
            "duplicates_skipped": run.duplicates_skipped,
            "error_message": run.error_message,
        }
        for run in runs
    ]
