import type { FeedResponse, RefreshStatus, Technology } from "../types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

const emptyFeed: FeedResponse = {
  items: [],
  total: 0,
  page: 1,
  page_size: 20,
  new_updates: 0,
  requiring_action: 0,
  technologies_tracked: 0,
  last_updated_at: null,
  refresh_running: false,
  refresh_started: false,
  cooldown_until: null,
};

export async function getTechnologies(): Promise<Technology[]> {
  const response = await fetch(`${API_BASE_URL}/api/technologies`);
  if (!response.ok) throw new Error("Unable to load technologies");
  return response.json();
}

export async function getFeed(params: { technologySlugs: string[]; category: string; query: string }): Promise<FeedResponse> {
  if (params.technologySlugs.length === 0) return emptyFeed;

  const search = new URLSearchParams();
  params.technologySlugs.forEach((slug) => search.append("technology_slugs", slug));
  if (params.category !== "All") search.set("category", params.category);

  const trimmedQuery = params.query.trim();
  const endpoint = trimmedQuery ? "search" : "feed";
  if (trimmedQuery) search.set("q", trimmedQuery);

  const response = await fetch(`${API_BASE_URL}/api/${endpoint}?${search.toString()}`);
  if (!response.ok) throw new Error(trimmedQuery ? "Unable to search updates" : "Unable to load feed");
  return response.json();
}

export async function requestLatestUpdates(technologySlugs: string[]): Promise<RefreshStatus & { started: boolean; message: string }> {
  const response = await fetch(`${API_BASE_URL}/api/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(technologySlugs),
  });
  if (!response.ok) throw new Error("Unable to request latest updates");
  return response.json();
}

export async function getRefreshStatus(): Promise<RefreshStatus> {
  const response = await fetch(`${API_BASE_URL}/api/refresh/status`);
  if (!response.ok) throw new Error("Unable to load refresh status");
  return response.json();
}
