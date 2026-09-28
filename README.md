# InvoicePilot AI

Turn customer messages into verified invoices.

**AI understands. Your catalog prices. You approve.**

InvoicePilot AI is a full-stack AI invoice automation product built for the **KODNEXUS AI BUILD BATTLE – Smart Invoice Challenge**.

It converts a natural-language customer requirement into a structured, catalog-priced, human-reviewed invoice and generates a professional PDF only after approval.

The original Streamlit MVP remains in `invoicepilot_ai/` for reference. The current application is a full-stack system built with Next.js, FastAPI, PostgreSQL, Groq, and deterministic financial calculations.

---

## Core Principle

**AI is not the source of truth for money.**

InvoicePilot separates language understanding from financial logic:

- The AI extracts customer details and requested services.
- The service catalog supplies the actual unit prices.
- The backend performs all financial calculations using Python `Decimal`.
- Tax is controlled by workspace settings rather than guessed by AI.
- A human reviews and approves the invoice before PDF export.

For example, if a customer says:

> "Make me a website for ₹50,000."

but the catalog lists **Corporate Website at ₹40,000**, InvoicePilot uses the catalog price of **₹40,000**.

The AI cannot invent or override catalog prices.

---
## Demo Login

You can use the following demo account to explore the deployed application:

**Email:** `frontendtest@example.com`  
**Password:** `TestPassword123!`

### Live Demo

https://invoicepilot-ai-six.vercel.app/

### Demo Flow

After logging in:

1. Open **Service Catalog** to view the available services and prices.
2. Open **Settings** to view company and tax configuration.
3. Go to **Create Invoice**.
4. Enter a customer requirement in natural language.
5. Review the AI-extracted customer details and requested services.
6. Resolve any missing or ambiguous services if required.
7. Review the calculated invoice.
8. Approve the invoice.
9. Generate the final professional PDF invoice.

> **Note:** The demo account is provided for evaluation purposes. Prices are retrieved from the Service Catalog, and AI does not generate or invent service prices.

## Key Features

### AI-powered requirement extraction

Converts natural-language customer messages into structured information:

- Customer name
- Customer email
- Requested services
- Quantities
- Notes
- Missing information
- Ambiguous requests

The Groq model is used only for language understanding and structured extraction.

### Deterministic service matching

Requested services are matched against the service catalog using:

1. Exact matching
2. Normalized matching
3. Alias matching
4. Fuzzy matching

### Missing service protection

If a requested service does not exist in the catalog:

- It is marked **Not Found**
- No price is invented
- The invoice cannot be approved until resolved

### Ambiguous service protection

If a request could match multiple catalog services:

- The invoice is marked **Selection Required**
- The user chooses the correct service
- The system does not silently guess

### Deterministic pricing

Prices always come from the service catalog.

The backend calculates:

- Quantity × unit price
- Subtotal
- Tax
- Grand total

Financial calculations use Python `Decimal`.

### Human review and approval

Invoices pass through a review workflow before PDF export.

Unresolved services cannot be approved.

### Professional PDF invoices

Approved invoices can be exported as professional PDF documents using ReportLab.

PDF generation is restricted to approved invoices.

### Authentication and workspace isolation

Each user has their own workspace.

Invoices, services, and settings are scoped to the authenticated user.

### Workspace tax settings

Tax is configured through workspace settings.

Supported configuration includes:

- Tax enabled/disabled
- Tax type
- Default tax rate
- GSTIN
- Business state
- Currency

The configured tax rate is applied to new invoices rather than being determined by AI.

### Service catalog management

Users can maintain their own service catalog with:

- Service name
- Description
- Unit
- Price
- Currency
- Aliases
- Service code

---

# Workflow

```text
Customer Requirement
        ↓
AI Extraction
        ↓
Service Matching
        ↓
Catalog Price Resolution
        ↓
Deterministic Calculation
        ↓
Human Review
        ↓
Approval
        ↓
Professional PDF

The application follows the principle:

AI interprets language.
The catalog supplies prices.
Python performs financial calculations.
A human approves before export.
Architecture
┌───────────────────────────────┐
│        Customer Message       │
└───────────────┬───────────────┘
                ↓
┌───────────────────────────────┐
│       Groq AI Extraction      │
│   Structured data only        │
│   No prices / no totals       │
└───────────────┬───────────────┘
                ↓
┌───────────────────────────────┐
│      Service Matching         │
│ Exact → Normalized → Alias    │
│ → Fuzzy                       │
└───────────────┬───────────────┘
                ↓
┌───────────────────────────────┐
│       Service Catalog         │
│     Authoritative pricing     │
└───────────────┬───────────────┘
                ↓
┌───────────────────────────────┐
│   Decimal Financial Engine     │
│ Subtotal → Tax → Grand Total  │
└───────────────┬───────────────┘
                ↓
┌───────────────────────────────┐
│       Human Review            │
│ Resolve → Review → Approve    │
└───────────────┬───────────────┘
                ↓
┌───────────────────────────────┐
│        ReportLab PDF          │
└───────────────────────────────┘
Tech Stack
Frontend
Next.js
TypeScript
Tailwind CSS
Backend
Python
FastAPI
Pydantic
SQLAlchemy
Alembic
Database
PostgreSQL
Neon PostgreSQL for the current hosted development/demo environment
pg8000 PostgreSQL driver
AI
Groq API
Model: openai/gpt-oss-20b

The openai/gpt-oss-20b value is the Groq model identifier. The application communicates with Groq's OpenAI-compatible API endpoint.

PDF
ReportLab
Authentication
JWT
Password hashing with pwdlib
Testing
pytest
TypeScript compiler
Next.js production build
Project Structure
InvoicePilot/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   ├── schemas/
│   │   └── services/
│   │
│   ├── alembic/
│   ├── requirements.txt
│   └── ...
│
├── frontend/
│   ├── app/
│   ├── components/
│   ├── lib/
│   └── ...
│
├── database/
│   └── seed/
│
├── docs/
│   └── DEPLOYMENT.md
│
├── invoicepilot_ai/
│   └── original Streamlit MVP
│
├── docker-compose.yml
├── .env.example
└── README.md
Local Development
1. Clone the repository
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd InvoicePilot
2. Configure environment variables

Copy the example environment file:

cp .env.example .env

For Windows PowerShell:

Copy-Item .env.example .env

Configure the backend environment variables.

Example:

DATABASE_URL=postgresql+pg8000://USER:PASSWORD@HOST/neondb

GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-20b
GROQ_BASE_URL=https://api.groq.com/openai/v1

JWT_SECRET=change-this-development-secret

CORS_ORIGINS=http://localhost:3000

COMPANY_NAME=InvoicePilot AI
COMPANY_EMAIL=billing@invoicepilot.demo
COMPANY_ADDRESS=Bengaluru, India
COMPANY_PAYMENT_INFO=Bank transfer · A/C InvoicePilot AI · IFSC DEMO0001234

DEFAULT_TAX_RATE=18
DEFAULT_CURRENCY=INR
Important

GROQ_API_KEY is server-side only.

Never:

Put it in frontend code
Prefix it with NEXT_PUBLIC_
Commit it to GitHub
Add it to Vercel frontend environment variables
3. Database

The current application uses PostgreSQL.

The development/demo environment can use Neon PostgreSQL.

Example:

DATABASE_URL=postgresql+pg8000://USER:PASSWORD@HOST/neondb

Run database migrations:

cd backend
alembic upgrade head

To load the sample service catalog:

python ../database/seed/seed.py

The database schema is managed through Alembic migrations.

4. Backend

From the project root:

cd backend

Create a virtual environment:

Windows
python -m venv .venv
.venv\Scripts\activate
macOS/Linux
python -m venv .venv
source .venv/bin/activate

Install dependencies:

pip install -r requirements.txt

Run migrations:

alembic upgrade head

Start FastAPI:

uvicorn app.main:app --reload --port 8000

Backend:

http://localhost:8000

API documentation:

http://localhost:8000/docs
5. Frontend

Open another terminal:

cd frontend

Install dependencies:

npm install

Create:

frontend/.env.local

with:

NEXT_PUBLIC_API_URL=http://localhost:8000

Start the frontend:

npm run dev

Open:

http://localhost:3000
Environment Variables
Backend
Variable	Purpose
DATABASE_URL	PostgreSQL database connection
GROQ_API_KEY	Server-side Groq API key
GROQ_MODEL	Groq model identifier
GROQ_BASE_URL	Groq OpenAI-compatible API endpoint
JWT_SECRET	JWT signing secret
CORS_ORIGINS	Allowed frontend origins
COMPANY_NAME	Default company name
COMPANY_EMAIL	Default company email
COMPANY_ADDRESS	Default company address
COMPANY_PAYMENT_INFO	Default payment information
DEFAULT_TAX_RATE	Default workspace tax rate
DEFAULT_CURRENCY	Default invoice currency
Frontend
Variable	Purpose
NEXT_PUBLIC_API_URL	Backend API URL
Invoice Workflow
1. Create

Paste a customer requirement into the Create Invoice page.

Example:

Hi, I'm Rahul. My email is rahul@example.com.
I need an e-commerce website and SEO optimization.
I need one of each.
2. Extract

Groq extracts:

Customer:
Rahul
rahul@example.com

Requested services:
E-commerce Website × 1
SEO Optimization × 1
3. Match

The backend matches each requested service against the authenticated user's service catalog.

4. Price

The catalog supplies the unit price.

The AI does not determine the price.

5. Calculate

The backend calculates:

Line total = quantity × unit price

Subtotal = sum(line totals)

Tax = subtotal × configured tax rate

Grand total = subtotal + tax

Calculations use Decimal.

6. Review

The user reviews:

Customer details
Services
Quantities
Unit prices
Tax
Notes
Totals
Matching status
7. Approve

The invoice can only be approved after unresolved services are resolved.

8. Export

An approved invoice can be downloaded as a PDF.

Invoice Statuses

InvoicePilot uses a human-readable review workflow:

DRAFT
   ↓
REVIEW_REQUIRED
   ↓
READY_FOR_APPROVAL
   ↓
APPROVED
   ↓
EXPORTED

Service resolution states include:

MATCHED
AMBIGUOUS
MISSING

Ambiguous and missing services require user action.

No-Price-Hallucination Design

InvoicePilot deliberately separates AI interpretation from financial authority.

The extraction schema contains no:
Price fields
Unit-price fields
Tax calculations
Invoice totals
Pricing is performed by:
Service Catalog
      ↓
Backend Matching
      ↓
Catalog Unit Price
      ↓
Decimal Calculation
Invoice line items snapshot:
Service name
Unit price
Quantity
Price source

This means historical invoices retain the price that was resolved at the time of invoice creation.

Approval protection

Approval is rejected if an invoice contains unresolved:

MISSING services
AMBIGUOUS services
Missing catalog prices
PDF protection

PDF generation is restricted to approved invoices.

Service Catalog

The demo catalog includes services such as:

Service	Price
Landing Page	₹15,000
Corporate Website	₹40,000
E-commerce Website	₹65,000
SEO Optimization	₹12,000
SEO Growth Package	₹25,000
Logo Design	₹5,000
Brand Identity	₹18,000
Social Media Campaign	₹8,000
Blog Article	₹2,500
Website Maintenance	₹6,000

The catalog can also contain additional demo services such as:

UI/UX Design Sprint
Mobile App Development
API Integration
Cloud Deployment
Performance Audit
Security Assessment
Conversion Rate Optimization
Email Marketing Setup
Product Photography
Video Editing Package

Prices are stored in the service catalog and are never generated by the AI.

Demo Scenarios
1. Happy Path

Input:

Hi, I'm Arjun. My email is arjun@example.com.
I need a mobile app and API integration, one of each.

Expected behavior:

Mobile App Development × 1
API Integration × 1
        ↓
Catalog prices
        ↓
Calculated subtotal
        ↓
Configured tax
        ↓
Grand total
        ↓
Review
        ↓
Approve
        ↓
PDF
2. Unknown Service

Input:

Hi, I'm Priya. My email is priya@example.com.
I need an AI automation consulting package, one of each.

Expected behavior:

AI automation consulting package
        ↓
NOT FOUND
        ↓
No invented price
        ↓
Approval blocked
3. Ambiguous Service

Input:

Hi, I'm Rahul. My email is rahul@example.com.
I need SEO services, one of each.

Expected behavior:

SEO
 ↓
Multiple possible catalog matches
 ↓
Selection Required
 ↓
Human chooses the correct service

Possible catalog matches include:

SEO Optimization
SEO Growth Package

The application does not silently choose between them.

Tax Configuration

Tax is controlled through Workspace Settings.

The user can configure:

Tax enabled/disabled
Tax type
Default tax rate
GSTIN
Business state
Currency

The AI does not determine the tax rate.

The invoice stores the applicable tax rate used for that invoice so historical calculations remain stable.

Tax configuration in the demo is an application setting and does not constitute tax or accounting advice.

Authentication and Data Isolation

InvoicePilot supports user authentication using:

Email/password signup
Email/password login
JWT access tokens

Workspace-owned data is isolated by authenticated user.

Services, invoices, and settings are associated with the appropriate workspace/user.

Testing
Backend
cd backend
pytest
Frontend type checking
cd frontend
npx tsc --noEmit
Frontend production build
npm run build
Screenshots

Add final demo screenshots here before submission.

Recommended screenshots:

Dashboard
Create Invoice with extracted services
Ambiguous service requiring selection
Invoice review screen
Approved invoice
Generated PDF
Service Catalog
Workspace Settings
Deployment

Deployment documentation:

docs/DEPLOYMENT.md

The production architecture is:

Next.js
   ↓
Hosted frontend
   ↓
FastAPI backend
   ↓
Neon PostgreSQL
   ↓
Groq API

The Groq API key must remain on the backend.

For a deployed backend:

GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-20b
GROQ_BASE_URL=https://api.groq.com/openai/v1

Set the frontend:

NEXT_PUBLIC_API_URL=https://YOUR-BACKEND-URL

Do not put GROQ_API_KEY into the frontend or expose it through NEXT_PUBLIC_*.

Original Streamlit MVP

The original prototype is preserved in:

invoicepilot_ai/

To run the earlier Streamlit interface:

cd invoicepilot_ai
streamlit run app.py

The original MVP also uses Groq for natural-language extraction.

The full-stack application in frontend/ and backend/ is the primary current implementation.

Hackathon Demo Flow

For the final demo, show the complete path:

Customer message
      ↓
AI extracts requirement
      ↓
Service catalog resolves prices
      ↓
Invoice totals calculated
      ↓
Human reviews invoice
      ↓
Approve
      ↓
Download PDF

Then demonstrate one safety case:

Unknown service
      ↓
Not Found
      ↓
No fabricated price
      ↓
Approval blocked

And one ambiguity case:

SEO request
      ↓
Multiple catalog matches
      ↓
Human selection required
Project Highlights

InvoicePilot AI demonstrates a practical approach to AI-powered financial automation:

Natural-language input
Structured AI extraction
Deterministic pricing
Catalog-backed financial calculations
Human-in-the-loop approval
Missing-service protection
Ambiguity handling
Tax configuration
PDF generation
Authentication
Workspace data isolation
Auditability through persisted invoice data and status history

The key design decision is simple:

Let AI understand the request, but never let AI decide the money.
