import type { NextRequest } from "next/server";
import { apiFetch, forwardJson, getApiBearer } from "@/lib/backend";
import { allowedOrigin } from "@/lib/security";

export const dynamic = "force-dynamic";

export async function GET(request: NextRequest) {
  const token = await getApiBearer(request);
  if (!token) return Response.json({ error: "Inicia sesión" }, { status: 401 });
  try {
    return await forwardJson(await apiFetch("/api/v1/notes", token));
  } catch {
    return Response.json({ error: "API no disponible" }, { status: 503 });
  }
}

export async function POST(request: NextRequest) {
  if (!allowedOrigin(request.headers.get("origin"), process.env.PORTAL_ORIGIN ?? "")) {
    return Response.json({ error: "Origen no permitido" }, { status: 403 });
  }
  if (!request.headers.get("content-type")?.startsWith("application/json")) {
    return Response.json({ error: "Content-Type inválido" }, { status: 415 });
  }
  const bearer = await getApiBearer(request);
  if (!bearer) return Response.json({ error: "Inicia sesión" }, { status: 401 });
  try {
    const raw = await request.text();
    if (raw.length > 12000) return Response.json({ error: "Petición excesiva" }, { status: 413 });
    const body: unknown = JSON.parse(raw);
    if (!body || typeof body !== "object" || Array.isArray(body)) {
      return Response.json({ error: "Formato inválido" }, { status: 400 });
    }
    const obj = body as Record<string, unknown>;
    if (typeof obj.title !== "string" || !obj.title.trim() ||
        obj.title.length > 160 ||
        typeof obj.content !== "string" || obj.content.length > 4000 ||
        Object.keys(obj).some((key) => !["title", "content"].includes(key))) {
      return Response.json({ error: "Datos inválidos" }, { status: 422 });
    }
    return await forwardJson(await apiFetch("/api/v1/notes", bearer, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title: obj.title.trim(), content: obj.content }),
    }));
  } catch {
    return Response.json({ error: "No se pudo guardar" }, { status: 503 });
  }
}
