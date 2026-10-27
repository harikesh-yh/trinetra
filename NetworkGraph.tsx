import { useEffect, useRef } from "react";
import { Network } from "vis-network";
import { DataSet } from "vis-data";

interface Node {
  id: number;
  label: string;
  cases: number;
}
interface Edge {
  from: number;
  to: number;
  weight: number;
}

export default function NetworkGraph({ nodes, edges }: { nodes: Node[]; edges: Edge[] }) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!ref.current || !nodes?.length) return;
    const visNodes = new DataSet(
      nodes.map((n) => ({
        id: n.id,
        label: n.label,
        value: n.cases,
        title: `${n.label} - ${n.cases} cases (ACCUSED, not convicted)`,
        color: { background: "#1a2740", border: "#4da3ff", highlight: { background: "#4da3ff" } },
        font: { color: "#e6edf7", size: 12 },
      }))
    );
    const visEdges = new DataSet(
      edges.map((e, i) => ({
        id: i,
        from: e.from,
        to: e.to,
        value: e.weight,
        color: { color: "#34507e", highlight: "#ffb347" },
      }))
    );
    const network = new Network(
      ref.current,
      { nodes: visNodes as any, edges: visEdges as any },
      {
        nodes: { shape: "dot", scaling: { min: 8, max: 40 } },
        edges: { smooth: { enabled: true, type: "continuous", roundness: 0.4 } },
        physics: { barnesHut: { gravitationalConstant: -8000, springLength: 120 }, stabilization: { iterations: 150 } },
        interaction: { hover: true, tooltipDelay: 120 },
      }
    );
    return () => network.destroy();
  }, [nodes, edges]);

  return <div id="network" ref={ref} />;
}
