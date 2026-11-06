"use client";
import { useState } from "react";
import { signOut } from "next-auth/react";

export default function LogoutButton() {
  const [busy, setBusy] = useState(false);
  async function logout() {
    if (busy) return;
    setBusy(true);
    // Revocación específica de esta API, luego cierre cookie Auth.js.
    // Si falla la API, el token sigue válido hasta expirar: deuda documentada.
    try {
      await fetch("/api/session/revoke", { method: "POST", credentials: "same-origin" });
    } finally {
      await signOut({ callbackUrl: "/" });
    }
  }
  return <button className="btn outline" disabled={busy} onClick={() => { void logout(); }}>
    {busy ? "Cerrando…" : "Cerrar sesión"}
  </button>;
}
