"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { addInquiryNote, getMyInquiries, transitionMyInquiry, type DriverInquiry } from "@/lib/marketplace";

const statuses = [["new","Nouvelle"],["notified","Chauffeur informé"],["viewed","Consultée"],["contacted","Client contacté"],["accepted","Acceptée"],["declined","Refusée"],["closed","Clôturée"],["archived","Archivée"],["spam","Indésirable"]];
const actions: Record<string, Array<[string,string]>> = { new: [["viewed","Marquer comme consultée"],["spam","Indésirable"]], notified: [["viewed","Marquer comme consultée"],["contacted","Client contacté"],["spam","Indésirable"]], viewed: [["contacted","Client contacté"],["spam","Indésirable"]], contacted: [["accepted","Accepter"],["declined","Refuser"],["spam","Indésirable"]], accepted: [["closed","Clôturer"]], declined: [["closed","Clôturer"]], closed: [["archived","Archiver"]] };

export function DriverInbox() {
  const [items, setItems] = useState<DriverInquiry[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [status, setStatus] = useState(""); const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true); const [error, setError] = useState("");
  const [busy, setBusy] = useState(false); const [note, setNote] = useState("");
  const [pendingAction, setPendingAction] = useState<[string,string] | null>(null);
  const requestSequence = useRef(0);
  const [reason, setReason] = useState("");
  const selected = items.find((item) => item.public_id === selectedId) ?? null;

  const refresh = useCallback(async () => { const sequence = ++requestSequence.current; setLoading(true); setError(""); try { const page = await getMyInquiries({ status, q: query }); if (sequence !== requestSequence.current) return; setItems(page.results); setSelectedId((current) => current && page.results.some((item) => item.public_id === current) ? current : page.results[0]?.public_id ?? null); } catch (caught) { setError(caught instanceof Error ? caught.message : "Chargement impossible."); } finally { setLoading(false); } }, [query, status]);
  useEffect(() => { const timer = window.setTimeout(() => { void refresh(); }, 0); return () => window.clearTimeout(timer); }, [refresh]);

  async function runAction(value: string, actionReason = "") { if (!selected) return; setBusy(true); setError(""); try { await transitionMyInquiry(selected.public_id, value, actionReason); setPendingAction(null); setReason(""); await refresh(); } catch (caught) { setError(caught instanceof Error ? caught.message : "Action impossible."); } finally { setBusy(false); } }
  function requestAction(action: [string,string]) { if (["declined","spam","closed","archived"].includes(action[0])) setPendingAction(action); else void runAction(action[0]); }
  async function saveNote() { if (!selected || !note.trim()) return; setBusy(true); try { await addInquiryNote(selected.public_id, note); setNote(""); await refresh(); } catch (caught) { setError(caught instanceof Error ? caught.message : "Note impossible."); } finally { setBusy(false); } }

  return <section className="mt-10 border-t border-slate-200 pt-10">
    <div className="flex flex-wrap items-end justify-between gap-4"><div><p className="eyebrow">Demandes clients</p><h2 className="mt-2 text-2xl font-black">Boîte de réception chauffeur</h2></div><button type="button" className="button button-secondary" onClick={() => void refresh()}>Actualiser</button></div>
    <div className="mt-6 grid gap-3 sm:grid-cols-[1fr_13rem_auto]"><label><span className="sr-only">Rechercher</span><input className="form-input" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Référence, client ou destination" /></label><label><span className="sr-only">Statut</span><select className="form-input" value={status} onChange={(event) => setStatus(event.target.value)}><option value="">Tous les statuts</option>{statuses.map(([value,label]) => <option key={value} value={value}>{label}</option>)}</select></label><button className="button button-primary" onClick={() => void refresh()}>Rechercher</button></div>
    {error ? <p className="form-status-error mt-5" role="alert">{error}</p> : null}
    {loading ? <Loading /> : items.length ? <div className="mt-6 grid gap-6 lg:grid-cols-[0.8fr_1.2fr]"><InquiryList items={items} selectedId={selectedId} onSelect={setSelectedId} />{selected ? <InquiryDetail inquiry={selected} busy={busy} note={note} setNote={setNote} requestAction={requestAction} saveNote={saveNote} /> : null}</div> : <Empty />}
    {pendingAction ? <div className="fixed inset-0 z-[100] grid place-items-center bg-slate-950/60 p-4" role="presentation"><div role="dialog" aria-modal="true" aria-labelledby="action-title" className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl"><h3 id="action-title" className="text-xl font-black">{pendingAction[1]}</h3><label className="mt-5 block"><span className="form-label">Raison obligatoire</span><textarea autoFocus className="form-input min-h-24" value={reason} onChange={(event) => setReason(event.target.value)} /></label><div className="mt-5 flex justify-end gap-3"><button className="button button-secondary" onClick={() => { setPendingAction(null); setReason(""); }}>Annuler</button><button className="button button-primary" disabled={!reason.trim() || busy} onClick={() => void runAction(pendingAction[0], reason)}>Confirmer</button></div></div></div> : null}
  </section>;
}

function InquiryList({ items, selectedId, onSelect }: { items: DriverInquiry[]; selectedId: string | null; onSelect: (id: string) => void }) { return <div className="max-h-[42rem] overflow-auto rounded-2xl border border-slate-200">{items.map((item) => <button type="button" key={item.public_id} onClick={() => onSelect(item.public_id)} className={`block w-full border-b border-slate-200 p-4 text-left hover:bg-blue-50 ${selectedId === item.public_id ? "bg-blue-50" : "bg-white"}`}><div className="flex justify-between gap-3"><span className="font-black text-blue-800">{item.reference}</span><span className="text-xs font-bold text-slate-600">{item.status_label}</span></div><p className="mt-2 font-bold">{item.airport_code} · {item.destination}</p><p className="mt-1 text-sm text-slate-500">{item.customer_name} · {new Intl.DateTimeFormat("fr-FR", { dateStyle: "medium" }).format(new Date(item.created_at))}</p></button>)}</div>; }

function InquiryDetail({ inquiry, busy, note, setNote, requestAction, saveNote }: { inquiry: DriverInquiry; busy: boolean; note: string; setNote: (value: string) => void; requestAction: (action: [string,string]) => void; saveNote: () => void }) {
  const deliveryProblem = Object.values(inquiry.notification_status).some((value) => value === "retrying" || value === "permanent_failure");
  return <article className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"><div className="flex flex-wrap justify-between gap-3"><div><p className="eyebrow">{inquiry.reference}</p><h3 className="mt-2 text-2xl font-black">{inquiry.airport_name} · {inquiry.destination}</h3></div><span className="h-fit rounded-full bg-blue-50 px-3 py-1 text-sm font-bold text-blue-800">{inquiry.status_label}</span></div>
    <dl className="mt-6 grid gap-3 text-sm sm:grid-cols-2"><Fact label="Client" value={inquiry.customer_name} /><Fact label="Voyage" value={`${inquiry.passenger_count} passager(s), ${inquiry.luggage_count} bagage(s)`} /><Fact label="Date" value={inquiry.pickup_at ? new Intl.DateTimeFormat("fr-FR", { dateStyle: "medium", timeStyle: "short" }).format(new Date(inquiry.pickup_at)) : "À convenir"} /><Fact label="Contact préféré" value={inquiry.preferred_contact_method} /></dl>
    <div className="mt-5 flex flex-wrap gap-2"><a className="button button-secondary" href={`mailto:${encodeURIComponent(inquiry.customer_email)}?subject=${encodeURIComponent(`Votre demande AirProche ${inquiry.reference}`)}`}>Écrire par e-mail</a><a className="button button-secondary" href={`tel:${inquiry.customer_phone.replace(/[^+\d]/g, "")}`}>Appeler</a>{inquiry.whatsapp_consent && inquiry.customer_whatsapp ? <a className="button button-secondary" target="_blank" rel="noreferrer" href={`https://wa.me/${inquiry.customer_whatsapp.replace(/\D/g, "")}`}>WhatsApp</a> : null}</div>
    {inquiry.message ? <div className="mt-6 rounded-xl bg-slate-50 p-4 text-sm leading-6"><p className="font-bold">Message du client</p><p className="mt-2 whitespace-pre-wrap">{inquiry.message}</p></div> : null}
    <div className="mt-6 flex flex-wrap gap-2">{(actions[inquiry.status] ?? []).map((action) => <button type="button" className="button button-secondary" disabled={busy} key={action[0]} onClick={() => requestAction(action)}>{action[1]}</button>)}</div>
    <div className="mt-6 border-t border-slate-200 pt-5"><label><span className="form-label">Note interne</span><textarea className="form-input min-h-24" value={note} onChange={(event) => setNote(event.target.value)} /></label><button className="button button-secondary mt-3" disabled={busy || !note.trim()} onClick={saveNote}>Ajouter la note</button></div>
    <div className="mt-6 border-t border-slate-200 pt-5"><h4 className="font-black">Historique</h4><ol className="mt-3 grid gap-2 text-sm text-slate-600">{inquiry.history.map((entry) => <li key={`${entry.changed_at}-${entry.to_status}`}>{entry.status_label} · {new Intl.DateTimeFormat("fr-FR", { dateStyle: "short", timeStyle: "short" }).format(new Date(entry.changed_at))}</li>)}</ol></div>
    {deliveryProblem ? <p className="mt-5 rounded-xl bg-amber-50 p-4 text-sm font-semibold text-amber-900">Un e-mail rencontre un problème de livraison. La demande reste disponible ici ; vérifiez les coordonnées avant de contacter le client.</p> : null}
  </article>;
}

function Fact({ label, value }: { label: string; value: string }) { return <div><dt className="text-slate-500">{label}</dt><dd className="font-bold">{value}</dd></div>; }
function Loading() { return <div className="mt-6 grid gap-3" role="status" aria-label="Chargement des demandes"><div className="h-24 animate-pulse rounded-2xl bg-slate-100 motion-reduce:animate-none" /><div className="h-24 animate-pulse rounded-2xl bg-slate-100 motion-reduce:animate-none" /></div>; }
function Empty() { return <div className="mt-6 rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center"><h3 className="font-black">Aucune demande</h3><p className="mt-2 text-sm text-slate-600">Les nouvelles demandes apparaîtront ici immédiatement, même si un e-mail rencontre un problème.</p></div>; }
