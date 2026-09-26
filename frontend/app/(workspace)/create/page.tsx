"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import {
  api,
  ApiError,
  downloadInvoicePdf,
  inr,
} from "@/lib/api";
import { useToast } from "@/components/Toast";
import { StatusBadge } from "@/components/StatusBadge";
import type {
  Extraction,
  Invoice,
  ItemMatch,
} from "@/types";

const STEPS = [
  "Customer requirement",
  "AI extraction",
  "Service verification",
  "Invoice editor",
  "Review",
  "Approval",
];

const PLACEHOLDER =
  "Hi, I'm Rahul. I need an e-commerce website and SEO for my new business. My email is rahul@example.com.";

export default function CreatePage() {
  const toast = useToast();
  const router = useRouter();

  const [step, setStep] = useState(1);
  const [message, setMessage] = useState(PLACEHOLDER);
  const [loading, setLoading] = useState(false);
  const [downloadingPdf, setDownloadingPdf] =
    useState(false);

  const [resolvingChoice, setResolvingChoice] =
    useState<number | null>(null);

  const [extraction, setExtraction] =
    useState<Extraction | null>(null);

  const [matches, setMatches] =
    useState<ItemMatch[]>([]);

  const [taxRate, setTaxRate] = useState("");

  const [invoice, setInvoice] =
    useState<Invoice | null>(null);

  const [error, setError] =
    useState<string | null>(null);

  /*
   * Load the workspace tax setting instead of
   * hardcoding a tax rate.
   */
  useEffect(() => {
    async function loadSettings() {
      try {
        const settings = await api.settings();

        setTaxRate(
          String(settings.default_tax_rate),
        );
      } catch (err) {
        setError(
          err instanceof ApiError
            ? err.message
            : "Could not load workspace settings.",
        );
      }
    }

    loadSettings();
  }, []);

  const resolvedSelections = useMemo(() => {
    const map: Record<number, string> = {};

    matches.forEach((match, index) => {
      if (match.matched_service) {
        map[index] =
          match.matched_service.service_id;
      }
    });

    return map;
  }, [matches]);

  const [choices, setChoices] =
    useState<Record<number, string>>({});

  const hasUnresolvedServices = useMemo(() => {
    return matches.some(
      (match, index) =>
        match.status === "MISSING" ||
        (match.status === "AMBIGUOUS" &&
          !choices[index]),
    );
  }, [matches, choices]);

  async function extract() {
    setLoading(true);
    setError(null);

    try {
      const result = await api.extract(message);

      setExtraction(result.extraction);
      setMatches(result.matches);
      setChoices({});
      setStep(2);

      toast.push("Information extracted");
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Extraction failed",
      );
    } finally {
      setLoading(false);
    }
  }

  async function rematchFromExtraction(
    next: Extraction,
  ) {
    const result = await api.match(
      next.requested_items,
    );

    setMatches(result);
    setChoices({});
  }

  async function selectAmbiguousService(
    index: number,
    serviceId: string,
  ) {
    setResolvingChoice(index);
    setError(null);

    setChoices((current) => ({
      ...current,
      [index]: serviceId,
    }));

    await new Promise((resolve) =>
      setTimeout(resolve, 250),
    );

    setResolvingChoice(null);
  }

  async function persistInvoice() {
    if (!extraction) return;

    if (!extraction.customer.name?.trim()) {
      setError(
        "Add a customer name before creating the invoice.",
      );
      setStep(2);
      return;
    }

    if (hasUnresolvedServices) {
      setError(
        "Resolve all missing or ambiguous services before continuing to the invoice.",
      );
      setStep(3);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const created =
        await api.createInvoice({
          customer: extraction.customer,
          notes: extraction.notes,
          tax_rate: taxRate,
          source_message: message,
          items:
            extraction.requested_items.map(
              (item, index) => ({
                requested_service:
                  item.requested_service,
                quantity:
                  item.quantity || "1",
                notes: item.notes,
                service_id:
                  choices[index] ||
                  resolvedSelections[index] ||
                  null,
              }),
            ),
        });

      setInvoice(created);
      setStep(4);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Could not create invoice",
      );
    } finally {
      setLoading(false);
    }
  }

  async function saveEdits(
    advance?: number,
  ) {
    if (!invoice) return;

    setLoading(true);
    setError(null);

    try {
      const updated =
        await api.updateInvoice(
          invoice.id,
          {
            customer: invoice.customer,
            notes: invoice.notes,
            tax_rate: invoice.tax_rate,
            items: invoice.items.map(
              (item) => ({
                requested_service:
                  item.requested_service,
                quantity: item.quantity,
                notes: item.notes,
                service_id: item.service_id,
              }),
            ),
          },
        );

      setInvoice(updated);

      toast.push(
        "Invoice updated successfully",
      );

      if (advance) {
        setStep(advance);
      }
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Save failed",
      );
    } finally {
      setLoading(false);
    }
  }

  async function approve() {
    if (!invoice) return;

    setLoading(true);
    setError(null);

    try {
      const updated =
        await api.approve(invoice.id);

      setInvoice(updated);
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

  async function handleDownloadPdf() {
    if (!invoice) return;

    setDownloadingPdf(true);
    setError(null);

    try {
      await downloadInvoicePdf(
        invoice.id,
      );

      toast.push("Invoice PDF downloaded");
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Failed to download invoice PDF.",
      );
    } finally {
      setDownloadingPdf(false);
    }
  }

  return (
    <div className="space-y-8">
      <div>
        <p className="text-sm uppercase tracking-[0.2em] text-gold">
          Workflow
        </p>

        <h1 className="mt-2 font-serif text-4xl">
          Create invoice
        </h1>

        <p className="mt-2 text-ink/60">
          AI extracts. Services are verified. You approve.
        </p>
      </div>

      {invoice && (
        <div className="flex flex-wrap gap-2 text-sm">
          <span className="rounded-full bg-emerald-100 px-3 py-1 text-emerald-800">
            AI Extracted ✓
          </span>

          <span
            className={
              invoice.items.every(
                (item) =>
                  item.price_source ===
                  "service_catalog",
              )
                ? "rounded-full bg-emerald-100 px-3 py-1 text-emerald-800"
                : "rounded-full bg-amber-100 px-3 py-1 text-amber-800"
            }
          >
            {invoice.items.every(
              (item) =>
                item.price_source ===
                "service_catalog",
            )
              ? "Price Verified ✓"
              : "Needs Review ⚠"}
          </span>

          {(invoice.status === "APPROVED" ||
            invoice.status === "EXPORTED") && (
            <span className="rounded-full bg-emerald-100 px-3 py-1 text-emerald-800">
              Approved ✓
            </span>
          )}

          {invoice.status === "EXPORTED" && (
            <span className="rounded-full bg-indigo-100 px-3 py-1 text-indigo-800">
              Exported ✓
            </span>
          )}
        </div>
      )}

      <div className="grid gap-2 md:grid-cols-6">
        {STEPS.map((label, index) => (
          <div
            key={label}
            className={`rounded-2xl px-3 py-3 text-sm ${
              step === index + 1
                ? "bg-ink text-white"
                : step > index + 1
                  ? "bg-emerald-50 text-emerald-900"
                  : "bg-white"
            }`}
          >
            <p className="text-xs opacity-70">
              Step {index + 1}
            </p>

            <p className="font-medium">
              {label}
            </p>
          </div>
        ))}
      </div>

      {error && (
        <div className="rounded-2xl bg-rose-50 px-4 py-3 text-rose-800">
          {error}
        </div>
      )}

      {/* STEP 1 */}
      {step === 1 && (
        <section className="rounded-3xl bg-white p-6 shadow-sm">
          <h2 className="font-serif text-2xl">
            Customer requirement
          </h2>

          <textarea
            className="mt-4 min-h-48 w-full rounded-2xl border border-ink/10 p-4"
            value={message}
            onChange={(event) =>
              setMessage(event.target.value)
            }
            placeholder={PLACEHOLDER}
          />

          <button
            onClick={extract}
            disabled={
              loading || !message.trim()
            }
            className="mt-4 rounded-full bg-ink px-5 py-3 text-white disabled:opacity-50"
          >
            {loading
              ? "Extracting…"
              : "Extract with AI"}
          </button>
        </section>
      )}

      {/* STEP 2 */}
      {step === 2 && extraction && (
        <section className="space-y-4 rounded-3xl bg-white p-6 shadow-sm">
          <div className="flex items-center justify-between">
            <h2 className="font-serif text-2xl">
              AI extraction
            </h2>

            <p className="text-emerald-700">
              ✓ Information extracted
            </p>
          </div>

          {extraction.missing_information
            .length > 0 && (
            <p className="rounded-xl bg-amber-50 px-4 py-3 text-amber-800">
              ⚠ Missing information:{" "}
              {extraction.missing_information.join(
                ", ",
              )}
            </p>
          )}

          <div className="grid gap-4 md:grid-cols-2">
            {(
              [
                "name",
                "email",
                "phone",
                "company",
              ] as const
            ).map((field) => (
              <label
                key={field}
                className="text-sm"
              >
                {field}

                <input
                  className="mt-1 w-full rounded-xl border border-ink/10 px-3 py-2"
                  value={
                    extraction.customer[
                      field
                    ] || ""
                  }
                  onChange={(event) =>
                    setExtraction({
                      ...extraction,
                      customer: {
                        ...extraction.customer,
                        [field]:
                          event.target.value,
                      },
                    })
                  }
                />
              </label>
            ))}
          </div>

          <div className="space-y-3">
            {extraction.requested_items.map(
              (item, index) => (
                <div
                  key={index}
                  className="grid gap-3 rounded-2xl bg-ivory p-4 md:grid-cols-3"
                >
                  <input
                    className="rounded-xl border border-ink/10 px-3 py-2"
                    value={
                      item.requested_service
                    }
                    onChange={(event) => {
                      const requested_items =
                        extraction.requested_items.map(
                          (
                            row,
                            rowIndex,
                          ) =>
                            rowIndex === index
                              ? {
                                  ...row,
                                  requested_service:
                                    event.target
                                      .value,
                                }
                              : row,
                        );

                      setExtraction({
                        ...extraction,
                        requested_items,
                      });
                    }}
                  />

                  <input
                    className="rounded-xl border border-ink/10 px-3 py-2"
                    value={
                      item.quantity || ""
                    }
                    placeholder="Quantity"
                    onChange={(event) => {
                      const requested_items =
                        extraction.requested_items.map(
                          (
                            row,
                            rowIndex,
                          ) =>
                            rowIndex === index
                              ? {
                                  ...row,
                                  quantity:
                                    event.target
                                      .value,
                                }
                              : row,
                        );

                      setExtraction({
                        ...extraction,
                        requested_items,
                      });
                    }}
                  />

                  <input
                    className="rounded-xl border border-ink/10 px-3 py-2"
                    value={
                      item.notes || ""
                    }
                    placeholder="Notes"
                    onChange={(event) => {
                      const requested_items =
                        extraction.requested_items.map(
                          (
                            row,
                            rowIndex,
                          ) =>
                            rowIndex === index
                              ? {
                                  ...row,
                                  notes:
                                    event.target
                                      .value,
                                }
                              : row,
                        );

                      setExtraction({
                        ...extraction,
                        requested_items,
                      });
                    }}
                  />
                </div>
              ),
            )}
          </div>

          <div className="flex gap-3">
            <button
              className="rounded-full border px-4 py-2"
              onClick={() => setStep(1)}
            >
              Back
            </button>

            <button
              className="rounded-full bg-ink px-4 py-2 text-white disabled:opacity-50"
              disabled={loading}
              onClick={async () => {
                if (extraction) {
                  setLoading(true);

                  try {
                    await rematchFromExtraction(
                      extraction,
                    );

                    setStep(3);
                  } catch (err) {
                    setError(
                      err instanceof ApiError
                        ? err.message
                        : "Could not verify services.",
                    );
                  } finally {
                    setLoading(false);
                  }
                }
              }}
            >
              {loading
                ? "Checking catalog…"
                : "Verify against catalog"}
            </button>
          </div>
        </section>
      )}

      {/* STEP 3 */}
      {step === 3 && (
        <section className="space-y-4 rounded-3xl bg-white p-6 shadow-sm">
          <div>
            <h2 className="font-serif text-2xl">
              Service verification
            </h2>

            <p className="mt-1 text-sm text-ink/50">
              Confirm that each requested service matches the intended catalog item.
            </p>
          </div>

          {matches.map(
            (match, index) => {
              const selectedServiceId =
                choices[index];

              const selectedCandidate =
                match.candidate_services.find(
                  (candidate) =>
                    candidate.service_id ===
                    selectedServiceId,
                );

              const isResolving =
                resolvingChoice === index;

              return (
                <div
                  key={index}
                  className={`rounded-2xl border p-4 transition-all duration-300 ${
                    isResolving
                      ? "border-emerald-200 bg-emerald-50/40 opacity-80"
                      : "border-ink/10"
                  }`}
                >
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <p className="text-sm text-ink/50">
                        Requested
                      </p>

                      <p className="font-medium">
                        {
                          match.requested_service
                        }
                      </p>
                    </div>

                    {selectedServiceId ? (
                      <span className="inline-flex items-center rounded-full bg-emerald-100 px-2.5 py-1 text-xs font-medium text-emerald-800">
                        ✓ Selected
                      </span>
                    ) : (
                      <StatusBadge
                        value={match.status}
                      />
                    )}
                  </div>

                  {match.status ===
                    "MATCHED" &&
                    match.matched_service && (
                      <p className="mt-3 text-emerald-700">
                        ✓{" "}
                        {
                          match
                            .matched_service
                            .name
                        }{" "}
                        ·{" "}
                        {inr(
                          match
                            .matched_service
                            .unit_price,
                          match
                            .matched_service
                            .currency,
                        )}{" "}
                        · Price verified from
                        service catalog
                      </p>
                    )}

                  {match.status ===
                    "AMBIGUOUS" &&
                    !selectedServiceId && (
                      <div className="mt-3 space-y-2">
                        <p className="text-amber-700">
                          ⚠ Choose the matching service
                        </p>

                        {match.candidate_services.map(
                          (candidate) => (
                            <label
                              key={
                                candidate.service_id
                              }
                              className="flex cursor-pointer items-center gap-3 rounded-xl bg-amber-50 px-3 py-2 transition hover:bg-amber-100"
                            >
                              <input
                                type="radio"
                                name={`choice-${index}`}
                                checked={
                                  choices[
                                    index
                                  ] ===
                                  candidate.service_id
                                }
                                onChange={() =>
                                  selectAmbiguousService(
                                    index,
                                    candidate.service_id,
                                  )
                                }
                              />

                              <span>
                                {
                                  candidate.name
                                }{" "}
                                —{" "}
                                {inr(
                                  candidate.unit_price,
                                  candidate.currency,
                                )}
                              </span>
                            </label>
                          ),
                        )}
                      </div>
                    )}

                  {isResolving && (
                    <div className="mt-3 flex items-center gap-2 rounded-xl bg-white px-3 py-3 text-sm text-ink/60">
                      <span className="h-4 w-4 animate-spin rounded-full border-2 border-ink/10 border-t-ink" />

                      <span>
                        Confirming selection…
                      </span>
                    </div>
                  )}

                  {match.status ===
                    "AMBIGUOUS" &&
                    selectedServiceId &&
                    !isResolving &&
                    selectedCandidate && (
                      <div className="mt-3 rounded-xl bg-emerald-50 p-3">
                        <p className="font-medium text-emerald-800">
                          ✓ Service selected
                        </p>

                        <p className="mt-1 text-sm text-emerald-700">
                          {
                            selectedCandidate.name
                          }{" "}
                          ·{" "}
                          {inr(
                            selectedCandidate.unit_price,
                            selectedCandidate.currency,
                          )}
                        </p>

                        <p className="mt-1 text-xs text-emerald-700">
                          Price verified from service catalog.
                        </p>
                      </div>
                    )}

                  {match.status ===
                    "MISSING" && (
                    <p className="mt-3 text-rose-700">
                      ✕ Service not found in catalog.
                      A matching service is required before continuing.
                    </p>
                  )}
                </div>
              );
            },
          )}

          {hasUnresolvedServices && (
            <div className="rounded-2xl bg-amber-50 p-4 text-amber-900">
              <p className="font-medium">
                Invoice creation is blocked.
              </p>

              <p className="mt-1 text-sm">
                Resolve every missing or ambiguous service before continuing.
              </p>
            </div>
          )}

          <div className="flex gap-3">
            <button
              className="rounded-full border px-4 py-2"
              onClick={() => setStep(2)}
            >
              Back
            </button>

            <button
              className="rounded-full bg-ink px-4 py-2 text-white disabled:cursor-not-allowed disabled:opacity-40"
              onClick={persistInvoice}
              disabled={
                loading ||
                hasUnresolvedServices ||
                !taxRate
              }
            >
              {loading
                ? "Creating invoice…"
                : hasUnresolvedServices
                  ? "Resolve service issues"
                  : "Continue to invoice"}
            </button>
          </div>
        </section>
      )}

      {/* STEPS 4-6 */}
      {step >= 4 && invoice && (
        <section
          className={`space-y-4 rounded-3xl bg-white p-6 shadow-sm transition-opacity duration-300 ${
            loading ? "opacity-70" : ""
          }`}
        >
          {/* STEP 4 */}
          {step === 4 && (
            <>
              <div>
                <p className="text-sm uppercase tracking-[0.18em] text-gold">
                  Step 4
                </p>

                <h2 className="mt-1 font-serif text-2xl">
                  Invoice editor
                </h2>

                <p className="mt-1 text-sm text-ink/50">
                  Review customer information, line items,
                  tax, and notes before moving to final review.
                </p>
              </div>

              {/* CUSTOMER DETAILS */}
              <div className="space-y-4">
                <div className="border-b border-ink/10 pb-3">
                  <h3 className="font-serif text-xl">
                    Customer details
                  </h3>

                  <p className="mt-1 text-sm text-ink/50">
                    Confirm who this invoice is being issued to.
                  </p>
                </div>

                <div className="grid gap-4 md:grid-cols-2">
                  <label className="block text-sm font-medium text-ink/70">
                    Customer name

                    <input
                      className="mt-2 w-full rounded-xl border border-ink/10 px-3 py-3 font-normal outline-none transition focus:border-ink/40"
                      value={
                        invoice.customer.name
                      }
                      onChange={(event) =>
                        setInvoice({
                          ...invoice,
                          customer: {
                            ...invoice.customer,
                            name: event.target
                              .value,
                          },
                        })
                      }
                    />
                  </label>

                  <label className="block text-sm font-medium text-ink/70">
                    Email address

                    <input
                      type="email"
                      className="mt-2 w-full rounded-xl border border-ink/10 px-3 py-3 font-normal outline-none transition focus:border-ink/40"
                      value={
                        invoice.customer.email ||
                        ""
                      }
                      onChange={(event) =>
                        setInvoice({
                          ...invoice,
                          customer: {
                            ...invoice.customer,
                            email:
                              event.target
                                .value,
                          },
                        })
                      }
                    />
                  </label>

                  <label className="block text-sm font-medium text-ink/70">
                    Phone number

                    <input
                      type="tel"
                      className="mt-2 w-full rounded-xl border border-ink/10 px-3 py-3 font-normal outline-none transition focus:border-ink/40"
                      value={
                        invoice.customer.phone ||
                        ""
                      }
                      onChange={(event) =>
                        setInvoice({
                          ...invoice,
                          customer: {
                            ...invoice.customer,
                            phone:
                              event.target
                                .value,
                          },
                        })
                      }
                    />
                  </label>

                  <label className="block text-sm font-medium text-ink/70">
                    Company

                    <input
                      className="mt-2 w-full rounded-xl border border-ink/10 px-3 py-3 font-normal outline-none transition focus:border-ink/40"
                      value={
                        invoice.customer.company ||
                        ""
                      }
                      onChange={(event) =>
                        setInvoice({
                          ...invoice,
                          customer: {
                            ...invoice.customer,
                            company:
                              event.target
                                .value,
                          },
                        })
                      }
                    />
                  </label>
                </div>
              </div>

              {/* BILLING SETTINGS */}
              <div className="space-y-4 pt-2">
                <div className="border-b border-ink/10 pb-3">
                  <h3 className="font-serif text-xl">
                    Billing settings
                  </h3>

                  <p className="mt-1 text-sm text-ink/50">
                    Set the applicable tax rate for this invoice.
                  </p>
                </div>

                <label className="block max-w-xs text-sm font-medium text-ink/70">
                  Tax rate (%)

                  <input
                    type="number"
                    min="0"
                    step="0.01"
                    className="mt-2 w-full rounded-xl border border-ink/10 px-3 py-3 font-normal outline-none transition focus:border-ink/40"
                    value={
                      invoice.tax_rate
                    }
                    onChange={(event) =>
                      setInvoice({
                        ...invoice,
                        tax_rate:
                          event.target.value,
                      })
                    }
                  />
                </label>
              </div>

              {/* LINE ITEMS */}
              <div className="space-y-4 pt-2">
                <div className="border-b border-ink/10 pb-3">
                  <h3 className="font-serif text-xl">
                    Line items
                  </h3>

                  <p className="mt-1 text-sm text-ink/50">
                    Services and prices are verified against your service catalog.
                  </p>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full min-w-[650px] text-sm">
                    <thead>
                      <tr className="border-b border-ink/10 text-left text-ink/50">
                        <th className="py-3 pr-4 font-medium">
                          Service
                        </th>

                        <th className="py-3 pr-4 font-medium">
                          Quantity
                        </th>

                        <th className="py-3 pr-4 font-medium">
                          Unit price
                        </th>

                        <th className="py-3 text-right font-medium">
                          Line total
                        </th>
                      </tr>
                    </thead>

                    <tbody>
                      {invoice.items.map(
                        (item, index) => (
                          <tr
                            key={item.id}
                            className="border-b border-ink/5 last:border-0"
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
                                    Requested:{" "}
                                    {
                                      item.requested_service
                                    }
                                  </p>
                                )}
                            </td>

                            <td className="py-4 pr-4">
                              <label className="sr-only">
                                Quantity for{" "}
                                {item.service_name_snapshot ||
                                  item.requested_service}
                              </label>

                              <input
                                className="w-24 rounded-lg border border-ink/10 px-3 py-2 outline-none transition focus:border-ink/40"
                                value={
                                  item.quantity
                                }
                                onChange={(
                                  event,
                                ) => {
                                  const items =
                                    invoice.items.map(
                                      (
                                        row,
                                        rowIndex,
                                      ) =>
                                        rowIndex ===
                                        index
                                          ? {
                                              ...row,
                                              quantity:
                                                event
                                                  .target
                                                  .value,
                                            }
                                          : row,
                                    );

                                  setInvoice({
                                    ...invoice,
                                    items,
                                  });
                                }}
                              />
                            </td>

                            <td className="whitespace-nowrap py-4 pr-4">
                              {item.unit_price
                                ? inr(
                                    item.unit_price,
                                    invoice.currency,
                                  )
                                : "—"}
                            </td>

                            <td className="whitespace-nowrap py-4 text-right font-medium">
                              {item.line_total
                                ? inr(
                                    item.line_total,
                                    invoice.currency,
                                  )
                                : "—"}
                            </td>
                          </tr>
                        ),
                      )}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* NOTES */}
              <div className="space-y-3 pt-2">
                <div>
                  <h3 className="font-serif text-xl">
                    Notes
                  </h3>

                  <p className="mt-1 text-sm text-ink/50">
                    Optional notes that will stay attached to the invoice.
                  </p>
                </div>

                <textarea
                  className="min-h-28 w-full rounded-xl border border-ink/10 p-3 outline-none transition focus:border-ink/40"
                  value={
                    invoice.notes || ""
                  }
                  placeholder="Add any customer-facing or internal invoice notes..."
                  onChange={(event) =>
                    setInvoice({
                      ...invoice,
                      notes: event.target
                        .value,
                    })
                  }
                />
              </div>

              {/* TOTALS */}
              <div className="rounded-2xl bg-ivory p-5">
                <div className="ml-auto max-w-sm space-y-2 text-right">
                  <p className="flex justify-between gap-6">
                    <span className="text-ink/60">
                      Subtotal
                    </span>

                    <span className="font-medium">
                      {inr(
                        invoice.subtotal,
                        invoice.currency,
                      )}
                    </span>
                  </p>

                  <p className="flex justify-between gap-6">
                    <span className="text-ink/60">
                      Tax ({invoice.tax_rate}%)
                    </span>

                    <span className="font-medium">
                      {inr(
                        invoice.tax_amount,
                        invoice.currency,
                      )}
                    </span>
                  </p>

                  <div className="my-3 border-t border-ink/10" />

                  <p className="flex justify-between gap-6">
                    <span className="font-serif text-xl">
                      Grand total
                    </span>

                    <span className="font-serif text-2xl">
                      {inr(
                        invoice.total,
                        invoice.currency,
                      )}
                    </span>
                  </p>
                </div>

                <p className="mt-4 text-right text-sm text-emerald-700">
                  ✓ Totals updated using verified service prices.
                </p>
              </div>

              {/* EDITOR ACTIONS */}
              <div className="flex flex-wrap gap-3 pt-2">
                <button
                  className="rounded-full border px-4 py-2 disabled:opacity-50"
                  onClick={() =>
                    saveEdits()
                  }
                  disabled={loading}
                >
                  {loading
                    ? "Recalculating…"
                    : "Recalculate"}
                </button>

                <button
                  className="flex items-center gap-2 rounded-full bg-ink px-4 py-2 text-white disabled:cursor-not-allowed disabled:opacity-50"
                  onClick={() =>
                    saveEdits(5)
                  }
                  disabled={loading}
                >
                  {loading && (
                    <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                  )}

                  {loading
                    ? "Preparing review…"
                    : "Review invoice"}
                </button>
              </div>
            </>
          )}

          {/* STEP 5 */}
          {step === 5 && (
            <>
              <div>
                <p className="text-sm uppercase tracking-[0.18em] text-gold">
                  Step 5
                </p>

                <h2 className="mt-1 font-serif text-2xl">
                  Review
                </h2>
              </div>

              <p className="text-sm text-emerald-700">
                ✓ Services and prices verified
              </p>

              <div className="rounded-2xl bg-ivory p-6">
                <div className="flex justify-between">
                  <div>
                    <p className="text-sm text-ink/50">
                      Bill to
                    </p>

                    <p className="font-medium">
                      {
                        invoice.customer
                          .name
                      }
                    </p>

                    <p>
                      {
                        invoice.customer
                          .email
                      }
                    </p>
                  </div>

                  <div className="text-right">
                    <p className="font-serif text-3xl">
                      {
                        invoice.invoice_number
                      }
                    </p>

                    <p>
                      {new Date(
                        invoice.created_at,
                      ).toLocaleDateString()}
                    </p>
                  </div>
                </div>

                <table className="mt-6 w-full text-sm">
                  <thead>
                    <tr className="text-left">
                      <th>Service</th>
                      <th>Qty</th>
                      <th>Price</th>
                      <th>Total</th>
                    </tr>
                  </thead>

                  <tbody>
                    {invoice.items.map(
                      (item) => (
                        <tr
                          key={item.id}
                          className="border-t"
                        >
                          <td className="py-2">
                            {item.service_name_snapshot ||
                              item.requested_service}
                          </td>

                          <td>
                            {item.quantity}
                          </td>

                          <td>
                            {item.unit_price
                              ? inr(
                                  item.unit_price,
                                  invoice.currency,
                                )
                              : "Unavailable"}
                          </td>

                          <td>
                            {item.line_total
                              ? inr(
                                  item.line_total,
                                  invoice.currency,
                                )
                              : "—"}
                          </td>
                        </tr>
                      ),
                    )}
                  </tbody>
                </table>

                <div className="mt-6 text-right">
                  <p>
                    Subtotal{" "}
                    {inr(
                      invoice.subtotal,
                      invoice.currency,
                    )}
                  </p>

                  <p>
                    Tax ({invoice.tax_rate}%){" "}
                    {inr(
                      invoice.tax_amount,
                      invoice.currency,
                    )}
                  </p>

                  <p className="font-serif text-3xl">
                    Grand total{" "}
                    {inr(
                      invoice.total,
                      invoice.currency,
                    )}
                  </p>
                </div>
              </div>

              <div className="flex gap-3">
                <button
                  className="rounded-full border px-4 py-2"
                  onClick={() =>
                    setStep(4)
                  }
                >
                  Back
                </button>

                <button
                  className="rounded-full bg-ink px-4 py-2 text-white disabled:cursor-not-allowed disabled:opacity-40"
                  onClick={() =>
                    setStep(6)
                  }
                  disabled={
                    invoice
                      .approval_blockers
                      .length > 0
                  }
                >
                  {invoice
                    .approval_blockers
                    .length > 0
                    ? "Resolve issues before approval"
                    : "Continue to approval"}
                </button>
              </div>
            </>
          )}

          {/* STEP 6 */}
          {step === 6 && (
            <>
              <div>
                <p className="text-sm uppercase tracking-[0.18em] text-gold">
                  Step 6
                </p>

                <h2 className="mt-1 font-serif text-2xl">
                  Approval
                </h2>
              </div>

              {invoice.approval_blockers
                .length > 0 ? (
                <div className="rounded-2xl bg-amber-50 p-4 text-amber-900">
                  <p className="font-medium">
                    Approval is blocked until
                    these are fixed:
                  </p>

                  <ul className="mt-2 list-disc pl-5">
                    {invoice.approval_blockers.map(
                      (issue) => (
                        <li key={issue}>
                          {issue}
                        </li>
                      ),
                    )}
                  </ul>
                </div>
              ) : (
                <p className="text-emerald-700">
                  Ready for approval. All services and prices have been verified.
                </p>
              )}

              <div className="flex flex-wrap gap-3">
                <button
                  className="rounded-full border px-5 py-3"
                  onClick={() =>
                    setStep(5)
                  }
                  disabled={loading}
                >
                  Back
                </button>

                <button
                  className="flex items-center gap-2 rounded-full bg-ink px-5 py-3 text-white disabled:cursor-not-allowed disabled:opacity-40"
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
                  {loading && (
                    <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                  )}

                  {loading
                    ? "Approving invoice…"
                    : "Approve Invoice"}
                </button>

                {(invoice.status ===
                  "APPROVED" ||
                  invoice.status ===
                    "EXPORTED") && (
                  <button
                    type="button"
                    className="rounded-full bg-gold px-5 py-3 text-ink disabled:cursor-not-allowed disabled:opacity-50"
                    onClick={
                      handleDownloadPdf
                    }
                    disabled={
                      downloadingPdf
                    }
                  >
                    {downloadingPdf
                      ? "Downloading..."
                      : "Download PDF"}
                  </button>
                )}

                <button
                  className="rounded-full border px-5 py-3"
                  onClick={() =>
                    router.push(
                      `/invoices/${invoice.id}`,
                    )
                  }
                >
                  Open invoice
                </button>
              </div>
            </>
          )}
        </section>
      )}
    </div>
  );
}