import { useEffect, useMemo, useRef, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import {
  Bookmark,
  BookmarkCheck,
  Bot,
  Compass,
  Moon,
  RefreshCw,
  Search,
  Share2,
  Sparkles,
  Sun,
  User,
} from "lucide-react";

import { Button } from "../components/ui/button";
import { Card } from "../components/ui/card";
import { Input } from "../components/ui/input";
import { useLocalStorage } from "../hooks/useLocalStorage";
import { getFeed, getRefreshStatus, getTechnologies, requestLatestUpdates } from "../services/api";
import type { DeveloperUpdate } from "../types";

const categories = ["All", "Breaking", "Security", "Releases", "Deprecations", "Documentation", "AI Tools"];
const nav = [
  ["My Feed", Sparkles],
  ["Explore", Compass],
  ["AI Search", Bot],
  ["Bookmarks", Bookmark],
] as const;

function impactClass(level: string) {
  if (level === "Critical") return "border-red-200 bg-red-50 text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-200";
  if (level === "Important") return "border-orange-200 bg-orange-50 text-orange-700 dark:border-orange-900 dark:bg-orange-950 dark:text-orange-200";
  return "border-blue-200 bg-blue-50 text-blue-700 dark:border-blue-900 dark:bg-blue-950 dark:text-blue-200";
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

  return (
    <Card className="overflow-hidden p-5">
      <div className="flex min-w-0 flex-col gap-4">
        <div className="flex items-start justify-between gap-4">
          <div className="flex min-w-0 items-center gap-3">
            <span className="grid h-10 w-10 shrink-0 place-items-center rounded-md bg-muted text-xs font-bold text-primary">
              {update.technologies[0]?.icon ?? "Dev"}
            </span>
            <div className="min-w-0">
              <p className="text-sm font-semibold">{update.technologies.map((tech) => tech.name).join(", ")}</p>
              <p className="truncate text-xs text-slate-500 dark:text-slate-400">{update.source.name}</p>
            </div>
          </div>
          <div className="flex shrink-0 gap-2">
            <Button variant="ghost" aria-label={bookmarked ? "Remove bookmark" : "Bookmark update"} onClick={onBookmark}>
              {bookmarked ? <BookmarkCheck size={18} /> : <Bookmark size={18} />}
            </Button>
            <Button variant="ghost" aria-label="Share update" onClick={share}>
              <Share2 size={18} />
            </Button>
          </div>
        </div>

        <div>
          <h2 className="break-words text-lg font-semibold leading-snug">{update.title}</h2>
          <p className="mt-2 line-clamp-4 break-words text-sm leading-6 text-slate-600 dark:text-slate-300">
            {displayText(update.summary, "Not specified.")}
          </p>
        </div>

        <div className="grid gap-3 md:grid-cols-2">
          <div className="rounded-md border border-border p-3">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">Why it matters</p>
            <p className="mt-1 break-words text-sm">{displayText(update.why_it_matters, "Not specified.")}</p>
          </div>
          <div className="rounded-md border border-border p-3">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">Recommended action</p>
            <p className="mt-1 break-words text-sm">{displayText(update.recommended_action, "No action specified.")}</p>
          </div>
        </div>

        <div className="flex min-w-0 flex-wrap items-center gap-2">
          <span className="rounded-md border border-border px-2 py-1 text-xs font-medium">{update.category}</span>
          <span className={`rounded-md border px-2 py-1 text-xs font-medium ${impactClass(update.impact_level)}`}>{update.impact_level}</span>
          <span className="rounded-md border border-border px-2 py-1 text-xs font-medium">Version: {update.version ?? "Not specified"}</span>
          <span className="rounded-md border border-border px-2 py-1 text-xs font-medium">{formatDate(update.published_at)}</span>
          <a
            className="ml-auto inline-flex h-9 items-center justify-center rounded-md bg-primary px-3 text-sm font-medium text-white"
            href={update.canonical_url}
            target="_blank"
            rel="noreferrer"
          >
            Read source
          </a>
        </div>
      </div>
    </Card>
  );
}

export default function App() {
  const [dark, setDark] = useLocalStorage("devpulse-theme-dark", false);
  const [selected, setSelected] = useLocalStorage<string[]>("devpulse-tech-stack", ["react", "python", "fastapi", "expo", "typescript"]);
  const [bookmarks, setBookmarks] = useLocalStorage<number[]>("devpulse-bookmarks", []);
  const [category, setCategory] = useState("All");
  const [query, setQuery] = useState("");

  if (dark) document.documentElement.classList.add("dark");
  else document.documentElement.classList.remove("dark");

  const technologies = useQuery({ queryKey: ["technologies"], queryFn: getTechnologies });
  const feed = useQuery({
    queryKey: ["feed", selected, category, query],
    queryFn: () => getFeed({ technologySlugs: selected, category, query }),
  });
  const refreshStatus = useQuery({
    queryKey: ["refresh-status"],
    queryFn: getRefreshStatus,
    refetchInterval: (query) => (query.state.data?.running ? 2500 : false),
  });
  const latestRequest = useMutation({
    mutationFn: () => requestLatestUpdates(selected),
    onSuccess: () => refreshStatus.refetch(),
  });
  const wasRunning = useRef(false);

  useEffect(() => {
    const running = Boolean(refreshStatus.data?.running || feed.data?.refresh_running);
    if (wasRunning.current && !running) {
      feed.refetch();
    }
    wasRunning.current = running;
  }, [feed, refreshStatus.data?.running]);

  const selectedTech = useMemo(
    () => technologies.data?.filter((tech) => selected.includes(tech.slug)) ?? [],
    [selected, technologies.data]
  );

  const visibleItems = feed.data?.items ?? [];
  const toggleTech = (slug: string) => {
    setSelected((current) => (current.includes(slug) ? current.filter((item) => item !== slug) : [...current, slug]));
  };
  const toggleBookmark = (id: number) => {
    setBookmarks((current) => (current.includes(id) ? current.filter((item) => item !== id) : [...current, id]));
  };
  const refreshRunning = Boolean(feed.data?.refresh_running || refreshStatus.data?.running || latestRequest.isPending);
  const cooldownUntil = refreshStatus.data?.cooldown_until ?? feed.data?.cooldown_until;
  const cooldownActive = cooldownUntil ? new Date(cooldownUntil).getTime() > Date.now() : false;

  return (
    <div className="min-h-screen bg-background">
      <header className="sticky top-0 z-10 border-b border-border bg-card/95 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-3">
          <div className="flex items-center gap-3">
            <div className="grid h-10 w-10 place-items-center rounded-md bg-primary text-sm font-bold text-white">DP</div>
            <div>
              <p className="font-semibold">DevPulse AI</p>
              <p className="text-sm text-slate-500 dark:text-slate-400">All your tech updates. One place.</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="ghost" aria-label="Toggle dark mode" onClick={() => setDark((value) => !value)}>
              {dark ? <Sun size={18} /> : <Moon size={18} />}
            </Button>
            <div className="grid h-10 w-10 place-items-center rounded-full border border-border bg-muted" aria-label="User profile">
              <User size={18} />
            </div>
          </div>
        </div>
      </header>

      <div className="mx-auto grid max-w-7xl gap-6 px-4 py-6 lg:grid-cols-[240px_minmax(0,1fr)_280px]">
        <aside className="space-y-5">
          <Card className="p-3">
            <nav className="grid gap-1">
              {nav.map(([label, Icon]) => (
                <button key={label} className="flex h-10 items-center gap-3 rounded-md px-3 text-left text-sm font-medium hover:bg-muted">
                  <Icon size={17} />
                  {label}
                </button>
              ))}
            </nav>
          </Card>

          <Card className="p-4">
            <h2 className="text-sm font-semibold">My Tech Stack</h2>
            <div className="mt-3 flex flex-wrap gap-2">
              {selectedTech.map((tech) => (
                <span key={tech.slug} className="rounded-md bg-muted px-2 py-1 text-xs font-medium">
                  {tech.name}
                </span>
              ))}
            </div>
          </Card>

          <Card className="p-4">
            <h2 className="text-sm font-semibold">Configure Stack</h2>
            <div className="mt-3 grid max-h-72 gap-2 overflow-auto pr-1">
              {technologies.data?.map((tech) => (
                <label key={tech.slug} className="flex cursor-pointer items-center gap-2 text-sm">
                  <input type="checkbox" checked={selected.includes(tech.slug)} onChange={() => toggleTech(tech.slug)} />
                  <span>{tech.name}</span>
                </label>
              ))}
            </div>
          </Card>
        </aside>

        <main className="min-w-0 space-y-5">
          <section>
            <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
              <div>
                <h1 className="text-3xl font-bold tracking-normal">{greeting()}</h1>
                <p className="mt-1 text-slate-600 dark:text-slate-300">Here’s what changed across your stack.</p>
              </div>
              <Button
                variant="outline"
                disabled={refreshRunning || cooldownActive}
                onClick={() => latestRequest.mutate()}
                aria-live="polite"
              >
                <RefreshCw size={18} className={refreshRunning ? "animate-spin" : ""} />
                {refreshRunning ? "Checking latest" : "Check for latest updates"}
              </Button>
            </div>
            {(feed.data?.stale || refreshRunning || latestRequest.data?.message) && (
              <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
                {refreshRunning
                  ? "Saved updates are shown while Tavily checks trusted sources in the background."
                  : latestRequest.data?.message ?? "Saved updates are shown while newer results are prepared."}
              </p>
            )}
          </section>

          <div className="relative">
            <Search className="pointer-events-none absolute left-4 top-3.5 text-slate-400" size={20} />
            <Input className="pl-12" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Ask what changed in your stack..." />
          </div>

          <div className="flex gap-2 overflow-auto pb-1">
            {categories.map((item) => (
              <button
                key={item}
                onClick={() => setCategory(item)}
                className={`h-9 shrink-0 rounded-md border px-3 text-sm font-medium ${
                  category === item ? "border-primary bg-primary text-white" : "border-border bg-card hover:bg-muted"
                }`}
              >
                {item}
              </button>
            ))}
          </div>

          {feed.isLoading && (
            <div className="grid gap-4">
              {[1, 2, 3].map((item) => (
                <div key={item} className="h-52 animate-pulse rounded-lg border border-border bg-muted" />
              ))}
            </div>
          )}

          {feed.isError && <Card className="p-6 text-sm text-red-600">Could not load updates. Check that the FastAPI service is running.</Card>}

          {!feed.isLoading && !feed.isError && visibleItems.length === 0 && (
            <Card className="p-8 text-center">
              <h2 className="font-semibold">No matching updates</h2>
              <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">Adjust your stack, search, or filters to widen the feed.</p>
            </Card>
          )}

          <div className="grid gap-4">
            {visibleItems.map((update) => (
              <UpdateCard key={update.id} update={update} bookmarked={bookmarks.includes(update.id)} onBookmark={() => toggleBookmark(update.id)} />
            ))}
          </div>
        </main>

        <aside className="min-w-0 space-y-4">
          <Card className="p-4">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-semibold">Insights</h2>
              <Button variant="ghost" aria-label="Refetch saved feed" onClick={() => feed.refetch()}>
                <RefreshCw size={18} className={refreshRunning ? "animate-spin" : ""} />
              </Button>
            </div>
            <div className="mt-4 grid gap-3">
              <div className="rounded-md border border-border p-3">
                <p className="text-xs text-slate-500 dark:text-slate-400">New updates</p>
                <p className="text-2xl font-bold">{feed.data?.new_updates ?? 0}</p>
              </div>
              <div className="rounded-md border border-border p-3">
                <p className="text-xs text-slate-500 dark:text-slate-400">Requiring action</p>
                <p className="text-2xl font-bold">{feed.data?.requiring_action ?? 0}</p>
              </div>
              <div className="rounded-md border border-border p-3">
                <p className="text-xs text-slate-500 dark:text-slate-400">Technologies tracked</p>
                <p className="text-2xl font-bold">{selected.length}</p>
              </div>
            </div>
            <p className="mt-4 text-xs text-slate-500 dark:text-slate-400">
              Last updated {feed.data?.last_updated_at ? new Date(feed.data.last_updated_at).toLocaleString() : "Not specified"}
            </p>
            {refreshStatus.data?.last_status && (
              <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">Refresh status: {refreshStatus.data.last_status}</p>
            )}
          </Card>

          <Card className="p-4">
            <h2 className="text-sm font-semibold">Bookmarks</h2>
            <p className="mt-2 text-2xl font-bold">{bookmarks.length}</p>
          </Card>
        </aside>
      </div>
    </div>
  );
}
