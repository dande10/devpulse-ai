export type Technology = {
  id: number;
  name: string;
  slug: string;
  icon: string;
  keywords: string[];
  trusted_domains: string[];
  official_domains: string[];
  active: boolean;
  refresh_interval_hours: number;
};

export type Source = {
  id: number;
  name: string;
  domain: string;
  source_type: string;
  official: boolean;
  trust_score: number;
};

export type DeveloperUpdate = {
  id: number;
  title: string;
  canonical_url: string;
  summary: string;
  why_it_matters: string | null;
  recommended_action: string | null;
  version: string | null;
  category: string;
  impact_level: "Critical" | "Important" | "Informational";
  published_at: string | null;
  discovered_at: string;
  source: Source;
  technologies: Technology[];
};

export type FeedResponse = {
  items: DeveloperUpdate[];
  total: number;
  page: number;
  page_size: number;
  new_updates: number;
  requiring_action: number;
  technologies_tracked: number;
  last_updated_at: string | null;
  refresh_running: boolean;
  stale: boolean;
  refresh_started: boolean;
  cooldown_until: string | null;
};

export type RefreshStatus = {
  running: boolean;
  last_started_at: string | null;
  last_completed_at: string | null;
  last_status: string;
  last_error: string | null;
  cooldown_until: string | null;
};
