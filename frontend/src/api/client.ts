import axios from "axios";
import type { Paper, SearchResult, Topic } from "../types";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "/api";

export const api = axios.create({
  baseURL: API_BASE,
  timeout: 45000,
});

export async function searchPapers(params: {
  query: string;
  sources: string[];
  filters?: Record<string, unknown>;
  limit?: number;
  offset?: number;
}): Promise<SearchResult> {
  const { data } = await api.post<SearchResult>("/search/", {
    filters: {},
    limit: 20,
    offset: 0,
    ...params,
  });
  return data;
}

export async function fetchTopics(): Promise<Topic[]> {
  const { data } = await api.get<Topic[]>("/topics/");
  return data;
}

export async function createTopic(topic: {
  name: string;
  query: string;
  sources: string[];
  filters?: Record<string, unknown>;
}): Promise<Topic> {
  const { data } = await api.post<Topic>("/topics/", topic);
  return data;
}

export async function refreshTopic(topicId: string): Promise<void> {
  await api.post(`/topics/${topicId}/refresh`);
}

export async function deleteTopic(topicId: string): Promise<void> {
  await api.delete(`/topics/${topicId}`);
}

export async function fetchPapers(): Promise<Paper[]> {
  const { data } = await api.get<Paper[]>("/papers/");
  return data;
}

export async function updatePaper(
  paperId: string,
  updates: { tags?: string[]; notes?: string },
): Promise<Paper> {
  const { data } = await api.put<Paper>(`/papers/${paperId}`, updates);
  return data;
}

export async function createPaper(paper: {
  doi?: string | null;
  title: string;
  authors: { name: string }[];
  abstract?: string | null;
  year?: number | null;
  venue?: string | null;
  publication_type?: string | null;
  urls?: Paper["urls"];
  citation_count?: number;
  source_apis?: string[];
  is_open_access?: boolean;
  open_access_pdf?: string | null;
}): Promise<Paper> {
  const { data } = await api.post<Paper>("/papers/", {
    urls: {},
    tags: [],
    ...paper,
  });
  return data;
}

export async function exportPapers(
  paperIds: string[],
  format: "bibtex" | "ris" | "plain",
  options?: { groupByTopic?: boolean },
): Promise<{ content: string; groups?: string[] }> {
  const { data } = await api.post<{ content: string; groups?: string[] }>("/export/", {
    paper_ids: paperIds,
    format,
    group_by_topic: options?.groupByTopic ?? true,
  });
  return data;
}
