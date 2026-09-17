import logging
from urllib.parse import urlparse

from sqlalchemy.orm import Session

from app.ingestion import processor
from app.models import IngestionRun, Technology
from app.repositories.updates import UpdateRepository
from app.services.normalize import canonicalize_url
from app.services.tavily.client import TavilyClient

logger = logging.getLogger(__name__)

# topic="news" is the only Tavily search mode that returns a published_date
# per result — general-topic search and Extract never do. 200 days gives a
# buffer beyond the ~6 month recency window the feed displays by default.
SEARCH_RECENCY_DAYS = 200


class IngestionPipeline:
    """Coordinate Tavily discovery, processing, and PostgreSQL saves."""

    def __init__(self, db: Session, tavily: TavilyClient | None = None, repository: UpdateRepository | None = None) -> None:
        self.db = db
        self.tavily = tavily or TavilyClient()
        self.repository = repository or UpdateRepository(db)

    def refresh(self, technology_slugs: list[str] | None = None, reason: str = "scheduled") -> list[IngestionRun]:
        """Refresh all active technologies or only requested technology slugs."""
        runs: list[IngestionRun] = []
        technologies = self.repository.get_active_technologies(technology_slugs)
        for technology in technologies:
            runs.append(self._refresh_technology(technology, reason))
        return runs

    def _refresh_technology(self, technology: Technology, reason: str) -> IngestionRun:
        """Refresh one technology without stopping later technologies on failure."""
        run = self.repository.create_ingestion_run(technology)
        self.db.commit()

        if not self.tavily.configured:
            return self._skip_missing_api_key(run, reason)

        try:
            urls, found, note, url_dates = self._discover_urls(technology)
            new_urls, duplicate_count = self.repository.remove_existing_urls(urls)
            saved_count, fingerprint_duplicates = self._extract_new_urls(technology, new_urls, url_dates)
            run = self.repository.complete_ingestion_run(
                run,
                reason=reason,
                results_found=found,
                results_saved=saved_count,
                duplicates_skipped=duplicate_count + fingerprint_duplicates,
                note=note,
            )
            self.db.commit()
            return run
        except Exception as exc:
            logger.exception("Tavily ingestion failed for technology %s", technology.slug)
            self.db.rollback()
            run = self.db.merge(run)
            run = self.repository.fail_ingestion_run(run, reason, str(exc))
            self.db.commit()
            return run

    def _discover_urls(self, technology: Technology) -> tuple[list[str], int, str | None, dict[str, str | None]]:
        """Discover trusted update URLs using Tavily Search and optional Crawl."""
        url_dates: dict[str, str | None] = {}
        results_found = 0
        for template in technology.query_templates:
            search = self.tavily.search_updates(
                template, domains=self._search_domains(technology), topic="news", days=SEARCH_RECENCY_DAYS
            )
            results = search.get("results", [])
            results_found += len(results)
            for url, published_date in self._trusted_result_urls(results, technology):
                url_dates.setdefault(url, published_date)

        note = None
        if len(url_dates) < 3 and technology.official_domains:
            try:
                for url, published_date in self._crawl_official_update_pages(technology):
                    url_dates.setdefault(url, published_date)
            except Exception as exc:
                logger.exception("Tavily crawl discovery failed for technology %s", technology.slug)
                note = f"Crawl discovery skipped: {exc}"

        return list(url_dates.keys()), results_found, note, url_dates

    def _extract_new_urls(self, technology: Technology, urls: list[str], url_dates: dict[str, str | None]) -> tuple[int, int]:
        """Extract and process up to eight new URLs for a technology."""
        if not urls:
            return 0, 0
        results = self.tavily.extract_updates(urls[:8]).get("results", [])
        return self._process_results(technology, results, url_dates)

    def _process_results(self, technology: Technology, results: list[dict], url_dates: dict[str, str | None]) -> tuple[int, int]:
        """Save useful extracted updates and count duplicates."""
        saved = 0
        duplicates = 0
        for result in results:
            url = canonicalize_url(result.get("url", ""))
            published_at = processor.parse_published_date(url_dates.get(url))
            processed_update = processor.process(result, published_at=published_at)
            if not processed_update or self.repository.fingerprint_exists(processed_update.content_fingerprint):
                duplicates += 1
                continue
            self.repository.save_update(technology, processed_update)
            saved += 1
        return saved, duplicates

    def _crawl_official_update_pages(self, technology: Technology) -> list[tuple[str, str | None]]:
        """Discover official update pages with Tavily Crawl (never returns a date)."""
        urls: list[tuple[str, str | None]] = []
        for domain in technology.official_domains[:2]:
            crawl = self.tavily.crawl_official_source(f"https://{domain}", allowed_domains=[domain], max_depth=2, max_pages=10)
            urls.extend(self._trusted_result_urls(crawl.get("results", []), technology, update_pages_only=True))
        return urls

    def _trusted_result_urls(
        self, results: list[dict], technology: Technology, update_pages_only: bool = False
    ) -> list[tuple[str, str | None]]:
        """Normalize Tavily result URLs and keep trusted domains only, carrying each result's published_date along."""
        urls: list[tuple[str, str | None]] = []
        for result in results:
            url = result.get("url")
            if not url:
                continue
            normalized = canonicalize_url(url)
            if self._trusted(normalized, technology) and (not update_pages_only or processor.looks_like_update_page(normalized)):
                urls.append((normalized, result.get("published_date")))
        return urls

    def _trusted(self, url: str, technology: Technology) -> bool:
        """Return true when a URL belongs to trusted or official domains."""
        domain = urlparse(url).netloc.lower().removeprefix("www.")
        trusted = set(technology.trusted_domains + technology.official_domains)
        return any(domain == allowed or domain.endswith(f".{allowed}") for allowed in trusted)

    def _search_domains(self, technology: Technology) -> list[str]:
        """Combine trusted and official Tavily search domains."""
        return list(dict.fromkeys(technology.trusted_domains + technology.official_domains))

    def _skip_missing_api_key(self, run: IngestionRun, reason: str) -> IngestionRun:
        """Record a skipped run when Tavily is not configured."""
        run = self.repository.complete_ingestion_run(
            run,
            reason=reason,
            results_found=0,
            results_saved=0,
            duplicates_skipped=0,
            note="TAVILY_API_KEY is not configured; external updates were not fetched.",
            status="skipped",
        )
        self.db.commit()
        return run
