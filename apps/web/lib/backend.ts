/** BFF: las credenciales OIDC solo existen del lado del servidor. */
import type { NextRequest } from "next/server";
import { getToken } from "next-auth/jwt";
import { auth } from "@/auth";
import { backendUrl, validSessionId } from "./security";

export async function getApiBearer(request: NextRequest): Promise<string | null> {
  const session = await auth();
  // La existencia de auth() NO es suficiente: exigir identidad concreta.
  if (!validSessionId(session?.user?.id)) return null;
  const state = await getToken({
    req: request,
    secret: process.env.AUTH_SECRET,
    secureCookie: process.env.NODE_ENV === "production",
  });
  if (typeof state?.apiAccessToken !== "string" || state.apiAccessToken.length < 10 ||
      typeof state.apiExpiresAt !== "number" || state.apiExpiresAt <= Date.now() / 1000 + 30) {
    return null;
  }
  return state.apiAccessToken;
}

export async function apiFetch(path: string, bearer: string, init?: RequestInit): Promise<Response> {
  const url = backendUrl(
    process.env.SMARTUNI_API_INTERNAL_URL, path, process.env.NODE_ENV === "production"
  );
  return fetch(url, {
    ...init,
    headers: {
      ...(init?.headers ?? {}),
      Authorization: "Bearer " + bearer,
      Accept: "application/json",
    },
    cache: "no-store",
    redirect: "manual",
    signal: AbortSignal.timeout(8000),
  });
}

export async function forwardJson(response: Response): Promise<Response> {
  if (response.status >= 300 && response.status < 400) {
    return Response.json({ error: "Redirección backend rechazada" }, { status: 502 });
  }
  if (response.status >= 500) {
    return Response.json({ error: "Error de servicio" }, { status: 502 });
  }
  const body = await response.text();
  if (body.length > 524288) {
    return Response.json({ error: "Respuesta excesiva" }, { status: 502 });
  }
  return new Response(body, {
    status: response.status,
    headers: {
      "Content-Type": "application/json",
      "Cache-Control": "no-store, private",
    },
  });
}
