import { useState } from "react";
import { Alert, App, Divider, Space, Typography } from "antd";
import { useMutation } from "@tanstack/react-query";
import { SearchBox } from "../components/SearchBox";
import { AdvancedSearchHelp } from "../components/AdvancedSearchHelp";
import { PaperCard } from "../components/PaperCard";
import { createPaper, createTopic, searchPapers } from "../api/client";
import { DEFAULT_SOURCES, useSearchStore } from "../store/searchStore";
import type { Paper } from "../types";

const { Title, Text } = Typography;

export function HomePage() {
  const { message } = App.useApp();
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
        message.warning({ content: "请先输入主题关键词", key: "search-msg", duration: 2 });
        return;
      }
      message.error({
        content: "搜索失败：后端未启动或数据源限流，请稍后重试",
        key: "search-msg",
        duration: 3,
      });
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
      message.success({ content: "已收藏到文献库", key: "save-msg", duration: 2 });
    },
    onError: () => message.error({ content: "收藏失败", key: "save-msg", duration: 2 }),
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
      message.success({ content: "已保存为研究主题", key: "topic-msg", duration: 2 });
    } catch {
      message.error({ content: "保存失败", key: "topic-msg", duration: 2 });
    }
  };

  return (
    <div>
      <section className="ls-hero">
        <Title level={1} style={{ fontFamily: "var(--ls-font-display)", color: "var(--ls-ink)", marginBottom: 8 }}>
          检索开放学术源
        </Title>
        <p>
          直接输入主题关键词（支持中文），并行查询 Crossref、OpenAlex、Semantic Scholar、PubMed、arXiv。
          结果按相关度排序并过滤跑题文献。可收藏或保存为研究主题。
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
                找到 <Text strong>{papers.length}</Text> 条相关结果
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
                  type="info"
                  showIcon
                  closable
                  style={{ marginBottom: 8 }}
                  message={`${name} 本次未返回（限流或网络）`}
                  description="其它数据源结果仍可用；可稍后重试或配置 API Key。"
                />
              );
            }
            return null;
          })}

          <div className="ls-stack">
            {papers.length === 0 ? (
              <div className="ls-empty">
                没有足够相关的文献。可换个更具体的关键词（含核心对象，如「风速」），或多选数据源。
                <br />
                <Text type="secondary" style={{ fontSize: 12 }}>
                  说明：知网 / 官方 Web of Science 无免费公开 API，本工具不对接；已用类 WOS 语法 + 相关度过滤逼近。
                </Text>
              </div>
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
