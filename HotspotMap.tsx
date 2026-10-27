import { useEffect, useRef } from "react";
import L from "leaflet";

interface Point {
  Station: string;
  District: string;
  lat: number;
  lng: number;
  Cases: number;
}

export default function HotspotMap({ points, max }: { points: Point[]; max: number }) {
  const ref = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);
  const layerRef = useRef<L.LayerGroup | null>(null);

  useEffect(() => {
    if (!ref.current || mapRef.current) return;
    const map = L.map(ref.current).setView([13.0, 76.5], 7);
    L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
      attribution: "&copy; OpenStreetMap, &copy; CARTO",
      maxZoom: 19,
    }).addTo(map);
    mapRef.current = map;
    layerRef.current = L.layerGroup().addTo(map);
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    const layer = layerRef.current;
    if (!map || !layer) return;
    layer.clearLayers();
    const valid = points.filter((p) => p.lat && p.lng);
    valid.forEach((p) => {
      const intensity = max > 0 ? p.Cases / max : 0;
      const radius = 6 + intensity * 26;
      const color = intensity > 0.6 ? "#ff5c6c" : intensity > 0.3 ? "#ffb347" : "#4da3ff";
      L.circleMarker([p.lat, p.lng], {
        radius,
        color,
        fillColor: color,
        fillOpacity: 0.5,
        weight: 1.5,
      })
        .bindPopup(`<b>${p.Station}</b><br/>${p.District}<br/>${p.Cases} cases`)
        .addTo(layer);
    });
    if (valid.length) {
      const bounds = L.latLngBounds(valid.map((p) => [p.lat, p.lng] as [number, number]));
      map.fitBounds(bounds.pad(0.2));
    }
  }, [points, max]);

  return <div id="map" ref={ref} />;
}
