# STORY-002 Inventory Availability Lookups

## Parent Feature

- `FEATURE-001-cin7-read-only-mcp.md`

## User Story

As an operator, I want to ask chat questions about inventory availability so that I can quickly see on-hand, allocated, available, on-order, and in-transit stock by product and location.

## Acceptance Criteria

- The live Cin7 MCP server exposes a focused availability lookup tool.
- The tool uses the Product Availability endpoint at `/ref/productavailability`.
- The tool can filter by product, location, batch, and category.
- The skill documentation tells the agent to use the focused availability tool for inventory questions.

## Risks

- Availability can return multiple rows per product because the endpoint is location and batch aware.
- Name filtering on the endpoint is prefix-based, so ambiguous names should be resolved through product search first when needed.
