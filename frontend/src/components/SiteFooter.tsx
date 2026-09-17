import { useNavigate } from "react-router-dom";

export function SiteFooter({ onFeedback }: { onFeedback: () => void }) {
  const navigate = useNavigate();

  return (
    <footer className="container">
      <a className="brand" href="/">
        <span className="logo">DP</span>
        DevPulse AI
      </a>
      <a
        href="/#how"
        onClick={(event) => {
          event.preventDefault();
          if (window.location.pathname === "/") {
            document.getElementById("how")?.scrollIntoView({ behavior: "smooth" });
          } else {
            navigate("/#how");
          }
        }}
      >
        How it works
      </a>
      <a
        href="#feedback"
        onClick={(event) => {
          event.preventDefault();
          onFeedback();
        }}
      >
        Leave a review
      </a>
      <span className="muted">Free for developers. No sign-in required.</span>
    </footer>
  );
}
