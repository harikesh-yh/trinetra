import { useEffect, useState } from "react";
import { api, UserInfo } from "../api";
import { Lang, t } from "../i18n";

export default function Login({ lang, onLogin }: { lang: Lang; onLogin: (u: UserInfo) => void }) {
  const [users, setUsers] = useState<UserInfo[]>([]);
  const [selected, setSelected] = useState<string>("");
  const [error, setError] = useState<string>("");

  useEffect(() => {
    api
      .users()
      .then((u) => {
        setUsers(u);
        setSelected(u[0]?.username ?? "");
      })
      .catch(() => setError("Engine not reachable. Is the backend running on :8077?"));
  }, []);

  const signIn = async () => {
    try {
      const u = await api.login(selected);
      onLogin(u);
    } catch {
      setError("Login failed.");
    }
  };

  return (
    <div className="login-wrap">
      <div className="panel login-card">
        <div className="brand" style={{ marginBottom: 6 }}>
          <span className="logo">{t("appName", lang)}</span>
        </div>
        <div className="sub">{t("tagline", lang)}</div>
        <p className="sub">
          Select a role to sign in. Role-based access control (RBAC) restricts the data scope:
          SHO sees one station, DCP a district, ADGP the whole state.
        </p>
        {error && <div className="disclaimer">{error}</div>}
        {users.map((u) => (
          <div
            key={u.username}
            className={`user-option ${selected === u.username ? "active" : ""}`}
            onClick={() => setSelected(u.username)}
          >
            <span className="role-badge">{u.role}</span>
            <div>
              <div style={{ fontWeight: 600 }}>{u.username}</div>
              <div className="sub" style={{ margin: 0 }}>{u.scope}</div>
            </div>
          </div>
        ))}
        <button className="btn" style={{ width: "100%", marginTop: 8 }} disabled={!selected} onClick={signIn}>
          {t("login", lang)}
        </button>
      </div>
    </div>
  );
}
