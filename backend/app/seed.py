from sqlalchemy.orm import Session

from app.models import Technology

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
    (
        "Android",
        "android",
        "And",
        ["android", "android developers", "android studio", "jetpack"],
        ["developer.android.com", "android-developers.googleblog.com", "source.android.com"],
        ["developer.android.com", "source.android.com"],
    ),
    (
        "iOS",
        "ios",
        "iOS",
        ["ios", "swift", "xcode", "apple developer"],
        ["developer.apple.com", "swift.org"],
        ["developer.apple.com", "swift.org"],
    ),
    ("AWS", "aws", "AWS", ["aws"], ["aws.amazon.com"], ["aws.amazon.com"]),
    ("Azure", "azure", "Az", ["azure"], ["azure.microsoft.com"], ["azure.microsoft.com"]),
    (
        "GCP",
        "gcp",
        "GCP",
        ["google cloud", "gcp", "google cloud platform"],
        ["cloud.google.com", "googlecloudplatform.googleblog.com"],
        ["cloud.google.com"],
    ),
    ("Docker", "docker", "Doc", ["docker"], ["docs.docker.com"], ["docs.docker.com"]),
    ("Kubernetes", "kubernetes", "K8s", ["kubernetes"], ["kubernetes.io"], ["kubernetes.io"]),
]


def seed_database(db: Session) -> None:
    existing_by_slug = {technology.slug: technology for technology in db.query(Technology).all()}
    for name, slug, icon, keywords, trusted, official in TECHNOLOGIES:
        query_templates = [
            f"{name} official releases and breaking changes",
            f"{name} latest security advisories",
            f"{name} migration guide documentation updates",
        ]
        if slug == "gcp":
            query_templates = [
                "Google Cloud release notes latest updates",
                "Google Cloud security bulletins latest",
                "Google Cloud breaking changes migration guide",
                "Google Cloud blog developer updates",
            ]
        if slug == "android":
            query_templates = [
                "Android Developers latest release notes",
                "Android Studio latest release notes",
                "Android security bulletin latest",
                "Android Jetpack release notes latest",
                "Android migration guide breaking changes",
            ]
        if slug == "ios":
            query_templates = [
                "Apple Developer iOS latest release notes",
                "iOS SDK latest release notes developer",
                "Xcode release notes latest",
                "Swift release notes latest",
                "Apple Developer security updates iOS",
            ]
        if slug in existing_by_slug:
            technology = existing_by_slug[slug]
            technology.icon = icon
            technology.keywords = keywords
            technology.trusted_domains = trusted
            technology.official_domains = official
            technology.query_templates = query_templates
        else:
            db.add(
                Technology(
                    name=name,
                    slug=slug,
                    icon=icon,
                    keywords=keywords,
                    trusted_domains=trusted,
                    official_domains=official,
                    query_templates=query_templates,
                    refresh_interval_hours=24,
                )
            )
    db.commit()
