import base64
import json
from unittest.mock import patch

from src.marketplace_ocr import ocr_pdf, prepare_handoff


def test_handoff_publishes_buyer_update_after_searchable_text_exists():
    with patch("src.marketplace_ocr.ocr_pdf", return_value={"text": "SKU 42\nship Friday"}):
        handoff = prepare_handoff("ord-7", "invoice.pdf", b"pdf bytes")
    assert handoff.searchable_text == "SKU 42\nship Friday"
    assert handoff.buyer_update.startswith("Order ord-7:")


def test_ocr_sends_pdf_as_base64():
    class Response:
        status = 200
        headers = {}

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return None

        def read(self):
            return b'{"ok": true, "data": {"text": "readable"}}'

    pdf = b"%PDF-1.4\x00\xff"
    with patch.dict("src.marketplace_ocr.os.environ", {"INFRAI_API_KEY": "test-key"}):
        with patch("src.marketplace_ocr.urlopen", return_value=Response()) as send:
            assert ocr_pdf(pdf) == {"text": "readable"}
    payload = json.loads(send.call_args.args[0].data)
    assert base64.b64decode(payload["pdf"], validate=True) == pdf
    assert set(payload) == {"pdf", "lang", "quality"}
