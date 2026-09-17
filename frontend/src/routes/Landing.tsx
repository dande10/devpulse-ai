import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";

import { FeedbackModal } from "../components/FeedbackModal";
import { RequestTechnologyModal } from "../components/RequestTechnologyModal";
import { SiteFooter } from "../components/SiteFooter";
import { SiteHeader } from "../components/SiteHeader";
import { useLocalStorage } from "../hooks/useLocalStorage";
import { getReviews, getTechnologies } from "../services/api";
import type { Technology } from "../types";
import "../styles/landing.css";

// Ported from the reference design (devpulse-react/src.jsx), wired to real
// data: the technology catalog and "my stack" selection are the same ones
// the dashboard (/feed) reads, and the request dialog actually submits to
// the backend instead of copying to the clipboard. The three example feed
// cards stay illustrative, as labeled, same as the reference.
const groupBySlug: Record<string, string> = {
  javascript: "Languages",
  typescript: "Languages",
  python: "Languages",
  react: "Frameworks",
  "react-native": "Frameworks",
  vue: "Frameworks",
  angular: "Frameworks",
  nextjs: "Frameworks",
  expo: "Frameworks",
  flutter: "Frameworks",
  fastapi: "Frameworks",
  nodejs: "Frameworks",
  aws: "Cloud",
  azure: "Cloud",
  gcp: "Cloud",
};
const categories = ["All", "Languages", "Frameworks", "Cloud", "Tools"];

const exampleUpdates = [
  {
    slug: "nodejs",
    name: "Node.js",
    kind: "Release",
    title: "Release notes in one place",
    text: "See version details and changes relevant to your projects.",
    url: "https://nodejs.org/en/blog",
  },
  {
    slug: "expo",
    name: "Expo",
    kind: "Update",
    title: "Know what needs attention",
    text: "Review documented changes and follow the original guidance.",
    url: "https://expo.dev/changelog",
  },
  {
    slug: "azure",
    name: "Azure",
    kind: "Docs",
    title: "Follow your cloud tools",
    text: "Explore documentation for services in your stack.",
    url: "https://learn.microsoft.com/azure/",
  },
];

const steps = [
  ["Choose your technologies", "Select the tools and frameworks you care about."],
  ["Browse relevant updates", "Find updates for your selected stack."],
  ["Read the original source", "Follow links to official documentation and changelogs."],
] as const;

function scrollToId(id: string) {
  document.getElementById(id)?.scrollIntoView({ behavior: "smooth" });
}

export default function Landing() {
  const navigate = useNavigate();
  const technologies = useQuery({ queryKey: ["technologies"], queryFn: getTechnologies });
  const reviews = useQuery({ queryKey: ["reviews"], queryFn: getReviews });
  // Same key the dashboard's "My Tech Stack" reads — selecting here carries
  // straight into the real feed at /feed, no query params needed.
  const [selected, setSelected] = useLocalStorage<string[]>("devpulse-tech-stack", ["react", "python", "fastapi", "expo", "typescript"]);
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("All");
  const [personal, setPersonal] = useState(false);
  const [requestOpen, setRequestOpen] = useState(false);
  const [feedbackOpen, setFeedbackOpen] = useState(false);

  const toggle = (slug: string) => {
    setSelected((previous) => (previous.includes(slug) ? previous.filter((item) => item !== slug) : [...previous, slug]));
  };

  const visible = useMemo(() => {
    const all = technologies.data ?? [];
    const term = query.trim().toLowerCase();
    return all.filter((tech) => {
      const group = groupBySlug[tech.slug] ?? "Tools";
      if (category !== "All" && group !== category) return false;
      if (term && !tech.name.toLowerCase().includes(term)) return false;
      return true;
    });
  }, [technologies.data, query, category]);

  const previewTech = useMemo(
    () => (technologies.data ?? []).filter((tech) => selected.includes(tech.slug)).slice(0, 3),
    [technologies.data, selected]
  );
  const feed = personal ? exampleUpdates.filter((update) => selected.includes(update.slug)) : exampleUpdates;

  const openFeed = () => navigate("/feed");

  return (
    <div className="page">
      <SiteHeader />

      <main className="container">
        <section className="hero">
          <div>
            <p className="eyebrow">STAY INFORMED. BUILD FURTHER.</p>
            <h1>
              Keep up with
              <br />
              <span>your stack.</span>
            </h1>
            <p className="lead">Releases, breaking changes, and developer updates in one place.</p>
            <p className="muted">Free to use. No sign-in required.</p>
            <div className="actions">
              <a
                className="primary button"
                href="#technologies"
                onClick={(event) => {
                  event.preventDefault();
                  scrollToId("technologies");
                }}
              >
                Choose your technologies &rarr;
              </a>
              <button className="outline" onClick={openFeed}>
                Explore updates
              </button>
            </div>
          </div>

          <div className="preview panel">
            <div className="sectionline">
              <h2>Your developer feed</h2>
              <small>Illustrative preview</small>
            </div>
            <div className="chips">
              {previewTech.map((tech) => (
                <span className="chip" key={tech.slug}>
                  {tech.name}
                </span>
              ))}
              {previewTech.length === 0 && <span className="chip">No technologies selected</span>}
              <a
                className="chip"
                href="#technologies"
                onClick={(event) => {
                  event.preventDefault();
                  scrollToId("technologies");
                }}
              >
                + Add
              </a>
            </div>
            {exampleUpdates.map((update) => (
              <div className="previewrow" key={update.slug}>
                <span className="techicon">{update.name.slice(0, 1)}</span>
                <div>
                  <h3>{update.title}</h3>
                  <p>{update.text}</p>
                  <a href={update.url} target="_blank" rel="noreferrer">
                    Official source &#8599;
                  </a>
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="panel selector" id="technologies">
          <div className="sectionline">
            <h2>Find updates for your technologies</h2>
            <button className="textbutton" onClick={() => setRequestOpen(true)}>
              Request a technology &rarr;
            </button>
          </div>
          <label className="search">
            <span aria-hidden="true">&#8981;</span>
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search technologies&hellip;"
              aria-label="Search technologies"
            />
          </label>
          <div className="chips categories" aria-label="Technology categories">
            {categories.map((item) => (
              <button
                key={item}
                className={`chip ${category === item ? "active" : ""}`}
                aria-pressed={category === item}
                onClick={() => setCategory(item)}
              >
                {item}
              </button>
            ))}
          </div>
          <div className="chips">
            {visible.map((tech) => (
              <TechChip key={tech.slug} tech={tech} selected={selected.includes(tech.slug)} onToggle={() => toggle(tech.slug)} />
            ))}
          </div>
          {!visible.length && !technologies.isLoading && <p className="muted">No matching technology in this catalog.</p>}
          <div className="sectionline selectionfooter">
            <small>{selected.length} selected &middot; Preferences saved in this browser</small>
            <button className="textbutton" onClick={openFeed}>
              View selected stack &rarr;
            </button>
          </div>
        </section>

        <section id="examples" className="section">
          <p className="eyebrow">EXAMPLE FEED LAYOUT</p>
          <div className="sectionline">
            <h2 className="sectiontitle">See what&rsquo;s changing</h2>
            <button className="outline" onClick={() => setPersonal((value) => !value)}>
              {personal ? "Show all examples" : "Filter by my stack"}
            </button>
          </div>
          <p className="muted">Illustrative cards&mdash;not live news. Links open the original publishers.</p>
          <div className="grid">
            {feed.map((update) => (
              <article className="panel update" key={update.slug}>
                <div className="sectionline">
                  <h3>
                    <span className="miniicon">{update.name.slice(0, 1)}</span> {update.name}
                  </h3>
                  <span className="pill">{update.kind}</span>
                </div>
                <h3 className="cardtitle">{update.title}</h3>
                <p>{update.text}</p>
                <a className="source" href={update.url} target="_blank" rel="noreferrer">
                  Read source <span>&#8599;</span>
                </a>
              </article>
            ))}
          </div>
          {!feed.length && (
            <div className="panel empty">No example updates for this selection. Choose Node.js, Expo, or Azure to preview filtering.</div>
          )}
        </section>

        {(reviews.data?.length ?? 0) > 0 && (
          <section id="reviews" className="section">
            <p className="eyebrow">WHAT DEVELOPERS SAY</p>
            <h2 className="sectiontitle">Reviews</h2>
            <div className="grid">
              {reviews.data!.map((review) => (
                <article className="panel update" key={review.id}>
                  <div className="sectionline">
                    <h3>{review.name || "Anonymous"}</h3>
                    {review.rating && (
                      <span className="pill">
                        {"★".repeat(review.rating)}
                        {"☆".repeat(5 - review.rating)}
                      </span>
                    )}
                  </div>
                  <p>{review.message}</p>
                </article>
              ))}
            </div>
          </section>
        )}

        <section id="how" className="section">
          <p className="eyebrow">HOW IT WORKS</p>
          <h2 className="sectiontitle">Three steps to stay informed</h2>
          <div className="grid steps">
            {steps.map(([title, body], index) => (
              <div className="panel step" key={title}>
                <span className="number">0{index + 1}</span>
                <div>
                  <h3>{title}</h3>
                  <p>{body}</p>
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="panel cta">
          <div>
            <h2>
              Your stack. <span>Your updates.</span>
            </h2>
            <p className="muted">Stay informed. Build with confidence.</p>
          </div>
          <div>
            <button className="primary" onClick={openFeed}>
              Open feed &rarr;
            </button>
            <button className="textbutton" onClick={() => setRequestOpen(true)}>
              Request a technology &rarr;
            </button>
          </div>
        </section>
      </main>

      <SiteFooter onFeedback={() => setFeedbackOpen(true)} />

      <RequestTechnologyModal open={requestOpen} onClose={() => setRequestOpen(false)} />
      <FeedbackModal open={feedbackOpen} onClose={() => setFeedbackOpen(false)} />
    </div>
  );
}

function TechChip({ tech, selected, onToggle }: { tech: Technology; selected: boolean; onToggle: () => void }) {
  return (
    <button aria-pressed={selected} onClick={onToggle} className={`chip technology ${selected ? "selected" : ""}`}>
      <span className="miniicon">{tech.icon}</span>
      {tech.name}
      {selected && <span aria-hidden="true">&#10003;</span>}
    </button>
  );
}
