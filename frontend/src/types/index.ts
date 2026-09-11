export interface Author {
  name: string;
  orcid?: string;
}

export interface PaperUrls {
  doi?: string;
  source?: string;
  open_access_pdf?: string;
}

export interface Paper {
  id: string;
  doi?: string | null;
  title: string;
  authors: Author[];
  abstract?: string | null;
  year?: number | null;
  venue?: string | null;
  publication_type?: string | null;
  urls: PaperUrls;
  citation_count: number;
  source_apis: string[];
  is_open_access: boolean;
  open_access_pdf?: string | null;
  tags: string[];
  notes?: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface Topic {
  id: string;
  name: string;
  query: string;
  sources: string[];
  filters: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  last_results_count: number;
}

export interface SourceStatus {
  status: "ok" | "error";
  count?: number;
  error?: string;
}

export interface QueryTranslationInfo {
  free_text?: string;
  from_year?: number | null;
  until_year?: number | null;
  parse_ok?: boolean;
  parse_error?: string | null;
}

export interface SearchResult {
  papers: Paper[];
  total: number;
  sources: Record<string, SourceStatus>;
  query_translation?: QueryTranslationInfo | null;
}

export const AVAILABLE_SOURCES = [
  { value: "crossref", label: "Crossref" },
  { value: "openalex", label: "OpenAlex" },
  { value: "semantic_scholar", label: "Semantic Scholar" },
  { value: "pubmed", label: "PubMed" },
  { value: "arxiv", label: "arXiv" },
] as const;
