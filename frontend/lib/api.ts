import type {
  Dashboard,
  ExtractionResponse,
  Invoice,
  InvoiceListItem,
  ItemMatch,
  Service,
  WorkspaceSettings,
} from "@/types";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const TOKEN_KEY = "invoicepilot_access_token";
const USER_KEY = "invoicepilot_user";

export class ApiError extends Error {
  status: number;
  issues?: string[];

  constructor(
    message: string,
    status: number,
    issues?: string[],
  ) {
    super(message);
    this.status = status;
    this.issues = issues;
  }
}

export type AuthUser = {
  id: string;
  name: string;
  email: string;
  workspace_name: string;
  email_verified: boolean;
};

export type AuthResponse = {
  access_token: string;
  token_type: string;
  user: AuthUser;
};

/* -------------------------------------------------------------------------- */
/* Authentication                                                             */
/* -------------------------------------------------------------------------- */

export function getAccessToken(): string | null {
  if (typeof window === "undefined") {
    return null;
  }

  return window.localStorage.getItem(TOKEN_KEY);
}

export function setAccessToken(token: string): void {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.setItem(TOKEN_KEY, token);
}

export function clearAccessToken(): void {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.removeItem(TOKEN_KEY);
  window.localStorage.removeItem(USER_KEY);
}

export function setStoredUser(user: AuthUser): void {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.setItem(
    USER_KEY,
    JSON.stringify(user),
  );
}

export function getStoredUser(): AuthUser | null {
  if (typeof window === "undefined") {
    return null;
  }

  const raw = window.localStorage.getItem(USER_KEY);

  if (!raw) {
    return null;
  }

  try {
    return JSON.parse(raw) as AuthUser;
  } catch {
    window.localStorage.removeItem(USER_KEY);
    return null;
  }
}

/* -------------------------------------------------------------------------- */
/* Authenticated PDF download                                                 */
/* -------------------------------------------------------------------------- */

export async function downloadInvoicePdf(
  invoiceId: string,
): Promise<void> {
  const token = getAccessToken();

  if (!token) {
    throw new ApiError(
      "You must be logged in to download an invoice.",
      401,
    );
  }

  const pdfUrl =
    `${API_URL}/api/invoices/${invoiceId}/pdf`;

  console.log(
    "InvoicePilot PDF: Access token exists",
  );

  console.log(
    "InvoicePilot PDF URL:",
    pdfUrl,
  );

  let response: Response;

  try {
    response = await fetch(pdfUrl, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
      },
      credentials: "omit",
    });
  } catch (error) {
    console.error(
      "InvoicePilot PDF fetch error:",
      error,
    );

    throw new ApiError(
      "Cannot reach the InvoicePilot API. Is the backend running?",
      0,
    );
  }

  console.log(
    "InvoicePilot PDF response:",
    response.status,
  );

  if (!response.ok) {
    const body = await response
      .json()
      .catch(
        () => ({} as Record<string, unknown>),
      );

    console.error(
      "InvoicePilot PDF error response:",
      body,
    );

    const detail = (
      body as {
        detail?: unknown;
      }
    ).detail;

    throw new ApiError(
      typeof detail === "string"
        ? detail
        : "Unable to download the invoice PDF.",
      response.status,
    );
  }

  const blob = await response.blob();

  const contentDisposition =
    response.headers.get("Content-Disposition");

  let filename =
    `invoice-${invoiceId}.pdf`;

  if (contentDisposition) {
    const filenameMatch =
      contentDisposition.match(
        /filename="?([^"]+)"?/i,
      );

    if (filenameMatch?.[1]) {
      filename = filenameMatch[1];
    }
  }

  const url =
    window.URL.createObjectURL(blob);

  const link =
    document.createElement("a");

  link.href = url;
  link.download = filename;

  document.body.appendChild(link);
  link.click();
  link.remove();

  window.URL.revokeObjectURL(url);
}

/* -------------------------------------------------------------------------- */
/* Generic API request                                                        */
/* -------------------------------------------------------------------------- */

async function request<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  let response: Response;

  try {
    const token = getAccessToken();

    response = await fetch(
      `${API_URL}${path}`,
      {
        ...init,
        headers: {
          "Content-Type": "application/json",

          ...(token
            ? {
                Authorization:
                  `Bearer ${token}`,
              }
            : {}),

          ...(init?.headers || {}),
        },
      },
    );
  } catch {
    throw new ApiError(
      "Cannot reach the InvoicePilot API. Is the backend running?",
      0,
    );
  }

  if (!response.ok) {
    const body = await response
      .json()
      .catch(
        () => ({} as Record<string, unknown>),
      );

    const raw = (
      body as {
        detail?: unknown;
        issues?: string[];
      }
    ).detail;

    let message = "Request failed";

    if (typeof raw === "string") {
      message = raw;
    } else if (Array.isArray(raw)) {
      message = raw
        .map((item) =>
          typeof item === "string"
            ? item
            : (item as { msg?: string }).msg ||
              "Invalid value",
        )
        .join(" ");
    }

    throw new ApiError(
      message,
      response.status,
      (
        body as {
          issues?: string[];
        }
      ).issues,
    );
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

/* -------------------------------------------------------------------------- */
/* API                                                                        */
/* -------------------------------------------------------------------------- */

export const api = {
  health: () =>
    request<{
      status: string;
      database: string;
      groq_configured: boolean;
    }>("/api/health"),

  /* ------------------------------ Auth ---------------------------------- */

  signup: (payload: {
    name: string;
    email: string;
    password: string;
    confirm_password: string;
  }) =>
    request<AuthResponse>(
      "/api/auth/signup",
      {
        method: "POST",
        body: JSON.stringify(payload),
      },
    ),

  login: (payload: {
    email: string;
    password: string;
  }) =>
    request<AuthResponse>(
      "/api/auth/login",
      {
        method: "POST",
        body: JSON.stringify(payload),
      },
    ),

  /* ---------------------------- Dashboard ------------------------------- */

  dashboard: () =>
    request<Dashboard>("/api/dashboard"),

  /* ---------------------------- Extraction ------------------------------ */

  extract: (customer_message: string) =>
    request<ExtractionResponse>(
      "/api/extraction",
      {
        method: "POST",
        body: JSON.stringify({
          customer_message,
        }),
      },
    ),

  /* ----------------------------- Matching ------------------------------- */

  match: (
    items: {
      requested_service: string;
      quantity?: string | null;
      notes?: string | null;
    }[],
  ) =>
    request<ItemMatch[]>(
      "/api/matching",
      {
        method: "POST",
        body: JSON.stringify(items),
      },
    ),

  /* ----------------------------- Invoices ------------------------------- */

  invoices: (
    params?: Record<string, string>,
  ) => {
    const query = new URLSearchParams(
      params,
    ).toString();

    return request<InvoiceListItem[]>(
      `/api/invoices${
        query ? `?${query}` : ""
      }`,
    );
  },

  invoice: (id: string) =>
    request<Invoice>(
      `/api/invoices/${id}`,
    ),

  createInvoice: (payload: unknown) =>
    request<Invoice>(
      "/api/invoices",
      {
        method: "POST",
        body: JSON.stringify(payload),
      },
    ),

  updateInvoice: (
    id: string,
    payload: unknown,
  ) =>
    request<Invoice>(
      `/api/invoices/${id}`,
      {
        method: "PUT",
        body: JSON.stringify(payload),
      },
    ),

  resolveService: (
    id: string,
    item_id: string,
    service_id: string,
  ) =>
    request<Invoice>(
      `/api/invoices/${id}/resolve-service`,
      {
        method: "POST",
        body: JSON.stringify({
          item_id,
          service_id,
        }),
      },
    ),

  calculate: (id: string) =>
    request<Invoice>(
      `/api/invoices/${id}/calculate`,
      {
        method: "POST",
      },
    ),

  approve: (id: string) =>
    request<Invoice>(
      `/api/invoices/${id}/approve`,
      {
        method: "POST",
      },
    ),

  /*
   * Kept for compatibility.
   *
   * Do not use this directly in <a href=""> for PDF downloads,
   * because the browser will not attach the Authorization header.
   *
   * Use downloadInvoicePdf(id) instead.
   */
  pdfUrl: (id: string) =>
    `${API_URL}/api/invoices/${id}/pdf`,

  /* ----------------------------- Settings ------------------------------- */

  settings: () =>
    request<WorkspaceSettings>(
      "/api/settings",
    ),

  updateSettings: (
    payload: {
      company_name: string;
      company_email: string;
      company_address: string;
      payment_information: string;
      default_currency: string;
      tax_enabled: boolean;
      tax_type: "GST" | "CUSTOM" | "NONE";
      default_tax_rate: number;
      gstin?: string | null;
      business_state?: string | null;
    },
  ) =>
    request<WorkspaceSettings>(
      "/api/settings",
      {
        method: "PUT",
        body: JSON.stringify(payload),
      },
    ),

  /* ----------------------------- Services ------------------------------- */

  services: (q?: string) =>
    request<Service[]>(
      `/api/services${
        q
          ? `?q=${encodeURIComponent(q)}`
          : ""
      }`,
    ),

  createService: (payload: unknown) =>
    request<Service>(
      "/api/services",
      {
        method: "POST",
        body: JSON.stringify(payload),
      },
    ),

  updateService: (
    id: string,
    payload: unknown,
  ) =>
    request<Service>(
      `/api/services/${id}`,
      {
        method: "PUT",
        body: JSON.stringify(payload),
      },
    ),

  deactivateService: (id: string) =>
    request<Service>(
      `/api/services/${id}`,
      {
        method: "DELETE",
      },
    ),

  /* ------------------------- Service Import ---------------------------- */

  previewServiceImport: async (
    file: File,
  ) => {
    const token = getAccessToken();

    const formData = new FormData();
    formData.append("file", file);

    let response: Response;

    try {
      response = await fetch(
        `${API_URL}/api/services/import/preview`,
        {
          method: "POST",
          headers: token
            ? {
                Authorization: `Bearer ${token}`,
              }
            : {},
          body: formData,
        },
      );
    } catch {
      throw new ApiError(
        "Cannot reach the InvoicePilot API. Is the backend running?",
        0,
      );
    }

    if (!response.ok) {
      const body = await response
        .json()
        .catch(
          () => ({} as Record<string, unknown>),
        );

      const detail = (
        body as {
          detail?: unknown;
        }
      ).detail;

      throw new ApiError(
        typeof detail === "string"
          ? detail
          : "Could not preview the CSV.",
        response.status,
      );
    }

    return response.json() as Promise<{
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
    }>;
  },

  importServices: async (
    file: File,
  ) => {
    const token = getAccessToken();

    const formData = new FormData();
    formData.append("file", file);

    let response: Response;

    try {
      response = await fetch(
        `${API_URL}/api/services/import`,
        {
          method: "POST",
          headers: token
            ? {
                Authorization: `Bearer ${token}`,
              }
            : {},
          body: formData,
        },
      );
    } catch {
      throw new ApiError(
        "Cannot reach the InvoicePilot API. Is the backend running?",
        0,
      );
    }

    if (!response.ok) {
      const body = await response
        .json()
        .catch(
          () => ({} as Record<string, unknown>),
        );

      const detail = (
        body as {
          detail?: unknown;
        }
      ).detail;

      throw new ApiError(
        typeof detail === "string"
          ? detail
          : "Could not import the CSV.",
        response.status,
      );
    }

    return response.json() as Promise<{
      imported_count: number;
      services: Service[];
    }>;
  },
};

/* -------------------------------------------------------------------------- */
/* Currency formatting                                                        */
/* -------------------------------------------------------------------------- */

export function inr(
  value?: string | number | null,
  currency = "INR",
) {
  const amount = Number(value || 0);

  if (currency === "INR") {
    return new Intl.NumberFormat(
      "en-IN",
      {
        style: "currency",
        currency: "INR",
        maximumFractionDigits: 2,
      },
    ).format(amount);
  }

  return new Intl.NumberFormat(
    "en-US",
    {
      style: "currency",
      currency,
      maximumFractionDigits: 2,
    },
  ).format(amount);
}