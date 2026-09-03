import type { FeedResponse, Technology } from "../types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export async function getTechnologies(): Promise<Technology[]> {
  const response = await fetch(`${API_BASE_URL}/api/technologies`);
  if (!response.ok) throw new Error("Unable to load technologies");
  return response.json();
}

export async function getFeed(params: { technologySlugs: string[]; category: string; query: string }): Promise<FeedResponse> {
  if (params.query.trim()) {
    const response = await fetch(`${API_BASE_URL}/api/search?q=${encodeURIComponent(params.query)}`);
    if (!response.ok) throw new Error("Unable to search updates");
    return response.json();
  }
  const search = new URLSearchParams();
  params.technologySlugs.forEach((slug) => search.append("technology_slugs", slug));
  if (params.category !== "All") search.set("category", params.category);
  const response = await fetch(`${API_BASE_URL}/api/feed?${search.toString()}`);
  if (!response.ok) throw new Error("Unable to load feed");
  return response.json();
}
