# US-002 Backend Foundation (FastAPI)

## Status

planned

## Lane

normal

## Product Contract

FastAPI backend chạy được local, có:
- Health endpoint `/health`
- Settings CRUD (read/write từ SQLite)
- DB migration tự động khi start
- CORS cho phép Nuxt frontend gọi API

## Relevant Product Docs

- `docs/product/easyproxy-overview.md` (section 6, 7)

## Acceptance Criteria

1. `uvicorn apps.easyproxy_api.main:app` chạy được, port 8000
2. `GET /health` trả về `{"status": "ok"}`
3. SQLite database tự động tạo tables khi start
4. CORS mở cho `localhost:3002` (Nuxt dev server)
5. Settings API hoạt động: `GET/PUT /api/v1/settings`
6. Có `requirements.txt` hoặc `pyproject.toml`

## Design Notes

- **Project structure**: `apps/easyproxy-api/`
- **Entry point**: `main.py` với FastAPI app
- **Database**: SQLite via `sqlite3` (standard library)
- **DB init**: Auto-create tables on startup event
- **Settings**: Simple key-value table, cached in memory
- **CORS**: `fastapi.middleware.cors` allow `localhost:3002`

## Validation

| Layer | Expected proof |
|---|---|
| Unit | Test health endpoint |
| Integration | Settings write → read round-trip |
| E2E | Frontend gọi được backend API |
