# Hyperliquid write API notes

Relevant exchange actions from the official docs:

- `order`: place limit or trigger order
- `cancel`: cancel by oid
- `cancelByCloid`: cancel by client order id
- `scheduleCancel`: dead-man cancel
- `modify` / `batchModify`: modify existing order(s)
- `updateLeverage`: update cross or isolated leverage
- `updateIsolatedMargin`: add or remove isolated margin

This skill uses the official Python SDK rather than hand-rolling signatures.
