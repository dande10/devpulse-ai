from app.services.normalize import canonicalize_url, content_fingerprint


def test_canonicalize_url_removes_tracking_params() -> None:
    url = "HTTPS://React.Dev/blog/?utm_source=x&keep=1#section"
    assert canonicalize_url(url) == "https://react.dev/blog?keep=1"


def test_content_fingerprint_is_stable() -> None:
    assert content_fingerprint("Title", "Hello   world") == content_fingerprint(" title ", "hello world")
