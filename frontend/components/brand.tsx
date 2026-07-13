import Link from "next/link";

export function Brand({ name }: { name: string }) {
  return (
    <Link href="/" className="group inline-flex items-center gap-3" aria-label={`${name}, accueil`}>
      <span className="grid size-10 place-items-center rounded-xl bg-blue-700 text-white shadow-sm transition-transform group-hover:-translate-y-0.5" aria-hidden="true">
        <svg viewBox="0 0 40 40" className="size-7" fill="none">
          <path d="M8 23.5 31 12l-9.5 20-3.6-8.2L8 23.5Z" fill="currentColor" />
          <path d="m17.9 23.8 5.8-5.5" stroke="#10213f" strokeWidth="2.4" strokeLinecap="round" />
        </svg>
      </span>
      <span className="text-[15px] font-extrabold tracking-[-0.02em] text-slate-950 sm:text-base">{name}</span>
    </Link>
  );
}
