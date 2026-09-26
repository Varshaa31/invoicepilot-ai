import type { InvoiceStatus, ResolutionStatus } from "@/types";

const STATUS: Record<string, string> = {
  DRAFT: "bg-slate-100 text-slate-700",
  REVIEW_REQUIRED: "bg-amber-100 text-amber-800",
  READY_FOR_APPROVAL: "bg-sky-100 text-sky-800",
  APPROVED: "bg-emerald-100 text-emerald-800",
  EXPORTED: "bg-indigo-100 text-indigo-800",
  ACTIVE: "bg-emerald-100 text-emerald-800",
  INACTIVE: "bg-slate-100 text-slate-600",
  MATCHED: "bg-emerald-100 text-emerald-800",
  AMBIGUOUS: "bg-amber-100 text-amber-800",
  MISSING: "bg-rose-100 text-rose-800",
};

export function StatusBadge({ value }: { value: InvoiceStatus | ResolutionStatus | string }) {
  return (
    <span className={`inline-flex rounded-full px-2.5 py-1 text-xs font-medium ${STATUS[value] || "bg-slate-100"}`}>
      {value.replaceAll("_", " ")}
    </span>
  );
}
