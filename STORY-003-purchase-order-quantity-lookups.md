# STORY-003 Purchase Order Quantity Lookups

## Parent Feature

- `FEATURE-001-cin7-read-only-mcp.md`

## User Story

As an operator, I want to ask how many units of a product we ordered so that I can answer purchasing questions from chat without manually reviewing purchase orders.

## Acceptance Criteria

- The live Cin7 MCP server exposes purchase list and purchase detail tools.
- The live Cin7 MCP server exposes a focused ordered-units aggregation tool.
- The aggregation is based on purchase order lines.
- The skill documentation explains that the first implementation uses the simple purchase detail endpoint and may not cover advanced purchase flows.

## Risks

- The `/purchase` detail endpoint is documented as deprecated and limited to simple purchases.
- Advanced purchase workflows may require a separate follow-up implementation.
