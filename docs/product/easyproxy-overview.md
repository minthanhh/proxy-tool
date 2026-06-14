# EasyProxy — Product Contract

> Ứng dụng desktop proxy IP local, giúp chuyển đổi IP để vượt rate limit. Miễn phí, chạy local, dễ dùng.

---

## 1. Vision

EasyProxy là một ứng dụng desktop miễn phí chạy local, cho phép người dùng chuyển đổi IP một cách linh hoạt để giải quyết các vấn đề rate limit. Không cần trả phí cho VPN/proxy dịch vụ.

## 2. Target Users

| User | Problem | EasyProxy solution |
|---|---|---|
| Developer | API gọi bị rate limit (HTTP 429) | Tự động rotate IP khi detect 429 |
| Người dùng phổ thông | Cần đổi IP truy cập nội dung | Click đổi IP, system-wide proxy |

## 3. System Architecture

```
┌─────────────────────────────────────────────┐
│              User Applications               │
│  (Browser, API client, curl, v.v.)          │
└──────────────────┬──────────────────────────┘
                   │ HTTP/HTTPS
                   ▼
┌─────────────────────────────────────────────┐
│         EasyProxy System Proxy              │
│  (localhost:8080 - HTTP forward proxy)      │
├─────────────────────────────────────────────┤
│         ┌───────────────────────┐           │
│         │  Rotation Engine      │           │
│         │  - Auto-detect 429    │           │
│         │  - Manual rotate      │           │
│         │  - Schedule rotate    │           │
│         └───────┬───────┬───────┘           │
│                 │       │                    │
│         ┌───────▼──┐ ┌──▼────────┐          │
│         │ Static   │ │ Residential│          │
│         │ Proxy    │ │ Network   │          │
│         │ Pool     │ │ Provider  │          │
│         └──────────┘ └───────────┘          │
│                 │       │                    │
│         ┌───────▼───────▼───────┐           │
│         │  Local SQLite DB     │           │
│         │  (proxies, config,   │           │
│         │   stats, logs)       │           │
│         └───────────────────────┘           │
├─────────────────────────────────────────────┤
│  FastAPI Backend (Python) — localhost:8000  │
├─────────────────────────────────────────────┤
│  Electron Desktop App                       │
│  ┌──────────────────────────────────────┐   │
│  │  Nuxt UI (Vue 3)                     │   │
│  │  - Dashboard                         │   │
│  │  - Proxy manager                     │   │
│  │  - Settings                          │   │
│  │  - Stats & logs                      │   │
│  └──────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
```

### Cơ chế hoạt động

1. EasyProxy chạy local HTTP forward proxy server (port 8080)
2. Thiết lập system-wide proxy → tất cả traffic qua EasyProxy
3. Mỗi request được gửi qua một IP trong pool (theo chiến lược rotation)
4. Khi detect HTTP 429, tự động chuyển sang IP khác
5. User có thể manual rotate, xem trạng thái qua UI desktop

## 4. Functional Spec

### 4.1 Proxy Management

| Tính năng | Mô tả | Ưu tiên |
|---|---|---|
| Static proxy list | User nhập danh sách proxy (IP:port) thủ công | P1 |
| Import/Export list | Import từ file (txt, csv, json) | P1 |
| Proxy test | Kiểm tra proxy live/dead, latency | P1 |
| Proxy tagging | Gắn nhãn, nhóm proxy theo region/type | P2 |
| Residential network | Kết nối tới provider (BrightData, ProxyMesh, ...) | P1 |
| Auto-refresh pool | Tự động refresh residential IPs theo interval | P1 |

### 4.2 Rotation Engine

| Tính năng | Mô tả | Ưu tiên |
|---|---|---|
| Auto-detect 429 | Phát hiện HTTP 429 response, tự động rotate | P1 |
| Manual rotate | User bấm nút hoặc gọi CLI để đổi IP | P1 |
| Schedule rotate | Rotate theo thời gian (mỗi N phút) | P1 |
| Sticky session | Giữ nguyên IP cho một domain/session nếu không có lỗi | P1 |
| Rotation strategy | Round-robin, random, low-latency-first | P2 |
| Concurrent requests | Xử lý nhiều request qua nhiều IP cùng lúc | P2 |

### 4.3 Rate Limit Detection

| Tính năng | Mô tả | Ưu tiên |
|---|---|---|
| HTTP 429 detection | Detect status 429 + Retry-After header | P1 |
| Custom rule | User định nghĩa rule detect (status code, header, body) | P2 |
| Retry logic | Tự động retry request với IP mới | P1 |

### 4.4 Desktop App (Electron)

| Tính năng | Mô tả | Ưu tiên |
|---|---|---|
| System tray | Icon tray, on/off toggle, quick rotate | P1 |
| System proxy config | Tự động cài/gỡ proxy system-wide | P1 |
| Auto-start | Chạy cùng hệ thống | P2 |
| Dashboard UI | Xem trạng thái, stats, logs | P1 |
| Notifications | Thông báo khi rotate, lỗi, rate limit | P2 |

### 4.5 CLI

| Tính năng | Mô tả | Ưu tiên |
|---|---|---|
| `easyproxy start/stop` | Bật/tắt proxy | P1 |
| `easyproxy rotate` | Đổi IP | P1 |
| `easyproxy status` | Xem trạng thái, IP hiện tại | P1 |
| `easyproxy proxy add/list/remove` | Quản lý proxy list | P1 |
| `easyproxy logs` | Xem log | P2 |

### 4.6 Dashboard UI

| Màn hình | Mô tả |
|---|---|
| **Dashboard** | Trạng thái proxy (on/off), IP hiện tại, request count, rate limit events |
| **Proxy Manager** | Danh sách proxy, add/remove, test, import/export |
| **Residential** | Cấu hình provider, status, available IPs |
| **Settings** | Rotation strategy, schedule, system proxy, auto-start |
| **Logs** | Request log, rotation history, errors |

## 5. Tech Stack (Chi tiết)

| Layer | Technology | Version | Ghi chú |
|---|---|---|---|
| Desktop shell | Electron | latest | |
| Frontend | Nuxt 3 (Vue 3) | 3.x | `apps/easyproxy-ui/` |
| Backend | FastAPI (Python) | latest | `apps/easyproxy-api/` port 8000 |
| Proxy engine | Python (httpx) | | Forward proxy, rotation logic |
| Database | SQLite | | Via Python sqlite3 |
| Local proxy | Python (httpx + asyncio) | | HTTP forward proxy on port 8080 |
| CLI | Python (typer/click) | | Optional, built-in FastAPI |
| Packaging | PyInstaller (backend) + electron-builder (desktop) | | Bundle Python runtime |

## 6. API Design (Backend — FastAPI)

### Proxy endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Health check |
| GET | `/api/v1/proxy/status` | Trạng thái proxy (on/off, current IP, pool size) |
| POST | `/api/v1/proxy/start` | Bật proxy |
| POST | `/api/v1/proxy/stop` | Tắt proxy |
| POST | `/api/v1/proxy/rotate` | Rotate IP |
| GET | `/api/v1/proxy/logs` | Request logs |

### Proxy pool endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/pool` | Danh sách proxy trong pool |
| POST | `/api/v1/pool` | Thêm proxy |
| DELETE | `/api/v1/pool/{id}` | Xoá proxy |
| POST | `/api/v1/pool/test` | Test tất cả proxy |
| POST | `/api/v1/pool/import` | Import từ file |

### Residential network endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/residential/config` | Cấu hình provider hiện tại |
| PUT | `/api/v1/residential/config` | Cập nhật config |
| POST | `/api/v1/residential/refresh` | Refresh IP pool từ provider |

### Settings endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/settings` | Lấy settings |
| PUT | `/api/v1/settings` | Cập nhật settings |

## 7. Data Model (SQLite)

Xem `specs/data-model.md` — đầy đủ schemas, indexes, migration strategy.
Tables: `proxies`, `residential_config`, `settings`, `rotation_log`, `request_log`, `proxies_history`, `schema_version`.

## 8. Epics & Stories

### Epic 1: Foundation (P0)

| Story | Title | Mô tả |
|---|---|---|
| US-001 | Project Skeleton | Electron + Nuxt + FastAPI skeleton chạy được local |
| US-002 | Backend Foundation | FastAPI project với health endpoint, settings, DB init |
| US-003 | Forward Proxy Core | HTTP forward proxy server (port 8080) nhận request |

### Epic 2: Proxy Pool (P1)

| Story | Title | Mô tả |
|---|---|---|
| US-004 | Static Proxy CRUD | Thêm/xoá/sửa proxy list qua API + UI |
| US-005 | Proxy Import | Import proxy từ file (txt, csv, json) |
| US-006 | Proxy Health Check | Test proxy, ping, đo latency, đánh dấu alive/dead |

### Epic 3: Rotation Engine (P1)

| Story | Title | Mô tả |
|---|---|---|
| US-007 | Manual Rotation | User rotate IP bằng UI hoặc CLI |
| US-008 | Auto-detect Rate Limit | Detect HTTP 429, tự động rotate + retry |
| US-009 | Scheduled Rotation | Rotate theo interval (cấu hình được) |
| US-010 | Sticky Session | Giữ IP cho domain nếu không lỗi |

### Epic 4: Desktop App (P1)

| Story | Title | Mô tả |
|---|---|---|
| US-011 | Electron Shell | Electron app mở Nuxt UI, system tray |
| US-012 | System Proxy Config | Tự động cài/gỡ system proxy |
| US-013 | Dashboard UI | Trang dashboard: status, stats, IP hiện tại |
| US-014 | Proxy Manager UI | CRUD proxy + import + test |

### Epic 5: Residential Network (P1)

| Story | Title | Mô tả |
|---|---|---|
| US-015 | Residential Provider Integration | Kết nối tới provider API, lấy IP pool |
| US-016 | Auto-refresh Pool | Tự động refresh residential IPs |

### Epic 6: Polish (P2)

| Story | Title | Mô tả |
|---|---|---|
| US-017 | CLI Mode | easyproxy CLI commands |
| US-018 | Logs & Monitoring | Request log viewer, rotation history |
| US-019 | Notifications | OS notifications cho sự kiện quan trọng |
| US-020 | Auto-start | Chạy cùng hệ thống |

## 9. Implementation Order

```
Phase 1 (Foundation)
  US-001 → US-002 → US-003
  (Skeleton → Backend → Proxy core)

Phase 2 (Basic proxy)
  US-004 → US-005 → US-006 → US-007
  (Proxy CRUD → Import → Health → Manual rotate)

Phase 3 (Auto + Desktop)
  US-008 → US-009 → US-010 → US-011 → US-012 → US-013 → US-014
  (Auto-detect → Schedule → Sticky → Electron → System proxy → Dashboard → UI)

Phase 4 (Residential + Polish)
  US-015 → US-016 → US-017 → US-018 → US-019 → US-020
  (Residential → Auto-refresh → CLI → Logs → Notifications → Auto-start)
```

## 10. Open Decisions

1. ~~Backend stack~~ → **FastAPI (Python)** ✅ `docs/decisions/0008-fastapi-backend.md`
2. ~~Proxy routing mechanism~~ → **System-wide HTTP forward proxy** ✅ (quyết định ở trên)
3. Residential provider → Cần chọn cụ thể
4. Electron packaging: electron-builder vs electron-forge
5. Python distribution: Người dùng cài Python riêng hay bundle PyInstaller?
6. Cross-platform priority: macOS → Windows → Linux

## 11. Glossary

| Thuật ngữ | Định nghĩa |
|---|---|
| Proxy rotation | Chuyển đổi IP proxy đang dùng sang IP khác |
| Static proxy | Proxy list do user tự cấu hình (IP:port cố định) |
| Residential proxy | Proxy từ mạng residential provider, IP thật từ ISP |
| System proxy | Cài đặt proxy ở cấp hệ thống, tất cả app đều dùng |
| Rate limit detection | Phát hiện response HTTP 429 Too Many Requests |
| Sticky session | Giữ nguyên một IP cho một domain trong session |
