# EasyProxy — Feature Map

> Nhóm các tính năng theo domain, không theo phase triển khai. Mỗi feature là một đơn vị độc lập có thể breakdown tasks và implement riêng.

---

## 1. Backend Infrastructure

Backend core: database, API server, config, logging. Nền tảng cho mọi feature khác.

| Story | Title | Mô tả |
|---|---|---|
| US-001 | Project Skeleton | Python project, config, logging, DB init, CLI entrypoint |
| US-002 | Backend Foundation | FastAPI server, health endpoint, CORS, WebSocket, middleware |

**Phụ thuộc:** None
**File chính:** `easyproxy/` (core modules)

---

## 2. Proxy Core

HTTP forward proxy server — trái tim của EasyProxy. Nhận request, forward qua upstream proxy.

| Story | Title | Mô tả |
|---|---|---|
| US-003 | Forward Proxy Core | HTTP forward proxy + CONNECT tunnel trên port 8080 |

**Phụ thuộc:** Backend Infrastructure
**File chính:** `easyproxy/proxy/`

---

## 3. Proxy Pool Management

Quản lý danh sách proxy: CRUD, import/export, health check, phân loại.

| Story | Title | Mô tả |
|---|---|---|
| US-004 | Static Proxy CRUD | Thêm/xoá/sửa proxy, API + DB |
| US-005 | Proxy Import | Import từ file (TXT, CSV) |
| US-006 | Proxy Health Check | Background health check, latency, alive/dead |

**Phụ thuộc:** Backend Infrastructure
**File chính:** `easyproxy/pool/`

---

## 4. Rotation Engine

Cơ chế luân chuyển IP — linh hồn của EasyProxy.

| Story | Title | Mô tả |
|---|---|---|
| US-007 | Manual Rotation | Rotate IP theo yêu cầu, chọn proxy từ pool |
| US-008 | Auto-detect Rate Limit | Detect HTTP 429 → auto rotate → retry |
| US-009 | Scheduled Rotation | Rotate định kỳ theo interval |
| US-010 | Sticky Session | Giữ IP cho cùng domain trong session |

**Phụ thuộc:** Proxy Core + Proxy Pool Management
**File chính:** `easyproxy/rotation/`, `easyproxy/proxy/`

---

## 5. Residential Network

Kết nối tới residential proxy provider để lấy IP động.

| Story | Title | Mô tả |
|---|---|---|
| US-015 | Residential Provider Integration | BrightData, Oxylabs, Smartproxy adapters |
| US-016 | Auto-refresh Pool | Tự động refresh IP từ provider, prune dead IPs |

**Phụ thuộc:** Proxy Pool Management + Rotation Engine
**File chính:** `easyproxy/residential/`

---

## 6. Desktop Application

Electron desktop app — shell, system tray, system proxy, auto-start.

| Story | Title | Mô tả |
|---|---|---|
| US-011 | Electron Shell | Main process, window, tray, spawn Python backend |
| US-012 | System Proxy Config | Tự động cài/gỡ system-wide proxy (macOS/Win/Linux) |
| US-020 | Auto-start | Khởi động cùng hệ thống |

**Phụ thuộc:** Backend Infrastructure
**File chính:** `electron/`

---

## 7. User Interface

Giao diện người dùng — Nuxt 3 (Vue 3) pages và components.

| Story | Title | Mô tả |
|---|---|---|
| US-013 | Dashboard UI | Trạng thái proxy, stats, quick actions |
| US-014 | Proxy Manager UI | CRUD proxy table, import modal, test |
| US-018 | Logs & Monitoring | Request logs, rotation history, export |

**Phụ thuộc:** Backend Infrastructure + Desktop Application
**File chính:** `packages/ui/components/`

---

## 8. CLI Mode

Command-line interface — chạy không cần Electron.

| Story | Title | Mô tả |
|---|---|---|
| US-017 | CLI Mode | `easyproxy start/stop/status/pool/rotate` |

**Phụ thuộc:** Backend Infrastructure + Proxy Core + Proxy Pool
**File chính:** `easyproxy/cli/`

---

## 9. Notification System

Thông báo khi có sự kiện quan trọng.

| Story | Title | Mô tả |
|---|---|---|
| US-019 | Notifications | OS notification + in-app toast |

**Phụ thuộc:** Desktop Application + Rotation Engine
**File chính:** `electron/notifications.js`, `packages/ui/components/`

---

## Feature Dependency Graph

```
Backend Infrastructure
  ├── Proxy Core ──────────────────────────────┐
  │     ├── Proxy Pool Management              │
  │     │     ├── Residential Network           │
  │     │     └── Rotation Engine ──────────────┤
  │     │           ├── Notification System     │
  │     │           └── (uses Proxy Core)       │
  │     └── CLI Mode (uses Proxy Core + Pool)   │
  ├── Desktop Application                       │
  │     ├── User Interface (Dashboard, Proxy,   │
  │     │    Logs)                            ←─┘
  │     ├── Notification System (native)
  │     └── (spawns Python backend)
  └── CLI Mode (can run standalone)
```

## Implementation Order (theo feature)

Dựa trên feature dependencies, thứ tự triển khai hợp lý:

```
Feature 1: Backend Infrastructure ─── US-001, US-002
     │
Feature 2: Proxy Core ─────────────── US-003
     │
Feature 3: Proxy Pool Management ──── US-004, US-005, US-006
     │
Feature 4: Rotation Engine ────────── US-007, US-008, US-009, US-010
     │
Feature 5: Desktop Application ────── US-011, US-012, US-020
     │
Feature 6: User Interface ─────────── US-013, US-014, US-018
     │
Feature 7: Residential Network ────── US-015, US-016
     │
Feature 8: CLI Mode ───────────────── US-017
     │
Feature 9: Notification System ────── US-019
```

> **Ghi chú:** Feature 2 (Proxy Core) và Feature 3 (Proxy Pool) có thể làm song song sau Feature 1.

## Feature → Tasks Breakdown Template

Mỗi feature khi breakdown tasks sẽ theo cấu trúc:

```
## Feature: [Tên]
### Story: US-XXX
#### Tasks:
  - [ ] Task 1: Mô tả (file: ..., effort: S/M/L)
  - [ ] Task 2: Mô tả (file: ..., effort: S/M/L)
#### Acceptance Criteria:
  - [ ] AC 1
  - [ ] AC 2
#### Files affected:
  - path/to/file.py
  - path/to/test.py
```
