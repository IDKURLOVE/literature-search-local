import { Button, Empty, List, Popconfirm, Space, Tag, Typography } from "antd";
import { DeleteOutlined, ReloadOutlined } from "@ant-design/icons";
import type { Topic } from "../types";

const { Text } = Typography;

interface Props {
  topics: Topic[];
  loading?: boolean;
  onRefresh: (topic: Topic) => void;
  onDelete: (topic: Topic) => void;
  onOpen?: (topic: Topic) => void;
}

export function TopicList({ topics, loading, onRefresh, onDelete, onOpen }: Props) {
  if (!topics?.length) {
    return (
      <Empty
        className="ls-empty"
        description="还没有研究主题。先搜索，再点「保存为检索主题」。"
        image={Empty.PRESENTED_IMAGE_SIMPLE}
      />
    );
  }

  return (
    <List
      loading={loading}
      dataSource={topics}
      renderItem={(topic) => (
        <List.Item
          actions={[
            <Button
              key="refresh"
              icon={<ReloadOutlined />}
              onClick={() => onRefresh(topic)}
            >
              刷新
            </Button>,
            <Popconfirm
              key="del"
              title="删除该主题？"
              okText="删除"
              cancelText="取消"
              onConfirm={() => onDelete(topic)}
            >
              <Button danger icon={<DeleteOutlined />} />
            </Popconfirm>,
          ]}
        >
          <List.Item.Meta
            title={
              <Space wrap>
                <Text strong style={{ color: "var(--ls-ink)" }} onClick={() => onOpen?.(topic)}>
                  {topic.name}
                </Text>
                <Tag bordered={false}>{topic.last_results_count} 篇</Tag>
              </Space>
            }
            description={
              <Space direction="vertical" size={4}>
                <Text code style={{ color: "var(--ls-body)" }}>
                  {topic.query}
                </Text>
                <Text type="secondary" style={{ fontSize: 12 }}>
                  数据源：{(topic.sources || []).join(", ") || "默认"} · 更新于{" "}
                  {new Date(topic.updated_at).toLocaleString()}
                </Text>
              </Space>
            }
          />
        </List.Item>
      )}
    />
  );
}
