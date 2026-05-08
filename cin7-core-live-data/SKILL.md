---
name: cin7-core-live-data
description: Use live Cin7 Core data for read-only chat queries such as product cost, inventory availability, sale drill-down, purchase drill-down, units-sold lookups, and units-ordered lookups through the bundled MCP server. Trigger when the user wants current Cin7 Core answers instead of blueprint-only API planning.
---

# Cin7 Core Live Data

Use this skill when the user wants live Cin7 Core answers from chat, not just API construction guidance.

## Workflow

1. Confirm the bundled MCP server is configured with Cin7 credentials.
   - Read [references/setup-guide.md](references/setup-guide.md) if setup details are needed.

2. Use the focused live tools first.
   - `find_products` for SKU/name disambiguation
   - `get_product_cost` for cost and pricing lookups
   - `get_product_availability` for on-hand, allocated, available, on-order, and in-transit stock
   - `list_sales` and `get_sale` for sale drill-down
   - `get_units_sold` for aggregate quantity questions
   - `list_purchases`, `get_purchase`, and `get_units_ordered` for purchase-order questions

3. When the request falls outside the focused tools, use the existing `$cin7-core-api` skill and then call `raw_get`.
   - Keep the request read-only and GET-only.
   - Prefer exact blueprint-backed parameter names and casing.

4. Be explicit about what the answer means.
   - For product cost, say that the value comes from the Product `AverageCost` field unless the user asks for supplier cost.
   - For quantity questions, state whether the number is based on order, invoice, or another line source and whether credit notes were netted out.
   - For ordered-units questions, say that the current implementation aggregates `Purchase.Order.Lines` from `/purchase` and is therefore limited to simple purchases unless extended later.
   - If the server truncates a wide search window because of rate limits or sale caps, say so.

5. Stay within read-only use.
   - This bundled MCP server is intended for GET requests only.
   - Do not invent mutation support.

## Query Patterns

- Product cost and price tier questions usually map to `/product`.
- Inventory availability questions usually map to `/ref/productavailability`.
- Units-sold questions usually require `/saleList` to find candidate sales and `/sale` to inspect lines.
- Units-ordered questions usually require `/purchaseList` to find candidate purchases and `/purchase` to inspect `Order.Lines`.
- If the request needs a different resource family, use the navigation flow in `$cin7-core-api` before calling `raw_get`.

## References

- [references/setup-guide.md](references/setup-guide.md) for operator setup and client wiring
- [references/query-patterns.md](references/query-patterns.md) for request-to-tool mapping
- [$cin7-core-api](/Users/frankbluemke/.codex/skills/cin7-core-api/SKILL.md) for exact endpoint rules and blueprint-backed request shapes
