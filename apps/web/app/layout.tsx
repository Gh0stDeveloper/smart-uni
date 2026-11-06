import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SMART UNI · Portal académico",
  description: "Portal de desarrollo SMART UNI. Acceso OIDC; contenido de prueba, sin cifrado E2EE.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return <html lang="es"><body>{children}</body></html>;
}
