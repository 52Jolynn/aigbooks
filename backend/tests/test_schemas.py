"""Pydantic 模型验证测试（纯逻辑，不需 DB）。"""

import pytest
from pydantic import ValidationError

from app.schemas import VoteCreate


def test_vote_create_accepts_upvote():
    v = VoteCreate(vote_type=1, fingerprint="abcdef1234567890")
    assert v.vote_type == 1


def test_vote_create_accepts_downvote():
    v = VoteCreate(vote_type=-1, fingerprint="abcdef1234567890")
    assert v.vote_type == -1


def test_vote_create_rejects_zero():
    with pytest.raises(ValidationError):
        VoteCreate(vote_type=0, fingerprint="abcdef1234567890")


def test_vote_create_rejects_too_long_fingerprint():
    with pytest.raises(ValidationError):
        VoteCreate(vote_type=1, fingerprint="a" * 200)


def test_vote_create_rejects_short_fingerprint():
    with pytest.raises(ValidationError):
        VoteCreate(vote_type=1, fingerprint="short")
