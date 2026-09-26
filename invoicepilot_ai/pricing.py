from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
import csv
import re
from difflib import SequenceMatcher


@dataclass
class ResolveResult:
    status: str
    match: dict | None = None
    options: list[dict] | None = None


class PriceCatalog:
    def __init__(self, csv_path: str):
        self.csv_path = Path(csv_path)
        self.services = self._load()

    def _load(self) -> list[dict]:
        with self.csv_path.open("r", encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))

        required = {"service_id", "service_name", "aliases", "unit_price", "active"}
        if not rows or not required.issubset(rows[0].keys()):
            raise ValueError(f"Catalog must contain columns: {sorted(required)}")

        services = []
        for row in rows:
            if str(row["active"]).strip().lower() not in {"true", "1", "yes"}:
                continue
            services.append({
                "service_id": row["service_id"].strip(),
                "service_name": row["service_name"].strip(),
                "aliases": [x.strip().lower() for x in row["aliases"].split("|") if x.strip()],
                "unit_price": Decimal(row["unit_price"].strip()),
            })
        return services

    @staticmethod
    def _normalize(text: str) -> str:
        text = text.lower().strip()
        text = re.sub(r"[^a-z0-9\s]", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text

    def resolve(self, requested_service: str) -> ResolveResult:
        query = self._normalize(requested_service)

        exact = []
        for service in self.services:
            names = [service["service_name"].lower()] + service["aliases"]
            normalized_names = [self._normalize(x) for x in names]
            if query in normalized_names:
                exact.append(service)

        if len(exact) == 1:
            return ResolveResult("MATCHED", match=exact[0])
        if len(exact) > 1:
            return ResolveResult("AMBIGUOUS", options=exact)

        scored = []
        for service in self.services:
            candidates = [service["service_name"]] + service["aliases"]
            score = max(
                SequenceMatcher(None, query, self._normalize(candidate)).ratio()
                for candidate in candidates
            )
            scored.append((score, service))

        scored.sort(key=lambda x: x[0], reverse=True)

        if not scored or scored[0][0] < 0.72:
            return ResolveResult("MISSING")

        top_score = scored[0][0]
        top = [item for score, item in scored if score >= max(0.72, top_score - 0.05)]

        if len(top) == 1 and top_score >= 0.88:
            return ResolveResult("MATCHED", match=top[0])

        return ResolveResult("AMBIGUOUS", options=top[:5])

    @staticmethod
    def format_money(value: Decimal, currency: str = "INR") -> str:
        symbols = {"INR": "₹", "USD": "$", "EUR": "€"}
        return f"{symbols.get(currency, currency + ' ')}{Decimal(value):,.2f}"
