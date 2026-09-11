import { Input, Select, Button, Space, Tooltip } from "antd";
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
  return (
    <div className="ls-stack">
      <Space.Compact style={{ width: "100%" }}>
        <Input
          value={query}
          onChange={(e) => onQueryChange(e.target.value)}
          placeholder='例如：TI="large language model" AND PY=2023-2024'
          onPressEnter={onSearch}
          size="large"
          suffix={
            <Tooltip title="支持字段：TI 标题 · AU 作者 · AB 摘要 · SO 期刊 · PY 年份 · DO DOI · TS 主题 · AF 全部。算符：AND OR NOT NEAR/x">
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

      <div>
        <span style={{ marginRight: 8, color: "var(--ls-muted)", fontSize: 13 }}>数据源</span>
        <Select
          mode="multiple"
          value={sources}
          onChange={onSourcesChange}
          style={{ minWidth: 320, maxWidth: "100%" }}
          options={AVAILABLE_SOURCES.map((s) => ({ value: s.value, label: s.label }))}
          placeholder="选择至少一个数据源"
        />
      </div>
    </div>
  );
}
