import { useNavigate } from "react-router-dom";

function scrollToOrNavigate(navigate: ReturnType<typeof useNavigate>, id: string) {
  if (window.location.pathname === "/") {
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth" });
  } else {
    navigate(`/#${id}`);
  }
}

export function SiteHeader({ variant = "landing" }: { variant?: "landing" | "feed" }) {
  const navigate = useNavigate();

  return (
    <header>
      <nav className="container nav" aria-label="Main navigation">
        <a className="brand" href="/">
          <span className="logo">DP</span>
          DevPulse AI
        </a>
        <div className="navlinks">
          <a
            href="/#technologies"
            onClick={(event) => {
              event.preventDefault();
              scrollToOrNavigate(navigate, "technologies");
            }}
          >
            Explore
          </a>
          <a
            href="/#how"
            onClick={(event) => {
              event.preventDefault();
              scrollToOrNavigate(navigate, "how");
            }}
          >
            How it works
          </a>
        </div>
        <div className="navright">
          <span className="badge">&#9679; Free &middot; No sign-in</span>
          {variant !== "feed" && (
            <button className="primary" onClick={() => navigate("/feed")}>
              Open feed &#8599;
            </button>
          )}
        </div>
      </nav>
    </header>
  );
}
