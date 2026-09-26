import logging

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.router import api_router
from app.core.config import get_settings
from app.core.exceptions import (
    AppError,
    app_error_handler,
    http_error_handler,
    unhandled_error_handler,
    validation_error_handler,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

settings = get_settings()

app = FastAPI(
    title="InvoicePilot AI",
    description="AI extracts intent. The catalog prices. The backend calculates. A human approves.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list or ["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)
app.add_exception_handler(StarletteHTTPException, http_error_handler)
app.add_exception_handler(Exception, unhandled_error_handler)
app.include_router(api_router)


@app.get("/")
def root():
    return {
        "name": "InvoicePilot AI",
        "tagline": "Turn customer messages into verified invoices.",
        "docs": "/docs",
    }
