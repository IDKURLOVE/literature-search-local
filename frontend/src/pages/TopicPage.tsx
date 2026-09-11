import { App as AntApp, Typography, message } from "antd";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { TopicList } from "../components/TopicList";
import { deleteTopic, fetchTopics, refreshTopic } from "../api/client";
import type { Topic } from "../types";

const { Title, Paragraph } = Typography;

export function TopicPage() {
  const queryClient = useQueryClient();
  const { data, isLoading } = useQuery({ queryKey: ["topics"], queryFn: fetchTopics });

  const refreshMut = useMutation({
    mutationFn: (t: Topic) => refreshTopic(t.id),
    onSuccess: () => message.success("已加入刷新队列"),
    onError: () => message.error("刷新失败：任务队列可能未启动"),
  });

  const deleteMut = useMutation({
    mutationFn: (t: Topic) => deleteTopic(t.id),
    onSuccess: () => {
      message.success("已删除");
      queryClient.invalidateQueries({ queryKey: ["topics"] });
    },
    onError: () => message.error("删除失败"),
  });

  return (
    <AntApp>
      <section className="ls-hero">
        <Title level={1} style={{ fontFamily: "var(--ls-font-display)", color: "var(--ls-ink)" }}>
          研究主题
        </Title>
        <Paragraph type="secondary">
          每个主题保存一条检索式与数据源。Celery 定时任务会按配置周期自动刷新结果。
        </Paragraph>
      </section>
      <div className="ls-panel">
        <TopicList
          topics={data || []}
          loading={isLoading}
          onRefresh={(t) => refreshMut.mutate(t)}
          onDelete={(t) => deleteMut.mutate(t)}
        />
      </div>
    </AntApp>
  );
}
