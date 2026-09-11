import { Card, Tag, Space, Button, Typography } from "antd";
import { FilePdfOutlined, LinkOutlined, SaveOutlined } from "@ant-design/icons";
import type { Paper } from "../types";

const { Text, Paragraph } = Typography;

interface Props {
  paper: Paper;
  onSave?: (paper: Paper) => void;
  onOpen?: (paper: Paper) => void;
}

export function PaperCard({ paper, onSave, onOpen }: Props) {
  const authors = (paper.authors || []).map((a) => a.name).filter(Boolean).join(", ");
  return (
    <Card
      size="small"
      style={{ background: "transparent" }}
      title={
        <Text
          strong
          style={{ color: "var(--ls-ink)", fontFamily: "var(--ls-font-display)", fontSize: 17 }}
          onClick={() => onOpen?.(paper)}
        >
          {paper.title}
        </Text>
      }
      extra={
        <Space wrap>
          {paper.doi && (
            <Button
              type="link"
              icon={<LinkOutlined />}
              href={`https://doi.org/${paper.doi}`}
              target="_blank"
              rel="noreferrer"
            >
              DOI
            </Button>
          )}
          {paper.urls?.source && (
            <Button
              type="link"
              icon={<LinkOutlined />}
              href={paper.urls.source}
              target="_blank"
              rel="noreferrer"
            >
              来源
            </Button>
          )}
          {(paper.open_access_pdf || paper.urls?.open_access_pdf) && (
            <Button
              type="link"
              icon={<FilePdfOutlined />}
              href={paper.open_access_pdf || paper.urls?.open_access_pdf || "#"}
              target="_blank"
              rel="noreferrer"
            >
              PDF
            </Button>
          )}
          {onSave && (
            <Button icon={<SaveOutlined />} onClick={() => onSave(paper)}>
              收藏
            </Button>
          )}
        </Space>
      }
    >
      <Paragraph type="secondary" ellipsis={{ rows: 2 }} style={{ marginBottom: 8 }}>
        {authors || "未知作者"} · {paper.year ?? "年份未知"}
        {paper.venue ? ` · ${paper.venue}` : ""}
      </Paragraph>
      <Paragraph ellipsis={{ rows: 3 }} style={{ marginBottom: 12 }}>
        {paper.abstract || "暂无摘要"}
      </Paragraph>
      <Space wrap>
        {(paper.source_apis || []).map((source) => (
          <Tag key={source} bordered={false} style={{ background: "var(--ls-surface-soft)" }}>
            {source}
          </Tag>
        ))}
        {paper.is_open_access && (
          <Tag color="green" bordered={false}>
            开放获取
          </Tag>
        )}
        <Text type="secondary" style={{ fontSize: 12 }}>
          被引 {paper.citation_count ?? 0}
        </Text>
        {paper.doi && (
          <Text type="secondary" className="ls-doi">
            {paper.doi}
          </Text>
        )}
      </Space>
    </Card>
  );
}
