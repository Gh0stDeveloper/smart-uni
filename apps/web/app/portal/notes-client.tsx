"use client";
import { useEffect, useState } from "react";

type Note = { id: string; title: string; content: string };

export default function NotesClient() {
  const [notes, setNotes] = useState<Note[]>([]);
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [feedback, setFeedback] = useState("");
  const [saving, setSaving] = useState(false);

  async function load() {
    try {
      const response = await fetch("/api/notes", { credentials: "same-origin", cache: "no-store" });
      if (!response.ok) throw new Error("No se pueden consultar los apuntes.");
      const data: unknown = await response.json();
      if (!Array.isArray(data)) throw new Error("Datos inesperados.");
      setNotes(data as Note[]);
    } catch (err) {
      setFeedback(err instanceof Error ? err.message : "No disponible");
    }
  }

  useEffect(() => { void load(); }, []);

  async function add(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!title.trim() || saving) return;
    setSaving(true);
    setFeedback("");
    try {
      const response = await fetch("/api/notes", {
        method: "POST",
        credentials: "same-origin",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: title.trim(), content }),
      });
      if (!response.ok) throw new Error("No se pudo guardar el apunte de prueba.");
      setTitle("");
      setContent("");
      await load();
      setFeedback("Apunte de demostración guardado.");
    } catch (err) {
      setFeedback(err instanceof Error ? err.message : "Error");
    } finally {
      setSaving(false);
    }
  }

  return <div className="grid">
    <section className="card">
      <h2>Apuntes de prueba</h2>
      <div aria-live="polite">{notes.length === 0 ? <p className="muted">No hay apuntes guardados.</p> :
        notes.map(note => <div className="note" key={note.id}><strong>{note.title}</strong><p>{note.content}</p></div>)}</div>
      {feedback && <p role="status" className="muted">{feedback}</p>}
    </section>
    <section className="card">
      <h2>Agregar apunte ficticio</h2>
      <form onSubmit={add}>
        <label htmlFor="note-title">Título</label>
        <input id="note-title" maxLength={160} required value={title} onChange={e => setTitle(e.target.value)} />
        <label htmlFor="note-content">Descripción de prueba</label>
        <textarea id="note-content" maxLength={4000} value={content} onChange={e => setContent(e.target.value)} />
        <button className="btn secondary" type="submit" disabled={saving}>{saving ? "Guardando…" : "Guardar apunte"}</button>
      </form>
    </section>
  </div>;
}
