import { useState } from "react";
import { Alert, Divider, message, Space, Typography } from "antd";
import { useMutation } from "@tanstack/react-query";
import { SearchBox } from "../components/SearchBox";
import { AdvancedSearchHelp } from "../components/AdvancedSearchHelp";
import { PaperCard } from "../components/PaperCard";
import { createPaper, createTopic, searchPapers } from "../api/client";
import { DEFAULT_SOURCES, useSearchStore } from "../store/searchStore";
import type { Paper } from "../types";

const { Title, Text } = Typography;

export function HomePage() {
  const { query, sources, setQuery, setSources } = useSearchStore();
  const [papers, setPapers] = useState<Paper[]>([]);
  const [sourceStatus, setSourceStatus] = useState<Record<string, unknown>>({});

  const searchMutation = useMutation({
    mutationFn: () => {
      const q = query.trim();
      if (!q) {
        throw new Error("empty");
      }
      return searchPapers({
        query: q,
        sources: sources.length ? sources : DEFAULT_SOURCES,
      });
    },
    onSuccess: (data) => {
      setPapers(data.papers || []);
      setSourceStatus(data.sources || {});
    },
    onError: (err) => {
      if ((err as Error).message === "empty") {
        message.warning("请先输入主题关键词");
        return;
      }
      message.error("搜索失败：请检查后端是否已启动，或稍后重试（数据源可能限流）");
    },
  });

  const saveMutation = useMutation({
    mutationFn: (paper: Paper) =>
      createPaper({
        doi: paper.doi,
        title: paper.title,
        authors: paper.authors,
        abstract: paper.abstract,
        year: paper.year,
        venue: paper.venue,
        publication_type: paper.publication_type,
        urls: paper.urls,
        citation_count: paper.citation_count,
        source_apis: paper.source_apis,
        is_open_access: paper.is_open_access,
        open_access_pdf: paper.open_access_pdf,
      }),
    onSuccess: () => {
      message.success("已收藏到文献库");
    },
    onError: () => message.error("收藏失败"),
  });

  const saveQueryAsTopic = async () => {
    const q = query.trim();
    if (!q) return;
    try {
      await createTopic({
        name: q.slice(0, 80),
        query: q,
        sources: sources.length ? sources : DEFAULT_SOURCES,
      });
      message.success("已保存为研究主题");
    } catch {
      message.error("保存失败");
    }
  };

  return (
    <div>
      <section className="ls-hero">
        <Title level={1} style={{ fontFamily: "var(--ls-font-display)", color: "var(--ls-ink)", marginBottom: 8 }}>
          检索开放学术源
        </Title>
        <p>
          直接输入主题关键词，即可并行查询 Crossref、OpenAlex、Semantic Scholar、PubMed、arXiv。
          结果自动去重，可收藏到文献库，或保存为研究主题定时刷新。
        </p>
      </section>

      <div className="ls-panel">
        <SearchBox
          query={query}
          sources={sources}
          loading={searchMutation.isPending}
          onQueryChange={setQuery}
          onSourcesChange={setSources}
          onSearch={() => searchMutation.mutate()}
        />
        <div style={{ marginTop: 8 }}>
          <AdvancedSearchHelp />
        </div>
      </div>

      {searchMutation.isSuccess && (
        <>
          <Divider style={{ borderColor: "var(--ls-hairline)" }}>
            <Space>
              <Text>
                找到 <Text strong>{papers.length}</Text> 条结果
              </Text>
              <a onClick={saveQueryAsTopic}>保存为研究主题</a>
            </Space>
          </Divider>

          {Object.entries(sourceStatus).map(([name, status]) => {
            const s = status as { status?: string; error?: string; count?: number };
            if (s?.status === "error") {
              return (
                <Alert
                  key={name}
                  type="warning"
                  showIcon
                  style={{ marginBottom: 8 }}
                  message={`${name} 暂不可用`}
                  description={s.error || "请求失败或被限流"}
                />
              );
            }
            return null;
          })}

          <div className="ls-stack">
            {papers.length === 0 ? (
              <div className="ls-empty">没有匹配结果。换个关键词试试，或多选几个数据源。</div>
            ) : (
              papers.map((paper) => (
                <PaperCard
                  key={paper.id}
                  paper={paper}
                  onSave={(p) => saveMutation.mutate(p)}
                />
              ))
            )}
          </div>
        </>
      )}
    </div>
  );
}
