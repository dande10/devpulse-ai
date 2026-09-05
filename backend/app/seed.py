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
    ("Vue", "vue", "Vue", ["vue", "vue.js", "vuejs"], ["vuejs.org", "blog.vuejs.org"], ["vuejs.org", "blog.vuejs.org"]),
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
    (
        "H-1B Visa",
        "h1b",
        "H1B",
        ["h-1b", "h1b", "h-1b visa", "specialty occupation"],
        ["uscis.gov", "travel.state.gov", "federalregister.gov"],
        ["uscis.gov", "travel.state.gov"],
    ),
    (
        "H-4 EAD",
        "h4-ead",
        "H4",
        ["h-4 ead", "h4 ead", "h-4 employment authorization", "form i-765"],
        ["uscis.gov", "federalregister.gov"],
        ["uscis.gov"],
    ),
    (
        "EB-1 Green Card",
        "eb1",
        "EB1",
        ["eb-1", "eb1", "employment-based first preference", "extraordinary ability"],
        ["uscis.gov", "travel.state.gov"],
        ["uscis.gov", "travel.state.gov"],
    ),
    (
        "Visa Bulletin",
        "visa-bulletin",
        "Visa",
        ["visa bulletin", "priority date", "final action dates", "dates for filing"],
        ["travel.state.gov", "uscis.gov"],
        ["travel.state.gov", "uscis.gov"],
    ),
]


def seed_database(db: Session) -> None:
    """Create or update technology configuration.

    This does not create Source or DeveloperUpdate rows. Those come from Tavily
    ingestion only.
    """
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
        if slug == "vue":
            query_templates = [
                "Vue.js official release notes latest",
                "Vue.js changelog latest breaking changes",
                "Vue.js migration guide latest",
                "Vue.js security advisories latest",
                "Vue.js official blog developer updates",
            ]
        if slug == "h1b":
            query_templates = [
                "USCIS latest H-1B visa updates",
                "USCIS H-1B cap registration latest update",
                "USCIS H-1B specialty occupation rule update",
                "Federal Register H-1B visa latest rule",
                "Department of State H-1B visa update",
            ]
        if slug == "h4-ead":
            query_templates = [
                "USCIS latest H-4 EAD updates",
                "USCIS H-4 employment authorization latest update",
                "USCIS Form I-765 H-4 EAD latest",
                "Federal Register H-4 EAD latest rule",
            ]
        if slug == "eb1":
            query_templates = [
                "USCIS latest EB-1 updates",
                "USCIS EB-1 extraordinary ability latest update",
                "Department of State EB-1 priority date update",
                "USCIS employment based first preference update",
            ]
        if slug == "visa-bulletin":
            query_templates = [
                "Department of State latest visa bulletin",
                "USCIS latest visa bulletin adjustment of status filing chart",
                "Visa bulletin final action dates latest",
                "Visa bulletin dates for filing latest",
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
