"use client";
import { useEffect, useState } from "react";

type Metrics = { users: number; notes: number };

export default function AdminClient() {
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [message, setMessage] = useState("Verificando permisos…");
  useEffect(() => {
    async function load() {
      try {
        const response = await fetch("/api/admin/metrics", { credentials: "same-origin", cache: "no-store" });
        if (response.status === 403) { setMessage("Acceso denegado: necesitas permisos de administrador."); return; }
        if (!response.ok) throw new Error("No es posible obtener las métricas.");
        setMetrics(await response.json() as Metrics);
        setMessage("");
      } catch { setMessage("Servicio no disponible."); }
    }
    void load();
  }, []);
  return <section className="card">
    {message && <p role="status">{message}</p>}
    {metrics && <div className="grid">
      <div><p className="muted">Cuentas registradas</p><h2>{metrics.users}</h2></div>
      <div><p className="muted">Apuntes de prueba</p><h2>{metrics.notes}</h2></div>
    </div>}
  </section>;
}
