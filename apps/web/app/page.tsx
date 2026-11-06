import Image from "next/image";
import { auth, signIn } from "@/auth";
import Link from "next/link";

export const dynamic = "force-dynamic";

export default async function Home() {
  const session = await auth();
  async function enter() {
    "use server";
    await signIn("keycloak", { redirectTo: "/portal" });
  }
  return <main className="container">
    <header className="top">
      <Link href="/" className="brand"><Image src="/smartuni-icon.png" alt="SMART UNI" width={48} height={48} /> SMART UNI</Link>
      <span className="muted">Plataforma académica · Prototipo online</span>
    </header>
    <div className="grid">
      <section className="card">
        <h1>Organiza tu espacio académico</h1>
        <p className="muted">Una experiencia unificada para Windows, Linux y Android. Este portal constituye el primer módulo web de la etapa 5.</p>
        {session?.user?.id ?
          <Link href="/portal" className="btn">Entrar al panel</Link> :
          <form action={enter}><button className="btn" type="submit">Acceder con cuenta institucional</button></form>
        }
      </section>
      <section className="card">
        <h2>Acceso protegido</h2>
        <p>Inicio de sesión mediante un proveedor OIDC, validación de permisos en el backend y cookies de sesión HttpOnly.</p>
        <p className="muted">Solo se autorizan datos sintéticos de desarrollo. El almacenamiento E2EE, la sincronización y los archivos privados todavía no están habilitados.</p>
      </section>
    </div>
  </main>;
}
