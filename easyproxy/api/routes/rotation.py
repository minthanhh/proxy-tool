from fastapi import APIRouter, HTTPException, Request

router = APIRouter(tags=["rotation"])


@router.get("/api/v1/rotation-log")
async def rotation_log(
    request: Request,
    page: int = 1,
    per_page: int = 50,
):
    db = getattr(request.app.state, "db", None)
    if not db:
        raise HTTPException(status_code=503, detail="Database not available")

    offset = (page - 1) * per_page
    count_row = await db.conn.execute_fetchone("SELECT COUNT(*) FROM rotation_log")
    total = count_row[0] if count_row else 0

    rows = await db.conn.execute_fetchall(
        "SELECT * FROM rotation_log ORDER BY id DESC LIMIT ? OFFSET ?",
        (per_page, offset),
    )

    rotations = []
    for row in rows:
        d = dict(row)
        rotations.append({
            "id": d["id"],
            "timestamp": d["timestamp"],
            "reason": d["reason"],
            "trigger": d.get("trigger", "auto"),
            "from_proxy_id": d.get("from_proxy_id"),
            "from_proxy": d.get("from_proxy"),
            "to_proxy_id": d.get("to_proxy_id"),
            "to_proxy": d.get("to_proxy"),
            "retry_after_seconds": d.get("retry_after_seconds"),
            "request_url": d.get("request_url"),
            "retry_success": d.get("retry_success"),
        })

    return {"total": total, "page": page, "per_page": per_page, "rotations": rotations}
