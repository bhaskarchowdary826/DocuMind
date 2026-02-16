"use client";

import React, { useState, useRef, useEffect } from "react";

type Message = {
  role: "user" | "assistant";
  content: string;
};

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

export default function DocuMindPage() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [fileName, setFileName] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(`${BACKEND_URL}/upload`, {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail || "Upload failed");
      }

      const data = await res.json();
      setSessionId(data.session_id);
      setFileName(data.file_name);
      setMessages([]);
    } catch (err: any) {
      alert(err.message || "Upload error. Please try again.");
    } finally {
      setUploading(false);
    }
  };

  const handleSend = async () => {
    if (!input.trim() || !sessionId || loading) return;

    const question = input.trim();
    setInput("");

    const newMessages: Message[] = [
      ...messages,
      { role: "user", content: question },
    ];
    setMessages(newMessages);
    setLoading(true);

    try {
      const res = await fetch(`${BACKEND_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          message: question,
        }),
      });

      if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail || "Chat request failed");
      }

      const data = await res.json();
      const answer = data.answer || "No response received";

      setMessages([
        ...newMessages,
        { role: "assistant", content: answer },
      ]);
    } catch (err: any) {
      setMessages([
        ...newMessages,
        {
          role: "assistant",
          content: `Error: ${err.message || "Something went wrong. Please try again."}`,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-black text-white flex items-center justify-center px-4 py-8">
      <div className="w-full max-w-6xl rounded-3xl shadow-2xl overflow-hidden border border-neutral-800 bg-gradient-to-br from-neutral-950 via-neutral-900 to-neutral-950">
        {/* Header */}
        <div className="px-8 py-6 border-b border-neutral-800 flex items-center justify-between bg-neutral-950/80 backdrop-blur-sm">
          <div>
            <h1 className="text-4xl font-bold tracking-tight">
              <span className="text-white">Docu</span>
              <span className="text-amber-200">Mind</span>
            </h1>
            <p className="text-sm text-neutral-400 mt-1.5">
              Elegant document chat powered by Groq & RAG
            </p>
          </div>
          <div className="flex items-center gap-2 text-xs text-neutral-400">
            <span
              className={`inline-flex h-2.5 w-2.5 rounded-full mr-1.5 ${
                sessionId ? "bg-emerald-400" : "bg-neutral-600"
              }`}
            />
            {sessionId ? "Ready" : "Waiting for PDF"}
          </div>
        </div>

        {/* Body */}
        <div className="grid grid-cols-1 md:grid-cols-[1.1fr,1.4fr] gap-0">
          {/* Left: Document panel */}
          <div className="border-r border-neutral-800 bg-neutral-950/80 p-6 flex flex-col">
            <h2 className="text-sm font-semibold text-neutral-200 mb-4 uppercase tracking-wide">
              Document
            </h2>

            <div className="flex flex-col gap-3">
              <button
                onClick={() => fileInputRef.current?.click()}
                disabled={uploading || loading}
                className="inline-flex items-center justify-center rounded-xl border border-neutral-700 bg-neutral-900 px-5 py-3 text-sm font-medium text-neutral-100 hover:border-amber-300 hover:bg-neutral-900/80 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {uploading ? (
                  <>
                    <svg
                      className="animate-spin -ml-1 mr-2 h-4 w-4"
                      xmlns="http://www.w3.org/2000/svg"
                      fill="none"
                      viewBox="0 0 24 24"
                    >
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                      ></circle>
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                      ></path>
                    </svg>
                    Processing...
                  </>
                ) : fileName ? (
                  "Change PDF"
                ) : (
                  "Upload PDF"
                )}
              </button>
              <input
                ref={fileInputRef}
                type="file"
                accept="application/pdf"
                className="hidden"
                onChange={handleUpload}
              />

              <div className="mt-2 text-xs text-neutral-400">
                {fileName ? (
                  <>
                    <p className="font-medium text-amber-100 mb-1 truncate">
                      {fileName}
                    </p>
                    <p className="text-neutral-500">
                      Indexed and ready for Q&A.
                    </p>
                  </>
                ) : (
                  <p className="text-neutral-500">
                    Upload a PDF to start chatting with your document.
                  </p>
                )}
              </div>
            </div>

            <div className="mt-6 flex-1 rounded-2xl border border-neutral-800 bg-gradient-to-br from-neutral-950 via-neutral-900 to-neutral-950 p-4 text-xs text-neutral-400">
              <p className="font-semibold text-amber-100 mb-2 flex items-center gap-2">
                <svg
                  className="w-4 h-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
                Tips
              </p>
              <ul className="list-disc list-inside space-y-1.5 text-neutral-500">
                <li>Ask about specific sections or concepts</li>
                <li>Try "summarize this document in 5 bullet points"</li>
                <li>Ask "what are the key takeaways?" for a quick brief</li>
                <li>Be specific with your questions for better results</li>
              </ul>
            </div>
          </div>

          {/* Right: Chat panel */}
          <div className="bg-neutral-950 p-6 flex flex-col min-h-[600px]">
            <h2 className="text-sm font-semibold text-neutral-200 mb-4 uppercase tracking-wide">
              Chat
            </h2>

            <div className="flex-1 overflow-y-auto space-y-4 pr-2 mb-4">
              {messages.length === 0 && (
                <div className="text-xs text-neutral-500 border border-dashed border-neutral-700 rounded-2xl p-6 text-center">
                  <svg
                    className="w-12 h-12 mx-auto mb-3 text-neutral-600"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                    />
                  </svg>
                  <p className="font-medium mb-2">Start a conversation</p>
                  <p className="text-neutral-600">
                    Upload a PDF on the left, then ask questions like:
                  </p>
                  <ul className="list-disc list-inside mt-2 space-y-1 text-neutral-600">
                    <li>"What is this document mainly about?"</li>
                    <li>"What data do you have about X?"</li>
                    <li>"Summarize the main points for me."</li>
                  </ul>
                </div>
              )}

              {messages.map((m, idx) => (
                <div
                  key={idx}
                  className={`flex ${
                    m.role === "user" ? "justify-end" : "justify-start"
                  }`}
                >
                  <div
                    className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                      m.role === "user"
                        ? "bg-amber-100 text-neutral-900 font-medium"
                        : "bg-neutral-900 text-neutral-100 border border-neutral-800"
                    }`}
                  >
                    {m.content}
                  </div>
                </div>
              ))}

              {loading && (
                <div className="flex justify-start">
                  <div className="bg-neutral-900 border border-neutral-800 rounded-2xl px-4 py-3">
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-neutral-500 rounded-full animate-bounce"></div>
                      <div
                        className="w-2 h-2 bg-neutral-500 rounded-full animate-bounce"
                        style={{ animationDelay: "0.1s" }}
                      ></div>
                      <div
                        className="w-2 h-2 bg-neutral-500 rounded-full animate-bounce"
                        style={{ animationDelay: "0.2s" }}
                      ></div>
                    </div>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div className="flex items-center gap-2 pt-4 border-t border-neutral-800">
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleSend();
                  }
                }}
                className="flex-1 rounded-2xl bg-neutral-900 border border-neutral-700 px-4 py-3 text-sm text-neutral-100 placeholder:text-neutral-500 focus:outline-none focus:ring-2 focus:ring-amber-300 focus:border-transparent transition"
                placeholder={
                  sessionId
                    ? "Ask something about your document..."
                    : "Upload a PDF first..."
                }
                disabled={loading || !sessionId}
              />
              <button
                onClick={handleSend}
                disabled={loading || !sessionId || !input.trim()}
                className="rounded-2xl px-6 py-3 text-sm font-semibold bg-amber-200 text-neutral-950 hover:bg-amber-300 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-lg shadow-amber-200/20"
              >
                {loading ? (
                  <svg
                    className="animate-spin h-4 w-4"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    ></circle>
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    ></path>
                  </svg>
                ) : (
                  "Send"
                )}
              </button>
            </div>

            <div className="mt-3 text-[10px] text-neutral-600 text-right">
              DocuMind · Black / White / Beige · Powered by Groq
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}


