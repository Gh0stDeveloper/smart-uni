import Image from "next/image";
import Link from "next/link";
import { redirect } from "next/navigation";
import { auth, signOut } from "@/auth";
import NotesClient from "./notes-client";
import { validSessionId } from "@/lib/security";

export const dynamic = "force-dynamic";

export default async function Portal() {
  const session = await auth();
  if (!validSessionId(session?.user?.id)) redirect("/");
  async function leave() {
    "use server";
    await signOut({ redirectTo: "/" });
  }
  return <main className="container">
    <header className="top">
      <Link href="/" className="brand"><Image src="/smartuni-icon.png" alt="SMART UNI" width={48} height={48} /> SMART UNI</Link>
      <div className="controls">
        <Link href="/portal/admin">Panel administrativo</Link>
        <form action={leave}><button type="submit" className="btn outline">Cerrar sesión</button></form>
      </div>
    </header>
    <div className="notice"><strong>Entorno de desarrollo.</strong> Los apuntes de esta demostración NO están cifrados extremo a extremo. Usa solo datos ficticios.</div>
    <h1>Mi espacio académico</h1>
    <p className="muted">Sesión OIDC validada; el servidor decide a qué registros tienes acceso. No se puede asignar un rol desde esta pantalla.</p>
    <NotesClient />
  </main>;
}
