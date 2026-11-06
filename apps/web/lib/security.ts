/** Validadores sin operaciones de red, comprobados con node:test. */
export function validSessionId(value: unknown): value is string {
  return typeof value === "string" && value.length > 0 && value.length <= 255;
}

export function allowedOrigin(actual: string | null, expected: string, allowLocalHttp = false): boolean {
  if (!actual || !expected) return false;
  try {
    const actualUrl = new URL(actual);
    const expectedUrl = new URL(expected);
    return actual === actualUrl.origin && expected === expectedUrl.origin &&
      actualUrl.origin === expectedUrl.origin && (
        actualUrl.protocol === "https:" ||
        (allowLocalHttp && actualUrl.protocol === "http:" &&
          ["localhost", "127.0.0.1"].includes(actualUrl.hostname))
      );
  } catch {
    return false;
  }
}

/** Ruta interna fija hacia una URL de backend establecida por el operador. */
export function backendUrl(base: string | undefined, path: string, production: boolean): string {
  if (!base) throw new Error("SMARTUNI_API_INTERNAL_URL no configurada");
  const root = new URL(base);
  if (!["http:", "https:"].includes(root.protocol) || (production && root.protocol !== "https:")) {
    throw new Error("El backend requiere HTTPS en producción");
  }
  if (root.username || root.password || root.search || root.hash || root.pathname !== "/") {
    throw new Error("URL base del backend no permitida");
  }
  if (!path.startsWith("/api/v1/") || path.includes("?") || path.includes("#")) {
    throw new Error("Ruta de API no permitida");
  }
  return new URL(path, root).toString();
}
