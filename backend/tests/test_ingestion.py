import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.base import Base
from app.ingestion.pipeline import IngestionPipeline
from app.ingestion.processor import classify_category, classify_impact
from app.models import DeveloperUpdate, Source, Technology
from app.repositories.updates import UpdateRepository
from app.services.normalize import content_fingerprint


@pytest.fixture()
def db():
    """Create an isolated in-memory database for ingestion tests."""
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = Session()
    try:
        yield session
    finally:
        session.close()


def make_technology(**overrides) -> Technology:
    """Build a technology row with trusted and official source domains."""
    data = {
        "name": "Python",
        "slug": "python",
        "icon": "Py",
        "keywords": ["python"],
        "trusted_domains": ["python.org", "blog.python.org"],
        "official_domains": ["python.org"],
        "query_templates": ["latest python release"],
        "active": True,
        "refresh_interval_hours": 24,
    }
    data.update(overrides)
    return Technology(**data)


def useful_result(url: str = "https://www.python.org/downloads/release/python-314") -> dict:
    """Build a useful Tavily Extract-style result."""
    content = (
        "# Python 3.14 Release. This release includes a new version with security fixes. "
        "Developers should review the changelog before upgrading applications. "
        "The announcement includes SDK and migration details for teams."
    )
    return {"url": url, "title": "Python 3.14 Release", "content": content, "raw_content": content}


class FakeTavily:
    """Small Tavily test double."""

    configured = True

    def __init__(self) -> None:
        self.extracted_urls: list[str] = []
        self.search_calls = 0
        self.crawl_calls = 0

    def search_updates(self, query: str, domains: list[str] | None = None, days: int = 30) -> dict:
        self.search_calls += 1
        return {
            "results": [
                {"url": "https://www.python.org/downloads/release/python-314?utm_source=x"},
                {"url": "https://evil.example/release"},
                {"url": "https://blog.python.org/2026/08/python-release"},
            ]
        }

    def extract_updates(self, urls: list[str]) -> dict:
        self.extracted_urls = urls
        return {"results": [useful_result(urls[0])]} if urls else {"results": []}

    def crawl_official_source(self, url: str, allowed_domains: list[str], max_depth: int = 2, max_pages: int = 20) -> dict:
        self.crawl_calls += 1
        return {"results": [{"url": "https://www.python.org/security/"}]}


class FailingTavily(FakeTavily):
    def search_updates(self, query: str, domains: list[str] | None = None, days: int = 30) -> dict:
        raise RuntimeError("search exploded")


class MissingKeyTavily(FakeTavily):
    configured = False


def save_technology(db, technology: Technology | None = None) -> Technology:
    tech = technology or make_technology()
    db.add(tech)
    db.commit()
    return tech


def test_url_discovery_uses_search_and_crawl_for_trusted_urls(db) -> None:
    tech = save_technology(db)
    tavily = FakeTavily()
    pipeline = IngestionPipeline(db, tavily=tavily)

    urls, found, note = pipeline._discover_urls(tech)

    assert found == 3
    assert note is None
    assert tavily.crawl_calls == 1
    assert "https://www.python.org/downloads/release/python-314" in urls
    assert "https://blog.python.org/2026/08/python-release" in urls
    assert "https://www.python.org/security" in urls
    assert all("evil.example" not in url for url in urls)


def test_url_duplicate_detection_counts_existing_urls(db) -> None:
    tech = save_technology(db)
    source = Source(name="python.org", domain="python.org", source_type="trusted", official=True)
    db.add(source)
    db.flush()
    db.add(
        DeveloperUpdate(
            title="Existing",
            canonical_url="https://python.org/existing",
            source=source,
            summary="Existing release content",
            category="Releases",
            impact_level="Informational",
            content_fingerprint="abc",
            raw_metadata={},
            technologies=[tech],
        )
    )
    db.commit()

    new_urls, duplicate_count = UpdateRepository(db).remove_existing_urls(
        ["https://python.org/existing", "https://python.org/new", "https://python.org/new"]
    )

    assert new_urls == ["https://python.org/new"]
    assert duplicate_count == 1


def test_content_fingerprint_duplicate_detection(db) -> None:
    tech = save_technology(db)
    result = useful_result()
    fingerprint = content_fingerprint(result["title"], result["raw_content"])
    source = Source(name="python.org", domain="python.org", source_type="trusted", official=True)
    db.add(source)
    db.flush()
    db.add(
        DeveloperUpdate(
            title="Same content",
            canonical_url="https://python.org/other",
            source=source,
            summary="Same release content",
            category="Releases",
            impact_level="Informational",
            content_fingerprint=fingerprint,
            raw_metadata={},
            technologies=[tech],
        )
    )
    db.commit()

    saved, duplicates = IngestionPipeline(db, tavily=FakeTavily())._process_results(tech, [result])

    assert saved == 0
    assert duplicates == 1


def test_category_classification_uses_whole_word_ai_matching() -> None:
    assert classify_category("Security bulletin", "https://example.com", "CVE-2026-1 vulnerability") == "Security"
    assert classify_category("Migration guide", "https://example.com", "Breaking migration guide") == "Breaking"
    assert classify_category("Plain word", "https://example.com", "This contains said and paid but no acronym.") == "Releases"
    assert classify_category("LLM update", "https://example.com", "New AI agent and LLM tooling release") == "AI Tools"


def test_impact_classification() -> None:
    assert classify_impact("Security") == "Critical"
    assert classify_impact("Breaking") == "Important"
    assert classify_impact("Deprecations") == "Important"
    assert classify_impact("Releases") == "Informational"


def test_saving_an_extracted_update(db) -> None:
    tech = save_technology(db)
    saved, duplicates = IngestionPipeline(db, tavily=FakeTavily())._process_results(tech, [useful_result()])

    update = db.query(DeveloperUpdate).one()
    assert saved == 1
    assert duplicates == 0
    assert update.title == "Python 3.14 Release"
    assert update.source.domain == "python.org"
    assert update.technologies[0].slug == "python"


def test_tavily_failure_handling_continues_other_technologies(db) -> None:
    save_technology(db)
    run = IngestionPipeline(db, tavily=FailingTavily()).refresh(reason="scheduled")[0]

    assert run.status == "failed"
    assert "search exploded" in (run.error_message or "")


def test_missing_tavily_api_key_records_skipped_run(db) -> None:
    save_technology(db)
    run = IngestionPipeline(db, tavily=MissingKeyTavily()).refresh(reason="scheduled")[0]

    assert run.status == "skipped"
    assert "TAVILY_API_KEY is not configured" in (run.error_message or "")


def test_scheduler_triggered_refresh_uses_scheduled_reason(db) -> None:
    save_technology(db)
    run = IngestionPipeline(db, tavily=MissingKeyTavily()).refresh()[0]

    assert run.status == "skipped"
    assert (run.error_message or "").startswith("scheduled:")
