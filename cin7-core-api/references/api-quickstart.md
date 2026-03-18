# Cin7 Core API Quick Start

Use this file before opening the full blueprint. It captures the cross-cutting rules that matter when constructing or reviewing an integration.

## Core Request Rules

- Use base URL `https://inventory.dearsystems.com/ExternalApi/v2/`.
- Send these headers on every request:
  - `api-auth-accountid`
  - `api-auth-applicationkey`
- Send JSON only. The intro states: "The API accepts only JSON data format."
- Use `Content-type: application/json`.
- Assume the network will fail sometimes. Queue requests and retry them instead of treating the API as always reachable.

## Status Codes And Limits

- `200 OK`: success with content
- `204 No Content`: success without content
- `400 Bad Request`: validation or malformed-request failure
- `403 Forbidden`: authentication failure
- `404 Not found`: wrong endpoint path or missing resource
- `405 Not allowed`: wrong HTTP method
- `500 Internal Server Error`: parsing or server-side processing failure
- `429 Too Many Requests`: rate limit reached

The blueprint states a limit of 60 calls per minute per API application. Build pacing and backoff around that limit.

## Dates And Times

- Treat all documented date parameters and fields as UTC ISO 8601.
- The blueprint gives the format `yyyy-MM-ddTHH:mm:ss.fff`.
- Many filters use names like `ModifiedSince`, `UpdatedSince`, `UpdatedUntil`, `CreatedSince`, `FromDate`, `ToDate`, or `ShipBy`.

## Pagination Guidance

- The introduction names a short list of paginated endpoints, but many endpoint sections also expose `Page` and `Limit`.
- Trust the individual endpoint definition over the intro summary.
- When an endpoint supports pagination, expect:
  - query params like `Page` and `Limit`
  - default page size often `100`
  - max page size often `1000`
  - response metadata such as `Total` and sometimes `Page`

## Common Endpoint Shapes

- Reference and setup endpoints usually live under `/ref/...`.
- Master data commonly lives under endpoints such as:
  - `/customer`
  - `/supplier`
  - `/product`
  - `/productFamily`
- Transaction families commonly split into:
  - list/search endpoints such as `/saleList`, `/purchaseList`, `/stockTransferList`
  - base transactional endpoints such as `/sale`, `/purchase`, `/stockTransfer`
  - task detail or lifecycle subresources such as `/sale/order`, `/sale/invoice`, `/purchase/stock`, `/stockTransfer/order`
- Detail and mutation endpoints often key off `TaskID` rather than `ID`.
- Delete endpoints often use `Void={Void}`. Check the exact blueprint entry before implementing destructive actions.

## Common Query Patterns

- Incremental-sync filters:
  - `ModifiedSince`
  - `UpdatedSince`
  - `UpdatedUntil`
  - `CreatedSince`
- Include-flags on master data:
  - `IncludeDeprecated`
  - `IncludeProductPrices`
  - `IncludeBOM`
  - `IncludeSuppliers`
  - `IncludeMovements`
  - `IncludeAttachments`
  - `IncludeReorderLevels`
  - `IncludeCustomPrices`
- Search and status filters are common on list endpoints.

## Webhooks

- Webhooks are managed at `/webhooks`.
- Outbound webhook auth is separate from inbound Cin7 API auth.
- Supported outbound auth modes include `noauth`, `basicauth`, and `bearerauth`.
- The webhook section also documents retry behavior and activation limits. Read that section before implementing webhook registration or support tooling.

## Implementation Checklist

Before coding:

1. Identify the exact endpoint family in `endpoint-index.md`.
2. Open the matching section in `cin7-core-api.apib`.
3. Read the `Available fields` table and verb-specific examples.
4. Confirm the identity field used by that endpoint: `ID`, `TaskID`, `Code`, or other.
5. Confirm the response wrapper name and pagination metadata.

Before finishing:

1. Verify headers and content type.
2. Verify query parameter names and casing.
3. Verify required request fields from the table, not from guesswork.
4. Verify retry and rate-limit handling.
5. Verify date formatting and timezone behavior.
