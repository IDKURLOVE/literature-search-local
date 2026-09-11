import { useState } from "react";
import { Button, Checkbox, Form, Input, Space, Typography, message } from "antd";
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
  const queryClient = useQueryClient();
  const { data, isLoading } = useQuery({ queryKey: ["topics"], queryFn: fetchTopics });
  const [showForm, setShowForm] = useState(false);
  const [form] = Form.useForm<TopicFormValues>();

  const createMut = useMutation({
    mutationFn: (values: TopicFormValues) =>
      createTopic({
        name: values.name.trim(),
        query: values.query.trim(),
        sources: values.sources?.length ? values.sources : ["crossref", "openalex"],
      }),
    onSuccess: () => {
      message.success("主题已创建，正在后台抓取文献");
      form.resetFields();
      setShowForm(false);
      queryClient.invalidateQueries({ queryKey: ["topics"] });
      queryClient.invalidateQueries({ queryKey: ["papers"] });
    },
    onError: () => message.error("创建失败，请检查后端是否已启动"),
  });

  const refreshMut = useMutation({
    mutationFn: (t: Topic) => refreshTopic(t.id),
    onSuccess: () => {
      message.success("已开始刷新");
      queryClient.invalidateQueries({ queryKey: ["topics"] });
    },
    onError: () => message.error("刷新失败"),
  });

  const deleteMut = useMutation({
    mutationFn: (t: Topic) => deleteTopic(t.id),
    onSuccess: () => {
      message.success("已删除");
      queryClient.invalidateQueries({ queryKey: ["topics"] });
    },
    onError: () => message.error("删除失败"),
  });

  const openForm = () => {
    setShowForm(true);
    requestAnimationFrame(() => {
      document.getElementById("topic-name-input")?.focus();
    });
  };

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
            保存常用检索词，按配置周期自动刷新，也可手动立即刷新。
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
          onRefresh={(t) => refreshMut.mutate(t)}
          onDelete={(t) => deleteMut.mutate(t)}
        />
      </div>
    </div>
  );
}
