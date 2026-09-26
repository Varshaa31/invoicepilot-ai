"use client";

import { FormEvent, useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import type {
  TaxType,
  WorkspaceSettings,
} from "@/types";


export default function SettingsPage() {
  const [settings, setSettings] =
    useState<WorkspaceSettings | null>(null);

  const [companyName, setCompanyName] =
    useState("");

  const [companyEmail, setCompanyEmail] =
    useState("");

  const [companyAddress, setCompanyAddress] =
    useState("");

  const [paymentInformation, setPaymentInformation] =
    useState("");

  const [currency, setCurrency] =
    useState("INR");

  const [taxEnabled, setTaxEnabled] =
    useState(true);

  const [taxType, setTaxType] =
    useState<TaxType>("GST");

  const [taxRate, setTaxRate] =
    useState("18");

  const [gstin, setGstin] =
    useState("");

  const [businessState, setBusinessState] =
    useState("");

  const [loading, setLoading] =
    useState(true);

  const [saving, setSaving] =
    useState(false);

  const [error, setError] =
    useState("");

  const [success, setSuccess] =
    useState("");


  useEffect(() => {
    async function loadSettings() {
      try {
        const data = await api.settings();

        setSettings(data);

        setCompanyName(data.company_name);
        setCompanyEmail(data.company_email);
        setCompanyAddress(data.company_address);
        setPaymentInformation(
          data.payment_information,
        );
        setCurrency(data.default_currency);
        setTaxEnabled(data.tax_enabled);
        setTaxType(data.tax_type);
        setTaxRate(
          String(data.default_tax_rate),
        );
        setGstin(data.gstin || "");
        setBusinessState(
          data.business_state || "",
        );
      } catch (err) {
        setError(
          err instanceof ApiError
            ? err.message
            : "Unable to load settings.",
        );
      } finally {
        setLoading(false);
      }
    }

    loadSettings();
  }, []);


  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    setSaving(true);
    setError("");
    setSuccess("");

    try {
      const updated =
        await api.updateSettings({
          company_name: companyName.trim(),
          company_email: companyEmail.trim(),
          company_address:
            companyAddress.trim(),
          payment_information:
            paymentInformation.trim(),
          default_currency: currency,
          tax_enabled: taxEnabled,
          tax_type: taxType,
          default_tax_rate:
            taxEnabled && taxType !== "NONE"
              ? Number(taxRate)
              : 0,
          gstin: gstin.trim() || null,
          business_state:
            businessState.trim() || null,
        });

      setSettings(updated);

      setSuccess(
        "Your invoice settings have been saved.",
      );
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Unable to save settings.",
      );
    } finally {
      setSaving(false);
    }
  }


  if (loading) {
    return (
      <div className="p-8">
        <p className="text-sm text-ink/50">
          Loading settings…
        </p>
      </div>
    );
  }


  return (
    <main className="min-h-full bg-[#f4efe6] px-6 py-8">
      <div className="mx-auto max-w-5xl">

        <div className="mb-8">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-ink/40">
            Workspace
          </p>

          <h1 className="mt-2 font-serif text-4xl text-ink">
            Invoice Settings
          </h1>

          <p className="mt-2 max-w-2xl text-sm leading-6 text-ink/55">
            Manage your company information,
            invoice defaults, and tax configuration.
            These settings are used when creating
            new invoices.
          </p>
        </div>


        {error && (
          <div className="mb-5 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
            {error}
          </div>
        )}


        {success && (
          <div className="mb-5 rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
            {success}
          </div>
        )}


        <form
          onSubmit={handleSubmit}
          className="space-y-6"
        >

          {/* Company information */}

          <section className="rounded-3xl border border-black/10 bg-white p-6 shadow-sm">

            <div className="mb-6">
              <h2 className="font-serif text-2xl text-ink">
                Company Information
              </h2>

              <p className="mt-1 text-sm text-ink/50">
                This information appears on your invoices.
              </p>
            </div>


            <div className="grid gap-5 md:grid-cols-2">

              <Field
                label="Company name"
                value={companyName}
                onChange={setCompanyName}
                placeholder="Your company name"
              />

              <Field
                label="Billing email"
                type="email"
                value={companyEmail}
                onChange={setCompanyEmail}
                placeholder="billing@company.com"
              />

              <div className="md:col-span-2">
                <label className="mb-2 block text-sm font-medium text-ink">
                  Business address
                </label>

                <textarea
                  value={companyAddress}
                  onChange={(event) =>
                    setCompanyAddress(
                      event.target.value,
                    )
                  }
                  rows={3}
                  className="w-full rounded-2xl border border-black/10 bg-[#faf9f6] px-4 py-3 text-sm outline-none transition focus:border-black/30"
                  placeholder="Business address"
                />
              </div>

              <div className="md:col-span-2">
                <label className="mb-2 block text-sm font-medium text-ink">
                  Payment information
                </label>

                <textarea
                  value={paymentInformation}
                  onChange={(event) =>
                    setPaymentInformation(
                      event.target.value,
                    )
                  }
                  rows={3}
                  className="w-full rounded-2xl border border-black/10 bg-[#faf9f6] px-4 py-3 text-sm outline-none transition focus:border-black/30"
                  placeholder="Bank transfer details, payment instructions, etc."
                />

                <p className="mt-2 text-xs text-ink/40">
                  This can appear on the invoice PDF.
                </p>
              </div>

            </div>
          </section>


          {/* Invoice defaults */}

          <section className="rounded-3xl border border-black/10 bg-white p-6 shadow-sm">

            <div className="mb-6">
              <h2 className="font-serif text-2xl text-ink">
                Invoice Defaults
              </h2>

              <p className="mt-1 text-sm text-ink/50">
                Defaults used when creating new invoices.
              </p>
            </div>


            <div className="grid gap-5 md:grid-cols-2">

              <div>
                <label className="mb-2 block text-sm font-medium text-ink">
                  Currency
                </label>

                <select
                  value={currency}
                  onChange={(event) =>
                    setCurrency(event.target.value)
                  }
                  className="w-full rounded-2xl border border-black/10 bg-[#faf9f6] px-4 py-3 text-sm outline-none focus:border-black/30"
                >
                  <option value="INR">
                    INR — Indian Rupee
                  </option>

                  <option value="USD">
                    USD — US Dollar
                  </option>

                  <option value="EUR">
                    EUR — Euro
                  </option>

                  <option value="GBP">
                    GBP — British Pound
                  </option>
                </select>
              </div>


              <div className="rounded-2xl bg-[#f7f4ee] p-4">
                <p className="text-xs font-semibold uppercase tracking-wider text-ink/40">
                  How defaults work
                </p>

                <p className="mt-2 text-sm leading-5 text-ink/60">
                  These values are copied into
                  new invoices. Updating them later
                  does not change invoices that already
                  exist.
                </p>
              </div>

            </div>
          </section>


          {/* Tax */}

          <section className="rounded-3xl border border-black/10 bg-white p-6 shadow-sm">

            <div className="mb-6">
              <h2 className="font-serif text-2xl text-ink">
                Tax Configuration
              </h2>

              <p className="mt-1 text-sm text-ink/50">
                Set the default tax treatment for new invoices.
              </p>
            </div>


            <div className="space-y-5">

              <label className="flex cursor-pointer items-center justify-between rounded-2xl border border-black/10 bg-[#faf9f6] p-4">
                <div>
                  <p className="text-sm font-medium text-ink">
                    Apply tax to new invoices
                  </p>

                  <p className="mt-1 text-xs text-ink/45">
                    Turn this off for tax-free invoices.
                  </p>
                </div>

                <input
                  type="checkbox"
                  checked={taxEnabled}
                  onChange={(event) =>
                    setTaxEnabled(
                      event.target.checked,
                    )
                  }
                  className="h-5 w-5 accent-black"
                />
              </label>


              {taxEnabled && (
                <div className="grid gap-5 md:grid-cols-2">

                  <div>
                    <label className="mb-2 block text-sm font-medium text-ink">
                      Tax type
                    </label>

                    <select
                      value={taxType}
                      onChange={(event) =>
                        setTaxType(
                          event.target.value as TaxType,
                        )
                      }
                      className="w-full rounded-2xl border border-black/10 bg-[#faf9f6] px-4 py-3 text-sm outline-none focus:border-black/30"
                    >
                      <option value="GST">
                        GST
                      </option>

                      <option value="CUSTOM">
                        Custom tax
                      </option>

                      <option value="NONE">
                        No tax
                      </option>
                    </select>
                  </div>


                  <div>
                    <label className="mb-2 block text-sm font-medium text-ink">
                      Default tax rate
                    </label>

                    <div className="relative">
                      <input
                        type="number"
                        min="0"
                        max="100"
                        step="0.01"
                        value={taxRate}
                        disabled={taxType === "NONE"}
                        onChange={(event) =>
                          setTaxRate(
                            event.target.value,
                          )
                        }
                        className="w-full rounded-2xl border border-black/10 bg-[#faf9f6] px-4 py-3 pr-10 text-sm outline-none focus:border-black/30 disabled:cursor-not-allowed disabled:opacity-50"
                      />

                      <span className="absolute right-4 top-1/2 -translate-y-1/2 text-sm text-ink/40">
                        %
                      </span>
                    </div>
                  </div>


                  {taxType === "GST" && (
                    <>
                      <Field
                        label="GSTIN"
                        value={gstin}
                        onChange={setGstin}
                        placeholder="Optional GSTIN"
                      />

                      <Field
                        label="Business state"
                        value={businessState}
                        onChange={setBusinessState}
                        placeholder="e.g. Tamil Nadu"
                      />
                    </>
                  )}

                </div>
              )}


              <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4">
                <p className="text-sm font-medium text-amber-900">
                  Tax rate is a company setting
                </p>

                <p className="mt-1 text-xs leading-5 text-amber-800/75">
                  InvoicePilot does not ask the AI to
                  invent or determine tax rates. The
                  configured rate is applied to new
                  invoices and can be reviewed before
                  approval.
                </p>
              </div>

            </div>
          </section>


          <div className="flex justify-end pb-8">
            <button
              type="submit"
              disabled={saving}
              className="rounded-2xl bg-ink px-6 py-3 text-sm font-semibold text-white transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {saving
                ? "Saving…"
                : "Save Settings"}
            </button>
          </div>

        </form>
      </div>
    </main>
  );
}


function Field({
  label,
  value,
  onChange,
  placeholder,
  type = "text",
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  type?: string;
}) {
  return (
    <div>
      <label className="mb-2 block text-sm font-medium text-ink">
        {label}
      </label>

      <input
        type={type}
        value={value}
        onChange={(event) =>
          onChange(event.target.value)
        }
        placeholder={placeholder}
        className="w-full rounded-2xl border border-black/10 bg-[#faf9f6] px-4 py-3 text-sm outline-none transition focus:border-black/30"
      />
    </div>
  );
}