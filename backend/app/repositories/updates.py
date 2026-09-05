from datetime import datetime, timezone
from urllib.parse import urlparse

from sqlalchemy.orm import Session

from app.ingestion.processor import ProcessedUpdate
from app.models import DeveloperUpdate, IngestionRun, Source, Technology


class UpdateRepository:
    """PostgreSQL operations for developer updates and ingestion runs."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_active_technologies(self, technology_slugs: list[str] | None = None) -> list[Technology]:
        """Return active technologies, optionally filtered by slug."""
        query = self.db.query(Technology).filter(Technology.active.is_(True))
        if technology_slugs:
            query = query.filter(Technology.slug.in_(technology_slugs))
        return query.all()

    def update_url_exists(self, url: str) -> bool:
        """Return true when a canonical URL is already stored."""
        return self.db.query(DeveloperUpdate).filter(DeveloperUpdate.canonical_url == url).first() is not None

    def fingerprint_exists(self, fingerprint: str) -> bool:
        """Return true when equivalent update content is already stored."""
        return self.db.query(DeveloperUpdate).filter(DeveloperUpdate.content_fingerprint == fingerprint).first() is not None

    def remove_existing_urls(self, urls: list[str]) -> tuple[list[str], int]:
        """Deduplicate URLs and remove ones already saved."""
        new_urls: list[str] = []
        duplicates = 0
        for url in dict.fromkeys(urls):
            if self.update_url_exists(url):
                duplicates += 1
            else:
                new_urls.append(url)
        return new_urls, duplicates

    def get_or_create_source(self, url: str, technology: Technology) -> Source:
        """Find or create a source row for an update URL."""
        domain = urlparse(url).netloc.lower().removeprefix("www.")
        source = self.db.query(Source).filter(Source.domain == domain).first()
        if source:
            return source
        source = Source(name=domain, domain=domain, source_type="trusted", official=domain in technology.official_domains)
        self.db.add(source)
        self.db.flush()
        return source

    def save_update(self, technology: Technology, update: ProcessedUpdate) -> DeveloperUpdate:
        """Store one processed update for a technology."""
        source = self.get_or_create_source(update.canonical_url, technology)
        saved = DeveloperUpdate(
            title=update.title,
            canonical_url=update.canonical_url,
            source=source,
            original_excerpt=update.original_excerpt,
            extracted_content=update.extracted_content,
            summary=update.summary,
            why_it_matters=update.why_it_matters,
            recommended_action=update.recommended_action,
            version=update.version,
            category=update.category,
            impact_level=update.impact_level,
            published_at=None,
            content_fingerprint=update.content_fingerprint,
            raw_metadata=update.raw_metadata,
            technologies=[technology],
        )
        self.db.add(saved)
        self.db.flush()
        return saved

    def create_ingestion_run(self, technology: Technology) -> IngestionRun:
        """Create a running ingestion run row."""
        run = IngestionRun(technology=technology, tavily_endpoint="search/extract/crawl", status="running")
        self.db.add(run)
        self.db.flush()
        return run

    def complete_ingestion_run(
        self,
        run: IngestionRun,
        reason: str,
        results_found: int,
        results_saved: int,
        duplicates_skipped: int,
        note: str | None = None,
        status: str = "completed",
    ) -> IngestionRun:
        """Mark an ingestion run as completed or skipped."""
        run.status = status
        run.results_found = results_found
        run.results_saved = results_saved
        run.duplicates_skipped = duplicates_skipped
        run.completed_at = datetime.now(timezone.utc)
        run.error_message = f"{reason}: {note}" if note else reason
        self.db.add(run)
        return run

    def fail_ingestion_run(self, run: IngestionRun, reason: str, error: str) -> IngestionRun:
        """Mark an ingestion run as failed."""
        run.status = "failed"
        run.completed_at = datetime.now(timezone.utc)
        run.error_message = f"{reason}: {error}"
        self.db.add(run)
        return run
