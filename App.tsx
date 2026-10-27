import { useState } from "react";
import { UserInfo } from "./api";
import { Lang, t } from "./i18n";
import Login from "./components/Login";
import Copilot from "./components/Copilot";
import WarRoom from "./components/WarRoom";
import AuditLog from "./components/AuditLog";

type Tab = "copilot" | "warroom" | "audit";

export default function App() {
  const [user, setUser] = useState<UserInfo | null>(null);
  const [tab, setTab] = useState<Tab>("copilot");
  const [lang, setLang] = useState<Lang>("en");

  if (!user) return <Login lang={lang} onLogin={setUser} />;

  return (
    <div>
      <header className="app-header">
        <div className="brand">
          <span className="logo">{t("appName", lang)}</span>
          <span className="tag">{t("tagline", lang)}</span>
        </div>
        <div className="spacer" />
        <div className="tabs">
          <div className={`tab ${tab === "copilot" ? "active" : ""}`} onClick={() => setTab("copilot")}>
            {t("copilot", lang)}
          </div>
          <div className={`tab ${tab === "warroom" ? "active" : ""}`} onClick={() => setTab("warroom")}>
            {t("warRoom", lang)}
          </div>
          <div className={`tab ${tab === "audit" ? "active" : ""}`} onClick={() => setTab("audit")}>
            {t("audit", lang)}
          </div>
        </div>
        <div className="spacer" />
        <button className="lang-toggle" onClick={() => setLang(lang === "en" ? "kn" : "en")}>
          {lang === "en" ? "EN | ಕನ್ನಡ" : "ಕನ್ನಡ | EN"}
        </button>
        <span className="role-badge">{user.role}</span>
        <span className="scope-chip">{user.scope}</span>
        <button className="btn secondary" onClick={() => setUser(null)}>
          Logout
        </button>
      </header>

      <main className="container">
        {tab === "copilot" && <Copilot user={user} lang={lang} />}
        {tab === "warroom" && <WarRoom user={user} lang={lang} />}
        {tab === "audit" && <AuditLog user={user} />}
      </main>
    </div>
  );
}
