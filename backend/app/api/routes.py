from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from app.api.admin_auth import require_admin
from app.core.config import settings
from app.database.session import get_db
from app.ingestion.pipeline import IngestionPipeline
from app.ingestion.refresh_coordinator import refresh_coordinator
from app.models import DeveloperUpdate, Feedback, IngestionRun, Technology, TechnologyRequest
from app.schemas.feedback import FeedbackCreate, FeedbackPublicRead, FeedbackRead
from app.schemas.technology import TechnologyRead
from app.schemas.technology_request import TechnologyRequestCreate, TechnologyRequestRead
from app.schemas.update import DeveloperUpdateRead, FeedResponse
from app.seed import seed_database
from app.services.notifications import send_notification_email

router = APIRouter(prefix="/api")

# Default recency window for the feed/search: ~6 months back, no upper bound
# (future-dated announcements still show). Updates with no known publish date
# (older content ingested before Tavily topic="news" search was wired in)
# still show too, rather than disappearing outright.
DEFAULT_RECENCY_DAYS = 183


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


@router.post("/technology-requests", response_model=TechnologyRequestRead)
def create_technology_request(payload: TechnologyRequestCreate, db: Session = Depends(get_db)) -> TechnologyRequest:
    """Let any visitor ask us to start tracking a technology.

    Does not create a Technology row — an admin reviews the queue and, if it
    makes sense, hand-configures trusted/official domains in seed.py the same
    way every other tracked technology is. Re-requesting the same name just
    bumps its count instead of creating a duplicate row.
    """
    normalized = payload.name.strip().lower()
    existing = db.query(TechnologyRequest).filter(TechnologyRequest.normalized_name == normalized).first()
    if existing:
        existing.request_count += 1
        if payload.note and not existing.note:
            existing.note = payload.note
        db.commit()
        db.refresh(existing)
        send_notification_email(
            f"DevPulse: technology request bumped — {existing.name}",
            f"{existing.name} was requested again (now {existing.request_count} times).\n\nNote: {payload.note or '(none)'}",
        )
        return existing

    request = TechnologyRequest(name=payload.name.strip(), normalized_name=normalized, note=payload.note)
    db.add(request)
    db.commit()
    db.refresh(request)
    send_notification_email(
        f"DevPulse: new technology request — {request.name}",
        f"{request.name}\n\nNote: {payload.note or '(none)'}",
    )
    return request


@router.post("/feedback", response_model=FeedbackRead)
def create_feedback(payload: FeedbackCreate, db: Session = Depends(get_db)) -> Feedback:
    """Accept a review from the public site.

    Saved as "pending" — no email yet. The admin reviews the queue via
    GET /api/admin/feedback and only reviews approved through
    POST /api/admin/feedback/{id}/status get emailed.
    """
    feedback = Feedback(name=payload.name, email=payload.email, rating=payload.rating, message=payload.message.strip())
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return feedback


@router.get("/admin/feedback", response_model=list[FeedbackRead], dependencies=[Depends(require_admin)])
def admin_list_feedback(db: Session = Depends(get_db)) -> list[Feedback]:
    """Full review queue (every status) for local admin moderation."""
    return db.query(Feedback).order_by(Feedback.created_at.desc()).all()


@router.get("/reviews", response_model=list[FeedbackPublicRead])
def public_reviews(db: Session = Depends(get_db)) -> list[Feedback]:
    """Approved reviews shown on the public site — no email addresses."""
    return (
        db.query(Feedback)
        .filter(Feedback.status == "approved")
        .order_by(Feedback.created_at.desc())
        .limit(24)
        .all()
    )


@router.post("/admin/feedback/{feedback_id}/status", response_model=FeedbackRead, dependencies=[Depends(require_admin)])
def admin_update_feedback_status(feedback_id: int, status: str = Body(embed=True), db: Session = Depends(get_db)) -> Feedback:
    """Approve/reject a review. Approving emails the full review to the admin inbox."""
    if status not in {"pending", "approved", "rejected"}:
        raise HTTPException(status_code=400, detail="status must be pending, approved, or rejected")
    feedback = db.query(Feedback).filter(Feedback.id == feedback_id).first()
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")
    newly_approved = status == "approved" and feedback.status != "approved"
    feedback.status = status
    db.commit()
    db.refresh(feedback)
    if newly_approved:
        send_notification_email(
            "DevPulse: approved review" + (f" ({feedback.rating}/5)" if feedback.rating else ""),
            f"From: {feedback.name or 'Anonymous'} <{feedback.email or 'no email given'}>\n\n{feedback.message}",
        )
    return feedback


@router.get("/technology-requests", response_model=list[TechnologyRequestRead])
def list_technology_requests(db: Session = Depends(get_db)) -> list[TechnologyRequest]:
    """Public, transparent view of what developers are asking for — pending only."""
    return (
        db.query(TechnologyRequest)
        .filter(TechnologyRequest.status == "pending")
        .order_by(TechnologyRequest.request_count.desc(), TechnologyRequest.created_at.desc())
        .all()
    )


@router.get("/admin/technology-requests", response_model=list[TechnologyRequestRead], dependencies=[Depends(require_admin)])
def admin_list_technology_requests(db: Session = Depends(get_db)) -> list[TechnologyRequest]:
    """Full queue (every status) for the admin reviewing requests locally."""
    return db.query(TechnologyRequest).order_by(TechnologyRequest.request_count.desc(), TechnologyRequest.created_at.desc()).all()


@router.post(
    "/admin/technology-requests/{request_id}/status",
    response_model=TechnologyRequestRead,
    dependencies=[Depends(require_admin)],
)
def admin_update_technology_request_status(request_id: int, status: str = Body(embed=True), db: Session = Depends(get_db)) -> TechnologyRequest:
    """Mark a request approved/rejected/pending. Adding the actual Technology is a separate, manual seed.py change."""
    if status not in {"pending", "approved", "rejected"}:
        raise HTTPException(status_code=400, detail="status must be pending, approved, or rejected")
    request = db.query(TechnologyRequest).filter(TechnologyRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Technology request not found")
    request.status = status
    db.commit()
    db.refresh(request)
    return request


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
        query = query.filter(or_(DeveloperUpdate.published_at >= date_from, DeveloperUpdate.published_at.is_(None)))
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
    effective_date_from = date_from or (datetime.now(timezone.utc) - timedelta(days=DEFAULT_RECENCY_DAYS))
    base = apply_filters(updates_query(db), technology_slugs, category, impact_level, effective_date_from, date_to)
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
    recency_cutoff = datetime.now(timezone.utc) - timedelta(days=DEFAULT_RECENCY_DAYS)
    query = query.filter(or_(DeveloperUpdate.published_at >= recency_cutoff, DeveloperUpdate.published_at.is_(None)))
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


@router.post("/admin/refresh", dependencies=[Depends(require_admin)])
def admin_refresh(technology_slugs: list[str] | None = None, db: Session = Depends(get_db)) -> dict:
    """Manual refresh endpoint for debugging or operational use."""
    seed_database(db)
    runs = IngestionPipeline(db).refresh(technology_slugs)
    return {"runs": [{"id": run.id, "status": run.status, "error_message": run.error_message} for run in runs]}


@router.get("/admin/ingestion-runs", dependencies=[Depends(require_admin)])
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
