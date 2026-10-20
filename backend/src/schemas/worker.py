from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class BankDetails(BaseModel):
    account_holder_name: Optional[str] = Field(default=None, min_length=2, max_length=150)
    bank_name: Optional[str] = Field(default=None, min_length=2, max_length=150)
    account_number: Optional[str] = Field(default=None, min_length=6, max_length=34)
    ifsc_code: Optional[str] = Field(default=None, min_length=4, max_length=20)

    @field_validator("account_number")
    @classmethod
    def validate_account_number(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        normalized = "".join(ch for ch in value if ch.isdigit())
        if not normalized:
            raise ValueError("Account number must contain digits")
        return normalized

    @field_validator("ifsc_code")
    @classmethod
    def normalize_ifsc(cls, value: Optional[str]) -> Optional[str]:
        return value.upper().strip() if value else value


class AddressDetails(BaseModel):
    line1: Optional[str] = Field(default=None, max_length=255)
    line2: Optional[str] = Field(default=None, max_length=255)
    city: Optional[str] = Field(default=None, max_length=100)
    state: Optional[str] = Field(default=None, max_length=100)
    postal_code: Optional[str] = Field(default=None, max_length=20)


class WorkerCreateRequest(BaseModel):
    worker_code: str = Field(min_length=2, max_length=50)
    name: str = Field(min_length=2, max_length=160)
    mobile: Optional[str] = Field(default=None, max_length=20)
    aadhaar: Optional[str] = Field(default=None, min_length=12, max_length=12)
    address: AddressDetails = Field(default_factory=AddressDetails)
    trade: Optional[str] = Field(default=None, max_length=80)
    daily_wage: Decimal = Field(ge=0, decimal_places=2, max_digits=12)
    pf_rate_percent: Decimal = Field(default=Decimal("0.00"), ge=0, le=100, decimal_places=2, max_digits=5)
    joining_date: date
    assigned_site_id: Optional[str] = None
    bank_details: BankDetails = Field(default_factory=BankDetails)

    @field_validator("worker_code")
    @classmethod
    def normalize_worker_code(cls, value: str) -> str:
        return value.strip().upper()

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        return " ".join(value.strip().split())

    @field_validator("mobile")
    @classmethod
    def validate_mobile(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        normalized = "".join(ch for ch in value if ch.isdigit())
        if len(normalized) != 10:
            raise ValueError("Mobile number must contain exactly 10 digits")
        return normalized

    @field_validator("aadhaar")
    @classmethod
    def validate_aadhaar(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        normalized = "".join(ch for ch in value if ch.isdigit())
        if len(normalized) != 12:
            raise ValueError("Aadhaar number must contain exactly 12 digits")
        return normalized


class WorkerUpdateRequest(BaseModel):
    worker_code: Optional[str] = Field(default=None, min_length=2, max_length=50)
    name: Optional[str] = Field(default=None, min_length=2, max_length=160)
    mobile: Optional[str] = Field(default=None, max_length=20)
    aadhaar: Optional[str] = Field(default=None, min_length=12, max_length=12)
    address: Optional[AddressDetails] = None
    trade: Optional[str] = Field(default=None, max_length=80)
    daily_wage: Optional[Decimal] = Field(default=None, ge=0, decimal_places=2, max_digits=12)
    pf_rate_percent: Optional[Decimal] = Field(default=None, ge=0, le=100, decimal_places=2, max_digits=5)
    joining_date: Optional[date] = None
    assigned_site_id: Optional[str] = None
    bank_details: Optional[BankDetails] = None
    status: Optional[str] = Field(default=None, max_length=20)

    @field_validator("worker_code")
    @classmethod
    def normalize_worker_code(cls, value: Optional[str]) -> Optional[str]:
        return value.strip().upper() if value else value

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: Optional[str]) -> Optional[str]:
        return " ".join(value.strip().split()) if value else value

    @field_validator("mobile")
    @classmethod
    def validate_mobile(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        normalized = "".join(ch for ch in value if ch.isdigit())
        if len(normalized) != 10:
            raise ValueError("Mobile number must contain exactly 10 digits")
        return normalized

    @field_validator("aadhaar")
    @classmethod
    def validate_aadhaar(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        normalized = "".join(ch for ch in value if ch.isdigit())
        if len(normalized) != 12:
            raise ValueError("Aadhaar number must contain exactly 12 digits")
        return normalized

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        normalized = value.strip().lower()
        allowed = {"active", "inactive", "exited"}
        if normalized not in allowed:
            raise ValueError(f"Status must be one of: {', '.join(sorted(allowed))}")
        return normalized


class WorkerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    worker_code: str
    name: str
    mobile: Optional[str]
    aadhaar: Optional[str]
    address: AddressDetails
    trade: Optional[str]
    daily_wage: Decimal
    pf_rate_percent: Decimal
    joining_date: date
    assigned_site_id: Optional[str]
    assigned_site_name: Optional[str]
    bank_details: BankDetails
    status: str
    advance_count: int = 0
    advance_total: Decimal = Decimal("0.00")
    last_advance_date: Optional[date] = None
    last_advance_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class WorkerListResponse(BaseModel):
    items: list[WorkerResponse]
    page: int
    page_size: int
    total: int
    total_pages: int
