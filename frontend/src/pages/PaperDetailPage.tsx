import { useMemo, useState } from "react";
import { Button, Checkbox, Empty, Input, Select, Space, Typography, message } from "antd";
import { DownloadOutlined } from "@ant-design/icons";
import { useQuery } from "@tanstack/react-query";
import { PaperCard } from "../components/PaperCard";
import { exportPapers, fetchPapers, updatePaper } from "../api/client";
import type { Paper } from "../types";

const { Title, Paragraph, Text } = Typography;

export function PaperDetailPage() {
  const { data, isLoading, refetch } = useQuery({ queryKey: ["papers"], queryFn: fetchPapers });
  const [selected, setSelected] = useState<string[]>([]);
  const [format, setFormat] = useState<"bibtex" | "ris" | "plain">("bibtex");
  const [noteDrafts, setNoteDrafts] = useState<Record<string, string>>({});
  const [tagDrafts, setTagDrafts] = useState<Record<string, string[]>>({});

  const papers = data || [];
  const selectedSet = useMemo(() => new Set(selected), [selected]);

  const toggle = (id: string, checked: boolean) => {
    setSelected((prev) => (checked ? [...prev, id] : prev.filter((x) => x !== id)));
  };

  const handleExport = async () => {
    if (!selected.length) {
      message.warning("请先勾选要导出的文献");
      return;
    }
    try {
      const content = await exportPapers(selected, format);
      const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `litscope-export.${format === "bibtex" ? "bib" : format === "ris" ? "ris" : "txt"}`;
      a.click();
      URL.revokeObjectURL(url);
      message.success("导出已开始下载");
    } catch {
      message.error("导出失败");
    }
  };

  const saveNote = async (paper: Paper) => {
    const notes = noteDrafts[paper.id] ?? paper.notes ?? "";
    const tags = tagDrafts[paper.id] ?? paper.tags ?? [];
    try {
      await updatePaper(paper.id, { notes, tags });
      message.success("已保存标签与笔记");
      refetch();
    } catch {
      message.error("保存失败（文献可能尚未入库，请先收藏或通过主题刷新入库）");
    }
  };

  return (
    <div>
      <section className="ls-hero">
        <Title level={1} style={{ fontFamily: "var(--ls-font-display)", color: "var(--ls-ink)" }}>
          文献库
        </Title>
        <Paragraph type="secondary">
          主题刷新入库后的文献。可写笔记、打标签，并导出 BibTeX / RIS / Plain Text。
        </Paragraph>
      </section>

      <div className="ls-panel" style={{ marginBottom: 16 }}>
        <Space wrap>
          <Text type="secondary">已选 {selected.length} 篇</Text>
          <Select
            value={format}
            onChange={setFormat}
            style={{ width: 140 }}
            options={[
              { value: "bibtex", label: "BibTeX" },
              { value: "ris", label: "RIS" },
              { value: "plain", label: "Plain Text" },
            ]}
          />
          <Button type="primary" icon={<DownloadOutlined />} onClick={handleExport}>
            导出
          </Button>
        </Space>
      </div>

      {isLoading ? (
        <div className="ls-empty">加载中…</div>
      ) : papers.length === 0 ? (
        <Empty className="ls-empty" description="文献库为空。创建主题并触发刷新后，这里会出现收录结果。" />
      ) : (
        <div className="ls-stack">
          {papers.map((paper) => (
            <div key={paper.id} style={{ display: "grid", gridTemplateColumns: "auto 1fr", gap: 12, alignItems: "start" }}>
              <Checkbox
                checked={selectedSet.has(paper.id)}
                onChange={(e) => toggle(paper.id, e.target.checked)}
                style={{ marginTop: 20 }}
              />
              <div className="ls-stack">
                <PaperCard paper={paper} />
                <Select
                  mode="tags"
                  placeholder="添加标签，回车确认"
                  value={tagDrafts[paper.id] ?? paper.tags ?? []}
                  onChange={(tags) => setTagDrafts((prev) => ({ ...prev, [paper.id]: tags }))}
                  open={false}
                  suffixIcon={null}
                  style={{ width: "100%" }}
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
