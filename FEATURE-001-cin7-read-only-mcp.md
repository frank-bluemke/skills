# FEATURE-001 Read-Only Cin7 MCP Server

## Parent Epic

- `EPIC-001-cin7-live-query-skill.md`

## Goal

Expose a small set of Cin7 Core read-only tools through MCP so a chat agent can answer common operator questions.

## Functional Requirements

- Authenticate every request with Cin7 headers.
- Support product search and product cost lookup.
- Support inventory availability lookup.
- Support purchase search and purchase order quantity lookup.
- Support sale search and sale detail drill-down.
- Support a derived "units sold" query for a product across a date range.
- Provide a generic read-only GET escape hatch for blueprint-backed queries not yet wrapped in a dedicated tool.
- Respect Cin7 pacing and retry rules.

## Non-Functional Requirements

- Default to read-only behavior.
- Surface truncation and ambiguity rather than guessing.
- Run locally over `stdio` and optionally over HTTP for remote MCP clients.

## Downstream Impacts

- Sales aggregation can become slow on wide date ranges because Cin7 exposes line items on sale detail endpoints, not on the sale list endpoint.
- If usage grows, the next feature should add caching or narrower aggregation tools by status/date field.
