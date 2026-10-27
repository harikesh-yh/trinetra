import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

interface ChartSpec {
  type: "bar" | "line";
  labels: string[];
  values: number[];
  title?: string;
}

export default function Chart({ spec }: { spec: ChartSpec }) {
  const data = spec.labels.map((l, i) => ({ name: l, value: spec.values[i] }));
  const axis = { stroke: "#93a4c0", fontSize: 11 };
  return (
    <div style={{ marginTop: 10 }}>
      {spec.title && <div className="sub">{spec.title}</div>}
      <ResponsiveContainer width="100%" height={220}>
        {spec.type === "line" ? (
          <LineChart data={data}>
            <CartesianGrid stroke="#243352" strokeDasharray="3 3" />
            <XAxis dataKey="name" {...axis} />
            <YAxis {...axis} />
            <Tooltip contentStyle={{ background: "#131c2e", border: "1px solid #243352" }} />
            <Line type="monotone" dataKey="value" stroke="#4da3ff" strokeWidth={2} dot={false} />
          </LineChart>
        ) : (
          <BarChart data={data}>
            <CartesianGrid stroke="#243352" strokeDasharray="3 3" />
            <XAxis dataKey="name" {...axis} interval={0} angle={-20} textAnchor="end" height={60} />
            <YAxis {...axis} />
            <Tooltip contentStyle={{ background: "#131c2e", border: "1px solid #243352" }} />
            <Bar dataKey="value" fill="#4da3ff" radius={[4, 4, 0, 0]} />
          </BarChart>
        )}
      </ResponsiveContainer>
    </div>
  );
}
