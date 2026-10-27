import { useEffect, useState } from "react";
import { api, UserInfo } from "../api";

export default function AuditLog({ user }: { user: UserInfo }) {
  const [entries, setEntries] = useState<any[]>([]);

  useEffect(() => {
    api.audit(user.username, 100).then((d) => setEntries(d.entries));
  }, [user.username]);

  return (
    <div className="panel">
      <h3>Audit Trail</h3>
      <div className="sub">
        Every query to the engine is recorded with the requesting user, role, scope, the
        question asked, the module used, and the SQL executed. This is the accountability
        backbone that makes answers court-defensible.
      </div>
      <table>
        <thead>
          <tr>
            <th>Time</th>
            <th>User</th>
            <th>Role</th>
            <th>Scope</th>
            <th>Question</th>
            <th>Module</th>
          </tr>
        </thead>
        <tbody>
          {entries.map((e) => (
            <tr key={e.AuditID}>
              <td style={{ whiteSpace: "nowrap" }}>{e.Timestamp?.replace("T", " ")}</td>
              <td>{e.Username}</td>
              <td><span className="role-badge">{e.Role}</span></td>
              <td>{e.Scope}</td>
              <td style={{ maxWidth: 260 }}>{e.Question}</td>
              <td>{e.Module}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
