# US-001 EasyProxy Project Skeleton

## Status

planned

## Lane

normal

## Product Contract

EasyProxy có project skeleton hoàn chỉnh: Electron + Nuxt (frontend) + FastAPI (backend) chạy được local, kết nối được cơ bản.

## Relevant Product Docs

- `docs/product/easyproxy-overview.md`

## Acceptance Criteria

1. Nuxt app chạy được với `pnpm dev`, hiển thị trang chủ EasyProxy
2. FastAPI backend chạy được với `uvicorn`, có health endpoint `/health`
3. Electron app mở được cửa sổ hiển thị Nuxt UI
4. Frontend gọi được API health từ backend
5. Có `README.md` hướng dẫn chạy dev

## Design Notes

- **Frontend**: `apps/easyproxy-ui/` — Nuxt 3 app (Vue 3), port 3002
- **Backend**: `apps/easyproxy-api/` — FastAPI Python project, port 8000
- **Electron**: `apps/easyproxy-desktop/` — Electron shell wrapping Nuxt build
- **Communication**: Frontend gọi backend qua `fetch` tới `http://localhost:8000`
- **Monorepo**: Đặt trong `apps/` của Turborepo hiện tại

## Validation

| Layer | Expected proof |
|---|---|
| Unit | FastAPI health test |
| Integration | Frontend → backend health check |
| E2E | Electron window mở được UI |
| Platform | Chạy được trên macOS (trước), Windows/Linux sau |

## Harness Delta

- [x] Intake #2 recorded
- [x] Product doc created

## Backend choice decision

FastAPI (Python) vì:
- Dễ viết prototype nhanh
- Nhiều thư viện HTTP/proxy (`httpx`, `aiohttp`)
- Async support mạnh cho proxy rotation
