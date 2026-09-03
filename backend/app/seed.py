from datetime import datetime, timedelta, timezone

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.models import DeveloperUpdate, Source, Technology, UpdateTechnology
from app.core.config import settings
from app.services.normalize import canonicalize_url, content_fingerprint

TECHNOLOGIES = [
    ("React", "react", "React", ["react", "jsx"], ["react.dev"], ["react.dev"]),
    ("React Native", "react-native", "RN", ["react native"], ["reactnative.dev"], ["reactnative.dev"]),
    ("Expo", "expo", "Expo", ["expo", "expo sdk"], ["expo.dev"], ["expo.dev"]),
    ("TypeScript", "typescript", "TS", ["typescript", "tsc"], ["typescriptlang.org"], ["typescriptlang.org"]),
    ("JavaScript", "javascript", "JS", ["javascript", "ecmascript"], ["tc39.es"], ["tc39.es"]),
    ("Python", "python", "Py", ["python", "cpython"], ["python.org"], ["python.org"]),
    ("FastAPI", "fastapi", "API", ["fastapi"], ["fastapi.tiangolo.com"], ["fastapi.tiangolo.com"]),
    ("Node.js", "nodejs", "Node", ["node.js", "node"], ["nodejs.org"], ["nodejs.org"]),
    ("Next.js", "nextjs", "Next", ["next.js", "nextjs"], ["nextjs.org"], ["nextjs.org"]),
    ("Angular", "angular", "Ng", ["angular"], ["angular.dev"], ["angular.dev"]),
    ("Vue", "vue", "Vue", ["vue"], ["vuejs.org"], ["vuejs.org"]),
    ("Flutter", "flutter", "Fl", ["flutter"], ["flutter.dev"], ["flutter.dev"]),
    ("Android", "android", "And", ["android"], ["developer.android.com"], ["developer.android.com"]),
    ("iOS", "ios", "iOS", ["ios", "swift"], ["developer.apple.com"], ["developer.apple.com"]),
    ("AWS", "aws", "AWS", ["aws"], ["aws.amazon.com"], ["aws.amazon.com"]),
    ("Azure", "azure", "Az", ["azure"], ["azure.microsoft.com"], ["azure.microsoft.com"]),
    ("GCP", "gcp", "GCP", ["google cloud", "gcp"], ["cloud.google.com"], ["cloud.google.com"]),
    ("Docker", "docker", "Doc", ["docker"], ["docs.docker.com"], ["docs.docker.com"]),
    ("Kubernetes", "kubernetes", "K8s", ["kubernetes"], ["kubernetes.io"], ["kubernetes.io"]),
]


def seed_database(db: Session) -> None:
    if settings.tavily_api_key:
        demo_ids = [
            update_id
            for (update_id,) in db.query(DeveloperUpdate.id)
            .filter(DeveloperUpdate.raw_metadata["demo"].as_boolean().is_(True))
            .all()
        ]
        if demo_ids:
            db.execute(delete(UpdateTechnology).where(UpdateTechnology.update_id.in_(demo_ids)))
            db.execute(delete(DeveloperUpdate).where(DeveloperUpdate.id.in_(demo_ids)))
            db.commit()

    if db.query(Technology).count() == 0:
        for name, slug, icon, keywords, trusted, official in TECHNOLOGIES:
            db.add(
                Technology(
                    name=name,
                    slug=slug,
                    icon=icon,
                    keywords=keywords,
                    trusted_domains=trusted,
                    official_domains=official,
                    query_templates=[
                        f"{name} official releases and breaking changes",
                        f"{name} latest security advisories",
                        f"{name} migration guide documentation updates",
                    ],
                    refresh_interval_hours=24,
                )
            )
        db.commit()

    if db.query(Source).count() == 0:
        db.add_all(
            [
                Source(name="React Blog", domain="react.dev", source_type="official", official=True, trust_score=100),
                Source(name="Expo Changelog", domain="expo.dev", source_type="official", official=True, trust_score=100),
                Source(name="Python Release Notes", domain="python.org", source_type="official", official=True, trust_score=100),
                Source(name="FastAPI Release Notes", domain="fastapi.tiangolo.com", source_type="official", official=True, trust_score=100),
            ]
        )
        db.commit()

    if settings.tavily_api_key or db.query(DeveloperUpdate).count() > 0:
        return

    tech_by_slug = {technology.slug: technology for technology in db.query(Technology).all()}
    source_by_domain = {source.domain: source for source in db.query(Source).all()}
    now = datetime.now(timezone.utc)
    demo_updates = [
        (
            "React compiler guidance expands for production adoption",
            "https://react.dev/blog/react-compiler-demo",
            "react.dev",
            "The React team clarified compiler adoption paths and configuration expectations for application teams.",
            "Teams can plan compiler trials with fewer assumptions about unsupported patterns.",
            "Audit custom hooks and build tooling before enabling compiler checks.",
            None,
            "Documentation",
            "Informational",
            ["react", "typescript"],
            1,
        ),
        (
            "Expo SDK migration checklist highlights native module changes",
            "https://expo.dev/changelog/sdk-migration-demo",
            "expo.dev",
            "Expo published a migration checklist covering config plugins, native modules, and dependency alignment.",
            "Apps with custom native modules may need extra validation during upgrade windows.",
            "Run the upgrade command in a branch and verify native module compatibility.",
            "SDK latest",
            "Breaking",
            "Important",
            ["expo", "react-native"],
            2,
        ),
        (
            "Python security release reminder for maintained branches",
            "https://www.python.org/downloads/security-demo",
            "python.org",
            "Python maintainers reminded users to stay current on supported patch releases for security fixes.",
            "Outdated runtimes can miss fixes that affect production services and CI images.",
            "Check base images and runtime versions against supported Python branches.",
            None,
            "Security",
            "Critical",
            ["python", "docker"],
            4,
        ),
        (
            "FastAPI documentation refresh improves deployment examples",
            "https://fastapi.tiangolo.com/release-notes/demo",
            "fastapi.tiangolo.com",
            "FastAPI documentation examples were reorganized around deployment and dependency practices.",
            "Backend teams can compare their service layout with current framework guidance.",
            None,
            None,
            "Documentation",
            "Informational",
            ["fastapi", "python"],
            7,
        ),
    ]
    for title, url, domain, summary, why, action, version, category, impact, slugs, days in demo_updates:
        content = f"{summary} {why}"
        db.add(
            DeveloperUpdate(
                title=title,
                canonical_url=canonicalize_url(url),
                source=source_by_domain[domain],
                original_excerpt=summary,
                extracted_content=content,
                summary=summary,
                why_it_matters=why,
                recommended_action=action,
                version=version,
                category=category,
                impact_level=impact,
                published_at=now - timedelta(days=days),
                content_fingerprint=content_fingerprint(title, content),
                raw_metadata={"demo": True},
                technologies=[tech_by_slug[slug] for slug in slugs],
            )
        )
    db.commit()
