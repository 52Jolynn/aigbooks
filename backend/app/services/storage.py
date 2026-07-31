"""文件存储服务：封面 + 证据。"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import magic
from fastapi import HTTPException, UploadFile

from app.config import get_settings

_MIME_EXT_MAP = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "video/mp4": ".mp4",
}

_COVER_EXT_BY_MIME = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


async def save_cover(file: UploadFile, isbn: str) -> str:
    """保存封面：先用 python-magic 嗅探真实 MIME，再校验白名单。"""
    settings = get_settings()

    head = await file.read(2048)
    await file.seek(0)

    try:
        mime = magic.from_buffer(head, mime=True)
    except Exception as e:
        raise HTTPException(
            status_code=415,
            detail={"code": 415, "msg": f"无法识别文件类型: {e}"},
        ) from e

    ext = _COVER_EXT_BY_MIME.get(mime)
    if not ext:
        raise HTTPException(
            status_code=415,
            detail={"code": 415, "msg": f"封面格式不支持: {mime}"},
        )

    target = settings.covers_dir / f"{isbn}{ext}"
    target.parent.mkdir(parents=True, exist_ok=True)

    content = await file.read()
    if len(content) > settings.max_upload_size:
        raise HTTPException(status_code=413, detail={"code": 413, "msg": "封面文件过大"})
    target.write_bytes(content)
    return f"{isbn}{ext}"


async def save_evidence(file: UploadFile) -> tuple[str, str, int]:
    """保存证据文件，返回 (相对路径, mime_type, size_bytes)。

    使用 python-magic 嗅探真实 MIME 类型（避免依赖客户端 Content-Type 欺骗）。
    """
    settings = get_settings()
    head = await file.read(2048)
    await file.seek(0)
    mime = magic.from_buffer(head, mime=True)
    if mime not in settings.allowed_mime_types:
        raise HTTPException(
            status_code=415,
            detail={"code": 415, "msg": f"证据格式不支持: {mime}"},
        )

    content = await file.read()
    if len(content) > settings.max_upload_size:
        raise HTTPException(status_code=413, detail={"code": 413, "msg": "证据文件过大"})

    ext = _MIME_EXT_MAP.get(mime, ".bin")
    now = datetime.now(timezone.utc)
    rel = f"{now.year:04d}/{now.month:02d}/{uuid.uuid4().hex}{ext}"
    target = settings.evidence_dir / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)
    return rel, mime, len(content)
