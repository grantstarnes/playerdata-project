"use client";

import { useAuth } from "@clerk/nextjs";
import { useEffect, useRef, useState } from "react";

import type { ChatResponse, ModelInfo } from "@/lib/api";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Message = {
  role: "user" | "assistant";
  content: string;
  model?: string;
  tool_calls?: ChatResponse["tool_calls"];
  fallback_reason?: string | null;
};

const WELCOME = `**Performance Chat**

Ask about any athlete's data. For example:
- "Stats for athlete #1042"
- "Who is fastest in DI female soccer?"
- "Compare #1042 on session load"`;

function SparklesIcon({ size = 16 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.75} strokeLinecap="round" strokeLinejoin="round">
      <path d="m12 3-1.9 5.8a2 2 0 0 1-1.3 1.3L3 12l5.8 1.9a2 2 0 0 1 1.3 1.3L12 21l1.9-5.8a2 2 0 0 1 1.3-1.3L21 12l-5.8-1.9a2 2 0 0 1-1.3-1.3Z" />
    </svg>
  );
}

function SendIcon() {
  return (
    <svg width={16} height={16} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.75} strokeLinecap="round" strokeLinejoin="round">
      <path d="m22 2-7 20-4-9-9-4Z" />
      <path d="M22 2 11 13" />
    </svg>
  );
}

function XIcon() {
  return (
    <svg width={16} height={16} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
      <path d="M18 6 6 18" /><path d="m6 6 12 12" />
    </svg>
  );
}

export function ChatWidget({
  defaultModel,
  models,
}: {
  defaultModel: string;
  models: ModelInfo[];
}) {
  const { getToken } = useAuth();
  const [open, setOpen] = useState(true);
  const [model, setModel] = useState(defaultModel);
  const [input, setInput] = useState("");
  const [history, setHistory] = useState<Message[]>([
    { role: "assistant", content: WELCOME, model: "system" },
  ]);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [athleteCtx, setAthleteCtx] = useState<number | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Default open. Honor explicit close from previous navigation if set.
  useEffect(() => {
    const stored = sessionStorage.getItem("pd-chat-open");
    if (stored === "0") setOpen(false);
  }, []);
  useEffect(() => {
    sessionStorage.setItem("pd-chat-open", open ? "1" : "0");
  }, [open]);

  // Fetch the user's default athlete once per session (deterministic server-side
  // hash of Clerk sub). Cache in sessionStorage so subsequent page navs don't
  // hit the endpoint again.
  useEffect(() => {
    const cached = sessionStorage.getItem("pd-chat-athlete");
    if (cached) {
      const n = Number(cached);
      if (Number.isFinite(n)) setAthleteCtx(n);
      return;
    }
    (async () => {
      try {
        const token = await getToken();
        if (!token) return;
        const res = await fetch(`${API_URL}/api/chat/session`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!res.ok) return;
        const body: { athlete_ctx: number | null } = await res.json();
        if (body.athlete_ctx !== null) {
          setAthleteCtx(body.athlete_ctx);
          sessionStorage.setItem("pd-chat-athlete", String(body.athlete_ctx));
        }
      } catch { /* ignore */ }
    })();
  }, [getToken]);

  useEffect(() => {
    if (open && scrollRef.current)
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [history, pending, open]);

  async function send(override?: string) {
    const text = (override ?? input).trim();
    if (!text || pending) return;
    setError(null);
    setInput("");

    // Snapshot the conversation BEFORE appending the user's new message —
    // this is what the backend needs as `history`.
    const prior = history
      .filter((m) => m.model !== "system") // skip the local welcome bubble
      .map((m) => ({ role: m.role, content: m.content }));

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
          athlete_ctx: athleteCtx,
          history: prior,
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

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        aria-label="Open chat"
        style={{
          position: "fixed",
          right: 24,
          bottom: 24,
          width: 56,
          height: 56,
          borderRadius: "50%",
          background: "var(--pd-black)",
          color: "var(--pd-green)",
          border: 0,
          cursor: "pointer",
          boxShadow: "var(--shadow-md)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          zIndex: 40,
          transition: "transform 120ms",
        }}
        onMouseEnter={(e) => (e.currentTarget.style.transform = "scale(1.05)")}
        onMouseLeave={(e) => (e.currentTarget.style.transform = "scale(1)")}
      >
        <SparklesIcon size={22} />
      </button>
    );
  }

  return (
    <div
      className="pd-card"
      style={{
        position: "fixed",
        right: 24,
        bottom: 24,
        width: 420,
        height: 600,
        padding: 0,
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
        zIndex: 40,
        boxShadow: "var(--shadow-lg, 0 16px 48px rgba(10,10,10,.12))",
      }}
    >
      {/* Header */}
      <div
        className="flex items-center gap-2.5"
        style={{ padding: "12px 14px", borderBottom: "1px solid var(--pd-ink-100)" }}
      >
        <div
          className="flex items-center justify-center shrink-0"
          style={{ width: 28, height: 28, borderRadius: 8, background: "var(--pd-black)", color: "var(--pd-green)" }}
        >
          <SparklesIcon size={14} />
        </div>
        <div className="flex-1 min-w-0">
          <div style={{ fontWeight: 700, fontSize: 13 }}>Performance Chat</div>
          <div style={{ fontSize: 11, color: "var(--fg-3)" }}>
            {athleteCtx
              ? <>Context: <span style={{ fontFamily: "var(--font-mono)", color: "var(--pd-green-700)", fontWeight: 600 }}>#{athleteCtx}</span></>
              : "Session-scoped"}
          </div>
        </div>
        <select
          value={model}
          onChange={(e) => setModel(e.target.value)}
          style={{
            padding: "4px 8px",
            border: "1px solid var(--pd-ink-200)",
            borderRadius: 6,
            fontSize: 11.5,
            background: "#fff",
            maxWidth: 160,
          }}
        >
          {models.map((m) => (
            <option key={m.id} value={m.id} disabled={!m.installed}>
              {m.label}
            </option>
          ))}
        </select>
        <button
          onClick={() => setOpen(false)}
          className="pd-btn pd-btn--ghost pd-btn--sm"
          style={{ width: 28, height: 28, padding: 0, borderRadius: 6 }}
          aria-label="Close chat"
        >
          <XIcon />
        </button>
      </div>

      {/* Messages */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto"
        style={{ padding: 14, display: "flex", flexDirection: "column", gap: 10, background: "var(--pd-ink-50)" }}
      >
        {history.map((m, i) =>
          m.role === "user" ? (
            <UserBubble key={i}>{m.content}</UserBubble>
          ) : (
            <AssistantBubble key={i} model={m.model} fallbackReason={m.fallback_reason}>
              <Markdown>{m.content}</Markdown>
            </AssistantBubble>
          ),
        )}
        {pending && <AssistantBubble><span style={{ color: "var(--fg-3)" }}>thinking…</span></AssistantBubble>}
        {error && (
          <div style={{
            borderRadius: 8, background: "#FDECEE", border: "1px solid #F3B3B7",
            padding: "6px 10px", fontSize: 12, color: "#9B1C24",
          }}>{error}</div>
        )}
      </div>

      {/* Input */}
      <form
        className="flex gap-1.5 items-center"
        style={{ padding: "10px 12px", borderTop: "1px solid var(--pd-ink-100)", background: "#fff" }}
        onSubmit={(e) => { e.preventDefault(); send(); }}
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about performance data..."
          className="pd-input"
          style={{ height: 36, fontSize: 13 }}
          disabled={pending}
        />
        <button
          type="submit"
          disabled={pending || !input.trim()}
          className="pd-btn pd-btn--primary"
          style={{ height: 36, padding: "0 12px" }}
        >
          <SendIcon />
        </button>
      </form>
    </div>
  );
}

function UserBubble({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex justify-end">
      <div
        style={{
          background: "var(--pd-black)", color: "#fff", borderRadius: 12,
          padding: "8px 12px", maxWidth: "85%", fontSize: 13, lineHeight: 1.5,
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
    <div className="flex gap-2 items-start">
      <div
        className="flex items-center justify-center shrink-0"
        style={{ width: 22, height: 22, borderRadius: 6, background: "var(--pd-black)", color: "var(--pd-green)" }}
      >
        <SparklesIcon size={11} />
      </div>
      <div
        style={{
          background: "#fff", border: "1px solid var(--pd-ink-100)", borderRadius: 12,
          padding: "8px 12px", maxWidth: "85%", fontSize: 13, lineHeight: 1.55, color: "var(--fg-1)",
        }}
      >
        {model && model !== "system" && (
          <div className="pd-label-caps" style={{ fontSize: 9, marginBottom: 4 }}>
            {model}{fallbackReason && ` · fallback: ${fallbackReason}`}
          </div>
        )}
        {children}
      </div>
    </div>
  );
}

/**
 * Minimal Markdown renderer — supports bold, italic, inline code, bullet lists,
 * and pipe-style tables. No external deps. Cells/text are HTML-escaped; the
 * wrapping block tags we emit are trusted.
 */
function Markdown({ children }: { children: string }) {
  const esc = (s: string) =>
    s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  // Unescape common markdown escapes the LLM likes to emit (\_, \*, \|, \`).
  // These aren't meaningful in our restricted renderer and show as literal
  // backslashes otherwise.
  const unescape = (s: string) =>
    s.replace(/\\([_*|`\\])/g, "$1");

  const inline = (s: string) =>
    esc(unescape(s))
      .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
      .replace(/\*(.+?)\*/g, "<em>$1</em>")
      .replace(
        /`([^`]+)`/g,
        '<code style="font-family:var(--font-mono);background:var(--pd-ink-50);padding:1px 5px;border-radius:4px;font-size:12px">$1</code>',
      );

  const parseRow = (line: string) =>
    line
      .replace(/^\s*\|/, "")
      .replace(/\|\s*$/, "")
      .split("|")
      .map((c) => c.trim());

  const lines = children.replace(/\r\n/g, "\n").split("\n");
  const blocks: string[] = [];
  let i = 0;
  while (i < lines.length) {
    const line = lines[i];

    // Table: header line of `| … |` + separator `| --- | --- |`
    if (
      line.trim().startsWith("|") &&
      i + 1 < lines.length &&
      /^\s*\|?\s*[:\-| ]+\|?\s*$/.test(lines[i + 1]) &&
      lines[i + 1].includes("|")
    ) {
      const headers = parseRow(line);
      i += 2;
      const body: string[][] = [];
      while (i < lines.length && lines[i].trim().startsWith("|")) {
        body.push(parseRow(lines[i]));
        i++;
      }
      const theadCells = headers
        .map(
          (h, idx) =>
            `<th style="text-align:${idx === 0 ? "left" : "right"};padding:6px 10px 6px 0;font-size:11px;font-weight:600;color:var(--fg-3);border-bottom:1px solid var(--pd-ink-100);letter-spacing:.04em;text-transform:uppercase;white-space:nowrap">${inline(h)}</th>`,
        )
        .join("");
      const tbodyRows = body
        .map(
          (row) =>
            "<tr>" +
            row
              .map(
                (c, idx) =>
                  `<td style="padding:6px 10px 6px 0;border-bottom:1px solid var(--pd-ink-50);font-size:12.5px;font-variant-numeric:tabular-nums;text-align:${idx === 0 ? "left" : "right"};color:${idx === 0 ? "var(--fg-1)" : "var(--fg-2)"};font-weight:${idx === 0 ? 600 : 500}">${inline(c)}</td>`,
              )
              .join("") +
            "</tr>",
        )
        .join("");
      blocks.push(
        `<div style="overflow-x:auto;margin:6px 0"><table style="width:100%;border-collapse:collapse">` +
          `<thead><tr>${theadCells}</tr></thead>` +
          `<tbody>${tbodyRows}</tbody>` +
          `</table></div>`,
      );
      continue;
    }

    // Bullet list
    if (/^\s*-\s+/.test(line)) {
      const items: string[] = [];
      while (i < lines.length && /^\s*-\s+/.test(lines[i])) {
        items.push(
          `<li style="margin-bottom:2px">${inline(lines[i].replace(/^\s*-\s+/, ""))}</li>`,
        );
        i++;
      }
      blocks.push(
        `<ul style="margin:6px 0 6px 18px;padding:0;list-style:disc">${items.join("")}</ul>`,
      );
      continue;
    }

    // Blank line = paragraph break
    if (line.trim() === "") {
      blocks.push('<div style="height:6px"></div>');
      i++;
      continue;
    }

    // Plain text line
    blocks.push(`<div>${inline(line)}</div>`);
    i++;
  }

  return <div dangerouslySetInnerHTML={{ __html: blocks.join("") }} />;
}
