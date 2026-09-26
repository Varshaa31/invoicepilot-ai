export type InvoiceStatus =
  | "DRAFT"
  | "REVIEW_REQUIRED"
  | "READY_FOR_APPROVAL"
  | "APPROVED"
  | "EXPORTED";

export type ResolutionStatus = "MATCHED" | "AMBIGUOUS" | "MISSING";

export type Customer = {
  id?: string;
  name: string;
  email?: string | null;
  phone?: string | null;
  company?: string | null;
  address?: string | null;
};

export type ServiceCandidate = {
  service_id: string;
  name: string;
  description?: string | null;
  unit_price: string;
  currency: string;
  match_score?: number | null;
};

export type ItemMatch = {
  requested_service: string;
  quantity?: string | null;
  notes?: string | null;
  status: ResolutionStatus;
  matched_service: ServiceCandidate | null;
  candidate_services: ServiceCandidate[];
  unit_price?: string | null;
  currency?: string | null;
  price_source?: string | null;
  match_score?: number | null;
};

export type Extraction = {
  customer: Customer;
  requested_items: {
    requested_service: string;
    quantity?: string | null;
    notes?: string | null;
  }[];
  notes?: string | null;
  missing_information: string[];
};

export type ExtractionResponse = {
  extraction: Extraction;
  matches: ItemMatch[];
};

export type InvoiceItem = {
  id: string;
  invoice_id: string;
  service_id?: string | null;
  requested_service: string;
  service_name_snapshot?: string | null;
  quantity: string;
  unit_price?: string | null;
  line_total?: string | null;
  resolution_status: ResolutionStatus;
  match_score?: string | null;
  price_source: string;
  notes?: string | null;
  candidate_services: ServiceCandidate[];
};

export type AuditLog = {
  id: string;
  invoice_id: string;
  event_type: string;
  metadata?: Record<string, unknown> | null;
  created_at: string;
};

export type Invoice = {
  id: string;
  invoice_number: string;
  customer_id: string;
  status: InvoiceStatus;
  currency: string;
  subtotal: string;
  tax_rate: string;
  tax_amount: string;
  total: string;
  notes?: string | null;
  source_message?: string | null;
  created_at: string;
  updated_at: string;
  approved_at?: string | null;
  exported_at?: string | null;
  customer: Customer & { id: string; created_at: string; updated_at: string };
  items: InvoiceItem[];
  audit_logs: AuditLog[];
  approval_blockers: string[];
};

export type InvoiceListItem = {
  id: string;
  invoice_number: string;
  customer_name: string;
  status: InvoiceStatus;
  currency: string;
  total: string;
  created_at: string;
};

export type Service = {
  id: string;
  code: string;
  name: string;
  description?: string | null;
  unit: string;
  price: string;
  currency: string;
  active: boolean;
  aliases: string[];
};

export type Dashboard = {
  total_invoices: number;
  drafts: number;
  pending_review: number;
  approved: number;
  exported: number;
  total_revenue: string;
  recent: InvoiceListItem[];
};

export type TaxType =
  | "GST"
  | "CUSTOM"
  | "NONE";

export type WorkspaceSettings = {
  id: string;
  user_id: string;

  company_name: string;
  company_email: string;
  company_address: string;
  payment_information: string;

  default_currency: string;

  tax_enabled: boolean;
  tax_type: TaxType;
  default_tax_rate: string;

  gstin?: string | null;
  business_state?: string | null;
};
