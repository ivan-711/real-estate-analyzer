import { useCallback, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import api, { apiBaseURL, getToken } from "../lib/api";
import type { ChatSessionListItem, ChatSessionResponse } from "../types";

type DisplayMessage = { id?: string; role: string; content: string };

function parseSSEEvent(block: string): { event: string; data: string } | null {
  let event = "message";
  let data: string | null = null;
  for (const line of block.split("\n")) {
    const e = line.match(/^event:\s*(.+)$/);
    const d = line.match(/^data:\s*(.*)$/);
    if (e) event = e[1].trim();
    if (d) data = d[1].trim();
  }
  return data !== null ? { event, data } : null;
}

async function streamChat(
  message: string,
  sessionId: string | null,
  token: string,
  onChunk: (data: { text: string }) => void,
): Promise<{
  sessionId: string;
  userMessageId: string;
  assistantMessageId: string;
}> {
  const url = `${apiBaseURL}/api/v1/chat`;
  const res = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      message,
      session_id: sessionId || undefined,
    }),
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || `HTTP ${res.status}`);
  }
  const reader = res.body?.getReader();
  if (!reader) throw new Error("No response body");
  const dec = new TextDecoder();
  let buffer = "";
  let lastEvent: string | null = null;
  let lastData: string | null = null;
  let donePayload: {
    session_id: string;
    user_message_id: string;
    assistant_message_id: string;
  } | null = null;

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += dec.decode(value, { stream: true });
    const parts = buffer.split("\n\n");
    buffer = parts.pop() ?? "";
    for (const part of parts) {
      const parsed = parseSSEEvent(part);
      if (parsed) {
        lastEvent = parsed.event;
        lastData = parsed.data;
      }
      if (lastEvent && lastData !== null) {
        if (lastEvent === "chunk") {
          try {
            const data = JSON.parse(lastData) as { text?: string };
            if (data.text) onChunk({ text: data.text });
          } catch {
            // ignore
          }
        } else if (lastEvent === "done") {
          try {
            donePayload = JSON.parse(lastData) as {
              session_id: string;
              user_message_id: string;
              assistant_message_id: string;
            };
          } catch {
            // ignore
          }
        }
        lastEvent = null;
        lastData = null;
      }
    }
  }
  if (!donePayload) throw new Error("Stream ended without done event");
  return {
    sessionId: donePayload.session_id,
    userMessageId: donePayload.user_message_id,
    assistantMessageId: donePayload.assistant_message_id,
  };
}

export default function Chat() {
  const [sessions, setSessions] = useState<ChatSessionListItem[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<DisplayMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(true);
  const [streaming, setStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const token = getToken();

  const loadSessions = useCallback(() => {
    if (!token) return;
    api
      .get<ChatSessionListItem[]>("/api/v1/chat/sessions")
      .then((res) => setSessions(res.data))
      .catch(() => setError("Failed to load sessions."));
  }, [token]);

  useEffect(() => {
    if (!token) {
      setLoading(false);
      return;
    }
    loadSessions();
    setLoading(false);
  }, [token, loadSessions]);

  useEffect(() => {
    if (!currentSessionId) {
      setMessages([]);
      setLoading(false);
      return;
    }
    if (!token) return;
    setLoading(true);
    api
      .get<ChatSessionResponse>(`/api/v1/chat/sessions/${currentSessionId}`)
      .then((res) => setMessages(res.data.messages))
      .catch(() => setError("Failed to load session."))
      .finally(() => setLoading(false));
  }, [currentSessionId, token]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleNewChat = () => {
    setCurrentSessionId(null);
    setMessages([]);
    setError(null);
  };

  const handleSend = async () => {
    const text = input.trim();
    if (!text || !token || streaming) return;
    setInput("");
    setStreaming(true);
    setError(null);

    const userMsg: DisplayMessage = { role: "user", content: text };
    setMessages((prev) => [...prev, userMsg]);
    const assistantMsg: DisplayMessage = { role: "assistant", content: "" };
    setMessages((prev) => [...prev, assistantMsg]);

    try {
      const onChunk = (data: { text: string }) => {
        setMessages((prev) => {
          const next = [...prev];
          const last = next[next.length - 1];
          if (last?.role === "assistant") {
            next[next.length - 1] = {
              ...last,
              content: last.content + data.text,
            };
          }
          return next;
        });
      };
      const { sessionId } = await streamChat(
        text,
        currentSessionId,
        token,
        onChunk,
      );
      setCurrentSessionId(sessionId);
      loadSessions();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to send message.");
      setMessages((prev) => {
        const out = [...prev];
        if (
          out[out.length - 1]?.role === "assistant" &&
          out[out.length - 1]?.content === ""
        ) {
          out[out.length - 1] = {
            ...out[out.length - 1],
            content: "[Error: could not get response. Please try again.]",
          };
        }
        return out;
      });
    } finally {
      setStreaming(false);
    }
  };

  if (!token) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-12 text-center">
        <p className="text-slate">Log in to use the chat.</p>
        <Link
          to="/login"
          className="mt-4 inline-block rounded-lg bg-blue-primary px-4 py-2 font-medium text-white no-underline hover:bg-blue-light"
        >
          Log in
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto flex max-w-6xl flex-col px-4 py-6 lg:flex-row lg:gap-6">
      <aside className="mb-4 shrink-0 lg:w-56">
        <div className="rounded-xl border border-border bg-white p-3 shadow-sm">
          <div className="mb-2 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-navy">Chats</h2>
            <button
              type="button"
              onClick={handleNewChat}
              className="rounded bg-blue-subtle px-2 py-1 text-sm font-medium text-blue-primary hover:bg-blue-light hover:text-white"
            >
              New chat
            </button>
          </div>
          {loading && sessions.length === 0 ? (
            <p className="text-sm text-muted">Loading…</p>
          ) : (
            <ul className="max-h-64 space-y-1 overflow-y-auto lg:max-h-96">
              {sessions.map((s) => (
                <li key={s.id}>
                  <button
                    type="button"
                    onClick={() => setCurrentSessionId(s.id)}
                    className={`w-full rounded-lg px-2 py-1.5 text-left text-sm ${
                      currentSessionId === s.id
                        ? "bg-blue-subtle text-blue-primary"
                        : "text-slate hover:bg-section-bg"
                    }`}
                  >
                    {s.title || "New chat"}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </aside>

      <main className="flex min-h-[60vh] flex-1 flex-col rounded-xl border border-border bg-white shadow-sm">
        <div className="flex-1 overflow-y-auto p-4">
          {messages.length === 0 && !streaming && (
            <p className="text-muted">
              Send a message to start. Ask about your deals or portfolio.
            </p>
          )}
          <ul className="space-y-4">
            {messages.map((m, i) => (
              <li
                key={m.id ?? `msg-${i}`}
                className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-[85%] rounded-lg px-3 py-2 ${
                    m.role === "user"
                      ? "bg-blue-subtle text-navy"
                      : "bg-section-bg text-slate"
                  }`}
                >
                  <span className="text-xs font-medium text-muted">
                    {m.role === "user" ? "You" : "AI"}
                  </span>
                  <p className="mt-0.5 whitespace-pre-wrap break-words text-sm">
                    {m.content}
                  </p>
                </div>
              </li>
            ))}
          </ul>
          <div ref={messagesEndRef} />
        </div>
        {error && (
          <div className="border-t border-border px-4 py-2">
            <p className="text-sm text-red-negative">{error}</p>
          </div>
        )}
        <div className="border-t border-border p-4">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSend();
            }}
            className="flex gap-2"
          >
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type a message…"
              className="flex-1 rounded-lg border border-border px-4 py-2 text-slate placeholder-muted focus:border-blue-primary focus:outline-none focus:ring-1 focus:ring-blue-primary"
              disabled={streaming}
            />
            <button
              type="submit"
              disabled={streaming || !input.trim()}
              className="rounded-lg bg-blue-primary px-4 py-2 font-medium text-white hover:bg-blue-light disabled:opacity-50"
            >
              {streaming ? "Sending…" : "Send"}
            </button>
          </form>
        </div>
      </main>
    </div>
  );
}
