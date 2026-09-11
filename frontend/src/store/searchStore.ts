import { create } from "zustand";
import { persist } from "zustand/middleware";

interface SearchState {
  query: string;
  sources: string[];
  setQuery: (q: string) => void;
  setSources: (s: string[]) => void;
}

export const useSearchStore = create<SearchState>()(
  persist(
    (set) => ({
      query: 'TI="large language model" AND PY=2023-2024',
      sources: ["crossref", "openalex"],
      setQuery: (q) => set({ query: q }),
      setSources: (s) => set({ sources: s }),
    }),
    { name: "litscope-search" },
  ),
);
