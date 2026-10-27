import { useRef, useState } from "react";
import { api, UserInfo } from "../api";
import { Lang, mapKannada, t } from "../i18n";
import Chart from "./Chart";

interface BotMessage {
  role: "user" | "bot";
  text: string;
  payload?: any;
}

const SUGGESTIONS = [
  "chain snatching hotspots last month",
  "how many vehicle theft cases this year",
  "vehicle theft trend",
  "find similar modus operandi: gold chain snatched on a bike",
  "recent robbery cases",
];

export default function Copilot({ user, lang }: { user: UserInfo; lang: Lang }) {
  const [messages, setMessages] = useState<BotMessage[]>([
    {
      role: "bot",
      text:
        "Namaste. I am TRINETRA Copilot. Ask me about crime data in your scope. " +
        "Every answer cites source FIRs and shows the query I ran.",
    },
  ]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [listening, setListening] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  const send = async (raw?: string) => {
    const question = (raw ?? input).trim();
    if (!question || busy) return;
    const mapped = mapKannada(question);
    setMessages((m) => [...m, { role: "user", text: question }]);
    setInput("");
    setBusy(true);
    try {
      const res = await api.ask(user.username, mapped);
      res._question = mapped;
      setMessages((m) => [...m, { role: "bot", text: res.answer, payload: res }]);
    } catch (e) {
      setMessages((m) => [...m, { role: "bot", text: "Engine error. Is the backend running?" }]);
    } finally {
      setBusy(false);
      setTimeout(() => scrollRef.current?.scrollTo(0, scrollRef.current.scrollHeight), 50);
    }
  };

  const startVoice = () => {
    const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SR) {
      alert("Voice input not supported in this browser. Type your query instead.");
      return;
    }
    const rec = new SR();
    rec.lang = lang === "kn" ? "kn-IN" : "en-IN";
    rec.interimResults = false;
    setListening(true);
    rec.onresult = (e: any) => {
      const transcript = e.results[0][0].transcript;
      setListening(false);
      send(transcript);
    };
    rec.onerror = () => setListening(false);
    rec.onend = () => setListening(false);
    rec.start();
  };

  const downloadBrief = async (question: string) => {
    const r = await fetch(api.briefUrl(), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: user.username, question }),
    });
    const blob = await r.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "trinetra_brief.pdf";
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="grid cols-2">
      <div className="panel" style={{ gridColumn: "1 / -1" }}>
        <h3>{t("copilot", lang)}</h3>
        <div className="sub">
          Conversational AI over the FIR database, English + Kannada, voice-enabled,
          with citations, explainable SQL, and PDF export.
        </div>

        <div className="chip-row">
          {SUGGESTIONS.map((s) => (
            <span key={s} className="chip" onClick={() => send(s)}>
              {s}
            </span>
          ))}
        </div>

        <div className="chat-window" ref={scrollRef}>
          {messages.map((m, i) => (
            <div key={i} className={`msg ${m.role}`}>
              <div>{m.text}</div>
              {m.payload && <BotExtras payload={m.payload} lang={lang} onBrief={downloadBrief} />}
            </div>
          ))}
          {busy && <div className="msg bot">Thinking...</div>}
          {listening && <div className="msg bot">Listening (speak now)...</div>}
        </div>

        <div className="composer">
          <input
            value={input}
            placeholder={t("askPlaceholder", lang)}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && send()}
          />
          <button className="btn secondary" onClick={startVoice} title="Voice input">
            {listening ? "..." : t("voice", lang)}
          </button>
          <button className="btn" onClick={() => send()} disabled={busy}>
            {t("ask", lang)}
          </button>
        </div>
      </div>
    </div>
  );
}

function BotExtras({
  payload,
  lang,
  onBrief,
}: {
  payload: any;
  lang: Lang;
  onBrief: (q: string) => void;
}) {
  const conf = payload.confidence;
  const cited: number[] = payload.cited_ids || [];
  const results = payload.results || [];
  const question = payload._question || payload.question;

  return (
    <div>
      {payload.chart && payload.chart.labels?.length > 0 && <Chart spec={payload.chart} />}

      {results.length > 0 && (
        <table style={{ marginTop: 8 }}>
          <thead>
            <tr>
              <th>FIR</th>
              <th>Station</th>
              <th>Sim</th>
              <th>Brief</th>
            </tr>
          </thead>
          <tbody>
            {results.slice(0, 5).map((r: any) => (
              <tr key={r.CaseMasterID}>
                <td>#{r.CaseMasterID}</td>
                <td>{r.Station}</td>
                <td>{r.similarity}</td>
                <td style={{ maxWidth: 280 }}>{r.BriefFacts?.slice(0, 70)}...</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {payload.sql && (
        <div className="sql-box">
          <div className="sub" style={{ margin: "0 0 4px" }}>{t("sqlRun", lang)}:</div>
          {payload.sql}
        </div>
      )}

      {cited.length > 0 && (
        <div style={{ marginTop: 8 }}>
          <span className="sub">{t("citedFirs", lang)}: </span>
          {cited.slice(0, 12).map((c) => (
            <span key={c} className="cite">FIR #{c}</span>
          ))}
        </div>
      )}

      <div className="meta">
        {conf && (
          <span className={`confidence ${conf.level}`}>
            {t("confidence", lang)}: {conf.level} - {conf.caveat}
          </span>
        )}
        {payload.route && <span> &bull; via {payload.route}</span>}
      </div>

      <button
        className="btn secondary"
        style={{ marginTop: 10, fontSize: 12 }}
        onClick={() => onBrief(payload._question || "")}
      >
        {t("downloadBrief", lang)}
      </button>
    </div>
  );
}
