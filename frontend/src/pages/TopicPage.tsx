import { useEffect, useRef, useState } from "react";
import { App, Button, Checkbox, Form, Input, Space, Typography } from "antd";
import { PlusOutlined } from "@ant-design/icons";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { TopicList } from "../components/TopicList";
import { createTopic, deleteTopic, fetchTopics, refreshTopic } from "../api/client";
import { AVAILABLE_SOURCES } from "../types";
import type { Topic } from "../types";

const { Title, Paragraph } = Typography;

interface TopicFormValues {
  name: string;
  query: string;
  sources: string[];
}

export function TopicPage() {
  const { message } = App.useApp();
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [form] = Form.useForm<TopicFormValues>();
  const [refreshingIds, setRefreshingIds] = useState<string[]>([]);
  const baselineRef = useRef<Record<string, string>>({});
  const timersRef = useRef<number[]>([]);

  // Poll faster while any topic is refreshing
  const { data, isLoading } = useQuery({
    queryKey: ["topics"],
    queryFn: fetchTopics,
    refetchInterval: refreshingIds.length ? 1500 : false,
  });

  useEffect(() => {
    return () => {
      timersRef.current.forEach((id) => window.clearTimeout(id));
    };
  }, []);

  const toast = (type: "success" | "error" | "info", content: string) => {
    message.destroy("topic-op");
    message.open({ type, content, key: "topic-op", duration: 2 });
    const t = window.setTimeout(() => {
      message.destroy("topic-op");
    }, 2200);
    timersRef.current.push(t);
  };

  // When updated_at changes for a refreshing topic, mark done
  useEffect(() => {
    if (!data?.length || !refreshingIds.length) return;
    const still: string[] = [];
    let completed = 0;
    for (const id of refreshingIds) {
      const topic = data.find((t) => t.id === id);
      if (!topic) continue;
      const base = baselineRef.current[id];
      if (base && topic.updated_at !== base) {
        completed += 1;
      } else {
        still.push(id);
      }
    }
    if (completed > 0) {
      setRefreshingIds(still);
      toast("success", "主题刷新完成");
      queryClient.invalidateQueries({ queryKey: ["papers"] });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data, refreshingIds]);

  const createMut = useMutation({
    mutationFn: (values: TopicFormValues) =>
      createTopic({
        name: values.name.trim(),
        query: values.query.trim(),
        sources: values.sources?.length ? values.sources : ["crossref", "openalex"],
      }),
    onSuccess: (created) => {
      toast("success", "主题已创建，正在抓取文献");
      form.resetFields();
      setShowForm(false);
      if (created?.id) {
        baselineRef.current[created.id] = created.updated_at;
        setRefreshingIds((prev) => [...prev, created.id]);
      }
      queryClient.invalidateQueries({ queryKey: ["topics"] });
      queryClient.invalidateQueries({ queryKey: ["papers"] });
    },
    onError: () => toast("error", "创建失败，请检查后端是否已启动"),
  });

  const refreshMut = useMutation({
    mutationFn: (t: Topic) => refreshTopic(t.id).then(() => t),
    onSuccess: (t) => {
      baselineRef.current[t.id] = t.updated_at;
      setRefreshingIds((prev) => (prev.includes(t.id) ? prev : [...prev, t.id]));
      toast("info", "已开始刷新…");
      queryClient.invalidateQueries({ queryKey: ["topics"] });
    },
    onError: () => {
      toast("error", "刷新失败");
      setRefreshingIds((prev) => prev);
    },
  });

  const deleteMut = useMutation({
    mutationFn: (t: Topic) => deleteTopic(t.id),
    onSuccess: (_d, t) => {
      toast("success", "已删除");
      setRefreshingIds((prev) => prev.filter((id) => id !== t.id));
      queryClient.invalidateQueries({ queryKey: ["topics"] });
    },
    onError: () => toast("error", "删除失败"),
  });

  const openForm = () => {
    setShowForm(true);
    requestAnimationFrame(() => {
      document.getElementById("topic-name-input")?.focus();
    });
  };

  // Safety: never leave a topic stuck in refreshing forever
  useEffect(() => {
    if (!refreshingIds.length) return;
    const t = window.setTimeout(() => {
      setRefreshingIds([]);
      toast("info", "刷新仍在后台进行，可稍后查看篇数变化");
    }, 90000);
    return () => window.clearTimeout(t);
  }, [refreshingIds.length]);

  return (
    <div>
      <section
        className="ls-hero"
        style={{
          display: "flex",
          justifyContent: "space-between",
          gap: 16,
          alignItems: "flex-start",
          flexWrap: "wrap",
        }}
      >
        <div>
          <Title
            level={1}
            style={{
              fontFamily: "var(--ls-font-display)",
              color: "var(--ls-ink)",
              marginBottom: 8,
            }}
          >
            研究主题
          </Title>
          <Paragraph type="secondary" style={{ marginBottom: 0 }}>
            保存常用检索词，按配置周期自动刷新，也可手动立即刷新。刷新中按钮会显示进度。
          </Paragraph>
        </div>
        <Button type="primary" icon={<PlusOutlined />} onClick={openForm}>
          新建主题
        </Button>
      </section>

      {showForm && (
        <div className="ls-panel" style={{ marginBottom: 16 }}>
          <Form
            form={form}
            layout="vertical"
            initialValues={{ name: "", query: "", sources: ["crossref", "openalex"] }}
            onFinish={(values) => createMut.mutate(values)}
            style={{ maxWidth: 560 }}
          >
            <Form.Item
              name="name"
              label="主题名称"
              rules={[{ required: true, message: "请输入名称" }]}
            >
              <Input id="topic-name-input" placeholder="例如：LLM 综述" maxLength={80} />
            </Form.Item>
            <Form.Item
              name="query"
              label="检索词"
              rules={[{ required: true, message: "请输入关键词或检索式" }]}
              extra="直接输关键词即可，例如 large language model"
            >
              <Input.TextArea rows={2} placeholder="large language model" />
            </Form.Item>
            <Form.Item
              name="sources"
              label="数据源"
              rules={[
                {
                  validator: (_, v: string[]) =>
                    !v || v.length
                      ? Promise.resolve()
                      : Promise.reject(new Error("至少选择一个数据源")),
                },
              ]}
            >
              <Checkbox.Group
                options={AVAILABLE_SOURCES.map((s) => ({
                  value: s.value,
                  label: s.label,
                }))}
              />
            </Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" loading={createMut.isPending}>
                创建并抓取
              </Button>
              <Button onClick={() => setShowForm(false)}>取消</Button>
            </Space>
          </Form>
        </div>
      )}

      <div className="ls-panel">
        <TopicList
          topics={data || []}
          loading={isLoading}
          refreshingIds={refreshingIds}
          onRefresh={(t) => {
            if (refreshingIds.includes(t.id)) return;
            refreshMut.mutate(t);
          }}
          onDelete={(t) => deleteMut.mutate(t)}
        />
      </div>
    </div>
  );
}
