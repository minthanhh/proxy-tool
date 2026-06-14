import ipaddress
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class ProxyProtocol(str, Enum):
    HTTP = "http"
    HTTPS = "https"
    SOCKS5 = "socks5"


class ProxyStatus(str, Enum):
    UNTESTED = "untested"
    ALIVE = "alive"
    DEAD = "dead"


class ProxyCreate(BaseModel):
    address: str = Field(..., min_length=1, max_length=253)
    port: int = Field(..., ge=1, le=65535)
    protocol: ProxyProtocol = ProxyProtocol.HTTP
    username: Optional[str] = None
    password: Optional[str] = None
    region: Optional[str] = None
    source: str = "manual"
    residential_provider: Optional[str] = None

    @field_validator("address")
    @classmethod
    def validate_address(cls, v: str) -> str:
        try:
            ipaddress.ip_address(v)
            return v
        except ValueError:
            pass
        if not v or len(v) > 253:
            raise ValueError(f"Invalid address: {v}")
        if v.endswith("."):
            raise ValueError(f"Invalid address (trailing dot): {v}")
        labels = v.split(".")
        all_numeric = all(label.isdigit() for label in labels)
        if all_numeric:
            raise ValueError(f"Invalid address (bad IP): {v}")
        for label in labels:
            if not label or len(label) > 63:
                raise ValueError(f"Invalid address (bad label): {v}")
            if not label[0].isalnum() or not label[-1].isalnum():
                raise ValueError(f"Invalid address (label edge): {v}")
            if not all(c.isalnum() or c == "-" for c in label):
                raise ValueError(f"Invalid address (bad char): {v}")
        return v

    @field_validator("source")
    @classmethod
    def validate_source(cls, v: str) -> str:
        allowed = {"manual", "file", "api", "residential", "web"}
        if v not in allowed:
            raise ValueError(f"Invalid source: {v}. Must be one of {allowed}")
        return v


class ProxyUpdate(BaseModel):
    address: Optional[str] = None
    port: Optional[int] = Field(None, ge=1, le=65535)
    protocol: Optional[ProxyProtocol] = None
    username: Optional[str] = None
    password: Optional[str] = None
    region: Optional[str] = None
    status: Optional[ProxyStatus] = None
    latency_ms: Optional[int] = None


class ProxyResponse(BaseModel):
    id: int
    address: str
    port: int
    protocol: ProxyProtocol
    username: Optional[str] = None
    password: Optional[str] = None
    region: Optional[str] = None
    status: ProxyStatus
    latency_ms: Optional[int] = None
    last_checked_at: Optional[str] = None
    source: str
    residential_provider: Optional[str] = None
    error_count: int = 0
    success_count: int = 0
    consecutive_errors: int = 0
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}
