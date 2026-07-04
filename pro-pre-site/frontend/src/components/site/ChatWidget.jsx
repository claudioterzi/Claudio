import React from "react";
import { useTranslation } from "react-i18next";
import { MessageSquare, X, Send, Loader2 } from "lucide-react";
import { api } from "@/lib/api";

const GREETING = {
  fr: "Bonjour ! Je suis l'assistant de Pro-pre. Comment puis-je vous aider ?",
  en: "Hello! I'm the Pro-pre assistant. How can I help?",
  es: "¡Hola! Soy el asistente de Pro-pre. ¿En qué puedo ayudarte?",
  nl: "Hallo! Ik ben de Pro-pre-assistent. Hoe kan ik helpen?",
  it: "Ciao! Sono l'assistente di Pro-pre. Come posso aiutarti?",
};

export default function ChatWidget() {
  const { i18n, t } = useTranslation();
  const [open, setOpen] = React.useState(false);
  const [messages, setMessages] = React.useState([]);
  const [input, setInput] = React.useState("");
  const [loading, setLoading] = React.useState(false);
  const [sid, setSid] = React.useState(null);
  const endRef = React.useRef(null);

  React.useEffect(() => {
    if (open && messages.length === 0) {
      setMessages([{ role: "assistant", content: GREETING[i18n.language?.slice(0,2)] || GREETING.fr }]);
    }
  }, [open, i18n.language, messages.length]);

  React.useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const send = async () => {
    const text = input.trim();
    if (!text || loading) return;
    const next = [...messages, { role: "user", content: text }];
    setMessages(next);
    setInput("");
    setLoading(true);
    try {
      const r = await api.post("/chat", { messages: next, language: i18n.language, session_id: sid });
      if (r.data.session_id) setSid(r.data.session_id);
      setMessages([...next, { role: "assistant", content: r.data.reply }]);
    } catch (e) {
      setMessages([...next, { role: "assistant", content: "…" }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      {!open && (
        <button
          onClick={() => setOpen(true)}
          className="fixed bottom-5 right-24 z-50 flex h-14 items-center gap-2 rounded-full bg-[#5BA4D4] px-5 text-white shadow-xl hover:scale-105 transition-transform"
          data-testid="chat-open-btn"
          aria-label="Open chat"
        >
          <MessageSquare className="h-5 w-5" />
          <span className="hidden sm:inline font-medium text-sm">Chat</span>
        </button>
      )}
      {open && (
        <div className="fixed bottom-5 right-5 z-50 w-[min(380px,calc(100vw-2.5rem))] h-[520px] max-h-[80vh] flex flex-col rounded-2xl border border-slate-200 bg-white shadow-2xl" data-testid="chat-widget">
          <div className="flex items-center justify-between px-4 py-3 bg-[#1B2845] text-white rounded-t-2xl">
            <div className="flex items-center gap-2">
              <div className="h-9 w-9 rounded-lg bg-white p-1 flex items-center justify-center">
                <img src="https://customer-assets.emergentagent.com/job_tissu-propre/artifacts/89z1mmv7_4FE6D8C7-4FFC-421A-947D-FEC6CFFD80D7.png" alt="Pro-pre" className="max-h-full max-w-full object-contain" />
              </div>
              <div>
                <p className="font-semibold text-sm">Pro-pre Assistant</p>
                <p className="text-xs text-slate-300">Réponse instantanée</p>
              </div>
            </div>
            <button onClick={() => setOpen(false)} className="p-1 hover:bg-white/10 rounded" data-testid="chat-close-btn"><X className="h-4 w-4" /></button>
          </div>
          <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-slate-50">
            {messages.map((m, i) => (
              <div key={`msg-${i}-${m.role}`} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
                <div className={`max-w-[80%] rounded-2xl px-3 py-2 text-sm ${m.role === "user" ? "bg-[#5BA4D4] text-white" : "bg-white border border-slate-200 text-slate-700"}`}>
                  {m.content}
                </div>
              </div>
            ))}
            {loading && <div className="flex justify-start"><div className="rounded-2xl px-3 py-2 bg-white border border-slate-200"><Loader2 className="h-4 w-4 animate-spin text-[#5BA4D4]" /></div></div>}
            <div ref={endRef} />
          </div>
          <form onSubmit={e => { e.preventDefault(); send(); }} className="border-t border-slate-200 p-3 flex gap-2">
            <input
              value={input}
              onChange={e => setInput(e.target.value)}
              placeholder={i18n.language?.startsWith("fr") ? "Tapez votre message…" : "Type your message…"}
              className="flex-1 rounded-lg border border-slate-200 px-3 py-2 text-sm focus:border-[#5BA4D4] focus:outline-none focus:ring-2 focus:ring-[#5BA4D4]/20"
              data-testid="chat-input"
            />
            <button type="submit" disabled={loading || !input.trim()} className="rounded-lg bg-[#1B2845] text-white px-3 disabled:opacity-40" data-testid="chat-send-btn"><Send className="h-4 w-4" /></button>
          </form>
        </div>
      )}
    </>
  );
}
