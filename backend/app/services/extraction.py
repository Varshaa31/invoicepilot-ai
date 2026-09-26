import json
import logging

from groq import Groq
from pydantic import ValidationError

from app.core.config import get_settings
from app.core.exceptions import AppError
from app.schemas.common import InvoiceRequest


logger = logging.getLogger("invoicepilot.extraction")


SYSTEM_PROMPT = """
You are the structured requirement extraction engine for InvoicePilot AI.

Your ONLY job is to interpret a customer's natural-language invoice request.

Return ONLY valid JSON.

The JSON must have exactly these fields:

{
  "customer": {
    "name": "string or null",
    "email": "string or null"
  },
  "requested_items": [
    {
      "requested_service": "string",
      "quantity": "number or null"
    }
  ],
  "notes": "string or null",
  "missing_information": ["string"],
  "ambiguous_items": ["string"]
}

IMPORTANT QUANTITY RULES:

1. Extract an explicitly stated quantity for each service.

2. Understand natural-language quantity expressions.

Examples:

"3 landing pages and 2 logo designs"
→ Landing Page quantity = 3
→ Logo Design quantity = 2

"one landing page and two logo designs"
→ Landing Page quantity = 1
→ Logo Design quantity = 2

"I need one of each"
→ Every service mentioned in the request has quantity = 1.

"I need two of each"
→ Every service mentioned in the request has quantity = 2.

"I need one website and three logo designs"
→ Website quantity = 1
→ Logo Design quantity = 3

"I need both services"
→ Each previously mentioned service has quantity = 1,
unless another quantity is explicitly stated.

"three websites"
→ Website quantity = 3

"a website"
→ Website quantity = 1

"an SEO package"
→ SEO package quantity = 1

3. A singular article such as "a", "an", or "one" means quantity = 1.

4. "one of each", "one each", "one per service", or equivalent
means quantity = 1 for every requested service.

5. If a quantity genuinely cannot be determined, use null.

6. If any requested item has quantity null, include a concise
quantity-related entry in missing_information.

SERVICE RULES:

7. Extract every requested service.

8. Preserve the customer's wording in requested_service where useful.

9. Never invent a service.

10. Never invent a price.

11. Never calculate invoice totals.

12. Never determine prices from outside knowledge.

13. If a service description is vague or could reasonably refer
to multiple catalog services, include it in ambiguous_items.

14. Do NOT choose a catalog service yourself when the wording is ambiguous.

15. For example, "SEO" may be ambiguous if the catalog contains
multiple SEO services. Keep requested_service as "SEO" and add
"SEO" to ambiguous_items.

CUSTOMER INFORMATION:

16. Extract the customer name when explicitly provided.

17. Extract the customer email when explicitly provided.

18. If customer information is missing, add it to missing_information.

NOTES:

19. Notes should contain relevant customer instructions that are
not already represented by the structured customer or item fields.

20. Do not put prices, totals, catalog IDs, or currency amounts
into the extraction.

EXAMPLE 1:

Customer:
"Hi, I'm Priya from Acme Labs. Please invoice us for 3 landing pages and 2 logo designs. Send it to priya@acme.com."

Return:

{
  "customer": {
    "name": "Priya",
    "email": "priya@acme.com"
  },
  "requested_items": [
    {
      "requested_service": "landing pages",
      "quantity": 3
    },
    {
      "requested_service": "logo designs",
      "quantity": 2
    }
  ],
  "notes": null,
  "missing_information": [],
  "ambiguous_items": []
}

EXAMPLE 2:

Customer:
"Hi, I'm Rahul. My email is rahul@example.com. I need an e-commerce website and SEO optimization. I need one of each."

Return:

{
  "customer": {
    "name": "Rahul",
    "email": "rahul@example.com"
  },
  "requested_items": [
    {
      "requested_service": "e-commerce website",
      "quantity": 1
    },
    {
      "requested_service": "SEO optimization",
      "quantity": 1
    }
  ],
  "notes": null,
  "missing_information": [],
  "ambiguous_items": []
}

EXAMPLE 3:

Customer:
"Invoice Rahul for website development."

Return:

{
  "customer": {
    "name": "Rahul",
    "email": null
  },
  "requested_items": [
    {
      "requested_service": "website development",
      "quantity": null
    }
  ],
  "notes": null,
  "missing_information": [
    "customer email",
    "quantity"
  ],
  "ambiguous_items": [
    "website development"
  ]
}

EXAMPLE 4:

Customer:
"I need SEO for my business."

Return:

{
  "customer": {
    "name": null,
    "email": null
  },
  "requested_items": [
    {
      "requested_service": "SEO",
      "quantity": 1
    }
  ],
  "notes": "for my business",
  "missing_information": [
    "customer name",
    "customer email"
  ],
  "ambiguous_items": [
    "SEO"
  ]
}
"""


def extract_invoice_request(
    customer_message: str,
) -> InvoiceRequest:
    settings = get_settings()

    if not settings.groq_api_key:
        raise AppError(
            "GROQ_API_KEY is not set. Add it to the backend environment.",
            status_code=500,
            code="missing_groq_key",
        )

    if not customer_message.strip():
        raise AppError(
            "Customer message cannot be empty.",
            status_code=400,
            code="empty_customer_message",
        )

    try:
        client = Groq(
            api_key=settings.groq_api_key,
        )

        response = client.chat.completions.create(
            model=settings.groq_model,
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
                "type": "json_object",
            },
            temperature=0,
        )

    except Exception as exc:
        logger.exception(
            "Groq API request failed: %s",
            exc,
        )

        raise AppError(
            f"Groq API request failed: {exc}",
            status_code=502,
            code="groq_failure",
        ) from exc

    content = response.choices[0].message.content

    if not content:
        logger.error("Groq returned an empty response.")

        raise AppError(
            "The model returned no structured extraction.",
            status_code=502,
            code="invalid_ai_response",
        )

    logger.info(
        "Raw Groq extraction response: %s",
        content,
    )

    try:
        parsed_data = json.loads(content)
    except json.JSONDecodeError as exc:
        logger.exception(
            "Groq returned invalid JSON: %s",
            content,
        )

        raise AppError(
            "The AI response was not valid JSON.",
            status_code=502,
            code="invalid_ai_response",
        ) from exc

    try:
        parsed = InvoiceRequest.model_validate(parsed_data)
    except ValidationError as exc:
        logger.exception(
            "Groq response failed InvoiceRequest validation: %s",
            exc,
        )

        raise AppError(
            "The AI response could not be validated.",
            status_code=502,
            code="invalid_ai_response",
        ) from exc

    missing = [
        item.lower()
        for item in parsed.missing_information
    ]

    if (
        not parsed.customer.name
        and "customer name" not in missing
    ):
        parsed.missing_information.append(
            "customer name"
        )

    if (
        not parsed.customer.email
        and "customer email" not in missing
    ):
        parsed.missing_information.append(
            "customer email"
        )

    if parsed.customer.email and "@" not in parsed.customer.email:
        parsed.customer.email = None

        if "customer email" not in [
            item.lower()
            for item in parsed.missing_information
        ]:
            parsed.missing_information.append(
                "customer email"
            )

    if any(
        item.quantity is None
        for item in parsed.requested_items
    ):
        if "quantity" not in [
            item.lower()
            for item in parsed.missing_information
        ]:
            parsed.missing_information.append(
                "quantity for one or more services"
            )

    logger.info(
        "Groq extraction successful: %s item(s)",
        len(parsed.requested_items),
    )

    return parsed