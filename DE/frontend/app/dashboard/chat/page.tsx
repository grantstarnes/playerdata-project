import { api } from "@/lib/api";
import { ChatPanel } from "@/components/chat/chat-panel";

export default async function ChatPage() {
  const { default: defaultModel, models } = await api.chatModels();

  return (
    <main className="flex flex-1 flex-col p-6">
      <div className="mb-4">
        <h2 className="text-2xl font-bold tracking-tight">Chat</h2>
        <p className="text-sm text-pd-ink-400">
          Ask questions about athlete performance. Model-selectable: Gemma 4, Qwen 2.5, or instant rule-based fallback.
        </p>
      </div>
      <div className="flex-1 min-h-0">
        <ChatPanel defaultModel={defaultModel} models={models} />
      </div>
    </main>
  );
}
