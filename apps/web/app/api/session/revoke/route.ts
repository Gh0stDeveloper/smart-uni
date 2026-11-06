import type { NextRequest } from "next/server";
import { apiFetch, getApiBearer } from "@/lib/backend";
import { allowedOrigin } from "@/lib/security";

export const dynamic = "force-dynamic";

export async function POST(request: NextRequest) {
  if (!allowedOrigin(
    request.headers.get("origin"), process.env.PORTAL_ORIGIN ?? "",
    process.env.NODE_ENV !== "production"
  )) {
    return Response.json({ error: "Origen no permitido" }, { status: 403 });
  }
  const bearer = await getApiBearer(request);
  if (!bearer) return Response.json({ error: "No autenticado" }, { status: 401 });
  try {
    const response = await apiFetch("/api/v1/sessions/revoke", bearer, { method: "POST" });
    if (response.status === 204) return new Response(null, { status: 204 });
    return Response.json({ error: "Revocación no confirmada" }, { status: 502 });
  } catch {
    return Response.json({ error: "Revocación no disponible" }, { status: 503 });
  }
}
