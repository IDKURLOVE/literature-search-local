import { Input, Button, Space, Tooltip, Checkbox } from "antd";
import { QuestionCircleOutlined, SearchOutlined } from "@ant-design/icons";
import { AVAILABLE_SOURCES } from "../types";

interface Props {
  query: string;
  sources: string[];
  loading?: boolean;
  onQueryChange: (q: string) => void;
  onSourcesChange: (s: string[]) => void;
  onSearch: () => void;
}

export function SearchBox({
  query,
  sources,
  loading,
  onQueryChange,
  onSourcesChange,
  onSearch,
}: Props) {
  const selected = sources?.length ? sources : ["crossref", "openalex"];

  return (
    <div className="ls-stack">
      <Space.Compact style={{ width: "100%" }}>
        <Input
          value={query}
          onChange={(e) => onQueryChange(e.target.value)}
          placeholder="输入主题关键词，例如：large language model"
          onPressEnter={onSearch}
          size="large"
          allowClear
          suffix={
            <Tooltip title="直接输关键词即可。进阶：TI=标题 AU=作者 PY=年份 AND/OR/NOT">
              <QuestionCircleOutlined style={{ color: "var(--ls-muted)" }} />
            </Tooltip>
          }
        />
        <Button
          type="primary"
          size="large"
          icon={<SearchOutlined />}
          onClick={onSearch}
          loading={loading}
          style={{ minWidth: 110 }}
        >
          搜索
        </Button>
      </Space.Compact>

      <div className="ls-source-row">
        <span className="ls-source-label">数据源</span>
        <Checkbox.Group
          value={selected}
          onChange={(values) => onSourcesChange(values as string[])}
          options={AVAILABLE_SOURCES.map((s) => ({
            value: s.value,
            label: s.label,
          }))}
        />
      </div>
    </div>
  );
}
