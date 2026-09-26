"use client";

import { useEffect, useState } from "react";
import { api, inr } from "@/lib/api";
import { StatusBadge } from "@/components/StatusBadge";
import { useToast } from "@/components/Toast";
import type { Service } from "@/types";

const emptyForm = {
  name: "",
  description: "",
  unit: "project",
  price: "",
  currency: "INR",
  aliases: "",
};

type ImportPreview = {
  total_rows: number;
  valid_rows: number;
  invalid_rows: number;
  duplicate_rows: number;
  rows: {
    row_number: number;
    name: string | null;
    description: string | null;
    unit: string | null;
    price: string | null;
    currency: string | null;
    aliases: string[];
    code: string | null;
    status: string;
    message: string | null;
  }[];
};

export default function ServicesPage() {
  const toast = useToast();

  const [rows, setRows] = useState<Service[]>([]);
  const [query, setQuery] = useState("");
  const [form, setForm] = useState(emptyForm);
  const [editing, setEditing] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [selectedFile, setSelectedFile] =
    useState<File | null>(null);

  const [preview, setPreview] =
    useState<ImportPreview | null>(null);

  const [previewLoading, setPreviewLoading] =
    useState(false);

  const [importing, setImporting] =
    useState(false);

  async function load(nextQuery = query) {
    try {
      setError(null);
      setRows(
        await api.services(
          nextQuery || undefined,
        ),
      );
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Could not load catalog",
      );
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function save() {
    try {
      setError(null);

      const payload = {
        ...form,
        price: form.price,
        aliases: form.aliases
          .split(",")
          .map((item) => item.trim())
          .filter(Boolean),
      };

      if (editing) {
        await api.updateService(
          editing,
          payload,
        );

        toast.push("Service updated");
      } else {
        await api.createService(payload);

        toast.push("Service added");
      }

      setForm(emptyForm);
      setEditing(null);

      await load();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Save failed",
      );
    }
  }

  async function handlePreview() {
    if (!selectedFile) {
      setError(
        "Please choose a CSV file first.",
      );
      return;
    }

    try {
      setError(null);
      setPreviewLoading(true);

      const result =
        await api.previewServiceImport(
          selectedFile,
        );

      setPreview(result);
    } catch (err) {
      setPreview(null);

      setError(
        err instanceof Error
          ? err.message
          : "Could not preview the CSV.",
      );
    } finally {
      setPreviewLoading(false);
    }
  }

  async function handleImport() {
    if (!selectedFile || !preview) {
      return;
    }

    if (
      preview.invalid_rows > 0 ||
      preview.duplicate_rows > 0
    ) {
      setError(
        "Correct the invalid or duplicate rows before importing.",
      );
      return;
    }

    try {
      setError(null);
      setImporting(true);

      const result =
        await api.importServices(
          selectedFile,
        );

      toast.push(
        `${result.imported_count} service${
          result.imported_count === 1
            ? ""
            : "s"
        } imported`,
      );

      setSelectedFile(null);
      setPreview(null);

      const input =
        document.getElementById(
          "catalog-file",
        ) as HTMLInputElement | null;

      if (input) {
        input.value = "";
      }

      await load();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Import failed",
      );
    } finally {
      setImporting(false);
    }
  }

  function clearImport() {
    setSelectedFile(null);
    setPreview(null);

    const input =
      document.getElementById(
        "catalog-file",
      ) as HTMLInputElement | null;

    if (input) {
      input.value = "";
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm font-medium uppercase tracking-[0.18em] text-gold">
          Service Catalog
        </p>

        <h1 className="mt-2 font-serif text-4xl">
          Verified pricing
        </h1>

        <p className="mt-2 max-w-2xl text-ink/60">
          Your service catalog is the source of truth
          for invoice prices. Add services manually or
          import them from a CSV file.
        </p>
      </div>

      {error && (
        <div className="rounded-2xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800">
          {error}
        </div>
      )}

      {/* CSV Import */}
      <section className="rounded-3xl bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <h2 className="font-serif text-2xl">
              Import service catalog
            </h2>

            <p className="mt-1 max-w-2xl text-sm leading-6 text-ink/60">
              Upload a CSV, review the rows, then import
              them into your catalog. Existing services
              are never overwritten automatically.
            </p>
          </div>

          <div className="rounded-2xl bg-ivory px-4 py-3 text-xs leading-5 text-ink/60">
            <p className="font-medium text-ink">
              Required columns
            </p>
            <p className="mt-1">
              name, price
            </p>
            <p className="mt-2 font-medium text-ink">
              Optional
            </p>
            <p>
              description, unit, currency, aliases,
              code, active
            </p>
          </div>
        </div>

        <div className="mt-6 flex flex-col gap-3 sm:flex-row sm:items-center">
          <input
            id="catalog-file"
            type="file"
            accept=".csv,text/csv"
            className="block w-full rounded-xl border border-ink/10 bg-white px-3 py-2 text-sm file:mr-4 file:rounded-lg file:border-0 file:bg-ink file:px-3 file:py-2 file:text-sm file:font-medium file:text-white"
            onChange={(event) => {
              const file =
                event.target.files?.[0] ||
                null;

              setSelectedFile(file);
              setPreview(null);
              setError(null);
            }}
          />

          <button
            type="button"
            disabled={
              !selectedFile ||
              previewLoading
            }
            onClick={handlePreview}
            className="shrink-0 rounded-full bg-ink px-5 py-2.5 text-sm font-medium text-white transition hover:bg-ink/90 disabled:cursor-not-allowed disabled:opacity-40"
          >
            {previewLoading
              ? "Checking..."
              : "Preview CSV"}
          </button>
        </div>

        {selectedFile && (
          <p className="mt-3 text-xs text-ink/50">
            Selected: {selectedFile.name}
          </p>
        )}

        {preview && (
          <div className="mt-6 border-t border-ink/10 pt-6">
            <div className="grid gap-3 sm:grid-cols-3">
              <div className="rounded-2xl bg-emerald-50 p-4">
                <p className="text-xs font-medium uppercase tracking-wide text-emerald-700">
                  Ready
                </p>
                <p className="mt-1 text-2xl font-semibold text-emerald-900">
                  {preview.valid_rows}
                </p>
              </div>

              <div className="rounded-2xl bg-amber-50 p-4">
                <p className="text-xs font-medium uppercase tracking-wide text-amber-700">
                  Duplicates
                </p>
                <p className="mt-1 text-2xl font-semibold text-amber-900">
                  {preview.duplicate_rows}
                </p>
              </div>

              <div className="rounded-2xl bg-rose-50 p-4">
                <p className="text-xs font-medium uppercase tracking-wide text-rose-700">
                  Invalid
                </p>
                <p className="mt-1 text-2xl font-semibold text-rose-900">
                  {preview.invalid_rows}
                </p>
              </div>
            </div>

            <div className="mt-5 overflow-x-auto rounded-2xl border border-ink/10">
              <table className="w-full min-w-[760px] text-left text-sm">
                <thead className="bg-ivory text-xs uppercase tracking-wide text-ink/45">
                  <tr>
                    <th className="px-4 py-3">
                      Row
                    </th>
                    <th className="px-4 py-3">
                      Service
                    </th>
                    <th className="px-4 py-3">
                      Price
                    </th>
                    <th className="px-4 py-3">
                      Currency
                    </th>
                    <th className="px-4 py-3">
                      Status
                    </th>
                    <th className="px-4 py-3">
                      Details
                    </th>
                  </tr>
                </thead>

                <tbody>
                  {preview.rows.map((row) => (
                    <tr
                      key={row.row_number}
                      className="border-t border-ink/10"
                    >
                      <td className="px-4 py-3 text-ink/50">
                        {row.row_number}
                      </td>

                      <td className="px-4 py-3 font-medium">
                        {row.name || "—"}
                      </td>

                      <td className="px-4 py-3">
                        {row.price || "—"}
                      </td>

                      <td className="px-4 py-3">
                        {row.currency || "—"}
                      </td>

                      <td className="px-4 py-3">
                        {row.status === "ready" ? (
                          <StatusBadge value="ACTIVE" />
                        ) : row.status === "duplicate" ? (
                          <StatusBadge value="INACTIVE" />
                        ) : (
                          <StatusBadge value="MISSING" />
                        )}
                      </td>

                      <td className="max-w-xs px-4 py-3 text-ink/55">
                        {row.message || "Ready to import"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="mt-5 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <p className="text-sm text-ink/55">
                {preview.invalid_rows === 0 &&
                preview.duplicate_rows === 0
                  ? "All rows passed validation. You can import this catalog."
                  : "Import is blocked until invalid and duplicate rows are corrected."}
              </p>

              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={clearImport}
                  className="rounded-full border border-ink/10 px-4 py-2 text-sm font-medium text-ink/70 transition hover:bg-ivory"
                >
                  Clear
                </button>

                <button
                  type="button"
                  disabled={
                    importing ||
                    preview.invalid_rows > 0 ||
                    preview.duplicate_rows > 0
                  }
                  onClick={handleImport}
                  className="rounded-full bg-gold px-5 py-2 text-sm font-medium text-ink transition hover:bg-gold/90 disabled:cursor-not-allowed disabled:opacity-40"
                >
                  {importing
                    ? "Importing..."
                    : "Import services"}
                </button>
              </div>
            </div>
          </div>
        )}
      </section>

      {/* Manual service editor */}
      <section className="rounded-3xl bg-white p-6 shadow-sm">
        <div className="mb-5">
          <h2 className="font-serif text-2xl">
            {editing
              ? "Edit service"
              : "Add service manually"}
          </h2>

          <p className="mt-1 text-sm text-ink/55">
            Manually maintained catalog entries can be
            used alongside imported services.
          </p>
        </div>

        <div className="grid gap-3 md:grid-cols-3">
          <input
            className="rounded-xl border px-3 py-2"
            placeholder="Name"
            value={form.name}
            onChange={(e) =>
              setForm({
                ...form,
                name: e.target.value,
              })
            }
          />

          <input
            className="rounded-xl border px-3 py-2"
            placeholder="Unit"
            value={form.unit}
            onChange={(e) =>
              setForm({
                ...form,
                unit: e.target.value,
              })
            }
          />

          <input
            className="rounded-xl border px-3 py-2"
            placeholder="Price"
            value={form.price}
            onChange={(e) =>
              setForm({
                ...form,
                price: e.target.value,
              })
            }
          />

          <input
            className="rounded-xl border px-3 py-2 md:col-span-2"
            placeholder="Description"
            value={form.description}
            onChange={(e) =>
              setForm({
                ...form,
                description: e.target.value,
              })
            }
          />

          <input
            className="rounded-xl border px-3 py-2"
            placeholder="Aliases, comma separated"
            value={form.aliases}
            onChange={(e) =>
              setForm({
                ...form,
                aliases: e.target.value,
              })
            }
          />
        </div>

        <div className="mt-4 flex gap-2">
          <button
            type="button"
            className="rounded-full bg-ink px-4 py-2 text-white"
            onClick={save}
          >
            {editing
              ? "Save changes"
              : "Add service"}
          </button>

          {editing && (
            <button
              type="button"
              className="rounded-full border border-ink/10 px-4 py-2 text-ink/70"
              onClick={() => {
                setEditing(null);
                setForm(emptyForm);
              }}
            >
              Cancel
            </button>
          )}
        </div>
      </section>

      {/* Search */}
      <div className="flex flex-col gap-3 sm:flex-row">
        <input
          className="rounded-xl border px-3 py-2"
          placeholder="Search services"
          value={query}
          onChange={(e) =>
            setQuery(e.target.value)
          }
        />

        <button
          type="button"
          className="rounded-full border px-4 py-2"
          onClick={() => load(query)}
        >
          Search
        </button>
      </div>

      {/* Existing catalog */}
      <div className="overflow-x-auto rounded-3xl bg-white p-4 shadow-sm">
        <table className="w-full text-left text-sm">
          <thead className="text-ink/50">
            <tr>
              <th className="py-2">
                Service
              </th>
              <th>Description</th>
              <th>Unit</th>
              <th>Price</th>
              <th>Currency</th>
              <th>Status</th>
              <th />
            </tr>
          </thead>

          <tbody>
            {rows.map((row) => (
              <tr
                key={row.id}
                className="border-t"
              >
                <td className="py-3 font-medium">
                  {row.name}
                </td>

                <td>
                  {row.description}
                </td>

                <td>{row.unit}</td>

                <td>
                  {inr(
                    row.price,
                    row.currency,
                  )}
                </td>

                <td>{row.currency}</td>

                <td>
                  <StatusBadge
                    value={
                      row.active
                        ? "ACTIVE"
                        : "INACTIVE"
                    }
                  />
                </td>

                <td className="space-x-2">
                  <button
                    type="button"
                    className="text-sm font-medium text-ink/70 hover:text-ink"
                    onClick={() => {
                      setEditing(row.id);

                      setForm({
                        name: row.name,
                        description:
                          row.description ||
                          "",
                        unit: row.unit,
                        price: row.price,
                        currency:
                          row.currency,
                        aliases:
                          row.aliases.join(
                            ", ",
                          ),
                      });
                    }}
                  >
                    Edit
                  </button>

                  {row.active && (
                    <button
                      type="button"
                      className="text-sm font-medium text-rose-700 hover:text-rose-900"
                      onClick={async () => {
                        try {
                          await api.deactivateService(
                            row.id,
                          );

                          toast.push(
                            "Service deactivated",
                          );

                          await load();
                        } catch (err) {
                          setError(
                            err instanceof Error
                              ? err.message
                              : "Could not deactivate service",
                          );
                        }
                      }}
                    >
                      Deactivate
                    </button>
                  )}
                </td>
              </tr>
            ))}

            {rows.length === 0 && (
              <tr>
                <td
                  colSpan={7}
                  className="py-10 text-center text-sm text-ink/45"
                >
                  No services found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}