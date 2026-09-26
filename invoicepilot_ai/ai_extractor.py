import json
import os

from groq import Groq

from models import InvoiceRequest


SYSTEM_PROMPT = """
You are the structured requirement extraction engine for InvoicePilot AI.

Your job is ONLY to interpret a customer's natural-language invoice request.

Rules:
1. Extract customer name and email when explicitly present.
2. Extract every requested service and its quantity.
3. Preserve the customer's wording in requested_service where useful.
4. Never invent a price.
5. Never invent a service that the customer did not request.
6. Never calculate invoice totals.
7. If a quantity is absent or unclear, set quantity to null.
8. If customer information is absent, add a concise entry to missing_information.
9. If a service description is vague or ambiguous, add it to ambiguous_items.
10. Notes should contain relevant delivery or customer instructions.
11. Return data matching the supplied Pydantic schema.
12. Do not use outside knowledge to determine prices or catalog IDs.

Examples:

Customer:
"Hi, I'm Priya from Acme. Please invoice us for 3 landing pages and 2 logo designs. Send it to priya@acme.com."

Expected interpretation:
- customer name = Priya
- customer email = priya@acme.com
- items = Landing Page x3, Logo Design x2
- no fabricated prices

Customer:
"Invoice Rahul for website development."

Expected interpretation:
- customer name = Rahul
- item = website development
- quantity = null
- because the service may be ambiguous, include it in ambiguous_items
- do not select or invent a price
"""


def extract_invoice_request(
    customer_message: str,
) -> InvoiceRequest:
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not set. "
            "Add it to your environment or Streamlit secrets."
        )

    model = os.getenv(
        "GROQ_MODEL",
        "openai/gpt-oss-20b",
    )

    base_url = os.getenv(
        "GROQ_BASE_URL",
        "https://api.groq.com/openai/v1",
    )

    client = Groq(
        api_key=api_key,
        base_url=base_url,
    )

    schema = InvoiceRequest.model_json_schema()

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": customer_message,
                },
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "invoice_request",
                    "strict": True,
                    "schema": schema,
                },
            },
        )
    except Exception as exc:
        raise RuntimeError(
            "Groq AI extraction failed. "
            "Check your GROQ_API_KEY and GROQ_MODEL configuration."
        ) from exc

    content = response.choices[0].message.content

    if not content:
        raise RuntimeError(
            "The model returned no structured extraction."
        )

    try:
        parsed_data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            "The model returned invalid JSON."
        ) from exc

    try:
        return InvoiceRequest.model_validate(
            parsed_data
        )
    except Exception as exc:
        raise RuntimeError(
            "The model response could not be validated "
            "against the InvoiceRequest schema."
        ) from exc