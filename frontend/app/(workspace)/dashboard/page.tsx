
"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, inr } from "@/lib/api";
import { StatusBadge } from "@/components/StatusBadge";
import { Skeleton } from "@/components/Skeleton";
import type { Dashboard } from "@/types";

export default function DashboardPage() {
  const [data, setData] = useState<Dashboard | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .dashboard()
      .then(setData)
      .catch((err) => setError(err.message));
  }, []);

  const cards = data
    ? [
        {
          label: "Total invoices",
          value: String(data.total_invoices),
          href: "/invoices",
        },
        {
          label: "Drafts",
          value: String(data.drafts),
          href: "/invoices?status=DRAFT",
        },
        {
          label: "Pending review",
          value: String(data.pending_review),
          href: "/invoices?status=REVIEW_REQUIRED",
          action: true,
        },
        {
          label: "Approved",
          value: String(data.approved),
          href: "/invoices?status=APPROVED",
        },
        {
          label: "Invoice value",
          value: inr(data.total_revenue),
          href: "/invoices",
          isCurrency: true,
        },
      ]
    : [];

  return (
    <div className="space-y-8">
      <div>
        <p className="text-sm uppercase tracking-[0.2em] text-gold">
          Workspace
        </p>

        <h1 className="mt-2 font-serif text-4xl">Dashboard</h1>

        <p className="mt-2 text-ink/60">
          AI understands. Your catalog prices. You approve.
        </p>
      </div>

      {error && (
        <div className="rounded-2xl bg-rose-50 px-4 py-3 text-rose-800">
          {error}
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-5">
        {data
          ? cards.map((card) => (
              <Link
                key={card.label}
                href={card.href}
                className={`min-w-0 rounded-3xl bg-white p-5 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md ${
                  card.action ? "ring-1 ring-gold/30" : ""
                }`}
              >
                <p className="truncate text-sm text-ink/50">
                  {card.label}
                </p>

                <p
                  className={`mt-3 whitespace-nowrap font-serif tracking-tight ${
                    card.isCurrency ? "text-2xl" : "text-3xl"
                  }`}
                >
                  {card.value}
                </p>

                {card.action && data.pending_review > 0 && (
                  <p className="mt-2 text-xs font-medium text-gold">
                    Needs attention →
                  </p>
                )}
              </Link>
            ))
          : Array.from({ length: 5 }).map((_, index) => (
              <Skeleton key={index} className="h-28" />
            ))}
      </div>

      {data && data.pending_review > 0 && (
        <div className="rounded-3xl bg-ink p-6 text-white shadow-sm">
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div>
              <p className="text-sm uppercase tracking-[0.18em] text-gold">
                Human review
              </p>

              <h2 className="mt-2 font-serif text-2xl">
                {data.pending_review} invoice
                {data.pending_review === 1 ? "" : "s"} need attention
              </h2>

              <p className="mt-2 max-w-2xl text-sm text-white/65">
                Some invoices still have missing or ambiguous service details.
                Review them before approval and PDF export.
              </p>
            </div>

            <Link
              href="/invoices?status=REVIEW_REQUIRED"
              className="inline-flex shrink-0 items-center justify-center rounded-full bg-gold px-5 py-3 font-medium text-ink transition hover:opacity-90"
            >
              Review invoices
            </Link>
          </div>
        </div>
      )}

      <div className="rounded-3xl bg-white p-6 shadow-sm">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="font-serif text-2xl">Recent invoices</h2>

          <Link href="/invoices" className="text-sm text-ink/60">
            View all
          </Link>
        </div>

        {!data ? (
          <Skeleton className="h-40" />
        ) : data.recent.length === 0 ? (
          <div className="rounded-2xl bg-ivory px-6 py-10 text-center">
            <p className="font-serif text-2xl">No invoices yet</p>

            <p className="mt-2 text-ink/60">
              Paste a customer message and let InvoicePilot extract, match,
              and price it.
            </p>

            <Link
              href="/create"
              className="mt-5 inline-block rounded-full bg-ink px-5 py-3 text-white"
            >
              + Create Invoice
            </Link>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="text-ink/50">
                <tr>
                  <th className="py-2">Invoice</th>
                  <th>Customer</th>
                  <th>Date</th>
                  <th>Amount</th>
                  <th>Status</th>
                  <th />
                </tr>
              </thead>

              <tbody>
                {data.recent.map((row) => (
                  <tr key={row.id} className="border-t border-ink/5">
                    <td className="py-3 font-medium">
                      {row.invoice_number}
                    </td>

                    <td>{row.customer_name}</td>

                    <td>
                      {new Date(row.created_at).toLocaleDateString()}
                    </td>

                    <td>{inr(row.total, row.currency)}</td>

                    <td>
                      <StatusBadge value={row.status} />
                    </td>

                    <td className="text-right">
                      <Link
                        href={`/invoices/${row.id}`}
                        className="text-ink underline"
                      >
                        View
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

