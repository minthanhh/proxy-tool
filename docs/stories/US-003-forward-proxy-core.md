# US-003 Forward Proxy Core

## Status

planned

## Lane

normal

## Product Contract

EasyProxy có HTTP forward proxy server chạy local port 8080, nhận request từ trình duyệt/app, forward request qua proxy IP trong pool. Cho phép bật/tắt proxy qua API.

## Relevant Product Docs

- `docs/product/easyproxy-overview.md` (section 3, 4.1)

## Acceptance Criteria

1. HTTP forward proxy server chạy trên port 8080
2. Request đến proxy được forward thành công tới đích
3. Proxy có thể bật/tắt qua API (`POST /api/v1/proxy/start`, `POST /api/v1/proxy/stop`)
4. Khi tắt, request không qua proxy nữa
5. Cấu hình system proxy tự động khi bật proxy
6. Log request method, URL, status, duration

## Design Notes

- **Implementation**: Python `asyncio` + `httpx` hoặc dùng thư viện proxy có sẵn (`mitmproxy`, custom)
- **Port**: 8080 (configurable)
- **Flow**:
  ```
  Client → localhost:8080 → EasyProxy forward → Internet
  ```
- **System proxy**: macOS `networksetup -setwebproxy`, Windows registry, Linux env
- **CONNECT method**: Hỗ trợ HTTPS tunnel
- **Logging**: Mỗi request log → `request_log` table

## Validation

| Layer | Expected proof |
|---|---|
| Unit | Test proxy server start/stop |
| Integration | curl qua proxy → ra internet được |
| E2E | Browser qua proxy load trang thành công |
