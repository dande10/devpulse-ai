import re
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

from app.services.normalize import canonicalize_url, content_fingerprint

SECURITY_KEYWORDS = ("security advisory", "security bulletin", "cve-", "vulnerability", "critical vulnerability")
BREAKING_KEYWORDS = ("breaking", "migration")
DEPRECATION_KEYWORDS = ("deprecated", "deprecation")
DOCUMENTATION_KEYWORDS = ("documentation", "docs")
AI_PATTERN = re.compile(r"\b(ai|llm|artificial intelligence|ai agent|agentic)\b", re.IGNORECASE)
UPDATE_MARKERS = (
    "release",
    "changelog",
    "security",
    "cve",
    "deprecated",
    "deprecation",
    "breaking",
    "migration",
    "upgrade",
    "announcement",
    "sdk",
    "version",
    "uscis",
    "visa",
    "h-1b",
    "h4",
    "h-4",
    "ead",
    "eb-1",
    "priority date",
    "final action dates",
    "dates for filing",
    "employment authorization",
)
NOISY_MARKERS = (
    "this page displays a fallback because interactive scripts did not run",
    "make text smaller",
    "reset any font size",
)
UPDATE_PAGE_MARKERS = (
    "release",
    "changelog",
    "security",
    "migration",
    "announce",
    "blog",
    "docs",
    "visa",
    "bulletin",
    "h-1b",
    "i-765",
)


@dataclass(frozen=True)
class ProcessedUpdate:
    """Clean update data ready to be stored."""

    title: str
    canonical_url: str
    original_excerpt: str | None
    extracted_content: str
    summary: str
    why_it_matters: str
    recommended_action: str | None
    version: str | None
    category: str
    impact_level: str
    published_at: datetime | None
    content_fingerprint: str
    raw_metadata: dict


def parse_published_date(value: str | None) -> datetime | None:
    """Parse Tavily's RFC-2822-style published_date (only present for topic="news" search results, never on extract)."""
    if not value:
        return None
    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def clean_content(content: str) -> str:
    """Remove navigation and noisy markdown from Tavily Extract content."""
    heading = re.search(r"(#\s+[A-Z0-9][^\n]+)", content)
    if heading:
        content = content[heading.start() :]
    cleaned = re.sub(r"!\[[^\]]*]\([^)]*\)", " ", content)
    cleaned = re.sub(r"\[[^\]]*]\(javascript:[^)]*\)", " ", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\[[^\]]*]\([^)]*\)", " ", cleaned)
    # Orphaned "](url)" fragments — the matching "[" got cut off by the
    # heading-anchor above, landing mid-link.
    cleaned = re.sub(r"]\([^)]*\)", " ", cleaned)
    cleaned = re.sub(r"\*\*Notice:\*\*.*?(?=#|\n[A-Z]|\Z)", " ", cleaned, flags=re.IGNORECASE | re.DOTALL)
    cleaned = re.sub(r"\*{2,}", " ", cleaned)
    cleaned = re.sub(r"javascript:[^ ]+", " ", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"Solutions & technology Security Ecosystem Industries", " ", cleaned)
    cleaned = re.sub(r"Try Gemini Enterprise today", " ", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"^#+\s*", "", cleaned)
    cleaned = re.sub(r"(?m)^\s*-{3,}\s*$", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def is_useful_update(title: str, content: str) -> bool:
    """Return true when content looks like a developer update."""
    lower = f"{title} {content}".lower()
    if any(marker in lower for marker in NOISY_MARKERS):
        return False
    return len(content) >= 120 and any(marker in lower for marker in UPDATE_MARKERS)


def classify_category(title: str, url: str, content: str) -> str:
    """Classify update category using deterministic source text keywords."""
    lower = f"{title} {url} {content}".lower()
    if any(marker in lower for marker in SECURITY_KEYWORDS):
        return "Security"
    if any(marker in lower for marker in BREAKING_KEYWORDS):
        return "Breaking"
    if any(marker in lower for marker in DEPRECATION_KEYWORDS):
        return "Deprecations"
    if any(marker in lower for marker in DOCUMENTATION_KEYWORDS):
        return "Documentation"
    if AI_PATTERN.search(lower):
        return "AI Tools"
    return "Releases"


def classify_impact(category: str) -> str:
    """Map category to the impact labels used by the feed."""
    if category == "Security":
        return "Critical"
    if category in {"Breaking", "Deprecations"}:
        return "Important"
    return "Informational"


def create_summary(content: str) -> str:
    """Create a short summary from the first extracted sentences."""
    sentences = re.split(r"(?<=[.!?])\s+", content)
    summary = " ".join(sentence for sentence in sentences[:3] if sentence)
    return summary[:420] or "Not specified."


def looks_like_update_page(url: str) -> bool:
    """Return true when a crawled URL points to update-style content."""
    lower = url.lower()
    return any(marker in lower for marker in UPDATE_PAGE_MARKERS)


def process(result: dict, published_at: datetime | None = None) -> ProcessedUpdate | None:
    """Convert one Tavily Extract result into a saveable update.

    published_at comes from the earlier Tavily Search phase (topic="news"),
    matched back in by canonical URL — Extract itself never returns a date.
    """
    url = canonicalize_url(result.get("url", ""))
    content = clean_content(result.get("raw_content") or result.get("content") or "")
    title = result.get("title") or url
    if not url or not is_useful_update(title, content):
        return None

    category = classify_category(title, url, content)
    return ProcessedUpdate(
        title=title[:300],
        canonical_url=url,
        original_excerpt=result.get("content"),
        extracted_content=content,
        summary=create_summary(content),
        why_it_matters="Not specified.",
        recommended_action=None,
        version=None,
        category=category,
        impact_level=classify_impact(category),
        published_at=published_at,
        content_fingerprint=content_fingerprint(title, content),
        raw_metadata={"tavily": result},
    )
