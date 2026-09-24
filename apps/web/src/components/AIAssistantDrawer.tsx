
import React, { useState } from "react";
import { MessageSquareText, Send, X, RefreshCw } from "lucide-react";

interface AIAssistantDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  managerId: number;
  dataMode: "live" | "demo";
}

export const AIAssistantDrawer: React.FC<AIAssistantDrawerProps> = ({
  isOpen,
  onClose,
  managerId,
  dataMode,
}) => {
  const [messages, setMessages] = useState<Array<{ sender: "user" | "ai"; text: string }>>([
    {
      sender: "ai",
      text: "Ask me about the current transfer plan, captain shortlist or why rolling is preferred. I only use the recommendation currently produced by FPL Edge."
    }
  ]);
  const [inputVal, setInputVal] = useState("");
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  const quickQuestions = [
    "Why are you recommending to roll the transfer?",
    "Who is the safest captain and why?",
    "Why does Plan A beat Plan B?",
    "What is the expected gain over holding?"
  ];

  const handleSend = async (textToSend?: string) => {
    const query = textToSend || inputVal;
    if (!query || loading) return;

    setMessages((prev) => [...prev, { sender: "user", text: query }]);
    if (!textToSend) setInputVal("");
    setLoading(true);

    try {
      const resp = await fetch("/api/assistant", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: query, manager_id: managerId, data_mode: dataMode }),
      });

      if (resp.ok) {
        const data = await resp.json();
        setMessages((prev) => [...prev, { sender: "ai", text: data.answer }]);
      } else {
        setMessages((prev) => [
          ...prev,
          {
            sender: "ai",
            text: "I could not load the current recommendation. Refresh the data and run the planner again before asking about it."
          }
        ]);
      }
    } catch (e) {
      setMessages((prev) => [
        ...prev,
        {
          sender: "ai",
          text: "I could not reach the analysis service. Your existing plan has not changed."
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-y-0 right-0 w-full sm:w-[480px] bg-surface border-l border-surfaceBorder z-50 shadow-2xl flex flex-col animate-in slide-in-from-right duration-200">
      {/* Header */}
      <div className="p-4 border-b border-surfaceBorder flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-secondary/20 border border-secondary/30 flex items-center justify-center text-secondary">
              <MessageSquareText className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-bold text-slate-100 text-sm flex items-center gap-2">
              <span>Plan notes</span>
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-primary/10 text-primary font-mono">GROUNDED</span>
            </h3>
            <p className="text-[11px] text-slate-400">Answers from the current saved recommendation</p>
          </div>
        </div>

        <button
          onClick={onClose}
          className="p-2 rounded-xl bg-surfaceHover text-slate-400 hover:text-slate-100 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 p-4 overflow-y-auto space-y-4">
        {messages.map((m, idx) => (
          <div
            key={idx}
            className={`flex ${m.sender === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[85%] rounded-2xl p-4 text-xs leading-relaxed ${
                m.sender === "user"
                  ? "bg-primary text-slate-950 font-semibold"
                  : "bg-surfaceHover/80 border border-surfaceBorder text-slate-200"
              }`}
            >
              <div className="whitespace-pre-line">{m.text}</div>
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-surfaceHover border border-surfaceBorder rounded-2xl p-4 text-xs text-slate-400 flex items-center gap-2">
              <RefreshCw className="w-4 h-4 text-secondary animate-spin" />
              <span>Analyzing DECISION_CONTEXT...</span>
            </div>
          </div>
        )}
      </div>

      {/* Quick Questions Pills */}
      <div className="p-3 border-t border-surfaceBorder bg-surface/50 space-y-2">
        <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Suggested Questions</div>
        <div className="flex flex-wrap gap-1.5">
          {quickQuestions.map((q, idx) => (
            <button
              key={idx}
              onClick={() => handleSend(q)}
              className="text-[11px] bg-surfaceHover border border-surfaceBorder hover:border-primary/50 text-slate-300 px-2.5 py-1 rounded-lg transition-colors text-left"
            >
              {q}
            </button>
          ))}
        </div>
      </div>

      {/* Input Box */}
      <div className="p-4 border-t border-surfaceBorder bg-surface">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="flex items-center gap-2"
        >
          <input
            type="text"
            placeholder="Ask why this decision was recommended..."
            value={inputVal}
            onChange={(e) => setInputVal(e.target.value)}
            className="flex-1 bg-background text-xs text-slate-200 px-4 py-3 rounded-xl border border-surfaceBorder focus:outline-none focus:border-secondary"
          />
          <button
            type="submit"
            disabled={loading}
            className="bg-secondary text-slate-950 font-bold p-3 rounded-xl hover:bg-secondary/90 transition-colors disabled:opacity-50"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
};
