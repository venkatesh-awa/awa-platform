from __future__ import annotations

import json

import pytest

from services.bid_service import parse_bid_envelope
from services.exceptions import MalformedBidEvent


def _valid_envelope() -> dict:
    return {
        "bid_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "auction_id": "3fa85f64-5717-4562-b3fc-2c963f66afa7",
        "bidder_id": "3fa85f64-5717-4562-b3fc-2c963f66afa8",
        "amount": "1500.00",
        "submitted_at": "2026-07-03T10:00:00+00:00",
    }


def test_parse_valid_envelope() -> None:
    raw = json.dumps(_valid_envelope()).encode("utf-8")
    parsed = parse_bid_envelope(raw)
    assert parsed["auction_id"] == "3fa85f64-5717-4562-b3fc-2c963f66afa7"


def test_parse_rejects_invalid_json() -> None:
    with pytest.raises(MalformedBidEvent, match="invalid JSON"):
        parse_bid_envelope(b"{not-json")


def test_parse_rejects_missing_fields() -> None:
    envelope = _valid_envelope()
    del envelope["amount"]
    raw = json.dumps(envelope).encode("utf-8")

    with pytest.raises(MalformedBidEvent, match="missing fields"):
        parse_bid_envelope(raw)


def test_parse_rejects_non_numeric_amount() -> None:
    envelope = _valid_envelope()
    envelope["amount"] = "not-a-number"
    raw = json.dumps(envelope).encode("utf-8")

    with pytest.raises(MalformedBidEvent, match="invalid amount"):
        parse_bid_envelope(raw)


def test_parse_rejects_malformed_uuid() -> None:
    envelope = _valid_envelope()
    envelope["auction_id"] = "not-a-uuid"
    raw = json.dumps(envelope).encode("utf-8")

    with pytest.raises(MalformedBidEvent, match="invalid UUID"):
        parse_bid_envelope(raw)
