from io import BytesIO

import pytest
from fastapi import HTTPException, UploadFile

from app.services.storage import save_evidence


@pytest.mark.asyncio
async def test_evidence_uses_separate_50mb_limit(monkeypatch, settings, tmp_path):
    settings.evidence_dir = tmp_path
    settings.max_upload_size = 1
    settings.max_evidence_size = 50 * 1024 * 1024
    monkeypatch.setattr("app.services.storage.get_settings", lambda: settings)
    monkeypatch.setattr(
        "app.services.storage.magic.from_buffer",
        lambda *_args, **_kwargs: "image/jpeg",
    )
    file = UploadFile(filename="evidence.jpg", file=BytesIO(b"xx"))

    _, _, size = await save_evidence(file)

    assert size == 2


@pytest.mark.asyncio
async def test_multiple_evidences_are_validated_independently(monkeypatch, settings, tmp_path):
    settings.evidence_dir = tmp_path
    settings.max_evidence_size = 50 * 1024 * 1024
    monkeypatch.setattr("app.services.storage.get_settings", lambda: settings)
    monkeypatch.setattr(
        "app.services.storage.magic.from_buffer",
        lambda *_args, **_kwargs: "image/jpeg",
    )
    files = [
        UploadFile(filename=f"evidence-{index}.jpg", file=BytesIO(b"xx"))
        for index in range(3)
    ]

    results = [await save_evidence(file) for file in files]

    assert [size for _, _, size in results] == [2, 2, 2]


@pytest.mark.asyncio
async def test_evidence_over_50mb_is_rejected(monkeypatch, settings):
    settings.max_evidence_size = 50 * 1024 * 1024
    monkeypatch.setattr("app.services.storage.get_settings", lambda: settings)
    monkeypatch.setattr(
        "app.services.storage.magic.from_buffer",
        lambda *_args, **_kwargs: "image/jpeg",
    )
    file = UploadFile(
        filename="evidence.jpg",
        file=BytesIO(b"x" * (settings.max_evidence_size + 1)),
    )

    with pytest.raises(HTTPException) as exc_info:
        await save_evidence(file)

    assert exc_info.value.status_code == 413
