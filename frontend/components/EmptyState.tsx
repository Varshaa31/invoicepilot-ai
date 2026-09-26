import { ReactNode } from "react";

export function EmptyState({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="rounded-3xl border border-dashed border-ink/15 bg-white px-8 py-16 text-center">
      <p className="font-serif text-2xl">{title}</p>
      <div className="mt-3 text-sm text-ink/60">{children}</div>
    </div>
  );
}
