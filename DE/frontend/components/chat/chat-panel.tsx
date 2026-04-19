"use client";

import { useAuth } from "@clerk/nextjs";
import { useEffect, useRef, useState } from "react";
import { clsx } from "clsx";

import type { ChatResponse, ModelInfo } from "@/lib/api";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Message = {
  role: "user" | "assistant";
  content: string;
  model?: string;
  tool_calls?: ChatResponse["tool_calls"];
  fallback_reason?: string | null;
};

const WELCOME = `**What can I help with?**

Ask about any athlete's performance data in plain English. For example:
- "Show me stats for athlete #1042"
- "How fast am I compared to DI average?"
- "Where do I rank in total distance?"
- "What does a typical DI female soccer player run?"

Available metrics: total distance, max speed, session load, metres per minute, high intensity events, sprint events, accel / decel events, active minutes.`;

const SUGGESTIONS = [
  "Show me stats for athlete #1042",
  "Who is the fastest female athlete in DI?",
  "Compare athlete #1042 on session load",
  "What does a typical DI female soccer player run?",
];

function SparklesIcon({ size = 14 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.75} strokeLinecap="round" strokeLinejoin="round">
      <path d="m12 3-1.9 5.8a2 2 0 0 1-1.3 1.3L3 12l5.8 1.9a2 2 0 0 1 1.3 1.3L12 21l1.9-5.8a2 2 0 0 1 1.3-1.3L21 12l-5.8-1.9a2 2 0 0 1-1.3-1.3Z" />
    </svg>
  );
}

function SendIcon({ size = 16 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.75} strokeLinecap="round" strokeLinejoin="round">
      <path d="m22 2-7 20-4-9-9-4Z" />
      <path d="M22 2 11 13" />
    </svg>
  );
}

export function ChatPanel({
  defaultModel,
  models,
}: {
  defaultModel: string;
  models: ModelInfo[];
}) {
  const { getToken } = useAuth();
  const [model, setModel] = useState(defaultModel);
  const [athleteCtx, setAthleteCtx] = useState<string>("");
  const [input, setInput] = useState("");
  const [history, setHistory] = useState<Message[]>([
    { role: "assistant", content: WELCOME, model: "system" },
  ]);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current)
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [history, pending]);

  async function send(override?: string) {
    const text = (override ?? input).trim();
    if (!text || pending) return;
    setError(null);
    setInput("");
    setHistory((h) => [...h, { role: "user", content: text }]);
    setPending(true);
    try {
      const token = await getToken();
      const res = await fetch(`${API_URL}/api/chat`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: text,
          model,
          athlete_ctx: athleteCtx ? Number(athleteCtx) : undefined,
        }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const body: ChatResponse = await res.json();
      setHistory((h) => [
        ...h,
        {
          role: "assistant",
          content: body.response,
          model: body.model,
          tool_calls: body.tool_calls,
          fallback_reason: body.fallback_reason,
        },
      ]);
    } catch (e) {
      setError(e instanceof Error ? e.message : "request failed");
    } finally {
      setPending(false);
    }
  }

  return (
    <div
      className="pd-card flex flex-col"
      style={{ padding: 0, overflow: "hidden", height: 640 }}
    >
      {/* Header */}
      <div
        className="flex items-center gap-3"
        style={{ padding: "14px 18px", borderBottom: "1px solid var(--pd-ink-100)" }}
      >
        <div
          className="flex items-center justify-center shrink-0"
          style={{ width: 32, height: 32, borderRadius: 8, background: "var(--pd-black)", color: "var(--pd-green)" }}
        >
          <SparklesIcon size={16} />
        </div>
        <div className="flex-1">
          <div style={{ fontWeight: 700, fontSize: 14 }}>Performance Chat</div>
          <div style={{ fontSize: 11.5, color: "var(--fg-3)" }}>
            Model-selectable · answers from your session data
          </div>
        </div>
        <select
          value={model}
          onChange={(e) => setModel(e.target.value)}
          style={{
            padding: "6px 10px",
            border: "1px solid var(--pd-ink-200)",
            borderRadius: 8,
            fontSize: 12.5,
            background: "#fff",
          }}
        >
          {models.map((m) => (
            <option key={m.id} value={m.id} disabled={!m.installed}>
              {m.label}
              {!m.installed ? " (not installed)" : ""}
            </option>
          ))}
        </select>
        <input
          type="number"
          placeholder="athlete ctx"
          value={athleteCtx}
          onChange={(e) => setAthleteCtx(e.target.value)}
          className="pd-input"
          style={{ width: 110, height: 32, fontSize: 12.5, fontVariantNumeric: "tabular-nums" }}
        />
      </div>

      {/* Messages */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto"
        style={{ padding: 18, display: "flex", flexDirection: "column", gap: 14, background: "var(--pd-ink-50)" }}
      >
        {history.map((m, i) =>
          m.role === "user" ? (
            <UserBubble key={i}>{m.content}</UserBubble>
          ) : (
            <AssistantBubble key={i} model={m.model} fallbackReason={m.fallback_reason}>
              <Markdown>{m.content}</Markdown>
              {m.tool_calls && m.tool_calls.length > 0 && (
                <details style={{ marginTop: 8, fontSize: 11, color: "var(--fg-3)" }}>
                  <summary style={{ cursor: "pointer" }}>
                    {m.tool_calls.length} tool call{m.tool_calls.length > 1 ? "s" : ""}
                  </summary>
                  <pre
                    style={{
                      marginTop: 6,
                      padding: 8,
                      background: "#fff",
                      border: "1px solid var(--pd-ink-100)",
                      borderRadius: 6,
                      overflowX: "auto",
                      fontFamily: "var(--font-mono)",
                    }}
                  >
                    {JSON.stringify(m.tool_calls, null, 2)}
                  </pre>
                </details>
              )}
            </AssistantBubble>
          ),
        )}
        {pending && (
          <AssistantBubble>
            <span style={{ color: "var(--fg-3)" }}>thinking…</span>
          </AssistantBubble>
        )}
        {error && (
          <div
            style={{
              borderRadius: 10,
              background: "#FDECEE",
              border: "1px solid #F3B3B7",
              padding: "8px 12px",
              fontSize: 13,
              color: "#9B1C24",
            }}
          >
            {error}
          </div>
        )}
      </div>

      {/* Input */}
      <div style={{ padding: "10px 16px", borderTop: "1px solid var(--pd-ink-100)", background: "#fff" }}>
        <div className="flex gap-1.5 flex-wrap" style={{ marginBottom: 10 }}>
          {SUGGESTIONS.map((s) => (
            <button
              key={s}
              onClick={() => send(s)}
              className="pd-btn pd-btn--secondary pd-btn--sm"
              style={{ fontWeight: 500, color: "var(--fg-2)" }}
            >
              {s}
            </button>
          ))}
        </div>
        <form
          className="flex gap-2 items-center"
          onSubmit={(e) => {
            e.preventDefault();
            send();
          }}
        >
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about performance data..."
            className="pd-input"
            style={{ height: 42, fontSize: 14 }}
            disabled={pending}
          />
          <button
            type="submit"
            disabled={pending || !input.trim()}
            className="pd-btn pd-btn--primary"
            style={{ height: 42, padding: "0 18px" }}
          >
            <SendIcon size={16} /> Send
          </button>
        </form>
      </div>
    </div>
  );
}

function UserBubble({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex gap-2.5 items-start justify-end">
      <div
        style={{
          background: "var(--pd-black)",
          color: "#fff",
          borderRadius: 14,
          padding: "10px 14px",
          maxWidth: 560,
          fontSize: 13.5,
          lineHeight: 1.5,
        }}
      >
        {children}
      </div>
    </div>
  );
}

function AssistantBubble({
  children,
  model,
  fallbackReason,
}: {
  children: React.ReactNode;
  model?: string;
  fallbackReason?: string | null;
}) {
  return (
    <div className="flex gap-2.5 items-start">
      <div
        className="flex items-center justify-center shrink-0"
        style={{ width: 28, height: 28, borderRadius: 8, background: "var(--pd-black)", color: "var(--pd-green)" }}
      >
        <SparklesIcon size={14} />
      </div>
      <div
        style={{
          background: "#fff",
          border: "1px solid var(--pd-ink-100)",
          borderRadius: 14,
          padding: "14px 16px",
          maxWidth: 640,
          fontSize: 13.5,
          lineHeight: 1.55,
          color: "var(--fg-1)",
        }}
      >
        {model && model !== "system" && (
          <div
            className="pd-label-caps"
            style={{ fontSize: 10, marginBottom: 6 }}
          >
            {model}
            {fallbackReason && ` · fallback: ${fallbackReason}`}
          </div>
        )}
        {children}
      </div>
    </div>
  );
}

/** Minimal Markdown renderer — bold, italic, lists, line breaks. No deps. */
function Markdown({ children }: { children: string }) {
  const html = children
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.+?)\*/g, "<em>$1</em>")
    .replace(/`([^`]+)`/g, "<code style=\"font-family:var(--font-mono);background:var(--pd-ink-50);padding:1px 5px;border-radius:4px;font-size:12.5px\">$1</code>")
    .replace(/^- (.*)$/gm, "<li>$1</li>")
    .replace(/(<li>[\s\S]*?<\/li>)/g, "<ul style=\"margin:6px 0 6px 18px;padding:0\">$1</ul>")
    .replace(/\n/g, "<br/>");
  return <div dangerouslySetInnerHTML={{ __html: html }} />;
}
