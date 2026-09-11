import { create } from "zustand";
import { persist } from "zustand/middleware";

interface SearchState {
  query: string;
  sources: string[];
  setQuery: (q: string) => void;
  setSources: (s: string[]) => void;
}

export const DEFAULT_SOURCES = ["crossref", "openalex"];

export const useSearchStore = create<SearchState>()(
  persist(
    (set) => ({
      query: "",
      sources: [...DEFAULT_SOURCES],
      setQuery: (q) => set({ query: q }),
      setSources: (s) => set({ sources: s.length ? s : [...DEFAULT_SOURCES] }),
    }),
    {
      name: "litscope-search",
      version: 2,
      migrate: () => ({
        query: "",
        sources: [...DEFAULT_SOURCES],
      }),
    },
  ),
);
