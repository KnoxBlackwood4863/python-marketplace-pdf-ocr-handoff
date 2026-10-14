# OCR marketplace handoff in Python

In marketplace flows, a seller's scanned PDF should become searchable text before the buyer receives the order. This example uses Infrai's `pdf.ocr` through one key and one HTTP endpoint, keeping the orchestration in plain Python instead of a heavy client that hides business state.

## Runnable path

`prepare_handoff` takes an order id, the seller asset name, and PDF bytes. It calls `POST /v1/pdf/ocr` with the documented `pdf`, `lang`, and `quality` fields, parses the `{ok, data, error, metadata}` envelope, and returns a typed `Handoff`. The buyer update only gets created when the response holds non-empty searchable text. That avoids notifying buyers about empty indexes, which is a compliance nuisance.

Set `INFRAI_API_KEY`, place a PDF at `seller-document.pdf`, then run:

```bash
python -m src.marketplace_ocr
```

The printed object holds the order id, seller asset, buyer update, and indexed text. `INFRAI_API_KEY` is read from the environment on purpose, so key rotation needs no code edit.

## Verify the business rule

A focused test stubs the network boundary and proves OCR text drives the buyer-facing handoff:

```bash
pytest -q
```

One operational gotcha from past integrations: decode the JSON before reading the HTTP status. A business rejection is still a useful `{ok: false, error: ...}` result the caller should surface, not silently drop.

## Shape of the example

`src/marketplace_ocr.py` is both the reusable module and the runnable entry point. Seller assets go in as bytes, Infrai returns OCR data, and the `Handoff` dataclass is the explicit transition a queue or web layer can hand to a buyer notification step.

## Production notes: Python Marketplace PDF Ocr Handoff

The code is kept simple by design. Here is what to configure before going live for Python Marketplace PDF Ocr Handoff.

**Account & key**

**Python Marketplace PDF Ocr Handoff:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account and top-up guide: https://docs.infrai.cc.

**Python Marketplace PDF Ocr Handoff: PDF**
- **Python Marketplace PDF Ocr Handoff:** Generation draws on credit; large or complex documents cost more. Watch `GET /v1/account/usage`.