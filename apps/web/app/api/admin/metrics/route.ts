import type { NextRequest } from "next/server";
import { apiFetch, forwardJson, getApiBearer } from "@/lib/backend";

export const dynamic = "force-dynamic";

export async function GET(request: NextRequest) {
  const token = await getApiBearer(request);
  if (!token) return Response.json({ error: "No autenticado" }, { status: 401 });
  try {
    // El backend DB comprueba que el usuario tenga rol admin.
    return await forwardJson(await apiFetch("/api/v1/admin/metrics", token));
  } catch {
    return Response.json({ error: "API no disponible" }, { status: 503 });
  }
}
