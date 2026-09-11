import { useMemo, useState } from "react";
import { App, Button, Checkbox, Empty, Input, Radio, Space, Tag, Typography } from "antd";
import { DownloadOutlined } from "@ant-design/icons";
import { useQuery } from "@tanstack/react-query";
import { PaperCard } from "../components/PaperCard";
import { exportPapers, fetchPapers, updatePaper } from "../api/client";
import type { Paper } from "../types";

const { Title, Paragraph, Text } = Typography;

const FORMAT_LABEL: Record<string, string> = {
  bibtex: "BibTeX",
  ris: "RIS",
  plain: "Plain Text",
};

export function PaperDetailPage() {
  const { message } = App.useApp();
  const { data, isLoading, refetch } = useQuery({ queryKey: ["papers"], queryFn: fetchPapers });
  const [selected, setSelected] = useState<string[]>([]);
  const [format, setFormat] = useState<"bibtex" | "ris" | "plain">("bibtex");
  const [noteDrafts, setNoteDrafts] = useState<Record<string, string>>({});
  const [tagDrafts, setTagDrafts] = useState<Record<string, string[]>>({});

  const papers = data || [];
  const selectedSet = useMemo(() => new Set(selected), [selected]);
  const selectedPapers = useMemo(
    () => papers.filter((p) => selectedSet.has(p.id)),
    [papers, selectedSet],
  );

  const toggle = (id: string, checked: boolean) => {
    setSelected((prev) => (checked ? [...prev, id] : prev.filter((x) => x !== id)));
  };

  const handleExport = async () => {
    if (!selected.length) {
      message.warning({ content: "请先勾选要导出的文献", key: "lib-msg", duration: 2 });
      return;
    }
    try {
      const content = await exportPapers(selected, format);
      const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      const ext = format === "bibtex" ? "bib" : format === "ris" ? "ris" : "txt";
      a.download = `litscope-export-${selected.length}.${ext}`;
      a.click();
      URL.revokeObjectURL(url);
      message.success({
        content: `已导出 ${selected.length} 篇（${FORMAT_LABEL[format]}）`,
        key: "lib-msg",
        duration: 2,
      });
    } catch {
      message.error({ content: "导出失败", key: "lib-msg", duration: 2 });
    }
  };

  const saveNote = async (paper: Paper) => {
    const notes = noteDrafts[paper.id] ?? paper.notes ?? "";
    const tags = tagDrafts[paper.id] ?? paper.tags ?? [];
    try {
      await updatePaper(paper.id, { notes, tags });
      message.success({ content: "已保存标签与笔记", key: "lib-msg", duration: 2 });
      refetch();
    } catch {
      message.error({ content: "保存失败（文献可能尚未入库）", key: "lib-msg", duration: 3 });
    }
  };

  return (
    <div>
      <section className="ls-hero">
        <Title level={1} style={{ fontFamily: "var(--ls-font-display)", color: "var(--ls-ink)" }}>
          文献库
        </Title>
        <Paragraph type="secondary">
          主题刷新或收藏入库的文献。勾选后可导出；导出前可核对下方「将导出的文献」列表。
        </Paragraph>
      </section>

      <div className="ls-panel" style={{ marginBottom: 16 }}>
        <Space direction="vertical" size={12} style={{ width: "100%" }}>
          <Space wrap align="center">
            <Text strong>导出格式</Text>
            <Radio.Group
              value={format}
              onChange={(e) => setFormat(e.target.value)}
              optionType="button"
              buttonStyle="solid"
              options={[
                { label: "BibTeX", value: "bibtex" },
                { label: "RIS", value: "ris" },
                { label: "Plain Text", value: "plain" },
              ]}
            />
            <Button type="primary" icon={<DownloadOutlined />} onClick={handleExport}>
              导出所选
            </Button>
            {selected.length > 0 && (
              <Button onClick={() => setSelected([])}>清空选择</Button>
            )}
          </Space>

          <div>
            <Text type="secondary">
              已选 <Text strong>{selectedPapers.length}</Text> 篇
            </Text>
            {selectedPapers.length > 0 && (
              <div style={{ marginTop: 8, display: "flex", flexWrap: "wrap", gap: 8 }}>
                {selectedPapers.map((p) => (
                  <Tag
                    key={p.id}
                    closable
                    onClose={() => toggle(p.id, false)}
                    style={{ maxWidth: 360 }}
                  >
                    {p.year ? `${p.year} · ` : ""}
                    {(p.title || "").slice(0, 60)}
                    {(p.title || "").length > 60 ? "…" : ""}
                  </Tag>
                ))}
              </div>
            )}
            {selectedPapers.length === 0 && (
              <div style={{ marginTop: 6, color: "var(--ls-muted)", fontSize: 13 }}>
                在下方列表勾选文献后，这里会显示将要导出的标题。
              </div>
            )}
          </div>
        </Space>
      </div>

      {isLoading ? (
        <div className="ls-empty">加载中…</div>
      ) : papers.length === 0 ? (
        <Empty className="ls-empty" description="文献库为空。创建主题并触发刷新，或在检索页收藏文献。" />
      ) : (
        <div className="ls-stack">
          {papers.map((paper) => (
            <div
              key={paper.id}
              style={{ display: "grid", gridTemplateColumns: "auto 1fr", gap: 12, alignItems: "start" }}
            >
              <Checkbox
                checked={selectedSet.has(paper.id)}
                onChange={(e) => toggle(paper.id, e.target.checked)}
                style={{ marginTop: 20 }}
              />
              <div className="ls-stack">
                <PaperCard paper={paper} />
                <Input
                  placeholder="添加标签，回车确认"
                  value={(tagDrafts[paper.id] ?? paper.tags ?? []).join(", ")}
                  onChange={(e) => {
                    const parts = e.target.value
                      .split(/[,，]/)
                      .map((s) => s.trim())
                      .filter(Boolean);
                    setTagDrafts((prev) => ({ ...prev, [paper.id]: parts }));
                  }}
                />
                <Input.TextArea
                  rows={2}
                  placeholder="为这篇文献写笔记…"
                  value={noteDrafts[paper.id] ?? paper.notes ?? ""}
                  onChange={(e) =>
                    setNoteDrafts((prev) => ({ ...prev, [paper.id]: e.target.value }))
                  }
                />
                <Button onClick={() => saveNote(paper)} style={{ alignSelf: "flex-start" }}>
                  保存标签与笔记
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
