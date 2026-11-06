import Image from "next/image";
import Link from "next/link";
import { redirect } from "next/navigation";
import { auth } from "@/auth";
import { validSessionId } from "@/lib/security";
import AdminClient from "./admin-client";

export const dynamic = "force-dynamic";

export default async function Admin() {
  const session = await auth();
  if (!validSessionId(session?.user?.id)) redirect("/");
  return <main className="container">
    <header className="top">
      <Link href="/portal" className="brand"><Image src="/smartuni-icon.png" alt="SMART UNI" width={48} height={48} /> SMART UNI</Link>
      <Link href="/portal">Volver al espacio académico</Link>
    </header>
    <div className="notice">Las métricas solo estarán disponibles si la identidad tiene rol administrativo confirmado por PostgreSQL.</div>
    <h1>Panel de operación</h1>
    <AdminClient />
  </main>;
}
