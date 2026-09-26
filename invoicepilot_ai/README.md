# InvoicePilot AI

A hackathon-ready Streamlit application that converts natural-language customer requirements into review-ready invoices.

## Core principle

**AI interprets language. The service catalog supplies prices. Python performs financial calculations. A human approves before PDF export.**

This prevents the LLM from fabricating prices or authoritative totals.

## Features

- Natural-language customer requirement extraction
- Pydantic structured output
- Customer name/email extraction
- Service and quantity extraction
- Missing-information detection
- Ambiguous service detection
- CSV-backed service catalog
- Exact + fuzzy catalog matching
- Missing-price blocking
- Deterministic invoice calculations using Decimal
- Configurable tax
- Human review/approval step
- Professional PDF invoice
- Audit-friendly price provenance
- Basic unit tests

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env