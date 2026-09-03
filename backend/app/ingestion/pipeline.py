from datetime import datetime, timezone
from urllib.parse import urlparse

from sqlalchemy.orm import Session

from app.models import DeveloperUpdate, IngestionRun, Source, Technology
from app.services.normalize import canonicalize_url, content_fingerprint
from app.services.tavily.client import TavilyClient


class IngestionPipeline:
    def __init__(self, db: Session, tavily: TavilyClient | None = None) -> None:
        self.db = db
        self.tavily = tavily or TavilyClient()

    def refresh(self, technology_slugs: list[str] | None = None) -> list[IngestionRun]:
        query = self.db.query(Technology).filter(Technology.active.is_(True))
        if technology_slugs:
            query = query.filter(Technology.slug.in_(technology_slugs))
        runs = [self._refresh_technology(technology) for technology in query.all()]
        self.db.commit()
        return runs

    def _refresh_technology(self, technology: Technology) -> IngestionRun:
        run = IngestionRun(technology=technology, tavily_endpoint="search/extract", status="running")
        self.db.add(run)
        self.db.flush()
        if not self.tavily.configured:
            run.status = "skipped"
            run.completed_at = datetime.now(timezone.utc)
            run.error_message = "TAVILY_API_KEY is not configured; demo data remains active."
            return run

        try:
            candidate_urls: list[str] = []
            for template in technology.query_templates:
                search = self.tavily.search_updates(template, domains=technology.trusted_domains or technology.official_domains)
                results = search.get("results", [])
                run.results_found += len(results)
                for result in results:
                    url = result.get("url")
                    if url and self._trusted(url, technology):
                        candidate_urls.append(canonicalize_url(url))

            new_urls = []
            for url in dict.fromkeys(candidate_urls):
                if self.db.query(DeveloperUpdate).filter(DeveloperUpdate.canonical_url == url).first():
                    run.duplicates_skipped += 1
                else:
                    new_urls.append(url)

            for result in self.tavily.extract_updates(new_urls[:20]).get("results", []) if new_urls else []:
                if self._save_extracted_update(technology, result):
                    run.results_saved += 1
                else:
                    run.duplicates_skipped += 1
            run.status = "completed"
        except Exception as exc:
            run.status = "failed"
            run.error_message = str(exc)
        finally:
            run.completed_at = datetime.now(timezone.utc)
        return run

    def _trusted(self, url: str, technology: Technology) -> bool:
        domain = urlparse(url).netloc.lower().removeprefix("www.")
        trusted = set(technology.trusted_domains + technology.official_domains)
        return any(domain == allowed or domain.endswith(f".{allowed}") for allowed in trusted)

    def _save_extracted_update(self, technology: Technology, result: dict) -> bool:
        url = canonicalize_url(result.get("url", ""))
        content = result.get("raw_content") or result.get("content") or ""
        title = result.get("title") or url
        fingerprint = content_fingerprint(title, content)
        if self.db.query(DeveloperUpdate).filter(DeveloperUpdate.content_fingerprint == fingerprint).first():
            return False

        domain = urlparse(url).netloc.lower().removeprefix("www.")
        source = self.db.query(Source).filter(Source.domain == domain).first()
        if not source:
            source = Source(name=domain, domain=domain, source_type="trusted", official=domain in technology.official_domains)
            self.db.add(source)
            self.db.flush()

        lower = f"{title} {content}".lower()
        category = "Releases"
        if "security" in lower or "cve" in lower:
            category = "Security"
        elif "breaking" in lower or "migration" in lower:
            category = "Breaking"
        elif "deprecated" in lower or "deprecation" in lower:
            category = "Deprecations"
        elif "documentation" in lower or "docs" in lower:
            category = "Documentation"
        elif "ai" in lower or "agent" in lower:
            category = "AI Tools"

        impact = "Critical" if category == "Security" else "Important" if category in {"Breaking", "Deprecations"} else "Informational"
        summary = " ".join(content.split())[:420] or "Not specified."
        self.db.add(
            DeveloperUpdate(
                title=title[:300],
                canonical_url=url,
                source=source,
                original_excerpt=result.get("content"),
                extracted_content=content,
                summary=summary,
                why_it_matters="Not specified.",
                recommended_action=None,
                version=None,
                category=category,
                impact_level=impact,
                published_at=None,
                content_fingerprint=fingerprint,
                raw_metadata={"tavily": result},
                technologies=[technology],
            )
        )
        return True
