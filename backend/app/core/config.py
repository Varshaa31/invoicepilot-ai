from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = (
        "postgresql+pg8000://invoicepilot:invoicepilot"
        "@localhost:5432/invoicepilot"
    )

    # Groq AI configuration
    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-20b"
    groq_base_url: str = "https://api.groq.com/openai/v1"

    # Authentication
    jwt_secret: str = "change-this-development-secret"

    cors_origins: str = "http://localhost:3000"

    company_name: str = "InvoicePilot AI"
    company_email: str = "billing@invoicepilot.demo"
    company_address: str = "Bengaluru, India"
    company_payment_info: str = (
        "Bank transfer · A/C InvoicePilot AI · IFSC DEMO0001234"
    )

    default_tax_rate: str = "18"
    default_currency: str = "INR"

    @property
    def cors_origin_list(self) -> list[str]:
        return [
            item.strip()
            for item in self.cors_origins.split(",")
            if item.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()