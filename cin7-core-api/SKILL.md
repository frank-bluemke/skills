---
name: cin7-core-api
description: Build, extend, review, or debug integrations against the Cin7 Core Inventory API (formerly DEAR Systems / Dear Inventory). Use when Codex needs to construct Cin7 Core HTTP requests, choose the correct endpoint, shape JSON payloads, add authentication headers, implement pagination or retry handling, wire webhooks, or map sale, purchase, product, customer, supplier, stock, production, reference-book, or CRM resources using the bundled API blueprint.
---

# Cin7 Core API

Use this skill to turn the bundled Cin7 Core API blueprint into an implementation plan and correctly formed requests. Read the small references first, then open only the relevant slices of the full blueprint.

## Work The Blueprint

1. Identify the business object and operation.
   - Translate the request into a resource family such as product, customer, sale, purchase, stock, production, webhook, or CRM.
   - Decide whether the task is list, read, create, update, delete, or void.

2. Read [api-quickstart.md](references/api-quickstart.md).
   - Use it for the shared rules the blueprint repeats: base URL, auth headers, JSON-only requests, retries, rate limits, date format, pagination, and common endpoint shapes.

3. Find the exact section in [endpoint-index.md](references/endpoint-index.md), then inspect the matching portion of [cin7-core-api.apib](references/cin7-core-api.apib).
   - Use `rg -n "^# Group |^## .*\\[/" references/cin7-core-api.apib` to scan group and endpoint headings.
   - Use `rg -n "## Product \\[/product\\]|## Sale \\[/sale\\]|## Purchase \\[/purchase\\]" references/cin7-core-api.apib` when the business object is already known.
   - Use `rg -n "TaskID=\\{TaskID\\}|Void=\\{Void\\}|ModifiedSince|IncludeDeprecated|Available fields|### (GET|POST|PUT|DELETE)" references/cin7-core-api.apib` to find recurring implementation patterns.

4. Read only the relevant blueprint slice.
   - Capture the path, query parameters, supported verbs, field tables, request examples, response wrappers, and status-specific notes.
   - Prefer the endpoint-local definition over any higher-level summary if they conflict.
   - Do not invent fields or assume that a model from another endpoint can be reused unchanged.

5. Build the integration with Cin7-specific constraints.
   - Send `api-auth-accountid` and `api-auth-applicationkey` on every request.
   - Send JSON payloads with `Content-type: application/json`.
   - Preserve the documented path spelling and casing.
   - Queue and retry requests because the blueprint explicitly warns not to assume the API is always reachable.
   - Handle `429 Too Many Requests` with backoff and pacing.

6. Validate the integration before finishing.
   - Confirm whether the endpoint is paginated and whether the response includes `Total` and `Page`.
   - Confirm whether lookup and delete operations use `ID`, `TaskID`, `Code`, or another key.
   - Confirm whether deletion is a true delete or a void-style operation.
   - Confirm UTC ISO 8601 date handling for filters and payload fields.
   - Confirm the response wrapper names before writing parsers.

## Follow Cin7 Conventions

- Treat `/ref/...` endpoints as reference-book and setup resources.
- Treat master-data resources like `/customer`, `/supplier`, and `/product` as separate from transactional resources like `/sale`, `/purchase`, and `/stockTransfer`.
- Expect many transaction families to expose both list endpoints and task/detail subresources.
- Expect many delete operations to accept `Void={Void}` rather than silently hard-delete data.
- Use webhook docs only for outbound notification setup under `/webhooks`; they do not change the inbound API auth scheme.

## Produce High-Signal Outputs

When using this skill for a real task, return:

- the chosen endpoint and HTTP method
- the required headers, query parameters, and body shape
- the exact blueprint-backed fields that matter for the requested behavior
- pagination, retry, and rate-limit handling notes
- any remaining business questions that are not answered by the API blueprint

## References

- [api-quickstart.md](references/api-quickstart.md) for shared API rules and implementation checklist
- [endpoint-index.md](references/endpoint-index.md) for a navigation map of major resource families
- [cin7-core-api.apib](references/cin7-core-api.apib) for the full bundled Cin7 Core API blueprint
