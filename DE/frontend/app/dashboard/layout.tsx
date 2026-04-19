import { AppBar } from "@/components/layout/app-bar";
import { TabNav } from "@/components/layout/tab-nav";
import { ChatWidget } from "@/components/chat/chat-widget";
import { api } from "@/lib/api";

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { default: defaultModel, models } = await api.chatModels();

  return (
    <div className="flex flex-1 flex-col" style={{ background: "var(--pd-bg)" }}>
      <AppBar />
      <TabNav />
      <main className="mx-auto w-full" style={{ maxWidth: 1400, padding: "24px 32px 96px" }}>
        {children}
      </main>
      <ChatWidget defaultModel={defaultModel} models={models} />
    </div>
  );
}
