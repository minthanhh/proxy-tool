import re

HOP_BY_HOP_HEADERS = {
    "connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
    "te", "trailers", "transfer-encoding", "upgrade",
}

FORWARDED_HEADERS = {
    "x-forwarded-for", "x-forwarded-host", "x-forwarded-proto",
    "x-real-ip", "x-forwarded", "forwarded", "via",
}

VIA_PREFIX = "EasyProxy/0.1.0"


def filter_hop_by_hop(headers: dict[str, str]) -> dict[str, str]:
    result: dict[str, str] = {}
    hop_by_hop: set[str] = set()
    connection_header = headers.get("Connection", "")
    for part in re.split(r",\s*", connection_header):
        if part.strip():
            hop_by_hop.add(part.strip().lower())
    hop_by_hop.update(HOP_BY_HOP_HEADERS)
    for key, value in headers.items():
        if key.lower() not in hop_by_hop:
            result[key] = value
    return result


def sanitize_request_headers(headers: dict[str, str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for key, value in headers.items():
        key_lower = key.lower()
        if key_lower not in FORWARDED_HEADERS and key_lower not in HOP_BY_HOP_HEADERS:
            if key_lower != "connection":
                result[key] = value
    return result


def add_via_header(headers: dict[str, str]) -> dict[str, str]:
    result = dict(headers)
    existing = result.get("Via", "")
    if existing:
        result["Via"] = f"{existing}, {VIA_PREFIX}"
    else:
        result["Via"] = VIA_PREFIX
    return result


def prepare_request_headers(headers: dict[str, str]) -> dict[str, str]:
    headers = sanitize_request_headers(headers)
    headers = add_via_header(headers)
    return headers
