# 0008 FastAPI Backend for EasyProxy

Date: 2026-06-14

## Status

accepted

## Context

EasyProxy needs a backend for:
- Proxy rotation engine
- Rate limit detection
- Residential proxy network integration
- Local API for Electron/Nuxt frontend
- CLI commands

Candidates: FastAPI (Python), Axum/Actix (Rust), Express/Hono (Node.js), Nitro (Nuxt built-in).

## Decision

Use **FastAPI (Python)**.

## Rationale

1. **Speed of prototyping** — Python ecosystem cho phép viết nhanh các tính năng proxy
2. **Thư viện HTTP mạnh** — `httpx`, `aiohttp`, `requests` phù hợp cho proxy rotation
3. **Async support** — FastAPI native async, phù hợp với I/O-bound proxy workload
4. **Residential proxy integration** — hầu hết provider có Python SDK/samples
5. **Team fit** — user chọn Python backend

## Consequences

- Cần Python runtime trên máy user (hoặc bundle PyInstaller)
- Rust code (harness CLI) sẽ không tái dùng được cho EasyProxy backend
- Hiệu năng thấp hơn Rust/Go nhưng đủ cho use case proxy cá nhân
