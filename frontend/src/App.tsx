import { BrowserRouter, NavLink, Route, Routes } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ConfigProvider, theme, App as AntApp } from "antd";
import { HomePage } from "./pages/HomePage";
import { TopicPage } from "./pages/TopicPage";
import { PaperDetailPage } from "./pages/PaperDetailPage";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, refetchOnWindowFocus: false },
  },
});

const themeConfig = {
  algorithm: theme.defaultAlgorithm,
  token: {
    colorPrimary: "#cc785c",
    colorLink: "#cc785c",
    colorSuccess: "#5db872",
    colorError: "#c64545",
    colorText: "#3d3d3a",
    colorTextHeading: "#141413",
    colorBorder: "#e6dfd8",
    colorBorderSecondary: "#ebe6df",
    colorBgContainer: "#fffefb",
    colorBgElevated: "#fffefb",
    colorBgLayout: "#faf9f5",
    borderRadius: 8,
    borderRadiusLG: 12,
    borderRadiusSM: 6,
    fontFamily: `Inter, "Segoe UI", "PingFang SC", "Microsoft YaHei", system-ui, sans-serif`,
    fontSize: 14,
    controlHeight: 40,
  },
};

function Shell() {
  return (
    <div className="ls-shell">
      <header className="ls-header">
        <NavLink to="/" className="ls-brand">
          <span className="ls-brand-mark">LitScope</span>
          <span className="ls-brand-sub">Local</span>
        </NavLink>
        <nav className="ls-nav">
          <NavLink to="/" end>
            检索
          </NavLink>
          <NavLink to="/topics">研究主题</NavLink>
          <NavLink to="/library">文献库</NavLink>
        </nav>
      </header>
      <main className="ls-main">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/topics" element={<TopicPage />} />
          <Route path="/library" element={<PaperDetailPage />} />
        </Routes>
        <footer className="ls-footer">
          LitScope Local · 单用户免登录 · 由 Xiaomi MIMO — MiMo-X-Pro-Preview 协助开发
        </footer>
      </main>
    </div>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ConfigProvider theme={themeConfig}>
        <AntApp>
          <BrowserRouter>
            <Shell />
          </BrowserRouter>
        </AntApp>
      </ConfigProvider>
    </QueryClientProvider>
  );
}
