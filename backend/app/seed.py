from sqlalchemy.orm import Session

from app.models import Technology

TECHNOLOGIES = [
    ("React", "react", "React", ["react", "jsx"], ["react.dev"], ["react.dev"]),
    ("React Native", "react-native", "RN", ["react native"], ["reactnative.dev"], ["reactnative.dev"]),
    ("Expo", "expo", "Expo", ["expo", "expo sdk"], ["expo.dev"], ["expo.dev"]),
    ("TypeScript", "typescript", "TS", ["typescript", "tsc"], ["typescriptlang.org"], ["typescriptlang.org"]),
    ("JavaScript", "javascript", "JS", ["javascript", "ecmascript"], ["tc39.es"], ["tc39.es"]),
    ("Java", "java", "Java", ["java", "jdk", "openjdk"], ["openjdk.org", "oracle.com"], ["openjdk.org"]),
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
        "Visa Bulletin",
        "visa-bulletin",
        "Visa",
        ["visa bulletin", "priority date", "final action dates", "dates for filing"],
        ["travel.state.gov", "uscis.gov"],
        ["travel.state.gov", "uscis.gov"],
    ),
    (
        "OpenAI / ChatGPT",
        "openai",
        "GPT",
        ["openai", "chatgpt", "gpt-4", "gpt-5", "gpt"],
        ["openai.com", "help.openai.com", "platform.openai.com"],
        ["openai.com", "platform.openai.com"],
    ),
    (
        "Anthropic / Claude",
        "anthropic",
        "Claude",
        ["anthropic", "claude", "claude code", "claude opus", "claude sonnet"],
        ["anthropic.com", "docs.claude.com", "claude.com"],
        ["anthropic.com", "docs.claude.com"],
    ),
    (
        "Google Gemini",
        "gemini",
        "Gem",
        ["gemini", "google gemini", "gemini api", "google ai"],
        ["ai.google.dev", "blog.google", "deepmind.google"],
        ["ai.google.dev", "deepmind.google"],
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
        if slug == "visa-bulletin":
            query_templates = [
                "Department of State latest visa bulletin",
                "USCIS latest visa bulletin adjustment of status filing chart",
                "Visa bulletin final action dates latest",
                "Visa bulletin dates for filing latest",
            ]
        if slug == "openai":
            query_templates = [
                "OpenAI ChatGPT release notes latest",
                "OpenAI API changelog latest update",
                "OpenAI new model release GPT",
                "OpenAI platform breaking changes migration",
            ]
        if slug == "anthropic":
            query_templates = [
                "Anthropic Claude release notes latest",
                "Claude API changelog latest update",
                "Anthropic new Claude model release",
                "Claude Code changelog latest",
            ]
        if slug == "gemini":
            query_templates = [
                "Gemini API changelog latest update",
                "Google Gemini new model release",
                "Gemini API breaking changes migration",
                "Google AI Gemini developer blog update",
            ]
        if slug == "pmp-certification":
            query_templates = [
                "PMI PMP certification exam changes latest",
                "Project Management Professional certification update",
                "PMI CAPM certification update latest",
                "PMI exam content outline changes latest",
            ]
        if slug == "gcp-certification":
            query_templates = [
                "Google Cloud certification exam updates latest",
                "Google Cloud certified professional exam changes",
                "Google Cloud certification new exam guide latest",
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
