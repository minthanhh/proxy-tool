# EasyProxy — Tài liệu đặc tả kỹ thuật

> **EasyProxy** — Proxy IP desktop app giúp luân chuyển IP tự động để vượt qua rate limit.

## Danh sách file spec

| # | File | Mô tả |
|---|------|-------|
| 1 | `overview.md` | Tổng quan sản phẩm — tầm nhìn, vấn đề, người dùng mục tiêu, tính năng cốt lõi |
| 2 | `architecture.md` | Kiến trúc hệ thống — components, data flow, startup sequence, communication patterns |
| 3 | `api-specs.md` | Đặc tả API — REST endpoints, WebSocket, request/response schema, error codes |
| 4 | `proxy-engine.md` | Core proxy engine — HTTP forward proxy, CONNECT tunnel, rotation, rate limit detection |
| 5 | `ui-specs.md` | Đặc tả UI/UX — screens, user flows, component tree, design principles |
| 6 | `data-model.md` | Database schema — SQLite tables, columns, indexes, migration strategy |
| 7 | `implementation.md` | Kế hoạch triển khai — phases, user stories, dependency graph, acceptance criteria |
| 8 | `feature-map.md` | Feature map — nhóm features, dependency graph, template breakdown tasks |

## Tech stack

| Layer | Công nghệ |
|-------|-----------|
| Desktop shell | Electron |
| Frontend | Nuxt 3 (Vue 3, TypeScript) |
| Backend | FastAPI[standard] (Python 3.11+) — includes uvicorn |
| Database | SQLite (via aiosqlite) |
| Proxy engine | Python `asyncio` + `aiohttp` |
| Virtual env | `python3 -m venv .venv` |
| Package mgmt | `pip install -r requirements.txt` |

## Quy ước trong spec

- **US-XXX**: User story identifier
- `[x]`: acceptance criterion
- `S/M/L`: estimated effort (Small/Medium/Large)
- All technical content viết bằng tiếng Anh; overview và titles dùng tiếng Việt
