import { useState } from "react";
import { Alert, Divider, message, Space, Typography } from "antd";
import { useMutation } from "@tanstack/react-query";
import { SearchBox } from "../components/SearchBox";
import { AdvancedSearchHelp } from "../components/AdvancedSearchHelp";
import { PaperCard } from "../components/PaperCard";
import { createPaper, createTopic, searchPapers } from "../api/client";
import { useSearchStore } from "../store/searchStore";
import type { Paper } from "../types";

const { Title, Text } = Typography;

export function HomePage() {
  const { query, sources, setQuery, setSources } = useSearchStore();
  const [papers, setPapers] = useState<Paper[]>([]);
  const [sourceStatus, setSourceStatus] = useState<Record<string, unknown>>({});

  const searchMutation = useMutation({
    mutationFn: () => searchPapers({ query, sources }),
    onSuccess: (data) => {
      setPapers(data.papers || []);
      setSourceStatus(data.sources || {});
    },
    onError: () => {
      message.error("搜索失败：请检查后端是否已启动，或查询语法是否正确");
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
    if (!query.trim()) return;
    try {
      await createTopic({
        name: query.slice(0, 80),
        query,
        sources,
      });
      message.success("当前检索已保存为研究主题");
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
          用类 Web of Science 语法并行查询 Crossref、OpenAlex、Semantic Scholar、PubMed、arXiv。
          结果去重后展示 DOI / 开放获取链接，可一键保存为研究主题并定时刷新。
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
        <div style={{ marginTop: 12 }}>
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
              <a onClick={saveQueryAsTopic}>保存为检索主题</a>
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
                  message={`${name} 请求失败`}
                  description={s.error}
                />
              );
            }
            return null;
          })}

          <div className="ls-stack">
            {papers.length === 0 ? (
              <div className="ls-empty">没有匹配结果。试试放宽年份，或增加数据源。</div>
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
