import { useMemo, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AlertTriangle,
  ArrowUpRight,
  Bookmark,
  BookmarkCheck,
  Bot,
  Check,
  CheckCircle2,
  Compass,
  Globe2,
  Info,
  Layers,
  ListChecks,
  Plus,
  RefreshCw,
  Search,
  Send,
  Share2,
  Sparkles,
  Zap,
} from "lucide-react";

import { Button } from "../components/ui/button";
import { Card } from "../components/ui/card";
import { FeedbackModal } from "../components/FeedbackModal";
import { Input } from "../components/ui/input";
import { SiteFooter } from "../components/SiteFooter";
import { SiteHeader } from "../components/SiteHeader";
import { useLocalStorage } from "../hooks/useLocalStorage";
import { getAllUpdates, getFeed, getTechnologies, getTechnologyRequests, requestTechnology } from "../services/api";
import type { DeveloperUpdate } from "../types";

const categories = ["All", "Breaking", "Security", "Releases", "Deprecations", "Documentation", "AI Tools"];
const nav = [
  ["My Feed", Sparkles],
  ["Explore", Compass],
  ["AI Search", Bot],
  ["Bookmarks", Bookmark],
] as const;
type NavItem = (typeof nav)[number][0];

const impactStyles: Record<string, { classes: string; icon: typeof AlertTriangle }> = {
  Critical: {
    classes: "border-danger/25 bg-danger/10 text-danger",
    icon: AlertTriangle,
  },
  Important: {
    classes: "border-warning/25 bg-warning/10 text-warning",
    icon: Zap,
  },
  Informational: {
    classes: "border-primary/25 bg-primary/10 text-primary",
    icon: Info,
  },
};

function impactStyle(level: string) {
  return impactStyles[level] ?? impactStyles.Informational;
}

/** Deterministic gradient per technology so avatars stay stable across renders. */
const avatarGradients = [
  "from-blue-500 to-indigo-500",
  "from-violet-500 to-fuchsia-500",
  "from-emerald-500 to-teal-500",
  "from-orange-500 to-rose-500",
  "from-cyan-500 to-blue-500",
  "from-pink-500 to-rose-500",
];

function avatarGradient(seed: string) {
  let hash = 0;
  for (let i = 0; i < seed.length; i += 1) hash = (hash * 31 + seed.charCodeAt(i)) >>> 0;
  return avatarGradients[hash % avatarGradients.length];
}

function formatDate(value: string | null) {
  if (!value) return "Not specified";
  return new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric", year: "numeric" }).format(new Date(value));
}

function displayText(value: string | null | undefined, fallback: string) {
  const cleaned = (value ?? "")
    .replace(/#+\s*/g, "")
    .replace(/\*+/g, "")
    .replace(/\s+/g, " ")
    .trim();
  return cleaned || fallback;
}

function greeting() {
  const hour = new Date().getHours();
  if (hour < 12) return "Good morning, Developer";
  if (hour < 17) return "Good afternoon, Developer";
  return "Good evening, Developer";
}

function UpdateCard({
  update,
  bookmarked,
  onBookmark,
}: {
  update: DeveloperUpdate;
  bookmarked: boolean;
  onBookmark: () => void;
}) {
  const share = async () => {
    if (navigator.share) {
      await navigator.share({ title: update.title, url: update.canonical_url });
      return;
    }
    await navigator.clipboard.writeText(update.canonical_url);
  };

  const primaryTech = update.technologies[0];
  const impact = impactStyle(update.impact_level);
  const ImpactIcon = impact.icon;

  return (
    <Card className="group overflow-hidden p-5 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-card-hover">
      <div className="flex min-w-0 flex-col gap-4">
        <div className="flex items-start justify-between gap-4">
          <div className="flex min-w-0 items-center gap-3">
            <span
              className={`grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-gradient-to-br text-xs font-bold text-white shadow-sm ${avatarGradient(
                primaryTech?.slug ?? "dev"
              )}`}
            >
              {primaryTech?.icon ?? "Dev"}
            </span>
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold">{update.technologies.map((tech) => tech.name).join(", ")}</p>
              <p className="truncate text-xs text-slate-500 dark:text-slate-400">{update.source.name}</p>
            </div>
          </div>
          <div className="flex shrink-0 gap-1">
            <Button variant="ghost" aria-label={bookmarked ? "Remove bookmark" : "Bookmark update"} onClick={onBookmark}>
              {bookmarked ? <BookmarkCheck size={18} className="text-primary" /> : <Bookmark size={18} />}
            </Button>
            <Button variant="ghost" aria-label="Share update" onClick={share}>
              <Share2 size={18} />
            </Button>
          </div>
        </div>

        <div>
          <h2 className="break-words text-lg font-semibold leading-snug transition-colors group-hover:text-primary">{update.title}</h2>
          <p className="mt-2 line-clamp-4 break-words text-sm leading-6 text-slate-600 dark:text-slate-300">
            {displayText(update.summary, "Not specified.")}
          </p>
        </div>

        <div className="grid gap-3 md:grid-cols-2">
          <div className="rounded-lg border border-border bg-muted/40 p-3">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">Why it matters</p>
            <p className="mt-1 break-words text-sm">{displayText(update.why_it_matters, "Not specified.")}</p>
          </div>
          <div className="rounded-lg border border-border bg-muted/40 p-3">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">Recommended action</p>
            <p className="mt-1 break-words text-sm">{displayText(update.recommended_action, "No action specified.")}</p>
          </div>
        </div>

        <div className="flex min-w-0 flex-wrap items-center gap-2">
          <span className="rounded-full border border-border px-2.5 py-1 text-xs font-medium">{update.category}</span>
          <span className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-1 text-xs font-medium ${impact.classes}`}>
            <ImpactIcon size={12} />
            {update.impact_level}
          </span>
          <span className="rounded-full border border-border px-2.5 py-1 text-xs font-medium">Version: {update.version ?? "Not specified"}</span>
          <span className="rounded-full border border-border px-2.5 py-1 text-xs font-medium">{formatDate(update.published_at)}</span>
          <a
            className="ml-auto inline-flex h-9 items-center justify-center gap-1 rounded-lg bg-gradient-to-br from-primary to-primary-strong px-3 text-sm font-medium text-white shadow-sm transition hover:shadow-md hover:brightness-110"
            href={update.canonical_url}
            target="_blank"
            rel="noreferrer"
          >
            Read source
            <ArrowUpRight size={14} />
          </a>
        </div>
      </div>
    </Card>
  );
}

export default function App() {
  const queryClient = useQueryClient();
  const [selected, setSelected] = useLocalStorage<string[]>("devpulse-tech-stack", ["react", "python", "fastapi", "expo", "typescript"]);
  const [bookmarks, setBookmarks] = useLocalStorage<number[]>("devpulse-bookmarks", []);
  const [category, setCategory] = useState("All");
  const [query, setQuery] = useState("");
  const [activeView, setActiveView] = useState<NavItem>("My Feed");
  const [requestName, setRequestName] = useState("");
  const [requestSent, setRequestSent] = useState(false);
  const [feedbackOpen, setFeedbackOpen] = useState(false);
  const searchInputRef = useRef<HTMLInputElement>(null);

  const technologies = useQuery({ queryKey: ["technologies"], queryFn: getTechnologies });
  const feed = useQuery({
    queryKey: ["feed", selected, category, query],
    queryFn: () => getFeed({ technologySlugs: selected, category, query }),
  });
  // Every developer's view, not gated by a personal stack — Explore, AI
  // Search, and Bookmarks all search across every tracked technology.
  const allUpdates = useQuery({
    queryKey: ["all-updates", category, query],
    queryFn: () => getAllUpdates({ category, query }),
  });
  const technologyRequests = useQuery({
    queryKey: ["technology-requests"],
    queryFn: getTechnologyRequests,
    enabled: activeView === "Explore",
  });
  const submitTechnologyRequest = useMutation({
    mutationFn: (name: string) => requestTechnology(name),
    onSuccess: () => {
      setRequestName("");
      setRequestSent(true);
      void queryClient.invalidateQueries({ queryKey: ["technology-requests"] });
      setTimeout(() => setRequestSent(false), 3000);
    },
  });

  const selectedTech = useMemo(
    () => technologies.data?.filter((tech) => selected.includes(tech.slug)) ?? [],
    [selected, technologies.data]
  );
  const techSearch = activeView === "Explore" ? query : "";
  const visibleTechnologies = useMemo(() => {
    const all = technologies.data ?? [];
    if (!techSearch.trim()) return all;
    const term = techSearch.trim().toLowerCase();
    return all.filter((tech) => tech.name.toLowerCase().includes(term) || tech.slug.includes(term));
  }, [technologies.data, techSearch]);

  const personalView = activeView === "My Feed";
  const sourceItems = personalView ? feed.data?.items ?? [] : allUpdates.data?.items ?? [];
  const visibleItems = activeView === "Bookmarks" ? sourceItems.filter((update) => bookmarks.includes(update.id)) : sourceItems;
  const activeQuery = personalView ? feed : allUpdates;

  const toggleTech = (slug: string) => {
    setSelected((current) => (current.includes(slug) ? current.filter((item) => item !== slug) : [...current, slug]));
  };
  const toggleBookmark = (id: number) => {
    setBookmarks((current) => (current.includes(id) ? current.filter((item) => item !== id) : [...current, id]));
  };
  const selectView = (label: NavItem) => {
    setActiveView(label);
    if (label === "Explore") {
      setCategory("All");
      setQuery("");
    }
    if (label === "AI Search") {
      requestAnimationFrame(() => searchInputRef.current?.focus());
    }
  };

  return (
    <div className="min-h-screen">
      <SiteHeader variant="feed" />

      <div className="mx-auto grid w-full max-w-[1920px] gap-6 px-4 py-6 sm:px-6 lg:grid-cols-[260px_minmax(0,1fr)_300px] lg:px-10 xl:gap-8">
        <aside className="space-y-5 lg:sticky lg:top-20 lg:h-fit">
          <Card className="p-3">
            <nav className="grid gap-1">
              {nav.map(([label, Icon]) => (
                <button
                  key={label}
                  className={`flex h-10 items-center gap-3 rounded-lg px-3 text-left text-sm font-medium transition-colors ${
                    activeView === label
                      ? "bg-gradient-to-br from-primary to-primary-strong text-white shadow-sm"
                      : "text-slate-600 hover:bg-muted hover:text-foreground dark:text-slate-300"
                  }`}
                  onClick={() => selectView(label)}
                >
                  <Icon size={17} />
                  {label}
                </button>
              ))}
            </nav>
          </Card>

          <Card className="p-4">
            <h2 className="flex items-center gap-2 text-sm font-semibold">
              <Layers size={15} className="text-primary" />
              My Tech Stack
            </h2>
            <div className="mt-3 flex flex-wrap gap-2">
              {selectedTech.length === 0 && <p className="text-xs text-slate-500 dark:text-slate-400">Nothing added yet — pick some in Explore.</p>}
              {selectedTech.map((tech) => (
                <span key={tech.slug} className="rounded-full bg-muted px-2.5 py-1 text-xs font-medium">
                  {tech.name}
                </span>
              ))}
            </div>
          </Card>

          <Card className="p-4">
            <h2 className="text-sm font-semibold">Configure Stack</h2>
            <div className="mt-3 grid max-h-72 gap-1.5 overflow-auto pr-1">
              {technologies.data?.map((tech) => (
                <label
                  key={tech.slug}
                  className="flex cursor-pointer items-center gap-2 rounded-md px-1.5 py-1 text-sm hover:bg-muted"
                >
                  <input
                    type="checkbox"
                    className="accent-[hsl(var(--primary))]"
                    checked={selected.includes(tech.slug)}
                    onChange={() => toggleTech(tech.slug)}
                  />
                  <span>{tech.name}</span>
                </label>
              ))}
            </div>
          </Card>
        </aside>

        <main className="min-w-0 space-y-5">
          <section className={activeView === "Explore" ? "gradient-ring -mx-4 overflow-hidden rounded-2xl p-[1px] sm:mx-0" : undefined}>
            <div
              className={
                activeView === "Explore"
                  ? "rounded-2xl bg-card/95 px-5 py-6 sm:px-8"
                  : ""
              }
            >
              <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
                <div>
                  {activeView === "Explore" && (
                    <span className="mb-2 inline-flex items-center gap-1.5 rounded-full bg-primary/10 px-3 py-1 text-xs font-semibold text-primary">
                      <Globe2 size={13} />
                      Built for every developer
                    </span>
                  )}
                  <h1 className={activeView === "Explore" ? "text-3xl font-extrabold tracking-tight sm:text-4xl" : "text-3xl font-bold tracking-tight"}>
                    {activeView === "Bookmarks" ? (
                      "Bookmarked updates"
                    ) : activeView === "Explore" ? (
                      <>
                        Discover what&apos;s <span className="gradient-text">shipping</span>
                      </>
                    ) : (
                      greeting()
                    )}
                  </h1>
                  <p className="mt-1 max-w-xl text-slate-600 dark:text-slate-300">
                    {activeView === "Bookmarks"
                      ? "Updates you saved for later."
                      : activeView === "Explore"
                        ? "Search, browse, and follow any technology — free, public, and built for developers who don't have time to read every changelog."
                        : "Here’s what changed across your stack."}
                  </p>
                </div>
                {activeView === "Explore" && (
                  <div className="hidden shrink-0 items-center gap-4 rounded-xl border border-border bg-muted/40 px-4 py-3 sm:flex">
                    <div className="text-center">
                      <p className="text-xl font-bold text-primary">{technologies.data?.length ?? "—"}</p>
                      <p className="text-[11px] text-slate-500 dark:text-slate-400">technologies</p>
                    </div>
                    <div className="h-8 w-px bg-border" />
                    <div className="text-center">
                      <p className="text-xl font-bold text-primary">{allUpdates.data?.total ?? "—"}</p>
                      <p className="text-[11px] text-slate-500 dark:text-slate-400">tracked updates</p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </section>

          {activeView === "Explore" && (
            <>
            <Card className="p-4">
              <div className="flex items-center justify-between">
                <h2 className="flex items-center gap-2 text-sm font-semibold">
                  <Layers size={15} className="text-primary" />
                  All technologies
                </h2>
                <span className="text-xs text-slate-500 dark:text-slate-400">{selected.length} in your stack</span>
              </div>
              <div className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-4">
                {visibleTechnologies.map((tech) => {
                  const inStack = selected.includes(tech.slug);
                  return (
                    <button
                      key={tech.slug}
                      onClick={() => toggleTech(tech.slug)}
                      className={`group flex items-center gap-2.5 rounded-lg border px-3 py-2 text-left text-sm font-medium transition-all ${
                        inStack
                          ? "border-primary/40 bg-primary/10 shadow-sm"
                          : "border-border bg-card hover:border-primary/30 hover:bg-muted"
                      }`}
                    >
                      <span
                        className={`grid h-7 w-7 shrink-0 place-items-center rounded-md bg-gradient-to-br text-[10px] font-bold text-white ${avatarGradient(
                          tech.slug
                        )}`}
                      >
                        {tech.icon}
                      </span>
                      <span className="min-w-0 flex-1 truncate">{tech.name}</span>
                      {inStack ? (
                        <Check size={16} className="shrink-0 text-primary" />
                      ) : (
                        <Plus size={16} className="shrink-0 text-slate-400 transition-colors group-hover:text-primary" />
                      )}
                    </button>
                  );
                })}
                {visibleTechnologies.length === 0 && (
                  <p className="col-span-full text-sm text-slate-500 dark:text-slate-400">No technologies match that search.</p>
                )}
              </div>
            </Card>

            <Card className="p-4">
              <h2 className="flex items-center gap-2 text-sm font-semibold">
                <Send size={14} className="text-primary" />
                Don&apos;t see your stack? Request it.
              </h2>
              <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                Every request goes to a real person who configures trusted sources before we start tracking it.
              </p>
              <form
                className="mt-3 flex flex-col gap-2 sm:flex-row"
                onSubmit={(event) => {
                  event.preventDefault();
                  const trimmed = requestName.trim();
                  if (trimmed) submitTechnologyRequest.mutate(trimmed);
                }}
              >
                <Input
                  value={requestName}
                  onChange={(event) => setRequestName(event.target.value)}
                  placeholder="e.g. Rust, Deno, Svelte..."
                  className="h-10 flex-1"
                  maxLength={120}
                />
                <Button type="submit" disabled={!requestName.trim() || submitTechnologyRequest.isPending}>
                  {requestSent ? <CheckCircle2 size={16} /> : <Send size={16} />}
                  {requestSent ? "Sent!" : "Request"}
                </Button>
              </form>
              {submitTechnologyRequest.isError && <p className="mt-2 text-xs text-danger">Could not submit that request. Try again.</p>}

              {(technologyRequests.data?.length ?? 0) > 0 && (
                <div className="mt-4 border-t border-border pt-3">
                  <p className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                    Requested by other developers
                  </p>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {technologyRequests.data?.slice(0, 12).map((request) => (
                      <span
                        key={request.id}
                        className="inline-flex items-center gap-1.5 rounded-full border border-border bg-muted/50 px-2.5 py-1 text-xs font-medium"
                      >
                        {request.name}
                        <span className="rounded-full bg-primary/15 px-1.5 text-primary">{request.request_count}</span>
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </Card>
            </>
          )}

          <div className="relative">
            <Search className="pointer-events-none absolute left-4 top-3.5 text-slate-400" size={20} />
            <Input
              ref={searchInputRef}
              className="pl-12"
              value={query}
              onChange={(event) => {
                setQuery(event.target.value);
                if (event.target.value.trim() && activeView === "My Feed") setActiveView("AI Search");
              }}
              placeholder={activeView === "Explore" ? "Search technologies or updates..." : "Ask what changed in your stack..."}
            />
          </div>

          <div className="flex gap-2 overflow-auto pb-1">
            {categories.map((item) => (
              <button
                key={item}
                onClick={() => setCategory(item)}
                className={`h-9 shrink-0 rounded-full border px-3.5 text-sm font-medium transition-colors ${
                  category === item
                    ? "border-transparent bg-gradient-to-br from-primary to-primary-strong text-white shadow-sm"
                    : "border-border bg-card hover:bg-muted"
                }`}
              >
                {item}
              </button>
            ))}
          </div>

          {activeQuery.isLoading && (
            <div className="grid gap-4">
              {[1, 2, 3].map((item) => (
                <div key={item} className="h-52 animate-pulse rounded-xl border border-border bg-muted" />
              ))}
            </div>
          )}

          {activeQuery.isError && (
            <Card className="flex items-center gap-3 p-6 text-sm text-danger">
              <AlertTriangle size={18} />
              Could not load updates. Check that the FastAPI service is running.
            </Card>
          )}

          {!activeQuery.isLoading && !activeQuery.isError && visibleItems.length === 0 && (
            <Card className="p-10 text-center">
              <div className="mx-auto grid h-12 w-12 place-items-center rounded-full bg-primary/10 text-primary">
                {activeView === "Bookmarks" ? <Bookmark size={22} /> : <Search size={22} />}
              </div>
              <h2 className="mt-3 font-semibold">{activeView === "Bookmarks" ? "No bookmarks yet" : "No matching updates"}</h2>
              <p className="mx-auto mt-2 max-w-sm text-sm text-slate-500 dark:text-slate-400">
                {activeView === "Bookmarks" ? "Bookmark updates from your feed to see them here." : "Adjust your stack, search, or filters to widen the feed."}
              </p>
            </Card>
          )}

          <div className="grid gap-4">
            {visibleItems.map((update) => (
              <UpdateCard key={update.id} update={update} bookmarked={bookmarks.includes(update.id)} onBookmark={() => toggleBookmark(update.id)} />
            ))}
          </div>
        </main>

        <aside className="min-w-0 space-y-4 lg:sticky lg:top-20 lg:h-fit">
          <Card className="p-4">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-semibold">Insights</h2>
              <Button variant="ghost" aria-label="Refetch saved updates" onClick={() => activeQuery.refetch()}>
                <RefreshCw size={18} className={activeQuery.isFetching ? "animate-spin" : ""} />
              </Button>
            </div>
            <div className="mt-4 grid gap-2.5">
              <div className="flex items-center gap-3 rounded-lg border border-border p-3">
                <div className="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-primary/10 text-primary">
                  <Sparkles size={16} />
                </div>
                <div>
                  <p className="text-xs text-slate-500 dark:text-slate-400">New updates</p>
                  <p className="text-xl font-bold leading-tight">{activeQuery.data?.new_updates ?? 0}</p>
                </div>
              </div>
              <div className="flex items-center gap-3 rounded-lg border border-border p-3">
                <div className="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-warning/10 text-warning">
                  <ListChecks size={16} />
                </div>
                <div>
                  <p className="text-xs text-slate-500 dark:text-slate-400">Requiring action</p>
                  <p className="text-xl font-bold leading-tight">{activeQuery.data?.requiring_action ?? 0}</p>
                </div>
              </div>
              <div className="flex items-center gap-3 rounded-lg border border-border p-3">
                <div className="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-accent/10 text-accent">
                  <Layers size={16} />
                </div>
                <div>
                  <p className="text-xs text-slate-500 dark:text-slate-400">Technologies tracked</p>
                  <p className="text-xl font-bold leading-tight">{personalView ? selected.length : technologies.data?.length ?? 0}</p>
                </div>
              </div>
            </div>
            <p className="mt-4 text-xs text-slate-500 dark:text-slate-400">
              Last updated {activeQuery.data?.last_updated_at ? new Date(activeQuery.data.last_updated_at).toLocaleString() : "Not specified"}
            </p>
          </Card>

          <Card className="p-4">
            <h2 className="flex items-center gap-2 text-sm font-semibold">
              <Bookmark size={15} className="text-primary" />
              Bookmarks
            </h2>
            <p className="mt-2 text-2xl font-bold">{bookmarks.length}</p>
          </Card>

          <Card className="gradient-ring p-[1px]">
            <div className="rounded-[11px] bg-card p-4">
              <p className="text-sm font-semibold">Built for developers, by developers</p>
              <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                No account, no paywall. Every release, security advisory, and breaking change — surfaced from official sources only.
              </p>
            </div>
          </Card>
        </aside>
      </div>

      <SiteFooter onFeedback={() => setFeedbackOpen(true)} />
      <FeedbackModal open={feedbackOpen} onClose={() => setFeedbackOpen(false)} />
    </div>
  );
}
