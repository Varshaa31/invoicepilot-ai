"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  api,
  downloadInvoicePdf,
  inr,
} from "@/lib/api";
import { StatusBadge } from "@/components/StatusBadge";
import { EmptyState } from "@/components/EmptyState";
import type {
  InvoiceListItem,
  InvoiceStatus,
} from "@/types";

const STATUS_OPTIONS = [
  "DRAFT",
  "REVIEW_REQUIRED",
  "READY_FOR_APPROVAL",
  "APPROVED",
  "EXPORTED",
];

function statusLabel(status: string) {
  const labels: Record<string, string> = {
    DRAFT: "Draft",
    REVIEW_REQUIRED: "Needs Review",
    READY_FOR_APPROVAL: "Ready for Approval",
    APPROVED: "Approved",
    EXPORTED: "Exported",
  };

  return labels[status] || status;
}

export default function InvoicesPage() {
  const [rows, setRows] = useState<InvoiceListItem[]>([]);
  const [status, setStatus] = useState("");
  const [customer, setCustomer] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [downloadingId, setDownloadingId] =
    useState<string | null>(null);
  const [initialized, setInitialized] = useState(false);

  async function load() {
    try {
      setError(null);

      const params: Record<string, string> = {};

      if (status) {
        params.status = status;
      }

      if (customer) {
        params.customer = customer;
      }

      if (dateFrom) {
        params.date_from = new Date(
          dateFrom,
        ).toISOString();
      }

      if (dateTo) {
        const end = new Date(dateTo);
        end.setHours(23, 59, 59, 999);
        params.date_to = end.toISOString();
      }

      setRows(await api.invoices(params));
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to load invoices",
      );
    }
  }

  // Read a status filter passed from the dashboard.
  useEffect(() => {
    const params = new URLSearchParams(
      window.location.search,
    );

    const urlStatus = params.get("status") || "";

    setStatus(urlStatus);
    setInitialized(true);
  }, []);

  useEffect(() => {
    if (initialized) {
      load();
    }
  }, [status, initialized]);

  async function handleDownload(
    invoiceId: string,
  ) {
    try {
      setDownloadingId(invoiceId);
      setError(null);

      await downloadInvoicePdf(invoiceId);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to download invoice.",
      );
    } finally {
      setDownloadingId(null);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-sm uppercase tracking-[0.2em] text-gold">
            Workspace
          </p>

          <h1 className="mt-2 font-serif text-4xl">
            Invoices
          </h1>

          <p className="mt-2 text-ink/60">
            Searchable history with catalog-verified
            totals.
          </p>
        </div>

        <Link
          href="/create"
          className="rounded-full bg-ink px-5 py-3 text-sm font-medium text-white"
        >
          + Create Invoice
        </Link>
      </div>

      <div className="rounded-3xl bg-white p-4 shadow-sm">
        <div className="flex flex-wrap gap-3">
          <select
            className="rounded-xl border border-ink/10 bg-white px-3 py-2"
            value={status}
            onChange={(event) =>
              setStatus(event.target.value)
            }
          >
            <option value="">
              All statuses
            </option>

            {STATUS_OPTIONS.map((value) => (
              <option
                key={value}
                value={value}
              >
                {statusLabel(value)}
              </option>
            ))}
          </select>

          <input
            className="rounded-xl border border-ink/10 px-3 py-2"
            placeholder="Customer"
            value={customer}
            onChange={(event) =>
              setCustomer(event.target.value)
            }
          />

          <input
            className="rounded-xl border border-ink/10 px-3 py-2"
            type="date"
            value={dateFrom}
            onChange={(event) =>
              setDateFrom(event.target.value)
            }
          />

          <input
            className="rounded-xl border border-ink/10 px-3 py-2"
            type="date"
            value={dateTo}
            onChange={(event) =>
              setDateTo(event.target.value)
            }
          />

          <button
            type="button"
            className="rounded-full bg-ink px-5 py-2 text-sm font-medium text-white"
            onClick={load}
          >
            Filter
          </button>
        </div>
      </div>

      {error && (
        <div className="rounded-2xl bg-rose-50 p-3 text-rose-800">
          {error}
        </div>
      )}

      {rows.length === 0 ? (
        <EmptyState
          title={
            status === "REVIEW_REQUIRED"
              ? "No invoices need review"
              : "No invoices found"
          }
        >
          {status === "REVIEW_REQUIRED" ? (
            <p>
              Invoices with missing or ambiguous
              services will appear here.
            </p>
          ) : (
            <Link href="/create">
              Create an invoice from a customer
              message.
            </Link>
          )}
        </EmptyState>
      ) : (
        <div className="overflow-x-auto rounded-3xl bg-white p-4 shadow-sm">
          <table className="w-full min-w-[850px] text-left text-sm">
            <thead className="text-ink/50">
              <tr>
                <th className="py-3">
                  Invoice Number
                </th>
                <th>Customer</th>
                <th>Date</th>
                <th className="text-right">
                  Amount
                </th>
                <th>Status</th>
                <th className="text-right">
                  Actions
                </th>
              </tr>
            </thead>

            <tbody>
              {rows.map((row) => {
                const needsReview =
                  row.status === "REVIEW_REQUIRED";

                const canDownload =
                  row.status === "APPROVED" ||
                  row.status === "EXPORTED";

                return (
                  <tr
                    key={row.id}
                    className={`border-t border-ink/5 ${
                      needsReview
                        ? "bg-amber-50/40"
                        : ""
                    }`}
                  >
                    <td className="py-4 font-medium">
                      {row.invoice_number}
                    </td>

                    <td>
                      {row.customer_name}
                    </td>

                    <td className="whitespace-nowrap">
                      {new Date(
                        row.created_at,
                      ).toLocaleDateString()}
                    </td>

                    <td className="whitespace-nowrap text-right font-medium">
                      {inr(
                        row.total,
                        row.currency,
                      )}
                    </td>

                    <td>
                      <div className="flex items-center gap-2">
                        <StatusBadge
                          value={
                            row.status as InvoiceStatus
                          }
                        />

                        {needsReview && (
                          <span className="text-xs font-medium text-amber-700">
                            Action needed
                          </span>
                        )}
                      </div>
                    </td>

                    <td>
                      <div className="flex justify-end gap-3 whitespace-nowrap">
                        <Link
                          href={`/invoices/${row.id}`}
                          className="font-medium text-ink underline underline-offset-2"
                        >
                          View
                        </Link>

                        {row.status !== "APPROVED" &&
                          row.status !== "EXPORTED" && (
                            <Link
                              href={`/invoices/${row.id}`}
                              className="text-ink/60 underline underline-offset-2"
                            >
                              Edit
                            </Link>
                          )}

                        {canDownload && (
                          <button
                            type="button"
                            onClick={() =>
                              handleDownload(
                                row.id,
                              )
                            }
                            disabled={
                              downloadingId ===
                              row.id
                            }
                            className="text-ink/60 underline underline-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                          >
                            {downloadingId ===
                            row.id
                              ? "Downloading..."
                              : "Download"}
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}