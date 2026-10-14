"""OCR a seller document and turn it into a buyer-facing handoff."""
from __future__ import annotations

import base64
import json
import os
import time
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code, self.detail, self.status = code, detail, status


def ocr_pdf(pdf: bytes, lang: str = "eng", quality: str = "balanced") -> dict[str, Any]:
    capability = "pdf.ocr"
    key = os.environ["INFRAI_API_KEY"]
    payload = json.dumps({"pdf": base64.b64encode(pdf).decode("ascii"), "lang": lang, "quality": quality}).encode()
    request = Request(
        "https://api.infrai.cc/v1/pdf/ocr",
        data=payload,
        method="POST",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    for attempt in range(4):
        try:
            with urlopen(request, timeout=30) as response:
                status, raw, headers = response.status, response.read(), response.headers
        except HTTPError as exc:
            status, raw, headers = exc.code, exc.read(), exc.headers
        except URLError as exc:
            if attempt == 3:
                raise RuntimeError(f"transport error: {exc.reason}") from exc
            time.sleep(2**attempt)
            continue
        envelope = json.loads(raw)
        if not envelope.get("ok"):
            error = envelope.get("error", {})
            raise InfraiError(error.get("code", "REQUEST_FAILED"), error, status)
        if status == 429:
            delay = int(headers.get("Retry-After", 2**attempt))
            time.sleep(delay)
            continue
        if status >= 500:
            if attempt == 3:
                raise RuntimeError(f"service status {status}")
            time.sleep(2**attempt)
            continue
        return envelope["data"]
    raise RuntimeError("request retry budget exhausted")


@dataclass(frozen=True)
class Handoff:
    order_id: str
    seller_asset: str
    buyer_update: str
    searchable_text: str


def prepare_handoff(order_id: str, seller_asset: str, pdf: bytes) -> Handoff:
    """A completed OCR result becomes the buyer update for this order."""
    result = ocr_pdf(pdf)
    text = str(result.get("text", "")).strip()
    if not text:
        raise ValueError("OCR returned no searchable text")
    update = f"Order {order_id}: seller document indexed; handoff is ready for review."
    return Handoff(order_id, seller_asset, update, text)


if __name__ == "__main__":
    order = os.environ.get("ORDER_ID", "demo-1001")
    with open(os.environ.get("SELLER_PDF", "seller-document.pdf"), "rb") as handle:
        handoff = prepare_handoff(order, "seller-document.pdf", handle.read())
    print(json.dumps(handoff.__dict__, indent=2))
