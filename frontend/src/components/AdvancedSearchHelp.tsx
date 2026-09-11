import { Collapse, Typography } from "antd";

const { Text } = Typography;

const FIELDS = [
  ["TI", "标题"],
  ["AU", "作者"],
  ["AB", "摘要"],
  ["SO", "期刊/来源"],
  ["PY", "年份或区间，如 2023 或 2020-2024"],
  ["DO", "DOI"],
  ["TS", "主题"],
  ["AF", "全部字段"],
  ["IS", "ISSN"],
];

export function AdvancedSearchHelp() {
  return (
    <Collapse
      ghost
      items={[
        {
          key: "help",
          label: "类 WOS 检索语法说明",
          children: (
            <div className="ls-stack">
              <div>
                {FIELDS.map(([code, desc]) => (
                  <div key={code} style={{ marginBottom: 6 }}>
                    <Text code>{code}=</Text>{" "}
                    <Text type="secondary">{desc}</Text>
                  </div>
                ))}
              </div>
              <div>
                <Text type="secondary">
                  算符：<Text code>AND</Text> <Text code>OR</Text> <Text code>NOT</Text>{" "}
                  <Text code>NEAR/5</Text>；短语用引号，如 <Text code>TI="large language model"</Text>
                  。括号可组合。字段标签与等号之间不要加空格。
                </Text>
              </div>
              <div>
                <Text type="secondary">
                  示例：<Text code>TI=transformer AND PY=2023</Text>；{" "}
                  <Text code>(AU=lecun OR AU=bengio) AND AB=representation</Text>
                </Text>
              </div>
            </div>
          ),
        },
      ]}
    />
  );
}
