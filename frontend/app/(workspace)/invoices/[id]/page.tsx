"use client";

import Link from "next/link";
import { use, useEffect, useState } from "react";
import {
  api,
  ApiError,
  downloadInvoicePdf,
  inr,
} from "@/lib/api";
import { StatusBadge } from "@/components/StatusBadge";
import { useToast } from "@/components/Toast";
import type { Invoice } from "@/types";

const EVENT_LABEL: Record<string, string> = {
  invoice_created: "Invoice created",
  ai_extraction_completed: "Information extracted",
  service_matched: "Service matched",
  service_ambiguous: "Service selection required",
  service_missing: "Service not found",
  price_resolved: "Price confirmed",
  invoice_edited: "Invoice updated",
  invoice_approved: "Invoice approved",
  invoice_exported: "PDF exported",
};

export default function InvoiceDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const toast = useToast();

  const [invoice, setInvoice] =
    useState<Invoice | null>(null);

  const [error, setError] =
    useState<string | null>(null);

  const [loading, setLoading] =
    useState(false);

  const [resolvingItemId, setResolvingItemId] =
    useState<string | null>(null);

  const [selectedServiceId, setSelectedServiceId] =
    useState<string | null>(null);

  const [downloading, setDownloading] =
    useState(false);

  async function load() {
    try {
      setError(null);

      const result = await api.invoice(id);

      setInvoice(result);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Invoice not found",
      );
    }
  }

  useEffect(() => {
    load();
  }, [id]);

  async function resolve(
    itemId: string,
    serviceId: string,
  ) {
    setResolvingItemId(itemId);
    setSelectedServiceId(serviceId);
    setError(null);

    try {
      const updatedInvoice =
        await api.resolveService(
          id,
          itemId,
          serviceId,
        );

      setInvoice(updatedInvoice);

      toast.push("Service selected");
    } catch (err) {
      setSelectedServiceId(null);

      setError(
        err instanceof ApiError
          ? err.message
          : "Could not select the service",
      );
    } finally {
      setResolvingItemId(null);
    }
  }

  async function approve() {
    setLoading(true);
    setError(null);

    try {
      const approvedInvoice =
        await api.approve(id);

      setInvoice(approvedInvoice);

      toast.push("Invoice approved");
    } catch (err) {
      const apiErr = err as ApiError;

      setError(
        [
          apiErr.message,
          ...(apiErr.issues || []),
        ].join(" "),
      );
    } finally {
      setLoading(false);
    }
  }

  async function downloadPdf() {
    setDownloading(true);
    setError(null);

    try {
      await downloadInvoicePdf(
        invoice?.id || id,
      );

      toast.push("Invoice PDF downloaded");
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Could not download the invoice PDF.",
      );
    } finally {
      setDownloading(false);
    }
  }

  if (!invoice) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <div className="text-center">
          {error ? (
            <p className="rounded-2xl bg-rose-50 px-5 py-4 text-rose-800">
              {error}
            </p>
          ) : (
            <>
              <div className="mx-auto h-8 w-8 animate-spin rounded-full border-2 border-ink/10 border-t-ink" />

              <p className="mt-3 text-sm text-ink/50">
                Loading invoice…
              </p>
            </>
          )}
        </div>
      </div>
    );
  }

  const isApproved =
    invoice.status === "APPROVED" ||
    invoice.status === "EXPORTED";

  const hasCatalogPrices =
    invoice.items.some(
      (item) =>
        item.price_source ===
        "service_catalog",
    );

  const hasUnresolvedItems =
    invoice.items.some(
      (item) =>
        item.resolution_status ===
          "AMBIGUOUS" ||
        item.resolution_status ===
          "MISSING",
    );

  return (
    <div className="space-y-6">
      {/* HEADER */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <Link
            href="/invoices"
            className="text-sm text-ink/50 transition hover:text-ink"
          >
            ← Invoices
          </Link>

          <h1 className="mt-2 font-serif text-4xl">
            {invoice.invoice_number}
          </h1>

          <p className="mt-1 text-ink/60">
            {invoice.customer.name}
          </p>
        </div>

        <StatusBadge
          value={invoice.status}
        />
      </div>

      {error && (
        <div className="rounded-2xl bg-rose-50 p-3 text-sm text-rose-800">
          {error}
        </div>
      )}

      {/* WORKFLOW SUMMARY */}
      <section className="rounded-3xl bg-ink p-6 text-white shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-xs font-medium uppercase tracking-[0.18em] text-white/50">
              Invoice workflow
            </p>

            <h2 className="mt-1 font-serif text-2xl">
              From request to approved invoice
            </h2>

            <p className="mt-2 max-w-3xl text-sm leading-6 text-white/65">
              Customer information and requested services
              are extracted from the original message,
              prices are matched to your service catalog,
              and the invoice is reviewed before export.
            </p>
          </div>

          <div className="rounded-2xl bg-white/10 px-4 py-3 text-sm">
            <p className="text-white/50">
              Current stage
            </p>

            <p className="mt-1 font-medium">
              {isApproved
                ? "Approved"
                : hasUnresolvedItems
                  ? "Review required"
                  : "Ready for approval"}
            </p>
          </div>
        </div>

        <div className="mt-6 grid gap-2 sm:grid-cols-2 lg:grid-cols-6">
          <PipelineStep
            number="01"
            title="Customer Request"
            description="Original message"
          />

          <PipelineStep
            number="02"
            title="Information"
            description="Details extracted"
          />

          <PipelineStep
            number="03"
            title="Service Matching"
            description="Services identified"
          />

          <PipelineStep
            number="04"
            title="Price Verification"
            description="Catalog prices"
          />

          <PipelineStep
            number="05"
            title="Invoice Totals"
            description="Amounts calculated"
          />

          <PipelineStep
            number="06"
            title="Approval"
            description={
              isApproved
                ? "Completed"
                : "Pending review"
            }
          />
        </div>
      </section>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="space-y-4 lg:col-span-2">
          {/* LINE ITEMS */}
          <section className="rounded-3xl bg-white p-6 shadow-sm">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <h2 className="font-serif text-2xl">
                  Line items
                </h2>

                <p className="mt-1 text-sm text-ink/50">
                  Review each requested service,
                  quantity, price, and total.
                </p>
              </div>

              <SourceBadge
                label="From customer request"
                detail="Services & quantities"
                tone="ai"
              />
            </div>

            <div className="mt-4 overflow-x-auto">
              <table className="w-full min-w-[700px] text-sm">
                <thead>
                  <tr className="text-left text-ink/50">
                    <th className="py-2">
                      Service
                    </th>

                    <th>Qty</th>

                    <th>Unit price</th>

                    <th className="text-right">
                      Total
                    </th>
                  </tr>
                </thead>

                <tbody>
                  {invoice.items.map(
                    (item) => {
                      const isResolving =
                        resolvingItemId ===
                        item.id;

                      const isSelected =
                        selectedServiceId !==
                          null &&
                        item.candidate_services.some(
                          (candidate) =>
                            candidate.service_id ===
                            selectedServiceId,
                        );

                      const isUnresolved =
                        item.resolution_status ===
                          "AMBIGUOUS" ||
                        item.resolution_status ===
                          "MISSING";

                      return (
                        <tr
                          key={item.id}
                          className={`border-t align-top transition-all duration-300 ${
                            isResolving
                              ? "bg-emerald-50/40"
                              : ""
                          }`}
                        >
                          <td className="py-4 pr-4">
                            <p className="font-medium">
                              {item.service_name_snapshot ||
                                item.requested_service}
                            </p>

                            {item.requested_service !==
                              item.service_name_snapshot &&
                              item.service_name_snapshot && (
                                <p className="mt-1 text-xs text-ink/40">
                                  Requested as:{" "}
                                  {
                                    item.requested_service
                                  }
                                </p>
                              )}

                            <div className="mt-2 flex flex-wrap gap-2">
                              <StatusBadge
                                value={
                                  item.resolution_status
                                }
                              />

                              <SourceBadge
                                label="Customer request"
                                detail="Service"
                                tone="ai"
                              />
                            </div>

                            {/* RESOLVING */}
                            {isResolving && (
                              <div className="mt-3 flex items-center gap-2 rounded-xl bg-emerald-50 px-3 py-3 text-xs text-emerald-800">
                                <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-emerald-200 border-t-emerald-700" />

                                <span>
                                  Confirming selected service…
                                </span>
                              </div>
                            )}

                            {/* UNRESOLVED WARNING */}
                            {isUnresolved &&
                              !isResolving && (
                                <div className="mt-3 rounded-xl bg-amber-50 p-3 text-xs text-amber-900">
                                  <p className="font-medium">
                                    {item.resolution_status ===
                                    "AMBIGUOUS"
                                      ? "Choose a service"
                                      : "Service not found"}
                                  </p>

                                  <p className="mt-1 leading-5">
                                    {item.resolution_status ===
                                    "AMBIGUOUS"
                                      ? "Select the service that best matches the customer's request."
                                      : "This service is not available in the current catalog and needs review."}
                                  </p>
                                </div>
                              )}

                            {/* CANDIDATE SERVICES */}
                            {item.candidate_services
                              .length > 0 &&
                              !isResolving && (
                                <div className="mt-3 space-y-2">
                                  <p className="text-xs font-medium text-ink/50">
                                    Available services
                                  </p>

                                  <div className="flex flex-col gap-2">
                                    {item.candidate_services.map(
                                      (
                                        candidate,
                                      ) => {
                                        const candidateSelected =
                                          selectedServiceId ===
                                          candidate.service_id;

                                        return (
                                          <button
                                            key={
                                              candidate.service_id
                                            }
                                            type="button"
                                            disabled={
                                              resolvingItemId !==
                                              null ||
                                              isApproved
                                            }
                                            onClick={() =>
                                              resolve(
                                                item.id,
                                                candidate.service_id,
                                              )
                                            }
                                            className={`flex items-center justify-between rounded-xl border px-3 py-2 text-left text-xs transition ${
                                              candidateSelected
                                                ? "border-emerald-300 bg-emerald-50 text-emerald-900"
                                                : "border-amber-200 bg-amber-50 hover:bg-amber-100"
                                            } disabled:cursor-not-allowed disabled:opacity-50`}
                                          >
                                            <span className="flex items-center gap-2 font-medium">
                                              {candidateSelected && (
                                                <span className="text-emerald-700">
                                                  ✓
                                                </span>
                                              )}

                                              {
                                                candidate.name
                                              }
                                            </span>

                                            <span className="ml-3 whitespace-nowrap">
                                              {inr(
                                                candidate.unit_price,
                                                candidate.currency,
                                              )}
                                            </span>
                                          </button>
                                        );
                                      },
                                    )}
                                  </div>
                                </div>
                              )}

                            {/* VERIFIED PRICE */}
                            {item.price_source ===
                              "service_catalog" && (
                              <div className="mt-2 flex flex-wrap gap-2">
                                <SourceBadge
                                  label="Price verified"
                                  detail="Service catalog"
                                  tone="catalog"
                                />
                              </div>
                            )}
                          </td>

                          <td className="py-4">
                            <p>
                              {item.quantity}
                            </p>

                            <p className="mt-1 text-[11px] text-ink/40">
                              Quantity
                            </p>
                          </td>

                          <td className="py-4">
                            {item.unit_price ? (
                              <>
                                <p className="whitespace-nowrap">
                                  {inr(
                                    item.unit_price,
                                    invoice.currency,
                                  )}
                                </p>

                                {item.price_source ===
                                  "service_catalog" && (
                                  <p className="mt-1 text-[11px] font-medium text-emerald-700">
                                    Price verified
                                  </p>
                                )}
                              </>
                            ) : (
                              <div>
                                <p className="text-amber-700">
                                  Unavailable
                                </p>

                                <p className="mt-1 text-[11px] text-ink/40">
                                  Review required
                                </p>
                              </div>
                            )}
                          </td>

                          <td className="py-4 text-right">
                            {item.line_total ? (
                              <p className="whitespace-nowrap font-medium">
                                {inr(
                                  item.line_total,
                                  invoice.currency,
                                )}
                              </p>
                            ) : (
                              "—"
                            )}
                          </td>
                        </tr>
                      );
                    },
                  )}
                </tbody>
              </table>
            </div>

            {/* TOTALS */}
            <div className="mt-6 border-t pt-5 text-right">
              <p>
                <span className="text-ink/60">
                  Subtotal{" "}
                </span>
                {inr(
                  invoice.subtotal,
                  invoice.currency,
                )}
              </p>

              <p>
                <span className="text-ink/60">
                  Tax ({invoice.tax_rate}%)
                </span>{" "}
                {inr(
                  invoice.tax_amount,
                  invoice.currency,
                )}
              </p>

              <p className="mt-1 font-serif text-3xl">
                {inr(
                  invoice.total,
                  invoice.currency,
                )}
              </p>

              <div className="mt-3 flex flex-wrap justify-end gap-2">
                {hasCatalogPrices && (
                  <SourceBadge
                    label="Prices verified"
                    detail="Service catalog"
                    tone="catalog"
                  />
                )}

                <SourceBadge
                  label="Totals calculated"
                  detail="Invoice calculation"
                  tone="calculation"
                />
              </div>

              <p className="mt-2 text-xs text-ink/50">
                Prices are taken from your service catalog and
                invoice amounts are calculated automatically.
              </p>
            </div>
          </section>

          {/* INFORMATION SOURCES */}
          <section className="rounded-3xl bg-white p-6 shadow-sm">
            <div>
              <h2 className="font-serif text-2xl">
                Information sources
              </h2>

              <p className="mt-1 text-sm text-ink/50">
                See where the key invoice information comes from.
              </p>
            </div>

            <div className="mt-4 grid gap-3 sm:grid-cols-3">
              <ProvenanceCard
                icon="🧠"
                title="Customer message"
                description="Customer details, requested services, quantities, and notes are identified from the original request."
              />

              <ProvenanceCard
                icon="🗂️"
                title="Service catalog"
                description="Matching services and their prices come from the services available in your catalog."
              />

              <ProvenanceCard
                icon="✓"
                title="Invoice calculation"
                description="Line totals, tax, subtotal, and final amount are calculated automatically from the selected services and quantities."
              />
            </div>
          </section>
        </div>

        <div className="space-y-4">
          {/* CUSTOMER */}
          <section className="rounded-3xl bg-white p-6 shadow-sm">
            <div className="flex items-start justify-between gap-3">
              <div>
                <h2 className="font-serif text-2xl">
                  Customer
                </h2>

                <p className="mt-1 text-xs text-ink/50">
                  Customer information
                </p>
              </div>

              <SourceBadge
                label="From request"
                detail="Customer data"
                tone="ai"
              />
            </div>

            <div className="mt-4 space-y-1">
              <p className="font-medium">
                {invoice.customer.name}
              </p>

              <p className="break-all text-sm">
                {invoice.customer.email}
              </p>

              {invoice.customer.phone && (
                <p className="text-sm">
                  {invoice.customer.phone}
                </p>
              )}

              {invoice.customer.company && (
                <p className="text-sm">
                  {invoice.customer.company}
                </p>
              )}
            </div>

            {invoice.notes && (
              <div className="mt-4 rounded-2xl bg-ivory p-3">
                <p className="text-xs font-medium text-ink/50">
                  Notes
                </p>

                <p className="mt-1 text-sm text-ink/60">
                  {invoice.notes}
                </p>
              </div>
            )}
          </section>

          {/* APPROVAL */}
          <section
            className={`rounded-3xl bg-white p-6 shadow-sm transition-all duration-300 ${
              loading
                ? "opacity-70"
                : ""
            }`}
          >
            <div className="flex items-start justify-between gap-3">
              <div>
                <h2 className="font-serif text-2xl">
                  Approval
                </h2>

                <p className="mt-1 text-sm text-ink/50">
                  Review the invoice before approving it.
                </p>
              </div>

              {isApproved && (
                <SourceBadge
                  label="Approved"
                  detail="Review complete"
                  tone="human"
                />
              )}
            </div>

            {invoice.approval_blockers
              .length > 0 && (
              <div className="mt-4 rounded-2xl bg-amber-50 p-4">
                <p className="text-sm font-medium text-amber-900">
                  Review required
                </p>

                <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-amber-800">
                  {invoice.approval_blockers.map(
                    (issue) => (
                      <li key={issue}>
                        {issue}
                      </li>
                    ),
                  )}
                </ul>
              </div>
            )}

            {invoice.approval_blockers
              .length === 0 &&
              !isApproved && (
                <div className="mt-4 rounded-2xl bg-emerald-50 p-4">
                  <p className="font-medium text-emerald-800">
                    Ready for approval
                  </p>

                  <p className="mt-1 text-sm text-emerald-700">
                    All required details and service selections
                    have been confirmed.
                  </p>
                </div>
              )}

            <button
              type="button"
              className="mt-4 flex w-full items-center justify-center gap-2 rounded-full bg-ink py-3 text-white transition-all duration-200 hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
              disabled={
                loading ||
                invoice.approval_blockers
                  .length > 0 ||
                invoice.status ===
                  "APPROVED" ||
                invoice.status ===
                  "EXPORTED"
              }
              onClick={approve}
            >
              {loading ? (
                <>
                  <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />

                  <span>
                    Approving invoice…
                  </span>
                </>
              ) : (
                "Approve Invoice"
              )}
            </button>

            {(invoice.status ===
              "APPROVED" ||
              invoice.status ===
                "EXPORTED") && (
              <button
                type="button"
                className="mt-3 flex w-full items-center justify-center rounded-full bg-gold py-3 text-center text-ink transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
                onClick={downloadPdf}
                disabled={downloading}
              >
                {downloading
                  ? "Preparing PDF…"
                  : "Download PDF"}
              </button>
            )}

            {isApproved && (
              <p className="mt-3 text-center text-xs text-emerald-700">
                ✓ Invoice approved and ready to export
              </p>
            )}
          </section>

          {/* AUDIT HISTORY */}
          <section className="rounded-3xl bg-white p-6 shadow-sm">
            <div>
              <h2 className="font-serif text-2xl">
                Activity
              </h2>

              <p className="mt-1 text-sm text-ink/50">
                A record of important invoice actions.
              </p>
            </div>

            <ol className="mt-4 space-y-3">
              {invoice.audit_logs.map(
                (log) => (
                  <li
                    key={log.id}
                    className="border-l-2 border-gold pl-3"
                  >
                    <p className="text-xs text-ink/50">
                      {new Date(
                        log.created_at,
                      ).toLocaleTimeString(
                        [],
                        {
                          hour: "2-digit",
                          minute: "2-digit",
                        },
                      )}
                    </p>

                    <p>
                      {EVENT_LABEL[
                        log.event_type
                      ] ||
                        log.event_type}
                    </p>
                  </li>
                ),
              )}
            </ol>
          </section>
        </div>
      </div>
    </div>
  );
}

function PipelineStep({
  number,
  title,
  description,
}: {
  number: string;
  title: string;
  description: string;
}) {
  return (
    <div className="rounded-2xl bg-white/10 p-3">
      <p className="text-[10px] font-medium tracking-widest text-white/40">
        {number}
      </p>

      <p className="mt-1 text-sm font-medium">
        {title}
      </p>

      <p className="mt-1 text-xs text-white/50">
        {description}
      </p>
    </div>
  );
}

function SourceBadge({
  label,
  detail,
  tone,
}: {
  label: string;
  detail?: string;
  tone:
    | "ai"
    | "catalog"
    | "calculation"
    | "human";
}) {
  const toneClasses = {
    ai: "bg-violet-50 text-violet-800",
    catalog: "bg-emerald-50 text-emerald-800",
    calculation: "bg-blue-50 text-blue-800",
    human: "bg-amber-50 text-amber-900",
  };

  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-1 text-[11px] font-medium ${toneClasses[tone]}`}
    >
      {label}

      {detail && (
        <span className="ml-1 opacity-60">
          · {detail}
        </span>
      )}
    </span>
  );
}

function ProvenanceCard({
  icon,
  title,
  description,
}: {
  icon: string;
  title: string;
  description: string;
}) {
  return (
    <div className="rounded-2xl border border-ink/10 p-4">
      <div className="text-xl">
        {icon}
      </div>

      <h3 className="mt-2 font-medium">
        {title}
      </h3>

      <p className="mt-1 text-xs leading-5 text-ink/55">
        {description}
      </p>
    </div>
  );
}