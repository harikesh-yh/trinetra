import { useEffect, useState } from "react";
import { api, UserInfo } from "../api";
import { Lang } from "../i18n";
import HotspotMap from "./HotspotMap";
import NetworkGraph from "./NetworkGraph";
import Chart from "./Chart";

const CRIMES = [
  "Chain Snatching",
  "Vehicle Theft",
  "House Burglary",
  "Robbery",
  "Online Financial Fraud",
];

export default function WarRoom({ user }: { user: UserInfo; lang: Lang }) {
  const [crime, setCrime] = useState<string>("Chain Snatching");
  const [hotspots, setHotspots] = useState<any>(null);
  const [forecast, setForecast] = useState<any>(null);
  const [graph, setGraph] = useState<any>(null);
  const [anomalies, setAnomalies] = useState<any>(null);
  const [detection, setDetection] = useState<any>(null);
  const [risk, setRisk] = useState<any>(null);
  const [lag, setLag] = useState<any>(null);
  const [socio, setSocio] = useState<any>(null);
  const [socioDim, setSocioDim] = useState("occupation");

  useEffect(() => {
    api.hotspots(user.username, crime, 365).then(setHotspots);
    api.forecast(user.username, crime).then(setForecast);
    api.socio(user.username, crime, socioDim).then(setSocio);
  }, [user.username, crime]);

  useEffect(() => {
    api.socio(user.username, crime, socioDim).then(setSocio);
  }, [socioDim]);

  useEffect(() => {
    api.graph(user.username).then(setGraph);
    api.anomalies(user.username).then(setAnomalies);
    api.detection(user.username).then(setDetection);
    api.risk(user.username).then(setRisk);
    api.responseLag(user.username).then(setLag);
  }, [user.username]);

  return (
    <div className="grid cols-2">
      {/* Top stat strip */}
      <div className="panel" style={{ gridColumn: "1 / -1", display: "flex", gap: 28, alignItems: "center" }}>
        <div>
          <div className="stat">{hotspots?.points?.reduce((a: number, p: any) => a + p.Cases, 0) ?? "-"}</div>
          <div className="stat-label">{crime} cases (in scope)</div>
        </div>
        <div>
          <div className="stat">{forecast?.forecasts?.[0]?.forecast_next_month ?? "-"}</div>
          <div className="stat-label">Forecast next month (top station)</div>
        </div>
        <div>
          <div className="stat" style={{ color: "var(--danger)" }}>{anomalies?.alerts?.length ?? "-"}</div>
          <div className="stat-label">Active anomaly alerts</div>
        </div>
        <div>
          <div className="stat" style={{ color: "var(--warn)" }}>{graph?.communities?.length ?? "-"}</div>
          <div className="stat-label">Suspected networks</div>
        </div>
        <div className="spacer" />
        <div>
          <div className="stat-label" style={{ marginBottom: 4 }}>Crime focus</div>
          <select value={crime} onChange={(e) => setCrime(e.target.value)}>
            {CRIMES.map((c) => <option key={c}>{c}</option>)}
          </select>
        </div>
      </div>

      {/* Map */}
      <div className="panel">
        <h3>Geospatial Hotspots - {crime}</h3>
        <div className="sub">Bubble size = case volume. Click a station for the count.</div>
        {hotspots ? <HotspotMap points={hotspots.points} max={hotspots.max_cases} /> : <div className="loading">Loading map...</div>}
      </div>

      {/* Forecast */}
      <div className="panel">
        <h3>Hotspot Forecast & Patrol Recommendation</h3>
        <div className="sub">{forecast?.answer}</div>
        {forecast && (
          <table>
            <thead><tr><th>Station</th><th>Recent months</th><th>Forecast (next)</th></tr></thead>
            <tbody>
              {forecast.forecasts.slice(0, 8).map((f: any) => (
                <tr key={f.Station}>
                  <td>{f.Station}</td>
                  <td>{f.recent.join(", ")}</td>
                  <td style={{ fontWeight: 700, color: "var(--accent)" }}>{f.forecast_next_month}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Network graph */}
      <div className="panel" style={{ gridColumn: "1 / -1" }}>
        <h3>Criminal Network Analysis</h3>
        <div className="sub">{graph?.answer}</div>
        {graph ? <NetworkGraph nodes={graph.nodes} edges={graph.edges} /> : <div className="loading">Building network...</div>}
        {graph?.disclaimer && <div className="disclaimer">{graph.disclaimer}</div>}
        <div className="grid cols-2" style={{ marginTop: 14 }}>
          <div>
            <h3 style={{ fontSize: 13 }}>Top suspected kingpins (centrality)</h3>
            <table>
              <thead><tr><th>Name</th><th>Links</th><th>Cases</th></tr></thead>
              <tbody>
                {graph?.kingpins?.slice(0, 6).map((k: any) => (
                  <tr key={k.id}><td>{k.name}</td><td>{k.degree}</td><td>{k.cases}</td></tr>
                ))}
              </tbody>
            </table>
          </div>
          <div>
            <h3 style={{ fontSize: 13 }}>Repeat offenders</h3>
            <table>
              <thead><tr><th>Name</th><th>Distinct cases</th></tr></thead>
              <tbody>
                {graph?.repeat_offenders?.slice(0, 6).map((r: any) => (
                  <tr key={r.id}><td>{r.name}</td><td style={{ fontWeight: 700 }}>{r.cases}</td></tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Anomalies */}
      <div className="panel">
        <h3>Anomaly Alerts (spike detection)</h3>
        <div className="sub">{anomalies?.answer}</div>
        {anomalies?.alerts?.slice(0, 8).map((a: any, i: number) => (
          <div className="alert-row" key={i}>
            <div>
              <strong>{a.Crime}</strong> spike at {a.Station}
              <div className="sub" style={{ margin: 0 }}>
                {a.Month}: {a.Cases} cases (baseline {a.baseline_mean}, z={a.z_score})
              </div>
            </div>
            <span className={`sev ${a.severity}`}>{a.severity}</span>
          </div>
        ))}
      </div>

      {/* Detection quality */}
      <div className="panel">
        <h3>Detection Quality (cstype A/B/C)</h3>
        <div className="sub">{detection?.answer}</div>
        {detection && (
          <table>
            <thead><tr><th>Station</th><th>Chargesheet %</th><th>False %</th><th>Undetected %</th></tr></thead>
            <tbody>
              {detection.stations.slice(0, 8).map((s: any) => (
                <tr key={s.Station}>
                  <td>{s.Station}</td>
                  <td style={{ color: "var(--good)" }}>{s.chargesheet_rate}</td>
                  <td style={{ color: "var(--danger)" }}>{s.false_case_rate}</td>
                  <td style={{ color: "var(--warn)" }}>{s.undetected_rate}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Risk */}
      <div className="panel">
        <h3>Patrol Risk Score</h3>
        <div className="sub">{risk?.answer}</div>
        {risk && (
          <table>
            <thead><tr><th>Station</th><th>Risk /100</th><th>Heinous</th><th>Recent 90d</th></tr></thead>
            <tbody>
              {risk.scores.slice(0, 8).map((s: any) => (
                <tr key={s.Station}>
                  <td>{s.Station}</td>
                  <td style={{ fontWeight: 700, color: "var(--accent)" }}>{s.risk_score}</td>
                  <td>{s.heinous}</td>
                  <td>{s.recent_90d}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        {risk?.note && <div className="sub" style={{ marginTop: 8 }}>{risk.note}</div>}
      </div>

      {/* Response lag */}
      <div className="panel">
        <h3>Response Lag (reporting delay)</h3>
        <div className="sub">{lag?.answer}</div>
        {lag && (
          <table>
            <thead><tr><th>Station</th><th>Avg lag (days)</th><th>Max lag</th></tr></thead>
            <tbody>
              {lag.stations.slice(0, 8).map((s: any) => (
                <tr key={s.Station}>
                  <td>{s.Station}</td>
                  <td style={{ fontWeight: 700 }}>{s.avg_lag_days}</td>
                  <td>{s.max_lag_days}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Socio-economic */}
      <div className="panel" style={{ gridColumn: "1 / -1" }}>
        <h3>Socio-economic Victimization (guardrailed)</h3>
        <div style={{ display: "flex", gap: 10, alignItems: "center", marginBottom: 8 }}>
          <span className="sub" style={{ margin: 0 }}>Dimension:</span>
          <select value={socioDim} onChange={(e) => setSocioDim(e.target.value)}>
            <option value="occupation">Occupation</option>
            <option value="gender">Gender</option>
            <option value="religion">Religion (sensitive)</option>
            <option value="caste">Caste (sensitive)</option>
          </select>
        </div>
        <div className="sub">{socio?.answer}</div>
        {socio?.chart && socio.chart.labels.length > 0 && <Chart spec={socio.chart} />}
        {socio?.bias_disclaimer && <div className="disclaimer">{socio.bias_disclaimer}</div>}
      </div>
    </div>
  );
}
